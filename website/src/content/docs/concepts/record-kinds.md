---
title: Record Kinds
description: The eight record kinds Braingent uses, what each one contains, and when to write each.
section: Core Concepts
order: 3
---

Braingent recognizes eight record kinds. Each has a directory, a template,
a frontmatter shape, and a clear answer to *when do I write one of these?*

This page is the field guide.

## At a glance

Records cluster by **context** (the project, repo, topic, or tool they
belong to), not by kind. The `record_kind:` frontmatter field is what
discriminates them. So a decision about `acme/api` lives in
`repositories/repo--acme--api/` next to that repo's reviews and
learnings — not in a separate top-level `decisions/` directory.

| Kind | `record_kind:` | Lives in | Write when |
| --- | --- | --- | --- |
| Task (durable) | `task` | `tasks/archive/` or context dir | A piece of work is finished. |
| Live agent-task | `agent-task` | `tasks/active/BGT-NNNN.md` | Multi-agent coordination is in flight. |
| Decision | `decision` | The relevant context dir (repo / project / topic) | A non-obvious choice is made. |
| Review | `review` | The relevant context dir | A PR or code review surfaces something durable. |
| Learning | `learning` | The relevant context dir | A reusable lesson is identified. |
| Repo profile | `repo` | `repositories/<repo-slug>/profile.md` | A repo's local conventions need to be captured. |
| Project brief | `project` | `orgs/<org>/projects/<project>/brief.md` | A project starts or pivots. |
| Topic page | `topic` | `topics/<topic-slug>/<file>.md` | A topic spans multiple repos and needs synthesis. |
| Tool / version note | `tool` | `tools/<tool-slug>/<version>.md` | A tool upgrade has gotchas worth remembering. |
| Ticket stub | `ticket` | `tickets/ticket--<source>--<id>/` | An upstream ticket needs a home in memory. |
| Person | `person` | `people/<slug>.md` | A reviewer/stakeholder/team member matters across work. |

## I. Task records

Tasks capture the *what was done*: the goal, what changed, evidence,
follow-ups.

```yaml
---
id: BGT-0142
record_kind: agent-task
title: Backfill repo profile for acme/api
status: done            # planned | in_progress | done | abandoned
priority: P2
owner: claude
repos: [acme/api]
projects: [acme-platform]
topics: [repo-profiles, backfill]
created: 2026-04-28T09:14Z
closed: 2026-04-28T11:02Z
links:
  - decisions/2026-04-12-jobs-runtime.md
  - reviews/2026-04-28-backfill-pr.md
---

## Goal
Generate `repos/acme-api/profile.md` from local docs, git history, open PRs.

## What was done
- Scanned README + ADRs (3 ADRs surfaced).
- Drafted profile, 14 sections.
- jj flagged auth section as stale; rewrote.

## Evidence
- PR #428: https://github.com/acme/api/pull/428
- Reindex output: `indexes/recent.md` updated.

## Follow-ups
- BGT-0145 — refresh `tools/sqlite-3.46.md` based on this work.
```

**Write when:** a piece of work is shippable, even small. PRs opened,
fixes landed, refactors merged, decisions reached.

## II. Decision records

ADR-style: the choice, the context, the consequences. Decisions live
forever and supersede each other rather than getting deleted.

```yaml
---
id: DEC-0218
record_kind: decision
title: Move job runtime from BullMQ to Temporal
status: accepted        # proposed | accepted | rejected | superseded
date: 2026-04-12
authors: [jj, claude]
tags: [runtime, jobs, reliability]
supersedes: DEC-0091
---
```

**Write when:** you choose between two or more reasonable options, *and*
the choice is non-obvious enough that future-you might want to revisit it.
Don't write a decision record for "we used `let` instead of `const` here";
do write one for "we picked Temporal over BullMQ".

## III. Review records

Code review and PR review notes that surface durable signal.

```yaml
---
id: REV-2026-04-28-jobs-runtime-pr
record_kind: review
title: PR #428 review — Temporal migration first slice
date: 2026-04-28
reviewer: jj
repos: [acme/api]
links: [decisions/2026-04-12-jobs-runtime.md, tasks/done/BGT-0142.md]
tags: [temporal, jobs, pr-review]
---
```

**Write when:** the review surfaced a tradeoff, a missed case, or a
pattern worth re-applying. Skip it for routine "looks good, ship it"
reviews.

## IV. Learning records

Reusable lessons not tied to a single repo. The shape that travels.

```yaml
---
id: LRN-2026-04-bullmq-process-churn
record_kind: learning
title: BullMQ silent retries under process churn
date: 2026-04-12
tags: [jobs, reliability, runtime]
applies_to: [bullmq, fly.io]
links: [decisions/2026-04-12-jobs-runtime.md]
---
```

**Write when:** the same lesson would apply if you encountered the
problem in a different repo. Repo-specific gotchas go in the repo
profile, not here.

## V. Repository profiles

One file per repo: local conventions, build commands, gotchas, hot files,
agent guidance.

```yaml
---
id: repo-acme-api
record_kind: repo
title: acme/api
slug: acme-api
maintainers: [jj]
languages: [typescript, sql]
runtime: node-20
frameworks: [fastify, drizzle]
tags: [billing, api, jobs]
links:
  - decisions/2026-04-12-jobs-runtime.md
  - learnings/2026-04-bullmq-process-churn.md
---
```

**Write when:** an agent will work in this repo more than once. The
profile saves you re-explaining the layout next time.

## VI. Project briefs

One file per project: goal, stakeholders, current phase, key decisions.

```yaml
---
id: proj-acme-platform
record_kind: project
title: acme-platform
status: active          # active | paused | done | abandoned
phase: GA               # discovery | mvp | beta | GA | maintenance
started: 2026-01-15
stakeholders: [jj, ada, sam]
repos: [acme/api, acme/web, acme/jobs]
tags: [platform, multi-repo]
---
```

**Write when:** a piece of work spans more than one repo, or has
stakeholders beyond the immediate engineering team.

## VII. Topic pages

Cross-cutting synthesis. Auth across all repos. The migration playbook.
The "we always do X for Y" pattern.

```yaml
---
id: topic-auth
record_kind: topic
title: Authentication across acme repos
last_updated: 2026-04-30
repos: [acme/api, acme/web, acme/jobs, acme/admin]
tags: [auth, security, sessions]
links:
  - decisions/2025-09-04-jwt-rotation.md
  - decisions/2026-02-11-session-store-redis.md
---
```

**Write when:** you find yourself explaining the same cross-cutting topic
in two different sessions. Promote it.

## VIII. Tool / version notes

Quirks tied to a specific tool version. Especially useful for upgrades.

```yaml
---
id: tool-sqlite-3.46
record_kind: tool
title: SQLite 3.46 upgrade notes
tool: sqlite
version: '3.46'
date: 2026-04-15
tags: [sqlite, upgrade, indexes]
applies_to_repos: [acme/api]
---
```

**Write when:** a tool's behavior changed in a way that broke (or
unblocked) something. Save the next person the half-day of debugging.

## How records reference each other

Two mechanisms:

1. **`links:` in frontmatter** — for retrieval and graph queries.
2. **Markdown links in the body** — for prose context.

A well-linked record has both. Frontmatter `links` are how
`braingent_find` walks the graph; Markdown links are how a human reading
the page gets to the next thing.

## Where to go next

- [Frontmatter Schema](/concepts/frontmatter-schema/) — the fields that
  every kind shares.
- [Repository Shape](/concepts/repository-shape/) — where each kind goes
  on disk.
- [The Capture Loop](/guides/capture-loop/) — when to call which kind.
