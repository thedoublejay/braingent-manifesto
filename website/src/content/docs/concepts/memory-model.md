---
title: Memory Model
description: Five surfaces of memory — pinned context, durable records, derived lookup, live tasks, and an optional dashboard.
section: Core Concepts
order: 1
---

Braingent doesn't have *one* memory. It has five surfaces, each tuned for a
different access pattern. Understanding the surfaces is what lets you (and
your agents) put the right thing in the right place.

## The five surfaces

| Surface | Lives in | Read when | Written when |
| --- | --- | --- | --- |
| Pinned Context | Repo root + `preferences/` | At session start, before planning | Rarely, deliberately |
| Durable Records | `decisions/`, `reviews/`, `learnings/`, `tasks/`, `repos/`, `projects/`, `topics/`, `tools/` | Before planning, during research | After meaningful work |
| Derived Lookup | `indexes/*`, MCP tools, search caches | Whenever you need a focused context pack | Auto-regenerated from records |
| Live Multi-Agent Tasks | `tasks/active/BGT-NNNN.md` | While work is in flight | Continuously, by all agents |
| Optional Dashboard | Local Bun + React (TanStack) UI | When humans need to see live state | Read-only |

The order matters. Pinned context is small and stable. Records are durable
and intentional. Derived lookup is fast and disposable. Live tasks are
ephemeral but coordinated. The dashboard is just a window.

## I. Pinned Context

Pinned context is the small set of files an agent reads *first*, every
time, before planning anything.

It includes:

- **Agent entrypoints** — `CLAUDE.md`, `AGENTS.md`,
  `CHATGPT_PROJECT_BRIEF.md`, `GEMINI.md`. Tool-specific instructions.
- **Standing preferences** — `preferences/*.md`. Your durable rules:
  capture policy, note-taking conventions, naming, privacy posture.
- **Active workflows** — `workflows/*.md`. Named procedures the agent runs
  on trigger phrases (e.g. `index-repo.md`, `cleanup-braingent.md`).

Keep this surface **short, stable, and high-signal**. If you find yourself
adding a new pinned file every week, you're probably writing a record
disguised as a preference.

> **Tip:** A good test for "is this pinned context?" — ask yourself: *do I
> want every single session to read this?* If the answer is "only when
> planning around topic X", it belongs in a record, not a preference.

## II. Durable Records

Durable records are the bulk of your memory. They're typed Markdown files
with structured frontmatter, organized into directories by record kind.

The eight record kinds:

- **Tasks** — what was done, with evidence trails.
- **Decisions** — what was chosen, with reasoning and tradeoffs.
- **Reviews** — what code review or PR review surfaced.
- **Learnings** — what you'd do differently next time, reusable across
  repos.
- **Repository profiles** — local conventions, patterns, gotchas for one
  repo.
- **Tool / version notes** — version-specific quirks, breaking changes.
- **Summaries** — synthesis pages that cite back to records.
- **Ticket stubs** — placeholders for upstream tickets you'll touch later.

Records carry frontmatter so they can be filtered (`kind`, `status`,
`tags`, `topics`, `repos`, `tools`, `date`). The body is for humans; the
frontmatter is for searching.

See [Record Kinds](/concepts/record-kinds/) for the full schema and
examples of each.

## III. Derived Lookup

Derived lookup is everything that exists *only* to make finding records
fast:

- **Generated indexes** — `indexes/by-topic.md`, `indexes/by-repo.md`,
  `indexes/by-decision.md`. Auto-regenerated from frontmatter.
- **Search caches** — local `.sqlite` databases for ripgrep-style full-text
  search.
- **MCP tools** — `braingent_find`, `braingent_get`, `braingent_guide`.
- **Context packs** — focused, citation-ready bundles built for a single
  task.

You can delete every byte of derived lookup and lose nothing. Run
`scripts/reindex.sh` and it all comes back from the records.

This is the part of the system that lets you scale to thousands of records
without forcing agents to re-read everything every session.

## IV. Live Multi-Agent Tasks

`tasks/active/BGT-NNNN.md` is a different beast: a single Markdown file
that **multiple agents and humans write to in parallel** while work is in
flight.

A live task file holds:

- The goal and current status.
- An activity log with timestamps and authors.
- Open questions and blockers.
- Links to related decisions, reviews, and PRs.

Multiple Claude sessions, a Codex run, and you typing notes can all
update the same file. Git handles the conflicts. The dashboard renders
the live view. When work is done, `scripts/task-archive.sh` moves the file
from `tasks/active/` to `tasks/archive/` and marks it `status: closed`.

This is how Braingent supports multi-agent coordination without a
synchronization layer. See [Multi-Agent
Coordination](/guides/multi-agent-tasks/).

## V. Optional Dashboard

The dashboard is a local read-only **Bun + React + TanStack** UI that renders:

- The live `tasks/active/` queue.
- Generated indexes.
- Recent capture activity.
- Doctor / validate status.

It runs on your machine, against your filesystem. It never writes. Agents
and humans still capture through their normal flow — the dashboard just
makes the live state easier to see.

Use it when you have several agents in flight at once, or when a teammate
joins and needs a quick scan of what's happening.

## How the surfaces talk to each other

```
        ┌──────────────────────┐
        │  Pinned Context (I)  │  ← read every session, top of context
        └──────────┬───────────┘
                   │ tells the agent…
                   ▼
        ┌──────────────────────┐
        │ Durable Records (II) │  ← canonical memory, in Git
        └──────────┬───────────┘
                   │ regenerates…
                   ▼
        ┌──────────────────────┐
        │ Derived Lookup (III) │  ← indexes, search, MCP, context packs
        └──────────┬───────────┘
                   │ surfaces…
                   ▼
        ┌──────────────────────┐
        │ Live Tasks (IV)      │  ← in-flight coordination
        └──────────┬───────────┘
                   │ visualized by…
                   ▼
        ┌──────────────────────┐
        │ Dashboard (V)        │  ← read-only window
        └──────────────────────┘
```

The arrow that *doesn't* exist on this diagram is just as important: live
tasks and the dashboard never write to durable records on their own. A
human or agent still has to *capture* the outcome explicitly. That keeps
durable memory deliberate.

## Where to go next

- [Repository Shape](/concepts/repository-shape/) — the directory map.
- [Record Kinds](/concepts/record-kinds/) — what goes in each kind of
  record.
- [Frontmatter Schema](/concepts/frontmatter-schema/) — the fields that
  make searching work.
