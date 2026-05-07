---
title: Why Braingent is Different
description: Memory you can read, diff, move, and trust — instead of memory hidden inside someone else's database.
section: Introduction
order: 2
---

Most "memory" features for AI tools share a few traits. They live inside a
single product. They store your context as opaque rows in a database you
don't control. They expire on a schedule you didn't choose. They can't be
diffed, searched offline, or migrated when the tool changes.

Braingent takes the opposite stance.

## Memory should be a file, not a feature

Your engineering decisions, reviews, and learnings are some of the most
valuable artifacts you produce. They deserve the same treatment as your
source code:

- **Plain text** that opens in any editor.
- **Versioned** in Git, with `git log`, `git blame`, and `git diff`.
- **Diffable** so reviewers can spot when memory drifts.
- **Portable** — no export step, no proprietary format, no migration.
- **Owned by you**, on disk, in a repo you push to a host you trust.

A note hidden inside a chat tool's session store fails every one of those
tests.

## Tool-agnostic by construction

Braingent makes one bet: **Markdown will outlive every individual AI tool
you use this decade.** So it stores everything as Markdown with structured
YAML frontmatter and lets each agent's entrypoint file (`CLAUDE.md`,
`AGENTS.md`, `CHATGPT_PROJECT_BRIEF.md`, `GEMINI.md`) point into the same
memory repo.

The same record that Claude wrote yesterday is the record Codex will read
tomorrow. There is no "Claude memory" and "Codex memory" — there is just
*the* memory.

## Retrieval before planning, capture after work

Most chat tools optimize for the conversation. Braingent optimizes for the
**loop around it**:

1. **Before planning** — agents search Braingent for prior context,
   decisions, and known risks.
2. **During work** — humans and agents focus on shipping.
3. **After meaningful work** — agents capture a durable record and commit it.
4. **Forever after** — future sessions inherit instead of starting from zero.

The chat is ephemeral. The records are durable. That's the contract.

## A small CLI on top of files, not a service that owns them

Braingent ships a thin CLI (`braingent init`, `doctor`, `find`, `recall`,
`update`, `qa-generate`, `task-*`) and an MCP server. None of them are
required to *use* Braingent — they speed up things you'd otherwise do by
hand.

Delete the CLI tomorrow and your memory still works. The Markdown is the
source of truth; the tools are conveniences. That ordering matters.

## Privacy is a default, not a setting

Because everything is a file in a repo you control:

- It runs locally with **no network calls** by default.
- It has **no hosted account** to leak, expire, or be subpoenaed.
- It puts an explicit list of things it **never stores** in its starter
  pack: secrets, tokens, credentials, raw chat transcripts, and sensitive
  personal data. Your reviewers can `grep` for violations.

You decide what gets pushed to which remote. You decide who has read
access. You decide when to rotate or redact.

## Built for multiple agents at the same time

A single Markdown record can be read by Claude in one terminal, Codex in
another, and ChatGPT on the web — at the same time, with no sync layer.
Multi-agent task files (`tasks/active/BGT-NNNN.md`) coordinate handoffs
between them with nothing more than diffs.

This was built for the way modern engineers actually work: across multiple
tools, sometimes in parallel, often switching mid-task.

## What this means for you

You don't have to bet on a single AI vendor's memory roadmap. You don't have
to lose context when you switch tools. You don't have to pay a SaaS bill
for the privilege of remembering your own decisions.

You write Markdown. Git tracks it. Your agents read it. That's the whole
trick.
