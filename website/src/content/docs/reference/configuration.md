---
title: Configuration
description: Optional configuration knobs — most users never need them. Defaults are designed to be right.
section: Reference
order: 3
---

Braingent's defaults are intentional: the smallest configuration that
makes search, capture, and validation work out of the box. Most users
never touch any of these knobs. If you do, here's what's available.

## Configuration sources, in priority order

Higher in this list wins.

1. **CLI flags** (`--path`, `--strict`, etc.).
2. **Environment variables** (`BRAINGENT_PATH`, `BRAINGENT_NO_COLOR`).
3. **Repo-local config** (`.braingent/config.toml` inside the memory
   repo).
4. **User-level config** (`~/.braingent/config.toml`).
5. **Built-in defaults**.

## Repo-local config

Optional. Lives at `.braingent/config.toml` inside the memory repo.

```toml
# .braingent/config.toml
version = 1

[memory]
# Override the default record kind directories.
# Most users leave this alone.
decisions_dir = "decisions"
reviews_dir   = "reviews"
learnings_dir = "learnings"
tasks_dir     = "tasks"

[task_ids]
# Format for task IDs. Default: BGT-NNNN, zero-padded to 4.
prefix = "BGT"
pad    = 4

[capture]
# Trigger phrases that mean "capture this".
phrases = [
  "capture this",
  "save to braingent",
  "write to braingent",
  "task done",
  "done thanks",
  "ok done",
]

# Whether to auto-capture on PR open / merge / ticket close.
auto_capture_on_pr     = true
auto_capture_on_ticket = true

[indexes]
# Which indexes to regenerate on `braingent reindex`.
generate = ["by-topic", "by-repo", "by-tool", "decisions-index", "recent"]
recent_count = 50

[validate]
# Status vocabularies per record kind. Override only if you really mean it.
[validate.task]
allowed_status = ["planned", "in_progress", "done", "abandoned", "blocked"]

[mcp]
# Read-only mode. Currently every tool is read-only; this flag is
# future-proof for write tools.
read_only = false
```

`braingent doctor` validates this file at startup.

## User-level config

`~/.braingent/config.toml`. Same shape as the repo-local file. Useful
for personal preferences (clipboard tool, editor) you don't want to
commit.

```toml
[ui]
editor    = "code"           # what `braingent open <id>` launches
clipboard = "pbcopy"          # for `--copy` flags

[print_prompts]
default_agent = "claude"
```

## Privacy / safety knobs

```toml
[safety]
# Paths that should never appear inside committed Markdown.
# `braingent doctor` flags violations.
forbid_paths = ["~/private", "/Users/secrets"]

# Patterns that should never appear in record bodies.
forbid_patterns = [
  "AKIA[0-9A-Z]{16}",            # AWS access key ids
  "ghp_[A-Za-z0-9]{36}",         # GitHub PATs
  "sk-[A-Za-z0-9]{40,}",         # OpenAI / Anthropic-style keys
]
```

`forbid_patterns` is a defense-in-depth — the manifesto ships with the
most common patterns enabled. Add yours.

## Bootstrap hooks

`.braingent/hooks/` (optional). Each script runs at a known lifecycle
moment, if it exists.

| Hook | When it runs |
| --- | --- |
| `pre-capture.sh` | Before a record is written. Receives the draft frontmatter on stdin. Exit non-zero to abort. |
| `post-capture.sh` | After capture commits. Receives the commit SHA. |
| `pre-update.sh` | Before `braingent update` applies changes. |
| `post-doctor.sh` | After `doctor` runs. Receives the report on stdin. |

Hooks are plain shell scripts. Keep them small. If you find yourself
writing a long hook, you probably want a workflow under `workflows/`
instead.

## MCP server

The MCP server reads its config from CLI args, not a file. See
[Installation → MCP Server](/guides/installation/#install-the-mcp-server)
for the JSON config blocks per agent.

## Where to go next

- [CLI Reference](/reference/cli/) — every flag for every command.
- [Frontmatter Schema](/concepts/frontmatter-schema/) — the schema that
  `validate` checks against.
- [Repository Shape](/concepts/repository-shape/) — the layout that
  defaults assume.
