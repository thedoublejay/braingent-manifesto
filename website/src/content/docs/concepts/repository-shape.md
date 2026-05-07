---
title: Repository Shape
description: The directory map of a Braingent memory repo — and the rationale behind every folder.
section: Core Concepts
order: 2
---

A Braingent memory repo is a regular Git repository with a specific
directory layout. The shape is opinionated but small. Most folders
exist so that agents can navigate by convention instead of having to
ask.

This is the layout shipped in the starter pack. Today the public shell is
copyable files plus repo-local scripts; a future packaged setup helper can
stamp the same shape interactively.

## At a glance

```text
braingent/
├── README.md                 # human-facing index
├── INDEX.md                  # navigable site map
├── CURRENT_STATE.md          # what's live right now
├── FILE-TREE.md              # generated tree (refreshed by reindex)
├── CLAUDE.md                 # Claude entrypoint
├── AGENTS.md                 # Codex entrypoint
├── CHATGPT_PROJECT_BRIEF.md  # ChatGPT brief
├── GEMINI.md                 # Gemini CLI entrypoint
│
├── preferences/              # standing rules (pinned)
├── workflows/                # named procedures (pinned, trigger-loaded)
├── templates/                # frontmatter-stamped templates
│
├── orgs/<org-slug>/projects/<project-slug>/   # project records (nested)
├── repositories/<repo-slug>/                  # per-repo profiles + records
├── topics/<topic-slug>/                       # cross-cutting topic pages
├── tools/<tool-slug>/                         # tool / version notes
├── tickets/                                   # ticket stubs
├── people/                                    # people records
│
├── tasks/
│   ├── active/               # in-flight BGT-NNNN files
│   └── archive/              # archived task records
│
├── inbox/                    # unsorted captures awaiting triage
├── imports/
│   ├── raw/                  # raw imports from other systems
│   └── summaries/            # condensed imports
│
├── indexes/                  # generated, never edited by hand
└── dashboard/                # optional local dashboard data
```

## I. Root files

These live at the repo root because every agent and human reads them
first.

- **`README.md`** — what this memory repo is, who maintains it.
- **`INDEX.md`** — a navigable site map. Pointers, not content.
- **`CURRENT_STATE.md`** — short summary of what's live: open tasks,
  recent decisions, active projects. Refreshed during cleanup.
- **`FILE-TREE.md`** — refreshed by `scripts/reindex.sh`; humans rarely
  edit it.
- **`CLAUDE.md`, `AGENTS.md`, `CHATGPT_PROJECT_BRIEF.md`,
  `GEMINI.md`** — agent entrypoints. Short, ideally under 200 lines.
  Tells the agent where memory is, what to read first, when to capture,
  and what never to store.

## II. `preferences/` — standing rules

Files like `preferences/capture-policy.md`, `preferences/note-taking-and-ai-memory.md`,
`preferences/code-style.md`, `preferences/agent-task-protocol.md`. These
are **pinned**: agents read them every session.

Use it for things you'd want to apply across all your work:
- "Default capture phrases are *capture this*, *task done*, *save to
  braingent*."
- "Never include `Co-Authored-By` trailers in commit messages."
- "Always state assumptions before picking among multiple
  interpretations."

Keep them short and specific. A 2,000-line preferences file is a
preferences file nobody reads.

## III. `workflows/` — named procedures

Each file is a procedure that runs on a trigger phrase. The agent loads
it *only* when the trigger fires.

Examples in the starter pack:

- `index-repo.md` — backfill records for an existing codebase.
- `cleanup-braingent.md` — periodic maintenance.
- `retrieve-context.md` — build a focused context pack for one task.

See [Index Your Repos](/guides/index-your-repos/) and
[Keeping Memory Healthy](/guides/maintenance/) for the workflows in
action.

## IV. `templates/` — copy-and-customize starters

Templates are frontmatter-stamped Markdown files. When the agent
captures, it copies a template and fills in the body — so captured
records always have consistent frontmatter.

The starter pack includes templates for every record kind: full and
minimal task records, decision records (ADR-style), reviews, learnings,
repo profiles, tool/version notes.

## V. Records, organized by context

Records cluster by **context**, not by kind. The `record_kind:`
frontmatter field is what discriminates them — same directory can hold
tasks, decisions, reviews, and learnings for the same context.

### `orgs/<org-slug>/projects/<project-slug>/`

Project-scoped records nest here. A project record (the brief itself)
plus all the decisions, reviews, and learnings for that project live
together. Organizations group projects.

### `repositories/<repo-slug>/`

Per-repo profiles + records. The profile (`record_kind: profile`) sits
alongside repo-specific decisions, reviews, and learnings. A repo slug
follows the `repo--<owner>--<name>` convention in the starter pack.

### `topics/<topic-slug>/`

Cross-cutting synthesis pages. Auth across all our repos. The migration
playbook. The "we always do X for Y" pattern.

### `tools/<tool-slug>/`

Tool and version notes. "Bun 1.3 quirks", "Postgres 16 upgrade
gotchas". Each tool gets its own folder.

### `tickets/`

Ticket stubs and ticket-derived records. The starter pack uses
`tickets/ticket--<source>--<id>/` as the convention so ticket IDs are
greppable.

### `people/`

People records — engineers, reviewers, stakeholders. Useful when an
agent should know who reviews auth-related work, who owns a service,
who's on PTO this week. Standard privacy applies: nothing sensitive.

## VI. `tasks/`

Live multi-agent coordination. See [Multi-Agent
Coordination](/guides/multi-agent-tasks/).

- **`tasks/active/`** — `BGT-NNNN.md` files for work in flight.
- **`tasks/archive/`** — closed tasks moved here on
  `scripts/task-archive.sh`.

Live tasks use `record_kind: agent-task` and IDs like `BGT-0142`. When
a live task closes, important outcomes get **promoted** into durable
records (decisions, learnings) under the right context directory, with
`agent_task: BGT-0142` linking back.

## VII. `inbox/` and `imports/`

The "incoming" surfaces.

- **`inbox/`** — unsorted captures the agent (or you) haven't yet
  classified into the right context directory. Drains during cleanup.
- **`imports/raw/`** — raw imports from other systems (Jira CSV
  exports, ticket dumps, Slack channel exports if you really must).
- **`imports/summaries/`** — condensed imports the agent produced from
  `imports/raw/`.

These are intermediate surfaces. Records that matter graduate to a
proper context directory.

## VIII. `indexes/` — generated, untouched by humans

Auto-generated retrieval aids:

- `indexes/recent.md` — newest 50 records.
- `indexes/by-topic.md`, `by-repo.md`, `by-tool.md` — frontmatter rolls.
- `indexes/decisions-index.md` — chronological decision list.
- `.sqlite` files for full-text search.

Run `scripts/reindex.sh` to regenerate. Never edit by hand.

## IX. `dashboard/` (optional)

Local Bun + React (TanStack) read-only UI over `tasks/active/`. See
[Local Dashboard](/guides/dashboard/). The `dashboard/` directory in
the starter pack is the install target — copy the example into it and
run `bun install && bun run dev`.

## Naming conventions

Rules that make navigation predictable:

- **Slugs use the `--`-separator convention** for context dirs:
  `repositories/repo--acme--api/`, `orgs/org--acme/projects/project--acme--platform/`.
- **Dates prefix files** in date-sensitive contexts:
  `2026-04-12-jobs-runtime.md`.
- **Task IDs** follow `BGT-NNNN` (zero-padded, monotonically
  increasing).
- **Frontmatter fields are lowercase**, values are quoted only when
  YAML needs them.

## What the shape *isn't*

- It's not a hierarchy by *record kind*. Decisions don't live in
  `decisions/` — they live in the context directory of the project,
  repo, or topic they belong to, with `record_kind: decision` in
  frontmatter.
- It's not a database. There are no foreign keys; cross-references are
  Markdown links and `links:` arrays in frontmatter.
- It's not a CMS. There's no admin UI; you edit files.

## Where to go next

- [Record Kinds](/concepts/record-kinds/) — what each `record_kind:`
  value means.
- [Frontmatter Schema](/concepts/frontmatter-schema/) — the fields that
  make retrieval work.
- [Memory Model](/concepts/memory-model/) — how the surfaces fit
  together.
