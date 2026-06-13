---
name: pr-watch-fix
description: Watch the GitHub PR for the current branch, wait for CI to finish, and autonomously fix failing jobs by reading logs, editing sources, and pushing. Stops cleanly when stuck.
allowed-tools: Bash Read Grep Glob Edit Write AskUserQuestion
user-invocable: true
model: sonnet
---

Watch the open PR for the current branch, wait for CI, and fix failures.

This repo's CI (see `.github/workflows/`):

- **`build`** — a Python 3.10–3.14 matrix that runs `make check-codestyle`, `make check-safety`, and `make test` (Poetry-based). No Docker.
- **`MegaLinter`** — the python-flavor MegaLinter action with `APPLY_FIXES_MODE: commit`, so when it finds auto-fixable issues it pushes a `[MegaLinter] Apply linters fixes` commit **directly onto the PR branch** (handled in step 7).

> **Delegation hint** — to gather CI status and failure excerpts cheaply, delegate the polling/log-fetch step to the `pr-monitor` agent. Use it instead of running `gh pr checks` + log-fetch loops directly from this skill. Reserve this skill's main loop (sonnet) for deciding fixes, editing code, and pushing.

## Loop

Repeat until the PR is fully green or you stop intentionally:

### 0. Stop any prior PR-watch Monitor

Before doing anything else, cancel a previous run's still-running poller. Re-invoking `/pr-watch-fix` always wins — the new run resets state.

Use `TaskList` to find Monitors whose description starts with `PR watch:` (the convention used by step 3) and call `TaskStop` on each. Do not stop tasks that don't start with this prefix — they belong to other work.

### 1. Find the PR

```bash
BRANCH="$(git branch --show-current)"
PR_JSON="$(gh pr list --head "$BRANCH" --state open --json number,url,headRefOid --limit 1)"
PR_NUMBER="$(printf '%s' "$PR_JSON" | jq -r '.[0].number // empty')"
```

- If `PR_NUMBER` is empty → **STOP**. Tell the user there is no open PR for the branch.
- Save the PR URL for reporting and the `headRefOid` so you can detect when a new push lands.

### 2. Inspect CI state

```bash
gh pr checks "$PR_NUMBER" --json name,bucket,state,workflow,link
```

Classify each check by `bucket`/`state`:

- `pass` → success
- `fail`, `cancel`, `skipping` → failure (treat `skipping` as success if the user wants — default: only `fail` and `cancel` count as failures)
- `pending`, `in_progress`, `queued`, `waiting`, `requested` → still running

Decide:

- **All `pass`** → **STOP**. Report success and the PR URL.
- **Any failure** → go to step 4 (fix).
- **No failure but some running** → go to step 3 (wait).

### 3. Wait for running jobs

Poll every **5 minutes**, fixed interval. No backoff — the user explicitly wants a 5-minute cadence so failures surface fast. Use a persistent `Monitor` with a description that starts with `PR watch:` so step 0 of a future invocation can find and stop it.

Example:

```yaml
Monitor:
  description: "PR watch: PR #42 CI"
  persistent: true
  command: |
    while true; do
      state="$(gh pr checks 42 --json name,bucket 2>/dev/null || echo '[]')"
      counts="$(jq -r '[.[] | .bucket] | group_by(.) | map("\(.[0])=\(length)") | join(" ")' <<<"$state")"
      pending="$(jq -r '[.[] | select(.bucket=="pending")] | length' <<<"$state")"
      fail_now="$(jq -r '[.[] | select(.bucket=="fail" or .bucket=="cancel") | .name] | sort | join(",")' <<<"$state")"

      # Emit on new failures
      if [ -n "$fail_now" ] && [ "$fail_now" != "${prev_fail:-}" ]; then
        echo "[failures] $fail_now ($counts)"
        prev_fail="$fail_now"
      fi

      # Done condition: nothing pending
      if [ "$pending" = "0" ]; then
        echo "[final] $counts"
        break
      fi
      sleep 300
    done
```

The monitor emits notifications only on state changes (new failures or completion). It does not emit a notification every 5 minutes — that would be noise. If the user wants a heartbeat, they can ask.

If the same check has been pending for more than **90 minutes total** without a state change, the monitor must emit a `[stalled]` event and the agent should **ask the user** whether to keep waiting.

Do not poll faster than 5 minutes — it wastes API quota and produces no signal.

### 4. Collect logs from failing jobs

For each failing check, get its run ID:

```bash
RUN_ID="$(gh pr checks "$PR_NUMBER" --json name,bucket,link \
  | jq -r '.[] | select(.bucket=="fail") | .link' \
  | sed 's|.*/runs/||; s|/job/.*||' | head -1)"
gh run view "$RUN_ID" --log-failed > /tmp/pr-watch-fail.log
```

Then read the tail of `/tmp/pr-watch-fail.log` and grep for the first concrete error. By job:

- **`build` (python matrix)** — look for: black/isort diff (`would reformat`), `darglint` complaints, `mypy` `error:` lines with `file:line`, `safety`/`bandit` findings, or a `pytest` `FAILED`/assertion frame. The same fix usually clears all matrix Python versions at once — treat a failure that's identical across versions as **one** fix.
- **`MegaLinter`** — see the blocking-vs-warning note below.

Don't read the whole log if it's huge — find the actionable line. If multiple jobs fail with **different** errors, handle them in this order: build/install failures → test failures → lint/style failures → flaky/intermittent. Group jobs that fail with the **same** error and treat them as one fix.

**For the MegaLinter job specifically: only act on linters MegaLinter marks as ❌ (blocking).** MegaLinter prints a per-linter summary like `✅ Linted [X] files with [linter] successfully`, `⚠️ Linted [X] files with [linter]: Found N non blocking error(s)`, or `❌ Linted [X] files with [linter]: Found N error(s)`. The individual log lines from a warning linter still say `error` next to each finding, but those findings do **not** fail the build — fixing them is wasted churn. Filter the log to lines containing `❌ Linted` first, then collect per-file errors only from those linters. Example:

```bash
# Identify failing (blocking) linters from MegaLinter's own verdict
grep '❌ Linted' /tmp/pr-watch-fail.log
# Then pull per-file errors only from those linters
```

Note: because this repo runs MegaLinter with `APPLY_FIXES_MODE: commit`, auto-fixable style issues are usually fixed by the bot itself (step 7) rather than failing the job — the ❌ linters you see are the ones needing a manual code change.

### 5. Decide if you can fix it

Apply the **"can I fix this cleanly?"** test before editing:

- Is the cause clear from the log? (style diff with file/line, mypy error with file/line, test assertion with expected/actual, lint rule with location)
- Is the fix local to one or two files?
- Is the fix one of this repo's standard patterns? (run `make codestyle` to auto-apply pyupgrade+black, a small `mypy` type annotation, a test/fixture correction, a dependency pin in `pyproject.toml`)
- Have you already attempted this same fix and seen it fail? (track attempts in your task list — if the same error returns after a push, that's a strong signal you don't understand it)

If **any** answer is "no", **ASK THE USER** via `AskUserQuestion` instead of guessing:

- Show the failing job name, the key error line, and your hypothesis
- Offer 2-3 options when there are real alternatives
- Offer "stop and let me investigate" as an option when the cause is ambiguous

Specifically **STOP and ask** when:

- The error mentions an external service outage, rate limit, registry timeout, or "resource temporarily unavailable" (likely flake — pushing won't help). Note: `tests/test_gh_dependents_info/` hits the **live** GitHub dependents pages and is known to be slow/flaky; a network failure there is usually not a code bug.
- The same error appears after your previous fix push (your model of the bug is wrong)
- The fix would touch a **generated** file (`requirements.txt`, `assets/images/coverage.svg`, or the README block between `<!-- gh-dependents-info-used-by-start -->` and `<!-- gh-dependents-info-used-by-end -->`) — regenerate it from its source instead (see step 6)
- The fix would require destructive git operations (force-push, branch rewrite, deletion)
- More than **3** fix-push cycles have run without turning any check from fail → pass
- A failure is in a workflow you don't recognize and can't trace to a source file

### 6. Apply the fix

- Edit the source (Python in `github_dependents_info/`, tests/fixtures in `tests/`, config in `pyproject.toml`, workflows in `.github/workflows/`).
- For style/format failures, run `make codestyle` (pyupgrade + black) to auto-apply fixes rather than hand-editing — then `make check-codestyle` to confirm. (Makefile is bash-only; on Windows run via Git Bash/WSL or invoke the underlying `poetry run black ...` / `poetry run pyupgrade ...` directly.)
- **Never hand-edit generated files.** Regenerate instead:
  - `requirements.txt` → produced by `make install` (poetry lock + export)
  - `assets/images/coverage.svg` → regenerated by `make test`
  - README "Used by" block → produced by the tool itself, not edited manually
- Run any obvious local validation that doesn't require network: `make check-codestyle`, `make mypy`, `python -m py_compile <file>`, and the offline CLI tests `poetry run pytest tests/test_cli.py`. Avoid running `tests/test_gh_dependents_info/` locally just to validate a fix — it needs live GitHub access and is slow/flaky.
- Do **not** introduce defensive hacks (skip-on-fail, retries, `|| true`, `# type: ignore` without cause) just to make CI green — fix the root cause.

### 7. Commit & push

```bash
git status --short
git add <specific files>      # never `git add -A`
git commit -m "$(cat <<'EOF'
:wrench: Fix CI: <one-line summary of the failure>

<optional 1-2 line body if non-obvious>

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

This repo uses **gitmoji** commit prefixes (`:wrench:`, `:bug:`, `:arrow_up:`, `:white_check_mark:`, …) — pick the one matching the fix and follow recent `git log` style.

**Before pushing, reconcile with origin.** This repo's MegaLinter workflow (`APPLY_FIXES_MODE: commit`) pushes commits titled `[MegaLinter] Apply linters fixes` onto the PR branch. Detect and handle:

```bash
git fetch origin "$BRANCH"
NEW_REMOTE_COMMITS="$(git log --format='%s' HEAD..origin/"$BRANCH")"

if printf '%s\n' "$NEW_REMOTE_COMMITS" | grep -q '^\[MegaLinter\] Apply linters fixes'; then
    # Auto-fix bot pushed — try to rebase onto it (keeps the bot's fixes)
    if git pull --rebase origin "$BRANCH"; then
        # Amend the bot commit to add an emoji prefix, then push to re-trigger workflows
        _amend_megalinter_bot_commit_and_push "$BRANCH"
    else
        # Rebase failed with conflicts — abort and force-push our commit
        git rebase --abort
        git push --force-with-lease
    fi
else
    git push
fi
```

**Amend the MegaLinter bot commit with an emoji** to re-trigger CI workflows. The auto-fix commit often lands without triggering all required checks; amending its subject line forces a new workflow run:

```bash
_amend_megalinter_bot_commit_and_push() {
    local branch="$1"
    local orig_msg
    orig_msg="$(git log -1 --format='%s')"
    # Only amend if it's the bot commit (idempotent — skip if emoji already present)
    if printf '%s' "$orig_msg" | grep -q '^\[MegaLinter\]' && ! printf '%s' "$orig_msg" | grep -qP '^[\x{1F300}-\x{1FFFF}]'; then
        git commit --amend -m "$(printf '🤖 %s\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>' "$orig_msg")"
        git push --force-with-lease
    else
        git push
    fi
}
```

Notes:

- `--force-with-lease` (not `--force`) so we refuse to overwrite anything we haven't seen, except the bot commit we just observed
- This is the **only** authorized force-push path. Any other force-push needs explicit user permission
- If `NEW_REMOTE_COMMITS` contains commits that are **not** from the MegaLinter bot, **STOP** and ask the user — someone else pushed work, don't silently overwrite
- The emoji amendment is idempotent: if the commit already starts with an emoji, it is not amended again

After the push, capture the new `HEAD` SHA so you can wait for **its** workflow runs (not the previous ones). GitHub takes ~30s to register new runs; sleep 60 before re-entering step 2.

### 8. Loop

Go back to step 1. The loop ends when:

- All checks pass → success report
- You ask the user a question (loop pauses until they answer)
- You hit the 3-cycle cap without progress → ask before continuing
- The user interrupts

## Reporting

Each time you wake from a poll or finish a fix cycle, give the user **one short line**:

```text
Cycle 2: build (py3.12) failed (mypy), pushed e0a44f1. Waiting 5m.
```

Do not paste full job logs into the conversation. Summarize and link to the run.

## Safety

- `git push` is the only network-mutating action — confirm the branch is not `main` before pushing
- Force-push is only authorized in **one** case: a `[MegaLinter] Apply linters fixes` commit landed on origin and rebasing onto it produces conflicts. Use `--force-with-lease`, never `--force`. Any other force-push needs explicit user permission.
- If `git fetch` shows commits on origin that are **not** the MegaLinter bot, stop and ask — someone else is working on the branch
- Never edit generated files — regenerate them from source (step 6)
- If `gh` is not authenticated or the repo isn't a GitHub repo, **STOP** and tell the user
