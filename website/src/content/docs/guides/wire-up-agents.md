---
title: Wire Up Your Agents
description: One-time setup so every agent reads Braingent before planning and writes to it after work.
section: Get Started
order: 3
---

Braingent's contract is simple: every agent should read your memory repo
before planning, and write a record after meaningful work. That contract
lives in **entrypoint files** — short, agent-specific Markdown files that
the tool already loads automatically.

This page covers the smallest setup that gets each agent on the contract.
Detailed integration guides live under [Integrations](/integrations/overview/).

## The pattern

For every agent you use, you do exactly two things:

1. Drop the agent's entrypoint into the right location.
2. Personalize a small handful of placeholders inside it.

That's it. There's no daemon, no service, no plugin to install at this
layer. The agent reads Markdown; that's the whole interface.

## Claude Code

**Where it goes:** the root of any working repo (or `~/.claude/CLAUDE.md`
for global rules).

**What it does:** Claude reads `CLAUDE.md` automatically at session start
and treats it as system-level instructions.

```bash
cp ~/Documents/repos/braingent/CLAUDE.md ./CLAUDE.md
```

The starter `CLAUDE.md` already includes the **Engineering Memory** section
that points Claude at your memory repo and tells it when to search and
when to capture. Open it and replace the path placeholder with the
absolute path to your memory repo.

> **Tip:** If you want the same memory across every project, put the
> Braingent block in `~/.claude/CLAUDE.md` (your user-level file) so it
> applies everywhere.

See the full guide: [Claude Integration](/integrations/claude/).

## Codex / Codex CLI

**Where it goes:** the root of the working repo as `AGENTS.md`.

**What it does:** Codex automatically picks up `AGENTS.md` for context.

```bash
cp ~/Documents/repos/braingent/AGENTS.md ./AGENTS.md
```

Same pattern as Claude — replace placeholders, commit. See [Codex
Integration](/integrations/codex/).

## ChatGPT (Project / Custom GPT)

ChatGPT doesn't auto-read files from your machine, so the entrypoint goes
into a Project's "Instructions" field (or a custom GPT's system prompt).

1. Open the contents of `~/Documents/repos/braingent/CHATGPT_PROJECT_BRIEF.md`.
2. Paste it into your ChatGPT Project → **Instructions**.
3. Optionally, attach the few pinned files (`preferences/*.md`, the most
   relevant repo profile) to the Project's knowledge.

ChatGPT will treat the brief as standing instructions, including the
search-before-plan and capture-after-work rules. See [ChatGPT
Integration](/integrations/chatgpt/).

## Gemini CLI

**Where it goes:** the working directory as `GEMINI.md`.

**What it does:** Gemini CLI reads `GEMINI.md` for project-specific
context.

```bash
cp ~/Documents/repos/braingent/GEMINI.md ./GEMINI.md
```

Same placeholder pass, same commit. See [Gemini CLI
Integration](/integrations/gemini-cli/).

## Make sure it actually loads

After wiring an agent, run a tiny smoke test. Open a session and ask:

> What's the path to my Braingent memory repo, and what's the first thing
> you'll do before planning a non-trivial task?

A correctly wired agent answers with the absolute path you set and
restates the *search-before-plan, capture-after-work* contract. If it
doesn't, the entrypoint isn't loading — check the filename, location, and
that you saved.

## What about MCP?

MCP is the upgrade path. Once an agent supports the Model Context Protocol,
you can connect Braingent's MCP server and the agent gets dedicated
retrieval tools (`braingent_guide`, `braingent_find`, `braingent_get`)
instead of having to search by hand.

MCP is **strictly optional**. The entrypoint contract works without it.
See [Installation → MCP Server](/guides/installation/#install-the-mcp-server)
and [MCP Tools Reference](/reference/mcp-tools/).

## When you add a new tool

Pattern repeats:

1. Find out where that tool reads instructions from.
2. Drop a Braingent-flavored entrypoint there.
3. Replace placeholders.
4. Smoke test.

Markdown is universal; the only thing that changes is the filename.

## Where to go next

- [Agent Workflows](/guides/agent-workflows/) — what agents do once they're
  wired up.
- [The Capture Loop](/guides/capture-loop/) — trigger phrases and capture
  policy.
- [Integrations](/integrations/overview/) — per-agent reference.
