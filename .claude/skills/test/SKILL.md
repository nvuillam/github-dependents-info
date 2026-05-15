---
name: test
description: Phase 4 of the SDLC pipeline (also usable standalone). Use when the user invokes /test after a /implement, OR with a direct request to verify changes / run a specific test. Runs the test suite, type-checks, and linters against the changes, and reports a pass/fail verdict. Triages failures rather than blindly retrying.
---

# test — SDLC phase 4 (standalone-capable)

You are in the **verification** phase. Your job is to confirm the work is correct, conforms to conventions, and ready for review — and to triage anything that fails.

This skill can run after `/implement` OR standalone (e.g. user says `/test run only the CLI tests`, or `/test check coverage`). When invoked standalone, scope what you run to the user's request rather than always doing the full ladder below.

## Pre-flight

1. If a recent `/design` is in conversation context with a **Test plan**, use it to decide which targeted tests matter most.
2. Confirm via `git status` that there are actual changes worth verifying when running post-implement. If the tree is clean, ask the user whether the implementation was committed/reverted before running anything heavy.
3. If the user's `/test` arguments specify a scope ("just mypy", "only test_cli.py"), honour that and skip the rest.

## What to run, in order (full pipeline mode)

Run from the repo root with the Bash tool (the Makefile is bash-only — invoke `poetry run` directly on Windows). Stop on the first failure and triage before continuing.

1. **Fast offline tests first** — catches most regressions in seconds:
   ```bash
   poetry run pytest -c pyproject.toml tests/test_cli.py -vv
   ```
2. **Targeted tests from the test plan** (if any) — run only the specific test files/IDs added or modified:
   ```bash
   poetry run pytest -c pyproject.toml tests/path/to/changed_test.py::test_name -vv
   ```
3. **Type-check**:
   ```bash
   poetry run mypy --config-file pyproject.toml ./
   ```
4. **Code style**:
   ```bash
   poetry run black --diff --check --config pyproject.toml ./
   poetry run darglint --verbosity 2 github_dependents_info tests
   ```
5. **Full test suite with coverage** — hits live GitHub dependent pages for `nvuillam/npm-groovy-lint` and `nvuillam/github-dependents-info`. Slow and flaky on rate limits. **Ask the user before running this step** if network/time may be a concern:
   ```bash
   poetry run pytest -c pyproject.toml --cov-report=html --cov=github_dependents_info tests/
   ```
6. **Safety/security** — only if the change touched dependencies or shells out:
   ```bash
   poetry run bandit -ll --recursive github_dependents_info tests
   poetry run safety scan --target . --policy-file .safety-policy.yml --detailed-output
   ```

## Triage rules

- **Doctest failure in a module docstring**: pytest collects doctests because `pyproject.toml` sets `--doctest-modules`. Fix the example, don't disable the option.
- **Network/rate-limit failures in `tests/test_gh_dependents_info/`**: distinguish a real regression from GitHub returning 429/empty. Re-run the single failing test once with `-vv -s`; if it passes, note the flake and move on. Two consecutive failures = treat as real.
- **Black would reformat**: run `poetry run black --config pyproject.toml ./` to apply, then re-run the check. Don't argue with the formatter.
- **mypy errors**: fix the types in the implementation rather than adding `# type: ignore`, unless the error is in third-party stubs.
- **Import error / unexpected ModuleNotFoundError**: usually means the implementation missed an `__init__.py` re-export or a `pyproject.toml` dependency. Surface to the user.

## Rules

- **Do not modify production code to make a test pass.** If a test reveals a real bug, stop and tell the user; that's a feedback loop back to design/implementation, not a fix here.
- You **may** fix obviously-wrong test code you just wrote in `/implement` (typos, wrong fixture name) — but not pre-existing tests without asking.
- Do not commit. Reporting is the deliverable.

## Output

End with a verdict block:

```
Verdict: PASS | FAIL | PASS-with-flakes
- pytest (offline): <result>
- pytest (live, if run): <result>
- mypy: <result>
- black/darglint: <result>
- safety/bandit (if run): <result>

Notes:
<one or two sentences about anything flaky, skipped, or worth a follow-up>
```

If PASS: suggest the user review `git diff` and commit. If FAIL: list the specific failures with file:line references and the smallest reproducer, then stop.
