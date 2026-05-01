# Agent Task Coordination

Agent task coordination is an optional Braingent v3 module for tracking active work in Markdown. It is useful when multiple agents, humans, or sessions need a shared queue without introducing a separate project management database.

Braingent remains memory-first. Live tasks coordinate work in progress; durable records preserve what happened after the work is done.

## Purpose

Use the task layer when work needs:

- ownership across agents or sessions;
- status and priority visible from the terminal or dashboard;
- dependencies between pieces of work;
- append-only activity for handoffs;
- a clear closeout path into durable memory.

Do not use it for every tiny edit. The live task layer is for coordination, not ceremony.

## Boundary

| Concept | Mutability | Purpose | Typical location |
| --- | --- | --- | --- |
| Live agent task | Mutable until closed | Coordinate current work, assignment, dependencies, review, comments, and handoffs. | `tasks/active/BGT-NNNN--slug.md` |
| Durable task/review/decision record | Mostly immutable after capture | Preserve what happened, evidence, decisions, verification, and follow-ups. | `orgs/`, `topics/`, `tools/`, or `repositories/` |
| External ticket stub | Mutable as source changes | Link to Jira, Linear, GitHub Issues, or another source-of-truth tracker. | `tickets/` |

ELI5: the live task is the shared whiteboard. The durable record is the signed meeting note. The external ticket stub is a pointer to another team's tracker.

## Directory Layout

```text
tasks/
├── CLAUDE.md                  # scoped rules loaded only for task work
├── INDEX.md                   # generated live task index
├── README.md                  # human guide for the task module
├── active/
│   └── BGT-0001--example-review-task.md
└── archive/
    └── YYYY-MM/

indexes/
├── agent-task-queue.md        # generated queue grouped by status/priority
├── agent-task-graph.md        # generated dependency view
├── memory-summary.md          # short live counts plus memory summary
└── stale-candidates.md        # record and task hygiene candidates
```

The `tasks/` tree can be omitted until you need live work coordination.

## Task File Schema

Live task files are Markdown with YAML frontmatter. Use `record_kind: agent-task` so tools can separate them from retrospective `record_kind: task` records.

```yaml
---
id: BGT-0001
record_kind: agent-task
title: "Example review task"
status: triage
priority: medium
owner: agent--codex-cli
created: 2026-01-01
updated: 2026-01-01
depends_on: []
blocked_by: []
related_records: []
external_links: []
---
```

Recommended body sections:

- `## Goal`
- `## Context`
- `## Acceptance Criteria`
- `## Plan`
- `## Activity`
- `## Closeout`

Activity entries should be append-only and attributed:

```markdown
- 2026-01-01T10:00:00Z agent--codex-cli: Claimed task and checked existing records.
```

## Status Lifecycle

Recommended statuses:

| Status | Meaning |
| --- | --- |
| `triage` | Captured but not yet accepted or assigned. |
| `ready` | Clear enough for an agent to start. |
| `in-progress` | Actively being worked. |
| `blocked` | Cannot proceed until a dependency is resolved. |
| `in-review` | Implementation or capture is ready for review. |
| `completed` | Work is done and durable memory has been updated when needed. |
| `closed` | Intentionally closed without completion. |

Keep transitions boring and visible. If an agent changes status, it should add an activity entry explaining why.

## Agent Identity

Use concrete agent IDs in live task activity:

- `agent--codex-cli`
- `agent--claude-code`
- `agent--chatgpt`
- `agent--gemini-cli`
- `human--<handle>`

Use broad `ai_tools` values in durable records when describing which tool was involved:

- `codex`
- `claude`
- `chatgpt`
- `gemini`

The distinction matters because live tasks need accountable actors, while durable records usually need searchable tool families.

## Helper Commands

Task helpers are optional, but common commands are:

```bash
scripts/task-new.sh "Write setup guide" --priority medium
scripts/task-claim.sh BGT-0001 agent--codex-cli
scripts/task-comment.sh BGT-0001 agent--codex-cli "Validated frontmatter and updated docs."
scripts/task-status.sh BGT-0001 in-review
scripts/task-list.sh --status blocked
scripts/task-list.sh --count
scripts/task-archive.sh BGT-0001
scripts/task-dashboard.sh
```

Keep scripts as thin wrappers over Markdown. They should update task files and regenerate indexes, not hide state in a separate database.

## Generated Indexes

Generated task indexes should be rebuilt from Markdown and safe to delete:

- `tasks/INDEX.md` lists active tasks and archive pointers.
- `indexes/agent-task-queue.md` groups active work by status, owner, and priority.
- `indexes/agent-task-graph.md` shows dependencies and blocked work.
- `indexes/memory-summary.md` includes a short live count such as active, in-review, and blocked.
- `indexes/stale-candidates.md` includes live task hygiene candidates beside durable-record hygiene.

The generated files are reading surfaces, not source of truth.

## Local Dashboard

The optional dashboard is a read-only web UI over `tasks/active/` and generated indexes.

Expected views:

- queue grouped by status and priority;
- filters for status, owner, priority, and text search;
- task detail with goal, plan, acceptance criteria, closeout, and raw Markdown;
- dependency graph;
- recent activity with fixed-height pagination;
- guide page explaining the task workflow inside the app.

Expected contract:

- task Markdown remains canonical;
- the dashboard does not invent a separate schema;
- schema drift should be caught by end-to-end tests after reindexing;
- dashboard docs should state the stack if you ship one, for example Bun, React, TanStack Router, Tailwind, and Playwright.

## Promotion On Close

When a live task closes with `status: completed`, capture the durable outcome:

1. Create or update the relevant task, decision, review, learning, tool, topic, repository, or project record.
2. Add `agent_task: BGT-NNNN` to the durable record frontmatter or body.
3. Add a closeout entry in the live task linking the durable record.
4. Regenerate indexes.
5. Archive the closed live task when it no longer needs to appear in the active queue.

This prevents active task files from becoming the only place where important history lives.

## Stale Task Rules

Recommended stale candidates:

- `triage` older than 30 days;
- `blocked` older than 30 days;
- `in-progress` with no activity for 14 days;
- completed tasks that have no durable record link.

Surface stale tasks in the same cleanup queue as stale records so maintenance sees task hygiene and memory hygiene together.

## Anti-Patterns

- Treating `tasks/active/` as the permanent archive.
- Mixing `record_kind: agent-task` and `record_kind: task`.
- Recording agent activity without a concrete actor.
- Letting the dashboard become a second source of truth.
- Creating live tasks for edits that need no coordination.
- Closing completed tasks without durable capture.
- Storing private customer data, secrets, tokens, or raw chat transcripts in task files.

## Adoption Path

1. Start with durable records only.
2. Add `tasks/` when work begins spanning sessions or agents.
3. Add task helper scripts once manual edits become repetitive.
4. Add generated task indexes when the queue grows.
5. Add a dashboard only when a visual queue improves review or coordination.

ELI5: do not install a dispatch board before you have enough work to dispatch.
