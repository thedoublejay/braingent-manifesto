---
title: Gemini CLI Integration
description: Wire Gemini CLI to your Braingent memory repo via GEMINI.md.
section: Integrations
order: 5
---

Gemini CLI auto-reads `GEMINI.md` from the working directory. Same
contract as Claude and Codex; different filename.

## Where the file goes

`<working-directory>/GEMINI.md`. For a global setup, copy it into each
project root or symlink from a single source of truth.

```bash
cp ~/Documents/repos/braingent/GEMINI.md ./GEMINI.md
```

Or, for projects you don't want to commit the file to:

```bash
ln -s ~/Documents/repos/braingent/GEMINI.md ./GEMINI.md
```

## What goes in it

The starter pack's `GEMINI.md` carries the same Braingent contract:
search before plan, capture after meaningful work, never store secrets.

It also includes a small Gemini-specific section that maps Claude Code
tool names to their Gemini equivalents — useful for any superpowers /
skills workflow that was originally written for Claude.

## MCP setup

Gemini CLI's MCP support varies by version. When supported:

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

Path of the config file varies — see Gemini CLI docs for your version.

## Smoke test

```
Q: What's the path to my Braingent memory repo, and what's the first
   thing you'll do before planning a non-trivial task?
```

Gemini should answer with the absolute path and restate the contract.

## Where to go next

- [Wire Up Your Agents](/guides/wire-up-agents/) — generic pattern.
- [Agent Workflows](/guides/agent-workflows/) — what Gemini does once
  wired.
