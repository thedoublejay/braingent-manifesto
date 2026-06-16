---
title: Quickstart
description: Set up Braingent in about ten minutes with the Python CLI.
section: Get Started
order: 1
badge: 10 min
---

This is the shortest path from zero to a working Braingent memory repo.

By the end you'll have:

- The `braingent` CLI installed.
- A private memory repo at `~/Documents/repos/braingent`.
- Agent entrypoints for Claude, Codex, ChatGPT, and Gemini.
- Search, validation, indexing, and QA generation available from one command.

## Step 1 — Install The CLI

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install braingent
braingent --help
```

`uv` users can run:

```bash
uv tool install braingent
```

## Step 2 — Create Your Memory Repo

```bash
braingent init ~/Documents/repos/braingent
cd ~/Documents/repos/braingent
git init
git add .
git commit -m "feat: initialize braingent memory"
```

You now have:

- `CLAUDE.md`, `AGENTS.md`, `CHATGPT_PROJECT_BRIEF.md`, and `GEMINI.md`
- `preferences/` for standing rules
- `templates/` for frontmatter-backed records
- `workflows/` for repeatable agent procedures
- `tasks/` for live multi-agent work
- generated indexes and a local derived cache

## Step 3 — Verify The Repo

```bash
braingent doctor
braingent validate
braingent reindex --check
braingent find kind=decision --limit 1
```

`doctor` catches missing files, unreplaced placeholders, malformed
frontmatter, generated-index drift, private path leaks, and local tooling gaps.

## Step 4 — Personalize The Entry Points

Open the agent entrypoint files and replace the obvious placeholders:

- `<YOUR_NAME>` with your name or handle.
- `<YOUR_ROLE>` with the engineering role your agents should assume.
- `<MEMORY_PATH>` with the absolute path to this memory repo.
- Any organization, repo, or topic placeholders with your actual naming.

Keep this small. Braingent works because the pinned files stay compact and the
records carry the details.

## Step 5 — Wire Up Agents

Each agent reads one entrypoint:

| Agent | File |
| --- | --- |
| Claude Code | `CLAUDE.md` |
| Codex / Codex CLI | `AGENTS.md` |
| ChatGPT project or custom GPT | `CHATGPT_PROJECT_BRIEF.md` |
| Gemini CLI | `GEMINI.md` |

For MCP-aware agents, add the MCP server:

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

Install the optional MCP dependency first:

```bash
pipx inject braingent "mcp>=1.27.1"
```

## Step 6 — Capture Your First Task

Open any working repo and finish a small piece of real work. Then tell your
agent:

```text
capture this — short summary of what we just did
```

The agent should search Braingent, choose the correct record kind, write the
record into your memory repo, run validation, and commit the result.

## Step 7 — Use The Daily Commands

```bash
braingent recall repo=repo--example--owner--repo
braingent task-new "Backfill repo profile for example app" --priority medium
braingent qa generate --ticket-key ACME-1492 ./tickets/ACME-1492.md
braingent update . --dry-run
```

## What To Read Next

- [Installation](/guides/installation/) — optional tools, MCP, and updates.
- [CLI Workflows](/guides/cli-workflows/) — day-to-day commands.
- [Search & Recall](/guides/search-and-recall/) — how to query memory.
- [QA Test Planning](/guides/qa-test-planning/) — traceable test plans.
