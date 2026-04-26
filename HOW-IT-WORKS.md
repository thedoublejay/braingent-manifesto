# How Braingent Works

Braingent is built from a few simple parts that reinforce each other.

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

## 10. Raw Imports

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

## 11. The Feedback Loop

Braingent compounds through repetition:

1. Search memory before planning.
2. Use prior context to avoid repeating mistakes.
3. Work with better defaults.
4. Capture what changed.
5. Commit the memory update.
6. Start the next task with more context.

The repo becomes more useful every time this loop runs.

## 12. Why Markdown-Only First

Starting with Markdown keeps the system understandable.

You do not need:

- a database
- a server
- an account
- a paid tool
- an embedding pipeline
- a custom app

Those can be added later. The first useful version is a folder of well-written Markdown files.

