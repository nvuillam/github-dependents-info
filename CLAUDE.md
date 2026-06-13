# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`github-dependents-info` is a Python CLI (also packaged as a Docker-based GitHub Action) that scrapes GitHub's "Used by" / dependents HTML pages — because the GitHub REST/GraphQL APIs do not expose this data — and emits stats as text, JSON, markdown reports, and shields.io badges. Optionally generates an AI usage summary via `litellm` when an LLM provider API key is present in the env.

Distributed on PyPI; also runs as `nvuillam/github-dependents-info` GitHub Action backed by the Docker image in `docker/Dockerfile`.

## Architecture

There are essentially two source files; almost all logic lives in one class.

- `github_dependents_info/__main__.py` — Typer CLI. Builds a `gh_options` dict and instantiates `GithubDependentsInfo`. Note that LLM-related CLI options are only forwarded to the constructor when explicitly set, so env-var defaults (`GITHUB_DEPENDENTS_INFO_LLM_*`, `LITELLM_MODEL`, provider keys like `OPENAI_API_KEY`) keep working — preserve this pattern when adding new options.
- `github_dependents_info/gh_dependents_info.py` — the `GithubDependentsInfo` class (~1000 LOC) does everything: scraping, parsing, aggregation, markdown/badge building, CSV progress, and LLM summary. Entry point is `collect()` (sync wrapper around `collect_async()`).

The scraping pipeline:

1. `compute_packages_async()` — fetches `/{repo}/network/dependents` once to discover all `package_id`s (multi-package repos like `oxsecurity/megalinter`) by parsing anchors that start with `/{repo}/network/dependents?package_id=`. If none found, the repo itself is treated as a single package.
2. For each package, `fetch_all_package_pages()` walks paginated dependent HTML pages concurrently (bounded by `max_concurrent_requests`, default 10) via `httpx.AsyncClient`. `fetch_page()` parses each page with BeautifulSoup, extracts `(owner, name, stars)` rows from `.Box-row`, and follows the "Next" link until exhausted or `max_scraped_pages` is hit. The first page also yields total/public/private counts for the package.
3. `build_result()` / `build_markdown()` assemble badges (`build_badge()` produces shields.io URLs), aggregate cross-package totals, and write paginated markdown when `pagination=True` (default page size 500).
4. `maybe_generate_llm_summary()` runs after aggregation. Provider is auto-detected from env vars via `_detect_llm_provider()`; results are cached to `<csv_directory>/llm_summary_<repo>.json` and re-used on subsequent runs.

CSV-based crawl resumption: when `--csvdirectory` is provided, `save_progress()` writes one CSV per package plus a `packages_<repo>.csv` index. `load_progress()` rehydrates state on next run so an interrupted multi-hour scrape (e.g. angular/angular has millions of dependents) can resume. `--overwrite` forces a fresh crawl.

HTTP retry: `http_retry_attempts` / `http_retry_initial_delay` / `http_retry_backoff` / `http_retry_max_delay` (constructor-only, not CLI flags) wrap fetches with exponential backoff — GitHub's dependents page rate-limits aggressively.

Badge insertion into READMEs is done by `write_badge()`, which replaces everything between the literal markers `<!-- gh-dependents-info-used-by-start -->` and `<!-- gh-dependents-info-used-by-end -->`. Don't change these marker strings — they're a public contract used by every downstream README.

## Tooling

- **RTK (Rust Token Killer)** — ALWAYS use `rtk` for Bash commands when it is installed. Verify once per session with `rtk --version`. If present, **every** shell command must be prefixed: `rtk git ...`, `rtk ls`, `rtk grep`, `rtk test <cmd>`, `rtk err <cmd>`. On native Windows (PowerShell/cmd/Git Bash) the auto-rewrite hook does NOT fire — you MUST prefix manually, every command, every session. On macOS/Linux/WSL rewriting is automatic. Only skip the prefix (use `rtk proxy <cmd>` or raw) when exact unfiltered output is required (a diff you will edit from, a full stack trace). Not using `rtk` when it is available wastes tokens and is incorrect behavior.

## Commands

The project uses Poetry + Make. Makefile is bash-only (`SHELL := /usr/bin/env bash`) — on Windows run targets via WSL/Git Bash or invoke the underlying poetry commands directly.

```bash
make install              # poetry lock + export requirements.txt + poetry install --with dev
make install-local        # pip install -e . into the active env

make codestyle            # pyupgrade + black
make check-codestyle      # black --check + darglint
make mypy                 # type-check
make check-safety         # poetry check + safety scan + bandit
make lint                 # = test + check-codestyle + mypy + check-safety

make test                 # pytest with --cov, regenerates assets/images/coverage.svg
```

Running tests directly (works on Windows too):

```bash
poetry run pytest -c pyproject.toml tests/                         # full suite
poetry run pytest tests/test_cli.py                                # CLI parsing tests (offline, fast)
poetry run pytest tests/test_gh_dependents_info/ -k single_package # single test by name substring
```

`tests/test_gh_dependents_info/` hits the live GitHub dependents pages for `nvuillam/npm-groovy-lint` and `nvuillam/github-dependents-info` — they need network access and can be slow/flaky. `tests/test_cli.py` is offline and safe to run in isolation.

Note: `pyproject.toml` sets `addopts = ["--doctest-modules", ...]` so pytest also collects doctests from the package — any docstring with `>>>` gets executed.

Running the CLI from a checkout:

```bash
poetry run github-dependents-info --repo nvuillam/npm-groovy-lint --verbose
# or
python -m github_dependents_info --repo nvuillam/npm-groovy-lint --verbose
```

## Release flow

```bash
make release-version VERSION=patch   # or minor / major / explicit like 1.7.0
git push --follow-tags               # tag push triggers .github/workflows/release.yml
```

The tag push triggers the release workflow. The `action.yml` pins `image: docker://nvuillam/github-dependents-info:vX.Y.Z` — when bumping a major/minor that changes the action contract, that image tag must be updated in lockstep.

## Conventions worth knowing

- Python ≥ 3.10 required (project metadata says so), but `black`/`isort`/`mypy` configs target 3.9 — don't "modernize" those configs without intent.
- Line length: 120 (black + isort).
- Imports: isort `profile = "black"` with custom `known_typing` section ordered FUTURE → TYPING → STDLIB → THIRDPARTY → FIRSTPARTY → LOCALFOLDER.
- Commit messages in this repo use gitmoji prefixes (`:arrow_up:`, `:sparkles:`, etc.) — follow recent `git log` style when committing.
- MegaLinter runs in CI (`.github/workflows/mega-linter.yml`); `make lint` locally is a reasonable proxy.
