---
title: Multi-Agent Coordination
description: Coordinate Claude, Codex, ChatGPT, and Gemini on the same task — using a single Markdown file and Git.
section: Guides
order: 4
---

Real engineering with AI is rarely *one* agent in *one* terminal. It's
Claude in your editor, Codex in another window, a ChatGPT session
checking design, and you typing notes between them. Braingent's
multi-agent task files are how they coordinate without stepping on each
other.

## The problem

When two agents work on the same task at the same time:

- They duplicate work because neither knows what the other did.
- They give conflicting advice because they read different snapshots.
- They overwrite each other's notes because they're not aware of each
  other.

A coordination layer would normally solve this — a queue, a Slack channel,
a Linear ticket. Braingent's answer is simpler: **one Markdown file in
Git**.

## The mechanism — `tasks/active/BGT-NNNN.md`

Every active multi-agent task gets one file under
`tasks/active/BGT-NNNN.md`. The `BGT-NNNN` ID is monotonically
increasing.

The file has four canonical sections:

```markdown
---
id: BGT-0142
title: Backfill repo profile for acme/api
record_kind: agent-task
type: task
status: in-progress
status_category: active
priority: high
claimed_by: agent--claude-code
ai_tools: [Claude, Codex]
created: 2026-04-28T09:14Z
repositories: [repo--acme--api]
---

## Goal
Generate `repos/acme-api/profile.md` from local docs, git history,
open PRs.

## Status
- 2026-04-28 10:18 — claude — drafted profile, 14 sections.
- 2026-04-28 10:24 — jj    — flagged auth section as stale.
- 2026-04-28 10:31 — codex — reading auth/* to rewrite that section.

## Open questions
- Should we include the deprecated `/v1/login` endpoint history?
  Owner: jj. Decision needed before commit.

## Blockers
- (none)
```

Every agent updates that file. Git tracks the diff. The dashboard renders
the live view. Done.

## Who writes when

The convention:

- **Whoever opens the task** writes the initial frontmatter and goal.
- **Each agent appends to `## Status`** when it starts, finishes, or
  hands off.
- **The human (or any agent) raises `## Open questions`** when a
  decision is needed.
- **Anyone can mark blockers** in `## Blockers`.

Agents always *append* to status. Never rewrite history. The activity log
is the audit trail.

## How conflicts get resolved

Two agents update the same file, one commits first, the other gets a
conflict on push. Three options:

1. **`git pull --rebase`** — almost always works. Status logs are
   append-only, conflicts are rare.
2. **Manual merge** — for the rare case both agents updated frontmatter.
   The human picks the winning state.
3. **Recreate** — for total chaos, copy the file aside, regenerate, port
   activity log.

In practice, conflicts happen on maybe 1% of multi-agent tasks. The
append-only convention does most of the work.

## Lifecycle

```
tasks/active/BGT-0142.md   ->   tasks/archive/BGT-0142.md
       (in-progress)              (status: closed)
```

When work finishes:

1. The closing agent updates `status: closed`, sets a `resolution`, and adds a final status log entry.
2. `scripts/task-archive.sh` moves the file from `tasks/active/` to
   `tasks/archive/`.
3. Any captured decisions or learnings get linked from the task's
   `links:` frontmatter.

## When to use a live task vs a captured task

| Use a live task (BGT-NNNN) | Use a captured task |
| --- | --- |
| More than one agent is working on it | Solo agent in one session |
| Work spans more than one day | Work fits in one session |
| Decisions are still being made | Outcome is decided |
| Status updates matter | Only the result matters |

A captured task is a record of *what was done*. A live task is a record
of *what is being done*. Both have their place.

## CLI helpers

The starter pack ships these commands. Each is a thin wrapper around the
same Markdown manipulation.

```bash
# create a new live task
scripts/task-new.sh "Backfill repo profile for acme/api" --priority high

# claim it (sets owner)
scripts/task-claim.sh BGT-0142 --as agent--claude-code

# append a status update
scripts/task-comment.sh BGT-0142 "drafted profile, 14 sections" --as agent--claude-code

# move it to review
scripts/task-status.sh BGT-0142 in-review --as agent--claude-code --note "Ready for review"

# close and archive it
scripts/task-archive.sh BGT-0142 --as agent--claude-code --resolution completed
```

All of these are optional. Editing the file directly works the same.

## Dashboard view

If you're running the optional [Bun + React dashboard](/guides/dashboard/), it shows:

- All `tasks/active/` files in a kanban-style queue.
- Latest status update per task.
- Open questions that need a decision.
- Blockers across the board.

The dashboard is read-only. Agents and humans still update the files
directly through their normal flow.

## Pitfalls and how to avoid them

- **Forgetting to claim.** Two agents claim simultaneously → both think
  they own it. Mitigation: have agents run `scripts/task-claim.sh` before they start.
- **Skipping the status log.** Tempting when you're moving fast. Don't —
  the log is the only thing the next agent will read.
- **Over-using live tasks.** Solo work doesn't need one. If you're the
  only agent on the task, capture a regular task record at the end.

## Where to go next

- [The Capture Loop](/guides/capture-loop/) — capturing the outcome of a
  live task.
- [CLI Reference](/reference/cli/) — `task-*` commands in detail.
- [Memory Model](/concepts/memory-model/) — live tasks as the fourth
  surface.
