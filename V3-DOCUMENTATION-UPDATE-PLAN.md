# Braingent V3 Documentation Update Plan

## Goal

Bring the public `braingent-manifesto` documentation up to date with Braingent v3 while keeping the starter pack portable, private-safe, and Markdown-first.

## Feature Inventory

The documentation update must cover these v3 capabilities:

- Thin root entrypoints for agents: `AGENTS.md`, `CLAUDE.md`, `CHATGPT_PROJECT_BRIEF.md`, `README.md`, `INDEX.md`, and `CURRENT_STATE.md`.
- Durable Markdown records with YAML frontmatter for tasks, reviews, decisions, learnings, interactions, versions, notes, summaries, profiles, and ticket stubs.
- Structured retrieval through `scripts/find.sh`, `rg`, generated indexes, and optional local search/cache tooling.
- Generated maintenance surfaces: `indexes/records.md`, `indexes/records.json`, `indexes/followups.md`, `indexes/memory-summary.md`, and `indexes/stale-candidates.md`.
- Optional live-work layer under `tasks/` using `record_kind: agent-task`, `BGT-NNNN` IDs, status transitions, ownership, dependencies, and append-only activity.
- Agent identity convention: concrete IDs such as `agent--codex-cli` or `agent--claude-code` for live task activity, with broad `ai_tools` names kept for durable records.
- Task helper commands for creating, claiming, commenting, listing, counting, closing, archiving, and launching the local task dashboard.
- Promotion-on-close: completed live tasks produce or link to durable records with `agent_task: BGT-NNNN`.
- Task staleness rules: triage older than 30 days, blocked older than 30 days, and in-progress tasks with no activity for 14 days.
- Generated live-task read surfaces: `tasks/INDEX.md`, `indexes/agent-task-queue.md`, and `indexes/agent-task-graph.md`.
- Optional local dashboard for `tasks/active/`: read-only queue, filters, detail view, dependency graph, recent activity, raw Markdown, and built-in guide.
- Copyable dashboard sample under `examples/task-dashboard/` with synthetic task data and `BRAINGENT_MEMORY_ROOT` support.
- Dashboard contract: the web UI reads task files and generated indexes; it is not a second source of truth.
- Dashboard verification: run after reindexing so task schema drift fails in automation.
- Cleanup workflow that reviews durable records, follow-ups, stale candidates, live task health, entrypoint bloat, and generated indexes together.
- Public-safety rule: examples must not include private paths, secrets, customer data, internal ticket IDs, or personal work history.

## Documentation Changes

1. Update top-level overview docs.
   - Files: `README.md`, `HOW-IT-WORKS.md`, `MANIFESTO.md`.
   - Verify: a new reader can identify every v3 feature without opening the starter pack.
   - ELI5: make the front door explain the whole house before asking someone to inspect each room.

2. Promote task coordination documentation to an optional v3 module.
   - Files: `AGENT-TASK-COORDINATION.md`, `STRUCTURE.md`, `WORKFLOW.md`, `AGENT-INTEGRATION.md`.
   - Verify: docs clearly separate live `agent-task` files from retrospective durable `task` records.
   - ELI5: live task files are the shared workbench; durable records are the permanent notebook.

3. Update setup, initialization, maintenance, and FAQ docs.
   - Files: `SETUP.md`, `INITIALIZE.md`, `FILES-NEEDED.md`, `MAINTENANCE.md`, `FAQ.md`.
   - Verify: users can adopt core memory first and add live tasks/dashboard later.
   - ELI5: the starter should work as a bicycle first; the task dashboard is an optional cargo rack.

4. Add starter-pack live-task references and templates.
   - Files: `starter-pack/tasks/**`, `starter-pack/templates/agent-task.md`, `starter-pack/preferences/agent-task-protocol.md`, plus starter-pack indexes and entrypoints.
   - Verify: the starter pack contains a safe example `BGT-0001` task and enough instructions for an agent to operate without private context.
   - ELI5: ship a sample ticket and the rules for using tickets, not a private backlog.

5. Refresh publishing and contribution guidance.
   - Files: `PRIVACY-AND-SAFETY.md`, `PUBLISHING-CHECKLIST.md`, `CONTRIBUTING.md`.
   - Verify: public contributors know how to document task/dashboard features without leaking real work.
   - ELI5: before sharing the system, check that the examples are props, not real receipts.

## Verification

- Run `git diff --check`.
- Search for obvious private leaks: local absolute paths, internal repo names, private customer names, secrets, and real ticket identifiers.
- Confirm every feature in the inventory appears in at least one public doc.
- Confirm optional dashboard wording does not imply the manifesto repo stores dashboard state outside Markdown.
- Commit changes on branch `thedoublejay/braingent-v3-docs`.
