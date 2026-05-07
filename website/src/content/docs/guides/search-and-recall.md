---
title: Search & Recall
description: Find prior context fast — by frontmatter, by topic, by repo, by graph walk, or by full-text search.
section: Guides
order: 3
---

If capture is the write half, **search and recall** is the read half. This
page covers the four ways to query Braingent memory, when to use each, and
how to build a focused context pack instead of dumping everything into
your agent's prompt.

## The four query modes

| Mode | Tool | Best for |
| --- | --- | --- |
| Structured filter | `braingent find` / `braingent_find()` MCP | "All decisions in `acme/api` last quarter" |
| Direct fetch | `braingent get` / `braingent_get()` MCP | "Read DEC-0218 in full" |
| Graph walk | `braingent recall` / `braingent_find(links=...)` | "Everything related to BGT-0142" |
| Full-text | `rg` / `braingent search` | "Where did we mention Temporal idempotency?" |

Use the most specific mode that answers your question. Frontmatter
filters are cheap and precise; full-text grep is the fallback when you
don't know what you're looking for.

## I. Structured filter — `braingent find`

Filter records by frontmatter fields.

```bash
# all accepted decisions about jobs in 2026
braingent find \
  --kind decision \
  --status accepted \
  --tag jobs \
  --since 2026-01-01

# every record that touches a specific repo
braingent find --repo acme/api --limit 20

# tasks owned by a specific agent
braingent find --kind task --owner claude --status done
```

Output is a sorted list of `id` + `title` + `path`. Pipe it into
`braingent get` for content.

> **Tip:** `--limit` is your friend. Most useful queries return fewer
> than 20 records; if you're getting hundreds back, your filter is too
> loose.

## II. Direct fetch — `braingent get`

Read one record. Two depth modes:

```bash
# summary — frontmatter + first paragraph or two
braingent get DEC-0218 --depth summary

# full — entire record body
braingent get DEC-0218 --depth full
```

For agents, **start with `summary`**. It's the cheapest way to know
whether a record is relevant. Only escalate to `full` when you need
exact evidence.

## III. Graph walk — `braingent recall`

`recall` builds a focused context pack for a single concept or task.
It walks the `links:` frontmatter graph, deduplicates, and returns the
most relevant set.

```bash
braingent recall "billing webhook idempotency" --max 8
braingent recall --task BGT-0142 --max 12
```

Output is a small bundle of records (titles + summaries) you can drop
straight into a prompt or open in your editor.

This is what the [`workflows/retrieve-context.md`](/concepts/repository-shape/#iii-workflows-named-procedures)
playbook orchestrates: retrieve once at the parent level, hand the same
pack to subagents, never re-walk the graph N times.

## IV. Full-text — `rg` and `braingent search`

When you don't know which frontmatter field has what you want, fall back
to body search.

```bash
# raw ripgrep — fastest
rg -n 'idempotency' ~/Documents/repos/braingent

# braingent wrapper — adds frontmatter context per hit
braingent search 'temporal AND idempotency' --kind decision
```

`braingent search` ranks hits by frontmatter match strength + body
relevance. Use it when grep finds too many or too few.

## How agents query (the right way)

A wired Braingent agent follows this order, every time:

1. **Skim by filter.** `braingent find` with the tightest filter possible.
2. **Read summaries.** `braingent get --depth summary` on candidates.
3. **Escalate when needed.** `braingent get --depth full` only when
   summary doesn't carry the evidence.
4. **Walk links.** Follow `links:` arrays one hop, twice if obviously
   on-topic.
5. **Stop early.** Once you have enough to plan, stop. Don't read
   everything.

If an agent ever does step 3 before step 1, the prompt needs tightening.

## Building a focused context pack

For non-trivial planning sessions, a context pack is better than
ad-hoc lookups. The standard recipe:

1. Identify scope: org / repo / project / ticket / topic.
2. Run two or three `braingent find` queries to enumerate candidates.
3. Run `braingent recall` on the most central one to walk links.
4. Classify the resulting set into pinned (always relevant), supporting
   (cite if asked), and excluded (out of scope).
5. Hand the pinned + supporting set to your agent.

The full procedure lives in `workflows/retrieve-context.md` in the
starter pack. When the user says *"retrieve braingent context"*, that's
the workflow your agent runs.

## MCP equivalents

If your agent supports MCP and Braingent's MCP server is connected, the
shell commands above have direct tool equivalents:

| Shell command | MCP tool |
| --- | --- |
| `braingent find ...` | `braingent_find(filters)` |
| `braingent get ID --depth summary` | `braingent_get(id, depth='summary')` |
| `braingent get ID --depth full` | `braingent_get(id, depth='full')` |
| `braingent recall ...` | `braingent_find(query, links=true, max=N)` |
| Walking the docs index | `braingent_guide()` |

The MCP path is preferred for agents because it's structured: the agent
gets typed JSON back, not parsed shell output.

## When search misses

Search finds nothing because:

- **The record exists but frontmatter is stale.** Run `braingent doctor`
  and fix it.
- **The record never existed.** That's a capture gap — capture this time
  so next time it does.
- **The query was too narrow.** Drop a filter, broaden a tag.

If you keep looking for something that should exist but doesn't, the
fastest fix is to capture it now. Your future self will thank you.

## Where to go next

- [The Capture Loop](/guides/capture-loop/) — the write half.
- [CLI Reference](/reference/cli/) — every flag for `find`, `get`,
  `recall`, `search`.
- [MCP Tools Reference](/reference/mcp-tools/) — full inputs and outputs.
