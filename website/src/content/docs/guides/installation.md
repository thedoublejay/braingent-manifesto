---
title: Installation
description: Install the Braingent Python CLI, initialize a memory repo, and enable optional MCP and dashboard tools.
section: Get Started
order: 2
---

Braingent installs as a Python command-line app. Install it once, then use
`braingent init` to create a private memory repo and `braingent update` to keep
starter files current.

## Requirements

| Tool | Why |
| --- | --- |
| Python 3.11+ | Runs the `braingent` package. |
| `pipx` | Installs CLI apps into isolated environments. |
| Git | Versions your memory repo. |

Optional tools:

| Tool | What it adds |
| --- | --- |
| `rg` | Fast full-text search. |
| `jq` | JSON inspection for generated indexes. |
| `sqlite3` | Local derived search cache. |
| `gh` | GitHub issue and PR import workflows. |
| Bun | Local dashboard and website development. |

## Install The CLI

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install braingent
braingent --help
```

`uv` users can install or run the same command surface:

```bash
uv tool install braingent
uvx braingent --help
```

Optional extras add features (combine them, e.g. `"braingent[mcp,tokens]"`):

| Extra | Adds |
| --- | --- |
| `braingent[mcp]` | MCP server for agent retrieval — see [Enable MCP Retrieval](#enable-mcp-retrieval). |
| `braingent[tokens]` | Token-count helpers (`tiktoken`) for context budgeting. |

## Initialize A Memory Repo

```bash
braingent init ~/Documents/repos/braingent
cd ~/Documents/repos/braingent
git init
git add .
git commit -m "feat: initialize braingent memory"
```

The generated repo contains the agent entrypoints, preferences, workflows,
templates, indexes, and example-safe directory structure Braingent expects.

## Verify The Install

```bash
braingent --root ~/Documents/repos/braingent doctor
braingent --root ~/Documents/repos/braingent validate
braingent --root ~/Documents/repos/braingent reindex --check
braingent --root ~/Documents/repos/braingent find kind=decision --limit 1
```

Run from inside the memory repo and you can omit `--root`:

```bash
cd ~/Documents/repos/braingent
braingent doctor
braingent find kind=decision --limit 1
```

## Enable MCP Retrieval

For Claude, Codex, Gemini, or any MCP-aware agent, install Braingent with the
`mcp` extra:

```bash
pipx install "braingent[mcp]"      # or, for uv: uv tool install "braingent[mcp]"
```

Already installed without the extra? Re-run with `--force` to add it:

```bash
pipx install --force "braingent[mcp]"
```

Then configure the agent to start Braingent through the package CLI:

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

The package also installs a dedicated `braingent-mcp` entrypoint, so
`{"command": "braingent-mcp", "args": ["--path", "/Users/you/Documents/repos/braingent"]}`
is equivalent.

Restart the agent. It should expose `braingent_guide`, `braingent_find`, and
`braingent_get`.

## Generate QA Plans

The QA generator ships with the package:

```bash
braingent --root ~/Documents/repos/braingent qa generate \
  --ticket-key ACME-1492 \
  --evidence-pack ./build/qa-evidence.json \
  --emit-format markdown \
  --output ./qa-plans/ACME-1492.md \
  ./tickets/ACME-1492.md
```

It can emit Markdown, Xray JSON, TestRail CSV, or Gherkin.

## Update Starter Files

Check what a package update would change:

```bash
braingent update ~/Documents/repos/braingent --dry-run
```

Apply non-conflicting updates:

```bash
braingent update ~/Documents/repos/braingent --write
```

If local edits conflict with updated starter files, Braingent reports them
instead of overwriting them.

## Install Optional Lightweight Tools

```bash
# macOS
brew install ripgrep jq sqlite gh

# Debian / Ubuntu
sudo apt install ripgrep jq sqlite3 gh

# Windows
winget install BurntSushi.ripgrep.MSVC stedolan.jq SQLite.SQLite GitHub.cli
```

## Install Bun For The Dashboard

```bash
curl -fsSL https://bun.sh/install | bash
bun --version
```

See [Local Dashboard](/guides/dashboard/) for dashboard setup.

## Where To Go Next

- [Quickstart](/guides/getting-started/) — create and commit your first memory repo.
- [CLI Workflows](/guides/cli-workflows/) — day-to-day `braingent` commands.
- [MCP Tools Reference](/reference/mcp-tools/) — agent retrieval tools.
