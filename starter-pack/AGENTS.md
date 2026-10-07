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
- Daily log and PM catch-up: `daily/README.md` and `workflows/daily-pm.md`

Never tag, mention, or assign another person unless JJ names them for that action.

## Epics

Work spanning many tickets or repositories gets one epic: `braingent new epic --org <org> --slug <slug>`. Tag records with `epic: [epic--<org>--<slug>]`, and tickets and PRs with the label `epic:<slug>`. Retrieve with `braingent find --epic <slug>`. Link to tickets and PRs from the epic page, never copy their status. Record config that must be set before the work is live in the page's `## Config to enable` ledger, and never write a secret's value. See `preferences/capture-policy.md`.

## Capture

Use `templates/task-record-minimal.md` unless the work is an incident or an accepted decision. Set `captured_by` to the agent that wrote the record. Then `braingent validate` and `braingent reindex`.

## Daily Log

When you start, finish, hand off for review, get blocked, or spawn a ticket or PR, append one line to today's log: `braingent daily-log <kind> "<what>" --ref <ticket-or-pr> --as <your-agent-id>`. See `daily/README.md`. "Run the daily PM" or "catch me up" → `workflows/daily-pm.md`.
