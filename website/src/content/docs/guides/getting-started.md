---
title: Quickstart
description: Set up Braingent in about ten minutes — clone, copy, point your agent, capture your first task.
section: Get Started
order: 1
badge: 10 min
---

This is the fastest path from zero to *your agent searches Braingent before
planning and writes to it after work*. Four steps. Around ten minutes.

By the end you'll have:

- A private memory repo at `~/Documents/repos/braingent` (rename freely).
- Personalized entrypoints for Claude, Codex, ChatGPT, and Gemini CLI.
- One captured task record committed in Git.
- Search and validation working locally.

> **Tip:** You don't need to install anything fancy on day one. Markdown
> works without a CLI. The optional `braingent` CLI just makes things
> faster.

## Prerequisites

The day-zero install is genuinely small:

- **Git** — to clone and track your memory repo.
- **A text editor** — anything that opens Markdown.
- **At least one AI agent** — Claude Code, Codex, ChatGPT, or Gemini CLI.

That's it. You can complete this entire Quickstart with only those.

Optional, in roughly the order most users add them:

- **`rg` (ripgrep) + `jq` + `sqlite3`** — fast search and index
  inspection.
- **`gh`** (GitHub CLI) — pull PRs and issues into memory.
- **Python ≥ 3.14 + `uv`** — runs the helper scripts (`doctor`, `find`,
  `recall`, `validate`, `reindex`, `synthesize`, `task-*`).
- **Bun ≥ 1.3** — runs the [Local Dashboard](/guides/dashboard/) and the
  website. Not used by the helper scripts.

See [Installation](/guides/installation/) for the full breakdown of what
each one buys you.

## Step 1 — Clone the manifesto

Get the public starter pack. It's MIT-licensed and contains everything
you'll need to bootstrap.

```bash
git clone https://github.com/thedoublejay/braingent-manifesto
cd braingent-manifesto
```

This repo is your **reference**. You will not commit work here. Your real
memory will live in a *separate* private repo.

## Step 2 — Copy the starter pack into your private memory repo

Create your memory repo wherever you keep code. The convention is
`~/Documents/repos/braingent`, but anywhere works.

```bash
mkdir -p ~/Documents/repos/braingent
cp -R starter-pack/* ~/Documents/repos/braingent/
cd ~/Documents/repos/braingent
git init
git add .
git commit -m "feat: bootstrap from braingent starter pack"
```

You now have a working memory repo with:

- `CLAUDE.md`, `AGENTS.md`, `CHATGPT_PROJECT_BRIEF.md`, `GEMINI.md` —
  agent entrypoints.
- `preferences/` — your standing rules and policies.
- `templates/` — frontmatter-stamped templates for every record kind.
- `workflows/` — named procedures agents follow on trigger phrases.
- Empty trees for `tasks/`, `decisions/`, `reviews/`, `learnings/`,
  `repos/`, `projects/`, `topics/`, and `tools/`.

## Step 3 — Personalize the placeholders

Open the entrypoint files and replace the obvious placeholders:

- `<YOUR_NAME>` → your name or handle.
- `<YOUR_ROLE>` → "senior backend engineer", "founder", whatever fits.
- `<MEMORY_PATH>` → the absolute path to this repo.
- Any company-specific tags or repo names.

Keep it small. You're not building a profile — you're seeding signal that
the agent will reference *before* planning.

> **Tip:** If you also use Braingent's optional CLI, you can run
> `braingent init` to walk through these prompts interactively and stamp
> the placeholders for you. See [Installation](/guides/installation/).

## Step 4 — Wire up your agents

Tell each AI tool to read from this memory repo before planning. The
starter pack includes ready-to-paste entrypoints; the only thing you do
is drop them in the right place.

**Claude Code** — already auto-loads `CLAUDE.md` from the repo root. Done.

**Codex / Codex CLI** — the file is `AGENTS.md`. Codex picks it up
automatically.

**ChatGPT (custom GPT or project)** — paste the contents of
`CHATGPT_PROJECT_BRIEF.md` into the Project's "Instructions" field.

**Gemini CLI** — Gemini reads `GEMINI.md` from the working directory.

For details, see [Wire Up Your Agents](/guides/wire-up-agents/) and the
[Integrations](/integrations/overview/) pages.

## Step 5 — Capture your first task

Open a regular working repo (not the memory repo) and finish any small
piece of real work — a bug fix, a refactor, a config change. Then say it
out loud to your agent:

```
capture this — short summary of what we just did
```

The agent will:

1. Resolve the right memory path (`~/Documents/repos/braingent`).
2. Pick the correct record kind (task, decision, review, or learning).
3. Generate frontmatter with `id`, `title`, `status`, `tags`, `repos`,
   `date`.
4. Write the file under the correct directory.
5. Commit it with a message like `capture: <slug>`.

Open the file in your memory repo. Read it. This is the smallest possible
unit of memory that survives across sessions, agents, and tools.

## You're done

That's the loop. From here it's just repetition:

- Tomorrow, your agent searches `~/Documents/repos/braingent` before
  planning a related task.
- Next week, a different agent reads the same record and inherits the
  context.
- Three months from now, you `git log` your memory repo and watch the
  decisions you forgot you made.

## What to read next

- [Installation](/guides/installation/) — get the optional CLI, MCP server,
  and dashboard.
- [The Capture Loop](/guides/capture-loop/) — when to capture, what to skip,
  and the trigger phrases agents already understand.
- [Memory Model](/concepts/memory-model/) — the five surfaces of memory
  and how they fit together.
- [Integrations](/integrations/overview/) — agent-by-agent setup details.
