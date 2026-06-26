---
title: MCP Tools Reference
description: Inputs, outputs, and examples for the Braingent MCP server.
section: Reference
order: 2
---

The Braingent MCP server exposes three read tools: `braingent_guide`,
`braingent_find`, and `braingent_get`. They are designed for token-efficient
access from MCP-aware agents.

For setup, see [Installation → Enable MCP Retrieval](/guides/installation/#enable-mcp-retrieval).
For command-line equivalents, see [CLI Reference](/reference/cli/).

## Connection

The server runs over MCP stdio. Configure your agent to launch it through the
installed Python CLI:

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

Install the optional MCP dependency before starting the agent:

```bash
pipx inject braingent "mcp>=1.28.0"
```

## `braingent_guide`

Returns the thin read order for the memory repo: entrypoints, pinned
preferences, and available workflows.

### Input

No arguments.

### When To Use

- At session start, before any other lookups.
- When the agent is about to run a workflow trigger phrase and needs the
  procedure.

## `braingent_find`

Frontmatter-filtered search. The structured equivalent of `braingent find`.

### Input

```json
{
  "query": {
    "kind": "decision",
    "status": "accepted",
    "repo": "repo--example--owner--repo",
    "q": "pagination"
  },
  "limit": 10
}
```

### Output

```json
[
  {
    "path": "orgs/org--example/projects/project--example/records/2026-05-01--decision--pagination.md",
    "title": "Prefer cursor pagination",
    "record_kind": "decision",
    "status": "accepted",
    "date": "2026-05-01",
    "summary": "..."
  }
]
```

### When To Use

- When you need a list of candidate records.
- When you can filter by repo, project, topic, ticket, tool, or kind.
- Before opening full record bodies.

## `braingent_get`

Fetch one record at a chosen depth.

### Input

```json
{
  "path": "orgs/org--example/projects/project--example/records/2026-05-01--decision--pagination.md",
  "depth": "summary"
}
```

`depth` can be `frontmatter`, `summary`, or `full`.

### When To Use

- When `braingent_find` returned a candidate and you need the body.
- Start with `summary`.
- Use `full` only when exact evidence matters.

## Token-Efficiency Tips

- Call `braingent_guide` first in a fresh session.
- Use `braingent_find` with the tightest filters you can.
- Default `braingent_get` to `summary`.
- Escalate to `full` only for the few records that drive the plan.

## Errors

The server returns structured errors through the MCP runtime. Common causes:

| Cause | Fix |
| --- | --- |
| Memory path is wrong | Check the `--path` argument. |
| MCP dependency is missing | Run `pipx inject braingent "mcp>=1.28.0"`. |
| Record path is missing | Run `braingent find` or `braingent_find` again with broader filters. |

## Where To Go Next

- [CLI Reference](/reference/cli/) — command-line equivalents.
- [Search & Recall](/guides/search-and-recall/) — when to use each query mode.
- [Agent Workflows](/guides/agent-workflows/) — how agents orchestrate these calls.
