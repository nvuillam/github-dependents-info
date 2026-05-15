---
name: implement
description: Phase 3 of the SDLC pipeline (also usable standalone). Use when the user invokes /implement after a /design in conversation context, OR with a direct task description. Executes the change list, editing source files. Reads design context from the conversation — not from disk. Does NOT run the full test suite (that is /test's job), but does sanity-check imports and syntax.
---

# implement — SDLC phase 3 (standalone-capable)

You are in the **implementation** phase. Your job is to execute concrete code changes.

This skill can run after `/design` OR standalone (e.g. user says `/implement add a --since flag` without prior phases). Input source, in priority order:

1. A `/design` output present in the recent conversation — use its **Change list** verbatim.
2. The user's `/implement` arguments — treat them as the task. Do a brief in-head plan, confirm with the user if non-trivial, then proceed.

## Pre-flight

1. Look for a recent `/design` Change list in the conversation. If absent and the user's instructions are non-trivial (more than one file, or unclear scope), ask the user whether they want you to do a quick design-in-head first or just execute. For simple/explicit tasks, just execute.
2. Read `CLAUDE.md` for conventions if you haven't already in this session.

## How to work

- For multi-step changes, use `TaskCreate` to mirror the change list as trackable tasks. Mark each `in_progress` when you start it and `completed` immediately when done — do not batch. For single-edit tasks, skip TaskCreate.
- Edit with `Edit` (preferred) or `Write` (only for new files). Read the file first if you have not already in this session.
- After each non-trivial edit to `gh_dependents_info.py` or `__main__.py`, run `poetry run python -c "import github_dependents_info; from github_dependents_info.__main__ import app"` to catch import/syntax errors early.
- If the plan specified test additions, write the test stubs/files in this phase — but do not run them. `/test` (or the user) runs them.

## Code conventions (enforced)

- Black, line length 120. Don't hand-format; let `make codestyle` reflow.
- isort sections: FUTURE → TYPING → STDLIB → THIRDPARTY → FIRSTPARTY → LOCALFOLDER.
- Python ≥ 3.10 syntax is fine (`X | None`, PEP 604 unions).
- Default to no comments. Only add a comment when the **why** is non-obvious.
- Don't refactor beyond the requested change. If you spot adjacent cleanup, note it as a follow-up in your end-of-phase summary, do not do it.
- Keep the CLI thin: behavior belongs on the `GithubDependentsInfo` class.
- Forward new CLI options with env-var fallbacks only when explicitly set (the `if X is not None: gh_options[...] = X` pattern in `__main__.py`).
- Mirror new user-facing CLI flags into `action.yml` inputs AND the shell `set -- "$@" ...` branches.

## Things not to touch unless explicitly requested

- The badge marker strings `<!-- gh-dependents-info-used-by-start -->` and `<!-- gh-dependents-info-used-by-end -->`.
- The `packages_<repo>.csv` / `dependents_<name>.csv` filename patterns under `csv_directory` — downstream users may script against them.
- The pinned `image: docker://nvuillam/github-dependents-info:vX.Y.Z` in `action.yml` — that moves at release time, not feature work.
- `requirements.txt` directly — it's regenerated from `poetry.lock` by `make install`.

## When you hit a problem

- Failing pre-commit hook on commit: fix the underlying issue, never `--no-verify`.
- An edit breaks an unrelated test: stop and surface it. Do not blindly "fix" it.
- A dependency needs adding: use `poetry add <pkg>` (or instruct the user), do not hand-edit `pyproject.toml`'s dependency list.

## Output

When all changes are done:

1. Summarize what changed in 2-3 sentences (one paragraph, no headers).
2. List any follow-ups you noticed but did not do.
3. End with a single line suggesting the next step, e.g. `Run /test to verify, or review the diff above.` — do not assume the user will continue.
