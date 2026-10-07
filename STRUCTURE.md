# Structure

This is the recommended structure for a Braingent-style memory repo.

```text
.
|-- README.md
|-- AGENTS.md
|-- CLAUDE.md
|-- CHATGPT_PROJECT_BRIEF.md
|-- INDEX.md
|-- CURRENT_STATE.md
|-- preferences/
|-- templates/
|-- workflows/
|-- tasks/                  # optional live agent-task queue
|-- dashboard/              # optional local task dashboard
|-- orgs/                   # includes <org>/epics/ for epic pages
|-- repositories/
|-- topics/
|-- tools/
|-- people/
|-- tickets/
|-- inbox/
|-- imports/
`-- indexes/
```

## Root Files

| File | Purpose |
| --- | --- |
| `README.md` | Explains what the memory repo is and how to use it. |
| `AGENTS.md` | Codex-style agent instructions and read order. |
| `CLAUDE.md` | Claude-style agent instructions and read order. |
| `CHATGPT_PROJECT_BRIEF.md` | Copyable ChatGPT project instructions. |
| `INDEX.md` | Human-curated map of important pages and records. |
| `CURRENT_STATE.md` | Current defaults, open questions, and recent changes. Active work lives in epics: see `indexes/epics.md`. |
| `AGENT-TASK-COORDINATION.md` | Optional v3 module for Markdown-based multi-agent task coordination. |

## Core Directories

### `preferences/`

Standing rules that agents should read before planning. Examples:

- naming
- agent workflow
- capture policy
- search recipes
- taxonomy
- content style
- note-taking and AI memory
- planning expectations
- code review expectations
- commit and PR hygiene
- project conventions
- privacy and safety

### `templates/`

Copyable Markdown templates for durable records:

- task
- minimal task
- review
- decision
- learning
- note
- repository profile
- tool version
- person interaction
- ticket stub
- epic page
- import summary

### `workflows/`

Step-by-step procedures triggered by explicit phrases.

Example:

- "index this repo to memory"
- "capture this"
- "backfill this project"
- "clean up braingent"
- "retrieve braingent context"

### `orgs/`

Organizations, clients, teams, or personal work areas.

Recommended key format:

```text
org--<slug>
```

Example:

```text
org--personal
org--client-name
```

### `orgs/<org>/projects/`

Projects inside an organization.

Recommended key format:

```text
project--<org-slug>--<project-slug>
```

### `orgs/<org>/epics/`

Epics: ad hoc groupings of work around one idea, such as `performance` or `checkout-latency`. An epic is created the first time work on the idea starts and is retired when the work ends.

Recommended key format:

```text
epic--<org-slug>--<slug>
```

The slug is lowercase kebab-case, one to four words. Use the same slug everywhere:

| Surface | Form |
| --- | --- |
| Tracker | A flat label `epic:<slug>`, so a ticket can be in two epics. |
| Pull requests | The same label `epic:<slug>`. |
| Entity | `orgs/<org>/epics/epic--<org-slug>--<slug>/README.md` |
| Record frontmatter | `epic: [epic--<org-slug>--<slug>]` |
| Daily log | `braingent daily-log ... --epic <slug>` |

The page is a mutable profile with the sections `## Goal`, `## Scope and sub-groups`, `## Links`, `## Decisions`, `## Config to enable` and `## Log`. It links to tickets and PRs and never copies their status. Frontmatter carries `status` (`active`, `paused`, `done` or `dropped`), an optional `parent_epic` for a sub-group that grew into its own epic, `created` and `updated`.

Create one with `braingent new epic --org <org> --slug <slug>`.

#### Config to enable

Anything that must be set before the work is live goes in the page's `## Config to enable` section as a fenced YAML block whose first line is `# config-to-enable/v1`. The same block is valid in a PR body or a ticket description, so `braingent config-ledger` can merge them.

```yaml
# config-to-enable/v1
- key: FEATURE_X_ENABLED
  kind: env          # env | flag | tf_var | helm_value | db_setting | db_role | operator_step | verify_check
  service: app
  repo: infra-repo
  path: apps/app/overlays/<env>/values.yaml
  env: staging       # staging | prod | all
  default: "false"
  target: "true"
  introduced_by: app-repo#12
  enabled_by: null   # repo#n once raised
  depends_on: []
  status: pending    # pending | pr-open | applied | verified | not-needed | dormant
  verify: "feature_x.batch > 0 within 1h"
```

`key`, `kind` and `status` are required. The ledger names each setting and where it lives. The value stays in source control, and a secret is written as "secret, see <store>". A section containing only `None` means nothing must be set.

### `orgs/<org>/projects/<project>/records/`

Task, review, decision, note, and summary records for project-specific work.

### `repositories/`

Repository profiles. These capture stack, common commands, conventions, risks, and important records.

Recommended key format:

```text
repo--<host>--<owner>--<repo-name>
```

Example:

```text
repo--github--owner--api-service
```

### `topics/`

Reusable learnings and decisions grouped by topic.

Recommended key format:

```text
topic--<slug>
```

Examples:

```text
topic--ai-memory
topic--rust
topic--testing
topic--backend-architecture
```

### `tools/`

Tool, framework, model, library, runtime, and version records.

Recommended key format:

```text
tool--<slug>
```

### `people/`

Optional collaboration context when useful for future engineering work. Keep it professional, minimal, and privacy-aware.

Recommended key format:

```text
person--<slug>
```

### `tickets/`

Cross-cutting ticket stubs. Use these only when one ticket spans multiple repositories or projects.

Recommended key format:

```text
ticket--<system>--<id>
```

### Optional `tasks/`

Some teams may want a live, Markdown-based queue for multi-agent coordination. Keep this separate from durable records and external ticket stubs.

Recommended layout:

```text
tasks/
|-- CLAUDE.md
|-- README.md
|-- INDEX.md
|-- active/
|   `-- BGT-0001--short-slug.md
`-- archive/
    `-- YYYY-MM/
```

Live task files use `record_kind: agent-task`. Retrospective task records use
`record_kind: task` and stay in the durable memory layer.

Use task IDs like `BGT-0001`, `BGT-0002`, and so on. The prefix is just a
local namespace for your memory repo; it is not a Jira or GitHub issue key.

See `AGENT-TASK-COORDINATION.md`.

### Optional `dashboard/`

If you build a local task dashboard, keep it under a scoped directory such as:

```text
dashboard/
`-- tasks/
```

The dashboard should read `tasks/active/` and generated indexes. It should not
store a second copy of task state.

The public manifesto repo includes a copyable sample at
`examples/task-dashboard/`. Copy it into `dashboard/tasks/` when you want a
working Bun/React UI.

### `inbox/`

Temporary notes waiting to be normalized. Keep this small. Empty it regularly.

### `imports/`

Raw AI exports, PR summaries, ticket exports, or local docs before they are curated.

Recommended split:

```text
imports/raw/
imports/summaries/
```

### `indexes/`

Human or generated indexes. If you do not have automation yet, maintain simple Markdown indexes by hand.

Common generated indexes include:

- `records.md`
- `records.json`
- `followups.md`
- `memory-summary.md`
- `stale-candidates.md`
- `agent-task-queue.md`
- `agent-task-graph.md`

## Record Filename Format

Use short, dated, readable filenames:

```text
yyyy-mm-dd--record-kind--short-subject.md
```

Examples:

```text
2026-04-26--task--initialize-memory-repo.md
2026-04-26--decision--use-thin-agent-entrypoints.md
2026-04-26--learning--capture-after-task-completion.md
```

Keep full metadata in frontmatter. Do not overload filenames with every ticket, repo, PR, or branch.

## Frontmatter Pattern

Every durable record starts with YAML frontmatter:

```yaml
---
title: Initialize Memory Repo
record_kind: task
status: completed
date: 2026-04-26
timezone: <timezone>
organization: org--personal
project: project--personal--memory
ticket: null
repositories: []
prs: []
commits: []
ai_tools: [Claude]
people: []
topics: [topic--ai-memory]
tools: []
agent_task: null
---
```

The exact fields can vary by record kind, but the convention should stay consistent.
