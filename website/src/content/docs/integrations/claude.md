---
title: Claude Integration
description: Wire Claude Code (and the broader Claude family) to your Braingent memory repo.
section: Integrations
order: 2
---

Claude Code reads `CLAUDE.md` automatically at session start. That single
file is the entire integration surface — drop a Braingent-flavored
`CLAUDE.md` in the right place and Claude is on the contract.

## Where the file goes

Three valid locations, in order of precedence:

1. **`~/.claude/CLAUDE.md`** — your global rules, applied to every project.
2. **`~/.claude/projects/<repo-hash>/CLAUDE.md`** — per-project, project-scoped.
3. **`<repo-root>/CLAUDE.md`** — committed alongside the code, shared with
   teammates.

Most users put their Braingent block in **`~/.claude/CLAUDE.md`** so
every project on their machine inherits the same memory contract.

## What goes in it

The starter pack's `CLAUDE.md` is ready to use. The key sections:

```markdown
# Engineering Memory: Braingent

`~/Documents/repos/braingent` is my durable engineering memory across all
repos and AI tools. It holds prior decisions, learnings, tool versions,
repository profiles, ticket history, and code review notes.

**Before planning any non-trivial task:** search Braingent for prior
context. Start at `~/Documents/repos/braingent/CLAUDE.md` for the thin
read order. When MCP tools are available, prefer `braingent_guide()`,
`braingent_find(...)`, and `braingent_get(path, depth='summary')`; use
`depth='full'` only when exact evidence or archived/playbook content
matters.

**After meaningful work:** capture a record. Triggers are PR opened,
ticket closed, code review done, key decision made, reusable learning
surfaced, or any of: "dump this to braingent" / "save to braingent" /
"capture" / "task done thanks" / "ok done".

**Never** store secrets, credentials, tokens, or sensitive personal data
in Braingent.
```

Replace `~/Documents/repos/braingent` with your actual memory repo path.

## MCP setup (recommended)

Claude Code supports MCP. Connect Braingent's MCP server for clean
structured tools.

`~/.claude/config.json` (or per-project equivalent):

```json
{
  "mcpServers": {
    "braingent": {
      "command": "braingent",
      "args": [
        "mcp", "serve",
        "--path", "/Users/you/Documents/repos/braingent"
      ]
    }
  }
}
```

Restart Claude Code. The tools `braingent_guide`, `braingent_find`, and
`braingent_get` should appear in the tools list.

## Smoke test

Open a new Claude Code session in any repo and ask:

> What's the path to my Braingent memory repo, and what's the first
> thing you'll do before planning a non-trivial task?

A correctly wired Claude responds with the absolute path and restates
the *search-before-plan, capture-after-work* contract.

## Subagent pattern

When you dispatch Claude subagents (via the `Task` tool) for parallel
work, **don't have each subagent rerun memory lookups**. Instead:

1. The parent agent retrieves a focused context pack once
   (`workflows/retrieve-context.md`).
2. The parent passes that pack into each subagent's prompt.
3. Subagents work; parent captures the outcome.

This avoids N round-trips through memory and keeps subagent context
focused on the specific subtask.

## Common pitfalls

- **`CLAUDE.md` not loading.** Filename is case-sensitive — must be
  exactly `CLAUDE.md`. Restart Claude Code after creating or moving the
  file.
- **Path placeholders not replaced.** Smoke-test the absolute path
  question; if Claude says `<MEMORY_PATH>`, you skipped step 2.
- **Memory-aware subagents not aware.** Make sure your subagent dispatch
  prompt includes the relevant context pack.

## Where to go next

- [Wire Up Your Agents](/guides/wire-up-agents/) — the same pattern for
  every other tool.
- [Agent Workflows](/guides/agent-workflows/) — what Claude does once
  it's wired.
- [MCP Tools Reference](/reference/mcp-tools/) — the MCP surface.
