---
name: design
description: Phase 2 of the SDLC pipeline (also usable standalone). Use when the user invokes /design with either a prior /analyze in conversation context OR a direct problem description. Produces an implementation plan inline in the conversation. Do NOT write production code in this phase. Do NOT save the design to disk unless the user explicitly asks.
---

# design — SDLC phase 2 (standalone-capable)

You are in the **design** phase. Your job is to turn a problem (either an `/analyze` output already in the conversation, or a fresh description from the user) into a concrete, ordered plan that `/implement` (or the user) can execute mechanically.

This skill can run after `/analyze` OR standalone. If the user invokes `/design` with their own description and no prior analysis, do a quick mental analysis first — but still output a design, not an analysis.

## Pre-flight

1. Check the conversation for a recent `/analyze` output. If present, use it as input. If not, treat the user's `/design` arguments as the problem statement.
2. Read `CLAUDE.md` for architecture and conventions.
3. If there are unresolved open questions (from a prior analysis or the user's prompt), ask the user to resolve them before proposing a design. Don't guess on non-trivial trade-offs.

## What to produce

Output the design **inline as your response**, in the conversation. Do NOT write it to a file unless the user explicitly asks ("save the design", "put it in a doc", etc.). The implementation phase reads from conversation context.

Structure:

```
# Design: <one-line solution statement>

## Approach
<3-6 sentences describing the chosen approach and why it fits the constraints.>

## Alternatives considered
<For each rejected alternative: one sentence on what it was, one sentence on why. Skip the section if the choice was obvious.>

## Change list
<Ordered, numbered list of concrete edits. Each item names a file, the function/region to touch, and the change. Example:
1. `github_dependents_info/gh_dependents_info.py:920` — extend `fetch_all_package_pages` signature with `since: datetime | None = None`; thread it through to `fetch_page`.
2. `github_dependents_info/__main__.py:80` — add `--since` Typer option, parse to datetime, forward via `gh_options`.
3. `action.yml` — add matching `since` input and shell branch that appends `--since=...`.
>

## Public-API impact
<Anything affecting downstream users: new/changed CLI flags, env vars, JSON schema, badge marker behavior, action.yml inputs. State "None" when applicable.>

## Test plan
<Specific tests to add or update. For each: which file, what it asserts, whether it needs network.>

## Risks & rollback
<What could break. How to revert.>
```

Skip sections that are genuinely empty — don't pad with "N/A".

## Design principles for this codebase

- **Keep logic in `GithubDependentsInfo`.** New behavior goes on the class, not in `__main__.py`. CLI is a thin shim.
- **CLI options with env-var fallbacks** are only forwarded to the constructor when explicitly set by the user — see `__main__.py` `llm_*` handling. Preserve that pattern.
- **`action.yml` mirrors the CLI.** New user-facing CLI flags need an `inputs:` entry and a `set -- "$@" ...` shell branch.
- **CSV-resume compatibility.** If a change alters what's stored mid-crawl, decide whether old `csv_directory` contents are invalidated or migrated, and say so.
- **Don't change badge marker strings** (`<!-- gh-dependents-info-used-by-start -->` / `...-end -->`).
- **Doctests run by default** (`addopts = ["--doctest-modules"]`). New `>>>` examples become tests.

## Rules

- **No code edits.** Design-only phase.
- **No files written.** Output stays in conversation unless the user explicitly asks to persist it.
- **Be specific about file paths and line numbers** in the change list so `/implement` (or a human) doesn't have to re-discover them.
- If the available analysis turns out to be wrong, say so and recommend re-running `/analyze` rather than designing on a bad foundation.
- End with a single line suggesting the next step, e.g. `Run /implement to execute, or refine the design above.` — do not assume the user will continue.
