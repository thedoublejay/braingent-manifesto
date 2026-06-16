---
title: CLI Reference
description: The installable Braingent Python CLI, commands, flags, and examples.
section: Reference
order: 1
---

The `braingent` command is the public API for creating, checking, searching,
updating, and serving a Braingent memory repo.

Run commands from the memory repo root, or pass `--root /path/to/repo`.

```bash
braingent --help
braingent --root ~/Documents/repos/braingent doctor
```

## Install

```bash
pipx install braingent          # or: uv tool install braingent
braingent --version
```

Optional extras: `braingent[mcp]` (MCP retrieval server, also installs the
`braingent-mcp` command) and `braingent[tokens]` (token-count helpers). Combine
as `braingent[mcp,tokens]`.

```bash
pipx install "braingent[mcp]"   # add --force to add the extra to an existing install
```

## `braingent init`

Create a new memory repo from the packaged starter template.

```bash
braingent init ~/Documents/repos/braingent
braingent init ~/Documents/repos/braingent --dry-run
braingent init ~/Documents/repos/braingent --force
```

| Flag | Description |
| --- | --- |
| `--dry-run` | Show what would be copied. |
| `--force` | Allow copying into a non-empty target. |

## `braingent update`

Update starter template files in an existing memory repo.

```bash
braingent update ~/Documents/repos/braingent --dry-run
braingent update ~/Documents/repos/braingent --write
braingent update ~/Documents/repos/braingent --write --force
```

| Flag | Description |
| --- | --- |
| `--dry-run` | Show add/update/conflict counts without writing. |
| `--write` | Apply non-conflicting updates. |
| `--force` | Overwrite conflicted template files when used with `--write`. |

## `braingent doctor`

Report memory-repo health: missing entrypoints, placeholder leftovers,
frontmatter issues, stale indexes, possible private paths, possible secrets,
and stale records.

```bash
braingent doctor
braingent doctor --json
braingent doctor --strict
```

| Flag | Description |
| --- | --- |
| `--json` | Emit the report as JSON. |
| `--strict` | Exit non-zero when warnings are present. |
| `--stale-days <n>` | Age threshold for stale profile/learning records. Default `180`. |

## `braingent validate`

Validate record frontmatter against `preferences/taxonomy.yml`.

```bash
braingent validate
braingent validate orgs/org--example/projects/project--example--memory/records/example.md
```

Arguments are optional Markdown paths. With no paths, the whole repo is
validated.

## `braingent reindex`

Regenerate derived indexes under `indexes/` and `.braingent.db`.

```bash
braingent reindex
braingent reindex --check
```

| Flag | Description |
| --- | --- |
| `--check` | Fail if generated indexes are stale, without writing changes. |
| `--dashboard-e2e` | Also run dashboard checks when the dashboard exists. |

## `braingent find`

Search durable records by structured frontmatter filters.

```bash
braingent find kind=decision
braingent find repo=repo--example--owner--repo status=active --limit 5
braingent find q="pagination state" --json
```

| Flag / Argument | Description |
| --- | --- |
| `key=value` | Filter by frontmatter or body text. Common keys: `kind`, `org`, `project`, `repo`, `topic`, `tool`, `ticket`, `status`, `q`. |
| `--json` | Emit JSON. |
| `--paths` | Emit only matching paths. |
| `--count` | Emit only the result count. |
| `--limit <n>` | Limit result count. |

## `braingent recall`

Build a focused context pack for an agent before planning or implementation.

```bash
braingent recall repo=repo--example--owner--repo
braingent recall ticket=ACME-123 --json
```

| Flag / Argument | Description |
| --- | --- |
| `key=value` | Same filter style as `find`. |
| `--json` | Emit JSON. |
| `--limit <n>` | Number of `must_read` records. Default `8`. |
| `--stale-days <n>` | Staleness threshold. Default `180`. |

## `braingent qa generate`

Generate a strict QA plan from ticket + memory + optional Gather Step evidence.
See [QA Test Planning](/guides/qa-test-planning/).

```bash
braingent qa generate \
  --ticket-key ACME-1492 \
  --evidence-pack ./build/qa-evidence.json \
  --emit-format markdown \
  --output ./qa-plans/ACME-1492.md \
  ./tickets/ACME-1492.md
```

| Flag | Description |
| --- | --- |
| `<ticket-path-or-inline-ticket-text>` | Source ticket text or path. Required. |
| `--ticket-key <key>` | Ticket key used in the output title and filename. |
| `--allow-missing-ac` | Allow product-intent-derived `REQ-*` cases when explicit AC is missing. |
| `--source <path-or-text>` | Supporting spec, PRD, note, design source, or pasted text. Repeatable. |
| `--implementation-state <state>` | `pre-implementation`, `in-progress`, or `post-implementation`. |
| `--no-diff` | Skip white-box implementation evidence. |
| `--diff <base..head>` | Diff range for implementation evidence. |
| `--gather-workspace <path>` | Workspace where Gather Step should run. |
| `--gather-target <target>` | Symbol, route, or event target for Gather Step. |
| `--projection-target <target>` | Optional field/contract target for projection impact evidence. |
| `--evidence-pack <path>` | Existing `qa-evidence.v1` manifest. |
| `--budget-tokens <n>` | Default `160000`. |
| `--emit-format <fmt>` | `markdown`, `xray-json`, `testrail-csv`, or `gherkin`. |
| `--output <path>` | Explicit output path. |
| `--output-dir <path>` | Output directory. Defaults to `.test-plans/`. |
| `--repo`, `--project`, `--topic`, `--tool` | Braingent memory filters. |
| `--print` | Print generated output after writing it. |

## `braingent synthesize`

Generate a source-indexed synthesis page from records.

```bash
braingent synthesize --topic topic--ai-memory
braingent synthesize --repo repo--example--owner--repo
braingent synthesize --project project--example--memory
```

Exactly one of `--topic`, `--repo`, or `--project` is required.

## Live Task Commands

Coordinate optional live `BGT-NNNN` task files under `tasks/`.

| Command | Purpose |
| --- | --- |
| `braingent task-new "<title>"` | Create a live task. |
| `braingent task-claim BGT-0001 --as agent--codex-cli` | Claim a task. |
| `braingent task-comment BGT-0001 "note" --as agent--codex-cli` | Append activity. |
| `braingent task-status BGT-0001 in-review --as agent--codex-cli` | Change status. |
| `braingent task-list` | List live and archived tasks. |
| `braingent task-list --count` | Print status counts. |
| `braingent task-archive BGT-0001 --resolution completed --as agent--codex-cli` | Close and archive. |

## MCP Server

Expose token-efficient retrieval tools to MCP-aware agents. Requires the
`braingent[mcp]` extra.

```bash
braingent mcp serve --path ~/Documents/repos/braingent
# equivalent dedicated entrypoint:
braingent-mcp --path ~/Documents/repos/braingent
```

Tools:

- `braingent_guide()`
- `braingent_find(query, limit)`
- `braingent_get(path, depth)`

Point your agent's MCP config at `braingent mcp serve --path <memory-repo>`.
