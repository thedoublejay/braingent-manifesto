---
title: Installation
description: What to install for Braingent — almost nothing on day one. Add tools as you grow.
section: Get Started
order: 2
---

Braingent works on day one with **nothing more than Git and a text
editor**. The starter pack is plain Markdown — every file you'd open
reads in any editor and lives in your repo. The CLI helpers, MCP
server, and dashboard are conveniences that make the loop faster.

This page lists what's available, what each one needs, and the
shortest path to a working install.

## Day-one minimum

| Tool | Why | Required? |
| --- | --- | --- |
| Git | Version control your memory repo | **Yes** |
| Text editor | Open Markdown | **Yes** |

That's it. Not a placeholder for a longer list — that's the actual list.
You can complete the [Quickstart](/guides/getting-started/) with only
these two and capture by hand using your editor + `git commit`.

## What you might add later

| Tool | What it gives you | Required? |
| --- | --- | --- |
| `gh` | Import GitHub PRs / issues into memory | Optional |
| `rg` (ripgrep) | Fast full-text search across records | Recommended |
| `jq` | Inspect generated JSON indexes | Recommended |
| `sqlite3` | Local search caches | Recommended |
| **Python ≥ 3.14 + `uv`** | Run the helper CLI (`doctor`, `find`, `recall`, `validate`, `reindex`, `synthesize`, `task-*`) | Optional |
| `mcp` Python package | Run the MCP server | Optional (needed for MCP) |
| **Bun ≥ 1.3** | Run the optional dashboard and the website | Optional |

You can stop reading at any row that doesn't apply to you.

## Recommended path

Most users install:

1. The lightweight CLI tools (`rg`, `jq`, `sqlite3`, `gh`).
2. **Python 3.14 + `uv`** for the helper scripts.
3. **Bun** if they want the [Local Dashboard](/guides/dashboard/).

In that order. Each is independent.

## Install the lightweight tools

```bash
# macOS (Homebrew)
brew install ripgrep jq sqlite gh

# Debian / Ubuntu
sudo apt install ripgrep jq sqlite3 gh

# Arch
sudo pacman -S ripgrep jq sqlite github-cli

# Windows (winget)
winget install BurntSushi.ripgrep.MSVC stedolan.jq SQLite.SQLite GitHub.cli
```

Verify:

```bash
rg --version && jq --version && sqlite3 --version && gh --version
```

## Install Python (≥ 3.14) and `uv`

The Braingent helper scripts (`doctor.sh`, `find.sh`, `recall.sh`,
`validate.sh`, `reindex.sh`, `synthesize.sh`, `task-*.sh`) are thin
shell wrappers around Python. They expect **Python 3.14+** and
**PyYAML 6.0.3**. The fastest way to install both is `uv`:

```bash
# install uv (cross-platform)
curl -LsSf https://astral.sh/uv/install.sh | sh

# install Python 3.14 via uv
uv python install 3.14
```

The wrappers detect `uv` and use it automatically. Without `uv`, they
fall back to your system `python3` — in which case you'll need PyYAML
yourself:

```bash
python3 -m pip install PyYAML==6.0.3
```

Verify the helper scripts run:

```bash
cd ~/Documents/repos/braingent
scripts/doctor.sh
```

`doctor` reports tooling gaps, missing entrypoints, stale placeholders,
and frontmatter issues. It exits non-zero on errors so you can wire
it into pre-commit or CI.

> **Tip:** `uv` is recommended over plain `pip` because the helper
> scripts use script-level metadata (`# /// script ...`) that lets `uv`
> manage their dependencies in a per-script ephemeral env. No global
> Python pollution.

## Install the MCP server (optional)

If your agent supports the Model Context Protocol (Claude Code, Codex
CLI, and many others do), you can run Braingent's MCP server for
token-efficient retrieval.

```bash
# inside your memory repo
python3 -m pip install -r requirements.txt
```

The `requirements.txt` in the manifesto repo pins the `mcp` package and
PyYAML. After install, your agent's MCP config points at:

```json
{
  "mcpServers": {
    "braingent": {
      "command": "python3",
      "args": [
        "/Users/you/Documents/repos/braingent/scripts/mcp_server.py"
      ]
    }
  }
}
```

Restart your agent. The tools `braingent_find`, `braingent_get`, and
`braingent_guide` should appear in the tools list. See [MCP Tools
Reference](/reference/mcp-tools/).

## Install Bun for the dashboard or website (optional)

The dashboard and the website both run on Bun. You only need this if
you want either.

```bash
# macOS / Linux
curl -fsSL https://bun.sh/install | bash

# Windows (PowerShell)
irm bun.sh/install.ps1 | iex
```

Verify:

```bash
bun --version    # ≥ 1.3
```

Then for the dashboard:

```bash
cd ~/Documents/repos/braingent-manifesto/examples/task-dashboard
bun install
BRAINGENT_MEMORY_ROOT=~/Documents/repos/braingent bun run dev
```

See [Local Dashboard](/guides/dashboard/) for the full guide.

## Bootstrap a memory repo

If you didn't follow the [Quickstart](/guides/getting-started/), the
starter pack lives in the manifesto repo. Copy it manually:

```bash
git clone https://github.com/thedoublejay/braingent-manifesto
mkdir -p ~/Documents/repos/braingent
cp -R braingent-manifesto/starter-pack/* ~/Documents/repos/braingent/
cd ~/Documents/repos/braingent
git init && git add . && git commit -m "feat: bootstrap from braingent starter pack"
```

The `BOOTSTRAP-PROMPT.md` in the manifesto can be pasted into any agent
to walk through placeholder replacement interactively. That's the
**zero-install** path: no Python, no Bun, no CLI — just Git and Markdown.

## Verification checklist

After installing whatever you opted into, run the matching checks:

```bash
# always
git -C ~/Documents/repos/braingent status

# if you installed Python helpers
~/Documents/repos/braingent/scripts/doctor.sh
~/Documents/repos/braingent/scripts/find.sh --kind decision --limit 1
~/Documents/repos/braingent/scripts/recall.sh "first task"

# if you installed Bun for the dashboard
cd ~/Documents/repos/braingent-manifesto/examples/task-dashboard && bun install
```

If any fail, the error messages tell you which tool is missing. The
most common failure is Python < 3.14 — install via `uv` and re-run.

## Upgrading later

Pull the manifesto, then patch your memory repo against the latest
starter pack:

```bash
git -C ~/Documents/repos/braingent-manifesto pull
~/Documents/repos/braingent-manifesto/scripts/update.sh ~/Documents/repos/braingent
```

The update tool always shows a plan before mutating files — your local
edits win unless you explicitly accept a template change.

## Where to go next

- [Wire Up Your Agents](/guides/wire-up-agents/) — point Claude / Codex
  / ChatGPT / Gemini at the memory repo.
- [Agent Workflows](/guides/agent-workflows/) — what the agent does
  with everything once it's installed.
- [Local Dashboard](/guides/dashboard/) — Bun + React UI over your live
  tasks.
