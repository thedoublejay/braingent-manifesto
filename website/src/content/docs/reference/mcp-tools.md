---
title: MCP Tools Reference
description: Inputs, outputs, and examples for the Braingent MCP server.
section: Reference
order: 2
---

The Braingent MCP server exposes three tools: `braingent_guide`,
`braingent_find`, and `braingent_get`. They are designed for
token-efficient access from MCP-aware agents.

This page is the canonical surface. For setup, see [Installation → MCP
Server](/guides/installation/#install-the-mcp-server). For the shell
equivalents, see [CLI Reference](/reference/cli/).

## Connection

The server runs over MCP stdio by default. Configure it in your agent's
MCP config:

```json
{
  "mcpServers": {
    "braingent": {
      "command": "braingent",
      "args": ["mcp", "serve", "--path", "/Users/you/Documents/repos/braingent"]
    }
  }
}
```

Verify by listing MCP tools in your agent — you should see all three.

## `braingent_guide`

Returns the thin "read order" for the memory repo: which entrypoints
exist, which preferences are pinned, and which workflows are available.

This is what an agent calls *first* in a fresh session.

### Input

```json
{
  "section": "all"   // optional; "entrypoints" | "preferences" | "workflows" | "all"
}
```

### Output

```json
{
  "entrypoints": [
    { "agent": "claude", "path": "CLAUDE.md", "summary": "..." },
    { "agent": "codex",  "path": "AGENTS.md", "summary": "..." }
  ],
  "preferences": [
    { "path": "preferences/capture-policy.md", "summary": "..." }
  ],
  "workflows": [
    { "trigger": "index this repo", "path": "workflows/index-repo.md" }
  ]
}
```

### When to use

- At session start, before any other lookups.
- When the agent is about to run a trigger phrase ("index this repo")
  and needs the procedure.

## `braingent_find`

Frontmatter-filtered search. The structured equivalent of `braingent
find`.

### Input

```json
{
  "kind": ["decision"],         // optional, repeatable
  "status": ["accepted"],       // optional
  "repos": ["acme/api"],        // optional
  "projects": ["acme-platform"],// optional
  "topics": ["jobs"],           // optional
  "tools": ["temporal"],        // optional
  "tags": ["reliability"],      // optional, AND across tags
  "owner": "claude",            // optional
  "since": "2026-01-01",        // optional, YYYY-MM-DD
  "until": "2026-12-31",        // optional
  "links_from": "BGT-0142",     // optional, walk graph from this id
  "links_to":   "DEC-0218",     // optional, find records that link to this id
  "query": "free text",         // optional, full-text body match
  "limit": 20,                  // default 50
  "sort":  "date_desc"          // "date_desc" | "date_asc" | "id"
}
```

### Output

```json
{
  "results": [
    {
      "id": "DEC-0218",
      "kind": "decision",
      "title": "Move job runtime from BullMQ to Temporal",
      "status": "accepted",
      "date": "2026-04-12",
      "path": "decisions/2026-04-12-jobs-runtime.md",
      "tags": ["runtime", "jobs", "reliability"],
      "links": ["DEC-0091"],
      "summary": "First two paragraphs..."
    }
  ],
  "total": 1,
  "truncated": false
}
```

### When to use

- When you need a list of candidates.
- When you want to walk the graph (`links_from`, `links_to`).
- When the user has a specific kind / repo / topic in mind.

## `braingent_get`

Fetch one record at a chosen depth.

### Input

```json
{
  "id":    "DEC-0218",         // or "path": "decisions/..."
  "depth": "summary"           // "summary" | "full"
}
```

### Output

```json
{
  "id": "DEC-0218",
  "kind": "decision",
  "title": "Move job runtime from BullMQ to Temporal",
  "status": "accepted",
  "date": "2026-04-12",
  "path": "decisions/2026-04-12-jobs-runtime.md",
  "frontmatter": { "...": "..." },
  "body": "## Context\n...",
  "links_resolved": [
    { "id": "DEC-0091", "title": "...", "summary": "..." }
  ]
}
```

### When to use

- When `braingent_find` returned a candidate and you need the body.
- Always start with `depth: "summary"` to see if it's relevant.
- Escalate to `depth: "full"` only when you need exact evidence.

## Token-efficiency tips

- Always call `braingent_guide` first in a fresh session — it's small and
  tells you what to read next.
- Default `braingent_get` to `summary`. Save `full` for the one or two
  records that actually matter.
- Use `braingent_find` with the tightest filters you can. `repos +
  topics` is usually all you need.
- Use `links_from` to walk graphs instead of doing N separate
  `braingent_get` calls.

## Errors

The server returns structured errors with stable codes:

| Code | Meaning |
| --- | --- |
| `not_found` | The id or path doesn't exist. |
| `invalid_filter` | A filter value didn't match its kind's vocabulary. |
| `path_outside_repo` | A path argument escaped the memory repo. |
| `truncated` | Output was clipped to fit the response budget. |

`truncated: true` is informational, not fatal — but agents should know
that follow-up calls are needed for the rest.

## Read-only mode

The starter-pack MCP server is read-only today:

```bash
python3 scripts/mcp_server.py
```

It exposes retrieval tools only. Future write tools should be guarded by an
explicit read-only mode before they are shipped.

## Where to go next

- [CLI Reference](/reference/cli/) — shell equivalents.
- [Search & Recall](/guides/search-and-recall/) — when to use which
  tool.
- [Agent Workflows](/guides/agent-workflows/) — how an agent should
  orchestrate these calls.
