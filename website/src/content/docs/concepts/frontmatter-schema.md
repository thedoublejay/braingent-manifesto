---
title: Frontmatter Schema
description: The YAML fields every Braingent record carries — and how retrieval uses them.
section: Core Concepts
order: 4
---

Frontmatter is the index. Every durable record carries a small block of
YAML at the top. That block is what `scripts/find.sh`,
`scripts/recall.sh`, and the MCP tools actually filter on. The body of
the record is for humans; the frontmatter is for retrieval.

This page is the canonical schema.

## Required fields (all kinds)

Every record, regardless of kind, has these.

| Field | Type | Notes |
| --- | --- | --- |
| `record_kind` | string | One of: `task`, `agent-task`, `decision`, `review`, `learning`, `interaction`, `version`, `note`, `summary`, `profile`, `ticket-stub`. |
| `title` | string | Short, descriptive, sentence case. |
| `status` | string | Kind-specific (see below). |
| `date` | date or datetime | Required for most durable records; summaries use `date_imported`. |

## Common optional fields

| Field | Type | Used for |
| --- | --- | --- |
| `tags` | string[] | Free-form tags, lowercase, kebab-case. |
| `topics` | string[] | Slugs that match files in `topics/`. |
| `repositories` | string[] | Repo slugs under `repositories/`, such as `repo--example--owner--repo`. |
| `projects` | string[] | Project slugs under `orgs/*/projects/`. |
| `tools` | string[] | Slugs that match files in `tools/`. |
| `authors` | string[] | Humans + agents. `claude`, `codex`, `gpt`, `gemini`, `jj`. |
| `links` | string[] | Relative paths to other records. |
| `supersedes` | string | Record `id` that this one replaces. |
| `superseded_by` | string | Filled in when *this* record is replaced. |
| `priority` | string | `critical`, `high`, `medium`, or `low` for live agent tasks. |
| `created` / `closed` | datetime | For tasks. ISO-8601. |

## Status vocabularies by kind

Different record kinds have different valid `status` values.

| Kind | Allowed `status` |
| --- | --- |
| Task | `planned`, `active`, `blocked`, `completed`, `superseded` |
| Agent-task | `triage`, `todo`, `in-progress`, `in-review`, `blocked`, `closed` |
| Decision | `proposed`, `accepted`, `rejected`, `superseded` |
| Review | `draft`, `completed`, `superseded` |
| Learning | `active`, `superseded` |
| Interaction | `active`, `superseded` |
| Version | `active`, `superseded` |
| Note | `draft`, `active`, `completed`, `superseded` |
| Summary | `draft`, `completed` |
| Profile | `active`, `archived`, `superseded` |
| Ticket-stub | `active`, `completed`, `abandoned` |

`scripts/doctor.sh` will warn you if a record uses a value outside its
kind's vocabulary.

## A complete example

A task record with most of the optional fields.

```yaml
---
id: BGT-0142
record_kind: agent-task
title: Backfill repo profile for acme/api
status: in-progress
status_category: active
priority: high
claimed_by: agent--claude-code
ai_tools: [Claude]
repositories: [repo--acme--api]
project: project--acme--platform
topics: [topic--repo-profiles]
tools: [sqlite, ripgrep]
created: 2026-04-28T09:14Z
closed: null
resolution: null
---
```

## How retrieval uses each field

- **`id`** — primary key for live `agent-task` records.
- **`kind`** — coarse filter: "give me all decisions in 2026".
- **`status`** — filter open vs done work, accepted vs rejected
  decisions.
- **`tags`, `topics`** — semantic filters used by `braingent_find`.
- **`repositories`, `projects`, `tools`** — scoped queries: "what decisions
  affected `acme/api` last quarter?"
- **`authors`** — filter by who wrote (or co-wrote) the record.
- **`links`** — graph walks. "Show me all reviews that link to this
  decision."
- **`supersedes` / `superseded_by`** — chain old decisions to their
  replacements without losing history.

## Validation

`scripts/doctor.sh` and `scripts/validate.sh` check frontmatter for:

- Missing required fields.
- `status` values outside the kind's vocabulary.
- Broken `links:` (file doesn't exist).
- Duplicate `id`s.
- Malformed dates.

Both commands exit non-zero on errors so you can wire them into pre-commit
or CI.

## Tips for staying disciplined

- **Use slugs, not display names.** `acme/api` not `Acme API`.
- **Lowercase tags, kebab-case slugs.** `repo-profiles`, not
  `Repo_Profiles`.
- **Don't invent fields ad-hoc.** Add them to the template if you need
  them everywhere; otherwise put them in the body, not the frontmatter.
- **Quote dates.** YAML's date parsing has surprised more than one person.
  ISO-8601 strings are always safe.
- **Run `scripts/doctor.sh` before commits.** It's the cheapest way to keep memory
  clean.

## Where to go next

- [Record Kinds](/concepts/record-kinds/) — full examples per kind.
- [CLI Reference](/reference/cli/) — `doctor`, `validate`, and `find`.
- [Search & Recall](/guides/search-and-recall/) — using frontmatter at
  query time.
