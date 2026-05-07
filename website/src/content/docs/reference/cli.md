---
title: CLI Reference
description: Every Braingent CLI command, every flag, every exit code.
section: Reference
order: 1
---

The `braingent` CLI is a thin wrapper around plain Markdown operations.
Every command can be replaced with a manual edit + `git commit` — but the
CLI is faster and adds validation, indexing, and templating.

This page is the canonical surface. For tutorial-style explanations, see
the [CLI Workflows guide](/guides/cli-workflows/).

## Global flags

These flags are accepted by every command:

| Flag | Default | Notes |
| --- | --- | --- |
| `--path <dir>` | `$BRAINGENT_PATH` or `~/Documents/repos/braingent` | The memory repo to operate on. |
| `--json` | off | Emit JSON instead of human-readable output. |
| `--quiet` | off | Suppress non-error output. |
| `--verbose` | off | Print debug detail. |
| `--no-color` | off | Disable ANSI colors. |
| `--version` | — | Print CLI version and exit. |

### Environment variables

| Variable | What it sets |
| --- | --- |
| `BRAINGENT_PATH` | Default value for `--path`. |
| `BRAINGENT_NO_COLOR` | Same as `--no-color`. |
| `BRAINGENT_LOG_LEVEL` | `debug` / `info` / `warn` / `error`. |

## `init`

Bootstrap a new memory repo from the starter pack.

```bash
braingent init [target-dir]
```

| Flag | Default | Description |
| --- | --- | --- |
| `target-dir` | required | Where to create or seed the repo. |
| `--from <path>` | bundled | Use a different starter pack source. |
| `--non-interactive` | off | Use defaults; skip prompts. |
| `--force` | off | Overwrite existing files (dangerous). |
| `--no-git` | off | Skip `git init`. |
| `--name <slug>` | from prompt | Repo display name. |

Exit codes:
- `0` — success.
- `2` — target directory not empty without `--force`.
- `3` — required tool missing.

## `doctor`

Health-check a memory repo.

```bash
braingent doctor [--strict]
```

| Flag | Default | Description |
| --- | --- | --- |
| `--strict` | off | Warnings become errors. |
| `--check <key>` | all | Run only the named checks. |
| `--skip <key>` | none | Skip the named checks. |

Check keys: `entrypoints`, `placeholders`, `frontmatter`, `indexes`,
`tooling`, `private-paths`, `links`.

Exit codes:
- `0` — clean.
- `1` — error(s) reported.
- `2` — warning(s) under `--strict`.

## `validate`

Check frontmatter only.

```bash
braingent validate [--kind <kind>] [--since <date>]
```

| Flag | Default | Description |
| --- | --- | --- |
| `--kind <kind>` | all | Limit to one record kind. |
| `--since <date>` | — | Only records created on or after this date. |
| `--fix` | off | Auto-fix safe issues (date formatting, slug case). |

## `find`

Filter records by frontmatter fields.

```bash
braingent find [--kind ...] [--repo ...] [--tag ...] [--status ...] [--since ...] [--limit N]
```

| Flag | Notes |
| --- | --- |
| `--kind <kind>` | One of: `task`, `decision`, `review`, `learning`, `repo`, `project`, `topic`, `tool`. Repeatable. |
| `--repo <slug>` | Repeatable. |
| `--project <slug>` | Repeatable. |
| `--topic <slug>` | Repeatable. |
| `--tool <slug>` | Repeatable. |
| `--tag <tag>` | Repeatable. |
| `--status <status>` | Kind-specific. |
| `--owner <name>` | Match `owner` field. |
| `--since <date>` | YYYY-MM-DD. |
| `--until <date>` | YYYY-MM-DD. |
| `--limit <n>` | Default 50. |
| `--sort <field>` | `date` (default), `id`, `title`. |

Output: `<id>  <title>  <path>` per line, or JSON with `--json`.

## `get`

Fetch one record.

```bash
braingent get <id> [--depth summary|full]
```

| Flag | Default | Description |
| --- | --- | --- |
| `--depth` | `summary` | `summary` returns frontmatter + first paragraph; `full` returns whole body. |
| `--with-links` | off | Include linked record summaries. |
| `--format <md\|json>` | `md` | Output format. |

## `recall`

Build a focused context pack.

```bash
braingent recall <query> [--task <id>] [--max N]
```

| Flag | Default | Description |
| --- | --- | --- |
| `<query>` | required (or `--task`) | Free-text concept. |
| `--task <id>` | — | Walk links from a specific task instead. |
| `--max <n>` | 12 | Maximum records in the pack. |
| `--depth <n>` | 2 | How many graph hops to walk. |
| `--include-archived` | off | Include archived records. |

## `search`

Full-text body search with frontmatter ranking.

```bash
braingent search <query> [--kind ...]
```

Standard boolean syntax: `temporal AND idempotency`, `(jobs OR webhooks)
AND -archived`.

| Flag | Default | Description |
| --- | --- | --- |
| `--kind <kind>` | all | Repeatable. |
| `--limit <n>` | 50 | |
| `--context <n>` | 1 | Lines of body context per hit. |

## `capture`

Write a record without touching an agent.

```bash
braingent capture --kind <kind> --title "..." [--tags ...] [--body ...]
```

| Flag | Required? | Description |
| --- | --- | --- |
| `--kind <kind>` | yes | The record kind. |
| `--title "..."` | yes | Record title. |
| `--status <status>` | no | Defaults to kind's "live" value. |
| `--repo <slug>` | repeatable | Adds to `repos`. |
| `--project <slug>` | repeatable | Adds to `projects`. |
| `--topic <slug>` | repeatable | Adds to `topics`. |
| `--tool <slug>` | repeatable | Adds to `tools`. |
| `--tags <a,b,c>` | comma-list | Adds to `tags`. |
| `--link <id>` | repeatable | Adds to `links`. |
| `--body @<path>` | no | Read body from file. |
| `--body "..."` | no | Inline body. |
| `--dry-run` | off | Print path + frontmatter, don't write. |
| `--no-commit` | off | Write file but skip `git commit`. |

## `update`

Apply starter-pack improvements safely.

```bash
braingent update [--apply auto|all|none] [--dry-run]
```

| Flag | Default | Description |
| --- | --- | --- |
| `--apply <mode>` | `auto` | `auto` = safe-only, `all` = include manual review, `none` = plan only. |
| `--dry-run` | off | Print plan, don't write. |
| `--from <path>` | bundled | Use a different starter-pack source. |

## `synthesize`

Generate a synthesis page that cites records.

```bash
braingent synthesize --topic <slug> --out <path>
```

| Flag | Required? | Description |
| --- | --- | --- |
| `--topic <slug>` | one of these | Synthesize within a topic. |
| `--repo <slug>` | one of these | Synthesize within a repo. |
| `--project <slug>` | one of these | Synthesize within a project. |
| `--since <date>` | no | Limit by date. |
| `--max-records <n>` | no, default 40 | Cap how many sources are included. |
| `--out <path>` | yes | Output Markdown path. |

## `qa-generate`

Generate a strict QA plan from ticket + memory + evidence. See [QA Test
Planning](/guides/qa-test-planning/).

```bash
braingent qa-generate --ticket <path> [--evidence <path>] [--gatherstep] [--format <fmt>] [--out <path>]
```

| Flag | Description |
| --- | --- |
| `--ticket <path or URL>` | Source ticket. Required. |
| `--allow-missing-ac` | Skip the AC requirement. Pair with `--intent`. |
| `--intent "..."` | Free-text product intent when AC is missing. |
| `--evidence <path>` | `qa-evidence.v1` manifest from your build. |
| `--gatherstep` | Pull native evidence from Gather Step's CLI. |
| `--memory <path>` | Path to memory repo (defaults to `--path`). |
| `--budget-tokens <n>` | Default 160000. |
| `--format <md\|xray\|testrail\|gherkin>` | Output format. |
| `--out <path>` | Output path. Required. |
| `--strict` | Treat precheck warnings as errors. |
| `--include-risks` | On by default. Add risks per case. |

Exit codes:
- `0` — plan generated.
- `1` — precheck error.
- `2` — strict-mode warning.

## Live task commands — `task-*`

See [Multi-Agent Coordination](/guides/multi-agent-tasks/) for the full
flow.

| Command | Notes |
| --- | --- |
| `task-new "<title>"` | `--priority P0..P4`, `--repo`, `--project`. |
| `task-claim <BGT-ID>` | `--as <agent>`. |
| `task-status <BGT-ID> "<line>"` | Append to status log. |
| `task-question <BGT-ID> "<text>"` | Add to open questions. |
| `task-block <BGT-ID> "<text>"` | Add to blockers. |
| `task-unblock <BGT-ID> "<text>"` | Resolve a blocker. |
| `task-close <BGT-ID>` | `--status done\|abandoned`. |
| `task-list` | `--status`, `--owner`, `--repo`. |
| `task-archive <BGT-ID>` | Move from `tasks/active/` to `tasks/done/`. |

## `mcp serve`

Start the MCP server.

```bash
braingent mcp serve [--port <n>] [--read-only]
```

| Flag | Default | Description |
| --- | --- | --- |
| `--port <n>` | stdio | Use TCP instead of stdio. |
| `--read-only` | off | Disable any future write tools. |

## `print-prompts`

Print agent entrypoint contents (no file changes).

```bash
braingent print-prompts --agent <claude|codex|chatgpt|gemini> [--copy]
```

| Flag | Default | Description |
| --- | --- | --- |
| `--agent <name>` | required | Which entrypoint to print. |
| `--copy` | off | Copy to clipboard instead of stdout. |

## `reindex`

Regenerate `indexes/*.md` and search caches.

```bash
braingent reindex [--check]
```

| Flag | Default | Description |
| --- | --- | --- |
| `--check` | off | Exit non-zero if indexes drifted; don't write. |

## Where to go next

- [CLI Workflows](/guides/cli-workflows/) — tutorial-style tour.
- [QA Test Planning](/guides/qa-test-planning/) — `qa-generate` end to
  end.
- [MCP Tools Reference](/reference/mcp-tools/) — the MCP equivalents.
