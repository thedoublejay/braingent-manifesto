---
title: The Capture Loop
description: When to capture, what to skip, and the trigger phrases every Braingent agent already understands.
section: Guides
order: 2
---

Capture is the *write half* of Braingent. Search-before-plan is what makes
sessions smarter; capture-after-work is what makes the next session
smarter. Together, they're the loop.

This page covers the trigger phrases, the capture policy, and the small
set of rules that keep durable memory clean.

## The default trigger phrases

Every Braingent-wired agent recognizes these phrases as *capture this
piece of work*:

- `capture this`
- `save to braingent`
- `write to braingent`
- `dump this to braingent`
- `task done`
- `task done thanks`
- `done thanks`
- `ok done`
- `ok task done`

You can configure more in `preferences/capture-policy.md`. The starter
pack lists the canonical set so every agent and tool stays consistent.

## Implicit triggers

Capture should also happen automatically (without an explicit phrase)
after:

- A pull request opens.
- A pull request merges.
- A ticket closes (`gh issue close`, Linear/Jira state change).
- A code review surfaces a durable tradeoff.
- A non-obvious decision is reached.
- A reusable learning is identified.

If you find yourself saying *capture this* on every PR, that's a sign
your agent's preferences need to lean more proactive. Tune
`preferences/capture-policy.md`.

## What gets captured

When an agent receives a capture trigger, it picks one record kind based
on what was just done:

| Outcome | Record kind |
| --- | --- |
| Code shipped | Task |
| A non-obvious choice was made | Decision |
| A PR or code review surfaced something durable | Review |
| A lesson learned that could apply elsewhere | Learning |
| A repo's local conventions were figured out | Repo profile (or update existing) |
| A new project kicked off or pivoted | Project brief |
| A topic spans multiple records | Topic page (synthesis) |
| A tool upgrade had quirks | Tool / version note |

Sometimes one piece of work generates more than one record (e.g. a task
*and* a decision). That's fine — write both.

## The minimum viable record

The bar for capture is **deliberately low**. Don't let perfect frontmatter
be the enemy of any record.

A minimal task record looks like this:

```yaml
---
id: BGT-0143
kind: task
title: Fix billing webhook race
status: done
date: 2026-04-29
repos: [acme/api]
tags: [billing, webhooks, fix]
---

## Goal
Stop duplicate billing events when the webhook handler retried.

## What was done
Added idempotency key on the handler. Backfilled missing keys from
last 30 days. PR #431 merged.

## Evidence
- PR #431
- Replay test passed: `bun test billing/webhook.test.ts`
```

That's the whole record. Start there. Add fields as you find you actually
filter on them.

## What never gets captured

The capture policy in the starter pack lists *don't store* explicitly,
because privacy is structural in Braingent:

- **Secrets, tokens, credentials** — ever.
- **Raw chat transcripts** — durable signal, not chat scrollback.
- **Sensitive personal data** — anything you wouldn't put in a public
  repo.
- **Speculative roadmap content** the user hasn't actually decided on.

If you ever see one of these in a draft record, the right move is to
abort the capture and fix the prompt — not to redact post-hoc.

## How agents pick a slug

The agent generates a slug from the title:

- Lowercase.
- Kebab-case.
- Date-prefixed for `decisions/` and `reviews/`:
  `2026-04-12-jobs-runtime.md`.
- Task ID-prefixed for tasks: `BGT-0142-backfill-acme-api.md`.

If a slug already exists, the agent appends `-2`, `-3`, etc.

## Where the file lands

Records cluster by **context** (project, repo, topic, tool), not by
kind. The agent picks the right context directory and stamps
`record_kind:` in frontmatter:

| Kind | Directory |
| --- | --- |
| task (durable) | `tasks/archive/` or the relevant context dir |
| agent-task (live) | `tasks/active/BGT-NNNN.md` |
| decision / review / learning | The matching `repositories/<slug>/`, `orgs/<o>/projects/<p>/`, or `topics/<slug>/` |
| repo profile | `repositories/<repo-slug>/profile.md` |
| project brief | `orgs/<org>/projects/<project>/brief.md` |
| topic page | `topics/<topic-slug>/<slug>.md` |
| tool note | `tools/<tool-slug>/<version>.md` |
| ticket stub | `tickets/ticket--<source>--<id>/` |
| person | `people/<slug>.md` |
| unsorted | `inbox/` (drains during cleanup) |

If the agent gets confused between *task* and *decision*, the right
question to ask is: *did we choose between two reasonable options?* Yes
→ decision. Just shipped a fix → task.

If the agent isn't sure where a record belongs, it should land in
`inbox/` and get classified during the next cleanup pass.

## What capture costs

Almost nothing. A capture is:

- One small file write.
- One frontmatter validation pass.
- One Git commit.

Total wall-clock time: a few seconds. Most of that is the agent thinking
about the right title.

The output, on the other hand, compounds. A captured decision will be
read dozens of times across sessions, agents, and humans for years.

## Where to go next

- [Search & Recall](/guides/search-and-recall/) — the read half of the
  loop.
- [Record Kinds](/concepts/record-kinds/) — full templates per kind.
- [Frontmatter Schema](/concepts/frontmatter-schema/) — the fields that
  let captures be searched.
