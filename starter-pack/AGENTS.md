# Agent Instructions

This repository is durable engineering memory. Search before planning. Capture after meaningful work. Never store secrets.

## Retrieve

1. Call `braingent_guide()` once if MCP is available, or read this file and `CURRENT_STATE.md`.
2. Search with `braingent find` (structured) or `rg` (free text). Do not open `indexes/records.md` or `indexes/followups.md`.
3. Hydrate hits with `braingent_get(path, depth="summary")`. Use `depth="full"` only when exact evidence is required.
4. `braingent recall` is bounded. If matches are omitted, narrow the filter.

If facts change, add a new record and set `supersedes` / `superseded_by` to repo-relative paths. Do not leave two accepted decisions for the same fact.

## Load on demand

- Capture: `preferences/capture-policy.md` and `templates/task-record-minimal.md`
- Review: `preferences/code-review.md`
- Commits/PRs: `preferences/pr-and-commit.md`
- Naming: `preferences/naming.md`
- Live `BGT-*` tasks: `tasks/CLAUDE.md`

Never tag, mention, or assign another person unless JJ names them for that action.

## Capture

Use `templates/task-record-minimal.md` unless the work is an incident or an accepted decision. Set `captured_by` to the agent that wrote the record. Then `braingent validate` and `braingent reindex`.
