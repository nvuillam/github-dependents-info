---
name: analyze
description: Phase 1 of the SDLC pipeline (also usable standalone). Use when the user invokes /analyze with a feature request, bug report, or change description. Gathers requirements and maps the affected code surface, then presents the analysis inline in the conversation for the next phase to consume. Do NOT propose solutions or write code in this phase. Do NOT save the analysis to disk unless the user explicitly asks.
---

# analyze — SDLC phase 1 (standalone-capable)

You are in the **analysis** phase. Your job is to understand the problem deeply enough that a follow-up `/design` (or the user directly) can plan a solution. You are NOT designing or implementing yet.

This skill can run as the first step of the pipeline OR standalone — e.g. the user may just want "tell me what would be affected if we did X" without intending to continue. Either way, the deliverable is the same: an inline analysis.

## Inputs

The user's `/analyze` arguments describe what they want investigated. If the request is ambiguous, ask up to 3 clarifying questions before proceeding — do not guess intent on non-trivial work.

## What to produce

Output the analysis **inline as your response**, in the conversation. Do NOT write it to a file unless the user explicitly asks ("save the analysis", "write it to disk", etc.). The next phase reads it from conversation context, not from disk.

Use this structure:

```
# Analysis: <one-line problem statement>

## Goal
<2-3 sentences: what the user wants and why>

## Current behavior
<How the relevant code behaves today. Cite specific files and line numbers using `path:line` format.>

## Affected surface
<Bulleted list of files/functions/classes that will likely need to change, with one-line justification each.>

## Constraints & invariants
<What must NOT break. Public API contracts, marker strings like `<!-- gh-dependents-info-used-by-start -->`, CLI flags, env vars, on-disk CSV format, the action.yml input names, doctests in package docstrings, etc.>

## Open questions
<Anything that a design phase or the user needs to resolve. Empty list if none.>

## Out of scope
<Things deliberately excluded.>
```

Keep it tight — this lives in the conversation, so every line costs context budget. Cut sections that are empty or trivially "None".

## How to investigate

1. Read `CLAUDE.md` first — it contains the architecture overview and conventions.
2. Use `Grep` and `Read` to confirm every claim before writing it down. Don't speculate about file contents.
3. For scraping/CLI/markdown/badge changes, trace the path through `github_dependents_info/gh_dependents_info.py` (the class is ~1000 LOC and holds nearly all logic).
4. For CLI flag changes, check both `github_dependents_info/__main__.py` AND `action.yml` — they must stay in sync.
5. If tests already cover the area, list the relevant test files in **Affected surface**.

## Rules

- **No solutions.** If you find yourself writing "we should change X to Y", stop and move it to a TODO for design.
- **No code edits.** Read-only phase.
- **No files written.** Output stays in conversation unless the user explicitly asks to persist it.
- **Be concrete.** "Modify the scraper" is useless; "Modify `fetch_all_package_pages` in `github_dependents_info/gh_dependents_info.py:920` to accept a `since` parameter" is useful.
- End your response with a single line suggesting the next step, e.g. `Run /design to plan changes, or refine the analysis above.` — but do not assume the user will continue.
