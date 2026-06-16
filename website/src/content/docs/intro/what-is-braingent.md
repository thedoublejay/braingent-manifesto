---
title: What is Braingent?
description: Braingent is a Git-backed, Markdown-first memory repo that gives every AI coding agent the same engineering context.
section: Introduction
order: 1
---

Braingent is **a shared memory for AI-assisted engineering** — a small set
of Markdown conventions, a starter pack, and a thin CLI that turn any Git
repository into a durable memory layer your agents can search before they
plan and write to after they ship.

It works the same with Claude Code, Codex, ChatGPT, Gemini CLI, and any
future tool that can read Markdown. Your decisions, reviews, learnings, and
repository profiles live as plain files. Git tracks them. You own them.

## The problem in one sentence

Agents start every session from zero, you re-explain the same context every
time, and decisions vanish into closed chat windows that nobody can search,
diff, or move.

Braingent fixes that without a vendor, a database, or a server.

## What you get

- **A shared memory across agents.** One canonical place to read before
  planning. Claude, Codex, ChatGPT, and Gemini CLI all retrieve from the
  same Markdown.
- **Eight record kinds.** Tasks, decisions, reviews, learnings, repository
  profiles, tool versions, summaries, and ticket stubs — typed enough to
  search, plain enough to read.
- **Five memory surfaces.** Pinned context, durable records, derived
  retrieval, live multi-agent task files, and an optional local dashboard.
- **Small, optional helpers.** `doctor`, `find`, `recall`, `reindex`,
  `qa-generate`, plus live-task helpers. Markdown is still the
  source of truth.
- **MCP retrieval out of the box.** `braingent_guide()`, `braingent_find()`,
  and `braingent_get()` give MCP-aware agents token-efficient retrieval
  without bloating context.
- **Local-first, Git-native.** No server. No hosted account. No vendor lock.
  If you can `git clone`, you can run Braingent.

## How it feels in practice

You start a new task. The agent reads the entrypoint at the root of your
memory repo, searches for prior decisions and reviews on the area you're
about to touch, and tells you what it found before it proposes a plan.

You ship. Evidence accrues — files touched, tradeoffs weighed, commands run.

You say *capture this* or *task done* and the agent writes a structured
record, validates the frontmatter, and commits it.

Tomorrow's session — and tomorrow's agent — search that memory before
planning and pick up where you left off.

## Who it's for

- Engineers who use AI agents daily and want them to stop forgetting.
- Teams who want a single, diffable memory shared across tools.
- Solo developers who want their decisions to outlive the chat window.
- Anyone tired of re-pasting "here's the architecture" into a fresh prompt.

## Where to go next

> **Tip:** If you have ten minutes, jump to the [Quickstart](/guides/getting-started/).
> If you want to read the why first, start with the [Manifesto](/intro/manifesto/).
