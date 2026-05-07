---
title: Search & Recall
description: Find prior context fast — by frontmatter, by topic, by repo, by context pack, or by full-text search.
section: Guides
order: 3
---

If capture is the write half, **search and recall** is the read half. This
page covers the ways to query Braingent memory and how to build a focused
context pack instead of dumping everything into an agent prompt.

## The query modes

| Mode | Tool | Best for |
| --- | --- | --- |
| Structured filter | `scripts/find.sh` / `braingent_find()` MCP | "All accepted decisions for a repo" |
| Direct fetch | `braingent_get()` MCP or opening the path from `find` | "Read one record in full" |
| Context pack | `scripts/recall.sh` | "Everything directly relevant to this ticket or repo" |
| Full-text | `rg` | "Where did we mention Temporal idempotency?" |

Use the most specific mode that answers your question. Frontmatter filters
are cheap and precise; `rg` is the fallback when you do not know which
metadata field carries the answer.

## Structured filter — `scripts/find.sh`

Filter records by frontmatter fields. Filters are `key=value` pairs. Common
aliases include `kind`, `org`, `project`, `repo`, `topic`, `tool`, `ticket`,
`person`, `ai`, and `q`.

```bash
# all accepted decisions
scripts/find.sh kind=decision status=accepted

# every record that touches a specific repo slug
scripts/find.sh repo=repo--example--owner--repo --limit 20

# tasks captured for one topic
scripts/find.sh kind=task topic=ai-memory --paths
```

Output is a sorted list of matching records. Add `--paths` for scriptable
path-only output, `--json` for structured output, or `--count` for a quick
volume check.

## Direct fetch — MCP or file paths

For MCP-aware agents, use `braingent_get(path, depth="summary")` first and
`depth="full"` only when exact evidence is needed.

For humans, use the paths from `scripts/find.sh --paths`:

```bash
scripts/find.sh kind=decision status=accepted --paths
sed -n '1,120p' orgs/org--example/projects/project--example--memory/records/2026-05-07--decision--example.md
```

Agents should prefer summaries first because they keep context small.

## Context pack — `scripts/recall.sh`

`recall` builds a focused context pack for one scope. It classifies results
into `must_read`, `supporting`, `stale_or_verify`, `do_not_use`, and
`capture_target`.

```bash
scripts/recall.sh repo=repo--example--owner--repo
scripts/recall.sh ticket=ACME-123 --json
scripts/recall.sh topic=qa --limit 8
```

This is what the [`workflows/retrieve-context.md`](/concepts/repository-shape/#iii-workflows-named-procedures)
playbook orchestrates: retrieve once at the parent level, hand the same pack
to subagents, and avoid repeated broad reads.

## Full-text — `rg`

When you do not know which frontmatter field has what you want, fall back to
body search.

```bash
rg -n 'idempotency' .
rg -n 'Temporal|webhook|retry' orgs repositories topics tools tickets
```

Prefer `rg` over broad file reads. It is fast, local, and transparent.

## How agents query

A wired Braingent agent follows this order:

1. **Skim by filter.** Use `braingent_find()` or `scripts/find.sh` with the tightest filter possible.
2. **Read summaries.** Use `braingent_get(..., depth="summary")` or open only the top matching paths.
3. **Escalate when needed.** Read full records only when the summary does not carry the evidence.
4. **Build a pack.** Use `scripts/recall.sh` when the task spans several records.
5. **Stop early.** Once there is enough context to plan, stop searching.

If an agent reads the whole repo before filtering, tighten the entrypoint
instructions.

## MCP equivalents

If your agent supports MCP and Braingent's MCP server is connected, the shell
helpers map to read-only tools:

| Shell helper | MCP tool |
| --- | --- |
| `scripts/find.sh kind=decision` | `braingent_find({"kind": "decision"})` |
| Open one returned path | `braingent_get(path, depth="summary")` |
| Open exact evidence | `braingent_get(path, depth="full")` |
| Read the thin entry chain | `braingent_guide()` |

The MCP path is preferred for agents because it returns structured JSON, not
parsed shell output.

## When search misses

Search finds nothing because:

- **The record exists but frontmatter is stale.** Run `scripts/doctor.sh` and fix it.
- **The record never existed.** That is a capture gap; capture this time so next time it does.
- **The query was too narrow.** Drop a filter, broaden a topic, or use `rg`.

If you keep looking for something that should exist but does not, the fastest
fix is to capture it now.

## Where to go next

- [The Capture Loop](/guides/capture-loop/) — the write half.
- [CLI Reference](/reference/cli/) — shipped helper scripts and flags.
- [MCP Tools Reference](/reference/mcp-tools/) — full inputs and outputs.
