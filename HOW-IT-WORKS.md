# How Braingent Works

Braingent is built from a few simple parts that reinforce each other.

## 0. Five Memory Surfaces

Braingent organizes memory into five surfaces:

1. **Pinned context:** root entry files (`CLAUDE.md`, `AGENTS.md`,
   `CURRENT_STATE.md`), and stable preferences. Keep this small and current.
   Agents read this layer for every task.
2. **Durable memory:** task, review, decision, learning, summary, version, and
   profile records. Markdown files with YAML frontmatter. These are canonical.
   Agents search and cite this layer.
3. **Derived retrieval:** generated indexes, optional local databases, MCP
   retrieval helpers, and future recall packs. These are aids — not source of
   truth. Rebuild from durable records on demand.
4. **Optional live work:** mutable `BGT-NNNN` task files under `tasks/active/`
   for current agent coordination. These are not final records. Close them by
   promoting important outcomes into durable memory.
5. **Optional local dashboard:** a read-only UI over live tasks and generated
   indexes. It improves visibility but does not own any state.

**ELI5:** The pinned layer is the short briefing. Durable records are the
receipts. Derived retrieval is the search assistant that pulls the right
receipts. Live work is the shared whiteboard for what is happening right now.
The dashboard is a window, not a second whiteboard.

## 1. The Memory Repo

The memory repo is a normal Git repository full of Markdown files.

Git gives you:

- history
- diffs
- branches
- backups
- pull requests, if you want review
- easy syncing across machines

Markdown gives you:

- human readability
- AI readability
- easy editing
- no vendor lock-in

## 2. Root Entrypoints

The root files are the front door:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `CHATGPT_PROJECT_BRIEF.md`
- `INDEX.md`
- `CURRENT_STATE.md`

These files tell humans and agents what the repo is, what to read first, and what matters right now.

The key design is that root files stay thin. They route readers into focused memory instead of trying to contain every detail.

## 3. Preferences

The `preferences/` directory holds standing rules.

Examples:

- how to name records
- when to capture work
- how agents should plan
- how to review code
- how to write durable notes
- what not to store

Preferences are not one-time events. They are stable defaults that should guide future work.

## 4. Records

Records are durable memories.

Common record kinds:

- `task` - work that was planned, active, blocked, completed, or superseded
- `review` - code or design review
- `decision` - a tradeoff that should guide future work
- `learning` - a reusable lesson
- `version` - a tool, dependency, runtime, model, or framework note
- `summary` - an imported historical baseline
- `profile` - a living profile for a repo or entity
- `ticket-stub` - a cross-cutting ticket index

Good records preserve evidence. A future agent should not need to reopen the old chat just to understand what happened.

## 5. Frontmatter

Frontmatter is the metadata block at the top of a Markdown file:

```yaml
---
title: Adopt Thin Agent Entrypoints
record_kind: decision
status: accepted
date: 2026-04-26
timezone: <timezone>
organization: org--personal
project: project--personal--memory
repositories: []
topics: [topic--ai-memory]
tools: []
---
```

The body explains the memory. The frontmatter makes it searchable.

This means you can later build scripts to answer questions like:

- show all accepted decisions
- show active records for this repo
- show learnings about testing
- show tasks linked to this ticket
- show tool versions used in this project

## 6. Entity Pages

Entity pages are stable anchors:

- organizations
- projects
- repositories
- topics
- tools
- people
- tickets

A repository profile, for example, should tell agents:

- what the repo does
- what stack it uses
- common commands
- conventions
- known risks
- important records

This keeps agents from rediscovering basic context every time.

## 7. Templates

Templates make capture fast and consistent.

Instead of inventing a shape every time, copy the right template and fill in the fields.

Templates also teach agents what a good record should contain.

## 8. Workflows

Workflows are procedures that can be triggered by a phrase.

Example:

```text
index this repo to memory
```

A workflow should explain:

- when it applies
- pre-flight checks
- source material
- steps
- outputs
- failure modes
- safety rules

Workflows turn repeated agent work into repeatable practice.

## 9. Indexes

Indexes make the memory navigable.

At first, indexes can be simple Markdown files updated by hand.

Later, they can be generated from frontmatter.

Useful indexes:

- organizations
- projects
- repositories
- topics
- tools
- people
- records
- follow-ups
- memory summary
- stale candidates
- live task queue
- live task graph

## 10. Optional Live Work

The live-work layer is for coordinating current work before it becomes durable memory.

Use it when:

- multiple agents may touch related work;
- work spans more than one session;
- a task needs ownership, dependencies, comments, or review state;
- a dashboard or terminal queue helps you see what is active.

Live task files live under `tasks/active/` and use `record_kind: agent-task`. A
typical task has a `BGT-NNNN` ID, title, status, priority, owner, dependencies,
timestamps, and an append-only activity log.

Durable task records still live under `orgs/`, `topics/`, `tools/`, or another
canonical memory location. When a live task closes as completed, create or link
a durable record with `agent_task: BGT-NNNN`.

Generated live-work surfaces usually include:

- `tasks/INDEX.md`
- `indexes/agent-task-queue.md`
- `indexes/agent-task-graph.md`
- a short active/in-review/blocked count in `indexes/memory-summary.md`

ELI5: the live task is the sticky note on the monitor. The durable record is the
entry in the engineering journal after the work is done.

## 11. Raw Imports

Raw imports are temporary source material:

- chat exports
- PR exports
- ticket exports
- local planning docs
- command logs

Raw imports should not become the permanent memory unless they are already concise and safe.

The preferred path is:

```text
raw source -> curated summary -> durable task/decision/learning records
```

## 12. The Capture Funnel

Not every piece of information is ready for a durable record immediately. Use
the capture funnel:

1. **Capture fast:** drop rough material into `inbox/` or `imports/raw/`.
2. **Classify:** choose the record kind before polishing.
3. **Normalize:** add frontmatter, exact identifiers, dates, and source links.
4. **Summarize:** write the shortest useful summary in your own words.
5. **Link:** add related records and promote repeated ideas to topics/tools.
6. **Validate and index:** run validation and index scripts if available.
7. **Review later:** stale, active, raw, and unchecked items are handled by
   the cleanup workflow.

Do not let `inbox/` become permanent storage.

## 13. The Retrieval Ladder

Agents should retrieve memory in this order — most precise first:

1. **Exact metadata search:** filter by repo, project, ticket, topic, tool,
   status, or date using structured search (`scripts/find.sh` or equivalent).
2. **Live task queue:** when the work may already be active, check
   `tasks/INDEX.md` or `indexes/agent-task-queue.md` before starting a duplicate
   task.
3. **Free-text body search:** use `rg` for error strings, API names, partial
   names, and exploratory queries.
4. **Full record reads:** only open records that passed the filter step.
5. **Raw imports:** read only when curated records are insufficient.

Do not ask agents to read every record for every task. Retrieve the smallest
useful set.

## 14. The Feedback Loop

Braingent compounds through repetition:

1. Search memory before planning.
2. Use prior context to avoid repeating mistakes.
3. Work with better defaults.
4. Use a live task when coordination or handoff matters.
5. Capture what changed.
6. Close completed live tasks by linking durable records.
7. Commit the memory update.
8. Start the next task with more context.

The repo becomes more useful every time this loop runs.

## 15. Why Markdown-Only First

Starting with Markdown keeps the system understandable.

You do not need:

- a database
- a server
- an account
- a paid tool
- an embedding pipeline
- a custom app

Those can be added later. The first useful version is a folder of well-written Markdown files.

When code is added, it should sit at the edges:

- setup code copies the starter pack and replaces placeholders;
- validation code checks frontmatter and structure;
- index code rebuilds Markdown, compact JSON, or SQLite from records;
- retrieval code searches indexes first and opens full Markdown only when
  evidence requires it;
- dashboard code reads Markdown and generated indexes without owning state.

That is the line: code can move, inspect, and index the house, but the house is
still the Markdown repo.
