---
title: Frontmatter Schema
description: The YAML fields every Braingent record carries — and how retrieval uses them.
section: Core Concepts
order: 4
---

Frontmatter is the index. Every durable record carries a small block of
YAML at the top. That block is what `braingent find`, `braingent recall`,
and the MCP tools actually filter on. The body of the record is for
humans; the frontmatter is for retrieval.

This page is the canonical schema.

## Required fields (all kinds)

Every record, regardless of kind, has these.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Unique. Pattern depends on kind: `BGT-0142`, `DEC-0218`, `REV-...`, `LRN-...`. |
| `record_kind` | string | One of: `task`, `agent-task`, `decision`, `review`, `learning`, `repo`, `project`, `topic`, `tool`, `ticket`, `person`. |
| `title` | string | Short, descriptive, sentence case. |
| `status` | string | Kind-specific (see below). |
| `date` | date or datetime | When the record was created (or finalized). |

## Common optional fields

| Field | Type | Used for |
| --- | --- | --- |
| `tags` | string[] | Free-form tags, lowercase, kebab-case. |
| `topics` | string[] | Slugs that match files in `topics/`. |
| `repos` | string[] | `<owner>/<repo>` or repo slugs in `repos/`. |
| `projects` | string[] | Slugs that match files in `projects/`. |
| `tools` | string[] | Slugs that match files in `tools/`. |
| `authors` | string[] | Humans + agents. `claude`, `codex`, `gpt`, `gemini`, `jj`. |
| `links` | string[] | Relative paths to other records. |
| `supersedes` | string | Record `id` that this one replaces. |
| `superseded_by` | string | Filled in when *this* record is replaced. |
| `priority` | string | `P0`–`P4` (mostly used by tasks). |
| `created` / `closed` | datetime | For tasks. ISO-8601. |

## Status vocabularies by kind

Different record kinds have different valid `status` values.

| Kind | Allowed `status` |
| --- | --- |
| Task / agent-task | `planned`, `in_progress`, `done`, `abandoned`, `blocked` |
| Decision | `proposed`, `accepted`, `rejected`, `superseded` |
| Review | `open`, `addressed`, `informational` |
| Learning | `draft`, `published`, `archived` |
| Repo | `active`, `archived` |
| Project | `active`, `paused`, `done`, `abandoned` |
| Topic | `living`, `frozen` |
| Tool | `active`, `deprecated` |
| Ticket | `open`, `in_progress`, `done`, `archived` |
| Person | `active`, `inactive` |

`braingent doctor` will warn you if a record uses a value outside its
kind's vocabulary.

## A complete example

A task record with most of the optional fields.

```yaml
---
id: BGT-0142
record_kind: agent-task
title: Backfill repo profile for acme/api
status: done
priority: P2
owner: claude
authors: [claude, jj]
repos: [acme/api]
projects: [acme-platform]
topics: [repo-profiles, backfill]
tools: [sqlite, ripgrep]
tags: [profile, indexing, agent-driven]
created: 2026-04-28T09:14Z
closed: 2026-04-28T11:02Z
links:
  - repositories/repo--acme--api/2026-04-12-jobs-runtime.md
  - repositories/repo--acme--api/2026-04-28-backfill-pr.md
  - topics/topic--reliability/2026-04-bullmq-process-churn.md
---
```

## How retrieval uses each field

- **`id`** — primary key for `braingent_get(id)`.
- **`kind`** — coarse filter: "give me all decisions in 2026".
- **`status`** — filter open vs done work, accepted vs rejected
  decisions.
- **`tags`, `topics`** — semantic filters used by `braingent_find`.
- **`repos`, `projects`, `tools`** — scoped queries: "what decisions
  affected `acme/api` last quarter?"
- **`authors`** — filter by who wrote (or co-wrote) the record.
- **`links`** — graph walks. "Show me all reviews that link to this
  decision."
- **`supersedes` / `superseded_by`** — chain old decisions to their
  replacements without losing history.

## Validation

`braingent doctor` and `braingent validate` check frontmatter for:

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
- **Run `doctor` before commits.** It's the cheapest way to keep memory
  clean.

## Where to go next

- [Record Kinds](/concepts/record-kinds/) — full examples per kind.
- [CLI Reference](/reference/cli/) — `braingent doctor`, `validate`,
  `find`.
- [Search & Recall](/guides/search-and-recall/) — using frontmatter at
  query time.
