---
title: Integrations Overview
description: One memory, every agent — wire Claude, Codex, ChatGPT, Gemini CLI, and Gather Step to the same Braingent repo.
section: Integrations
order: 1
---

Braingent is built so that every agent reads from and writes to the same
Markdown repo. The integration story is therefore boring on purpose:
**drop the right entrypoint file, replace placeholders, commit.** No
plugins, no daemons, no API keys.

This page is the map. Each agent has its own page with the exact paths,
quirks, and verification steps.

## Supported agents

| Agent | Entrypoint | Where it goes | Status |
| --- | --- | --- | --- |
| [Claude Code](/integrations/claude/) | `CLAUDE.md` | Repo root or `~/.claude/CLAUDE.md` | First-class |
| [Codex / Codex CLI](/integrations/codex/) | `AGENTS.md` | Repo root | First-class |
| [ChatGPT](/integrations/chatgpt/) | `CHATGPT_PROJECT_BRIEF.md` | Project Instructions | Pasted |
| [Gemini CLI](/integrations/gemini-cli/) | `GEMINI.md` | Working directory | First-class |

"First-class" means the tool auto-loads the file; "pasted" means you put
the contents into the tool's Instructions field.

## Partner

| Partner | What it adds | More |
| --- | --- | --- |
| [Gather Step](/integrations/gather-step/) | Native QA evidence for `qa-generate` | [Read why](/integrations/gather-step/) |

Braingent + Gather Step is the recommended pairing for any team that
ships software with QA — see the page for the full rationale.

## The shared contract

Regardless of agent, every entrypoint encodes the same contract:

1. **Read pinned context** before planning.
2. **Search Braingent** for prior decisions, reviews, and learnings.
3. **State assumptions** before proposing changes.
4. **Capture meaningful work** as durable records.
5. **Never store** secrets, raw transcripts, or sensitive personal data.

The starter pack ships entrypoints that already encode this contract.
You only need to personalize a few placeholders.

## MCP — the upgrade path

For agents that support the Model Context Protocol, Braingent's MCP
server provides token-efficient retrieval as native tools:

- `braingent_guide()` — discover sections of the memory repo.
- `braingent_find(...)` — frontmatter filters.
- `braingent_get(...)` — fetch a record at summary or full depth.

MCP is **strictly optional**. The entrypoint contract works without it.
Add MCP when an agent supports it and you find yourself wanting cleaner
structured retrieval.

See [Installation → MCP Server](/guides/installation/#install-the-mcp-server)
and [MCP Tools Reference](/reference/mcp-tools/).

## When you add a new tool

The pattern is the same:

1. Find where the tool reads instructions from.
2. Drop a Braingent-flavored entrypoint there.
3. Replace placeholders.
4. Smoke-test by asking the agent for the absolute path to your memory
   repo.

If a future tool can't read Markdown, it's the wrong tool. Markdown is
the universal interface.

## Where to go next

- [Claude Integration](/integrations/claude/)
- [Codex Integration](/integrations/codex/)
- [ChatGPT Integration](/integrations/chatgpt/)
- [Gemini CLI Integration](/integrations/gemini-cli/)
- [Gather Step Partner](/integrations/gather-step/)
