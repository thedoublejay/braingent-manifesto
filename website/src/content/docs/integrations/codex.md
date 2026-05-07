---
title: Codex Integration
description: Wire Codex / Codex CLI to your Braingent memory repo via AGENTS.md.
section: Integrations
order: 3
---

Codex (and Codex CLI) auto-reads `AGENTS.md` from the working directory.
The integration mirrors Claude's exactly — same contract, different
filename.

## Where the file goes

`<repo-root>/AGENTS.md` for project scope, or copy the same file into
each working repo for portability.

If you have a Braingent memory repo at `~/Documents/repos/braingent`, the
file is already there as `AGENTS.md` — just copy it into your working
repos:

```bash
cp ~/Documents/repos/braingent/AGENTS.md ./AGENTS.md
```

## What goes in it

`AGENTS.md` carries the same Braingent contract as `CLAUDE.md`:

- Pointer to the memory repo path.
- Search-before-plan rules.
- Capture-after-work triggers.
- Privacy boundaries.

The only meaningful difference is voice — `AGENTS.md` typically uses
plural "agents" framing because Codex is often invoked alongside other
tools.

## MCP setup

Codex CLI supports MCP. Configuration is similar to Claude:

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

Add this to Codex's MCP config (path varies by version — see Codex CLI
docs).

## Smoke test

```
Q: What's the path to my Braingent memory repo, and what's the first
   thing you'll do before planning a non-trivial task?
```

Codex should answer with the absolute path and restate the contract.

## Working alongside Claude

Codex and Claude can both work on the same memory repo at the same
time. They'll naturally pick up each other's records because they read
from the same Markdown.

When the same task is in flight under both, use a [live multi-agent
task](/guides/multi-agent-tasks/) — `tasks/active/BGT-NNNN.md` — for
coordination.

## Where to go next

- [Wire Up Your Agents](/guides/wire-up-agents/) — generic pattern.
- [Multi-Agent Coordination](/guides/multi-agent-tasks/) — Claude +
  Codex on the same task.
- [MCP Tools Reference](/reference/mcp-tools/) — the MCP surface Codex
  uses.
