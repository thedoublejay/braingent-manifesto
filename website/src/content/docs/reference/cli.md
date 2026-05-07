---
title: CLI Reference
description: Runnable Braingent starter-pack scripts, flags, and examples.
section: Reference
order: 1
---

Braingent's public starter pack ships runnable helper scripts under
`scripts/`. They are deliberately thin wrappers around Markdown files. You can
always replace them with manual edits plus `git commit`; the scripts make
search, validation, indexing, task coordination, MCP retrieval, and QA planning
faster.

Run these commands from the root of your copied memory repo.

## Runtime

Most scripts use `python3` with `PyYAML==6.0.3`, or `uv` as a fallback when the
dependency is not installed globally.

```bash
python3 -m pip install -r requirements.txt
```

## `scripts/doctor.sh`

Report memory-repo health: missing entrypoints, placeholder leftovers,
frontmatter issues, stale indexes, possible private paths, possible secrets,
and stale records.

```bash
scripts/doctor.sh
scripts/doctor.sh --json
scripts/doctor.sh --strict
```

| Flag | Description |
| --- | --- |
| `--json` | Emit the report as JSON. |
| `--strict` | Exit non-zero when warnings are present. |
| `--stale-days <n>` | Age threshold for stale profile/learning records. Default `180`. |

## `scripts/validate.sh`

Validate record frontmatter against `preferences/taxonomy.yml`.

```bash
scripts/validate.sh
scripts/validate.sh orgs/org--example/projects/project--example--memory/records/example.md
```

Arguments are optional Markdown paths. With no paths, the whole repo is
validated.

## `scripts/reindex.sh`

Regenerate derived indexes under `indexes/` and `.braingent.db`.

```bash
scripts/reindex.sh
scripts/reindex.sh --check
```

| Flag | Description |
| --- | --- |
| `--check` | Fail if generated indexes are stale, without writing changes. |
| `--dashboard-e2e` | Also run dashboard Playwright checks when the dashboard exists. |

## `scripts/find.sh`

Search durable records by structured frontmatter filters.

```bash
scripts/find.sh kind=decision
scripts/find.sh repo=repo--example--owner--repo status=active --limit 5
scripts/find.sh q="pagination state" --json
```

| Flag / Argument | Description |
| --- | --- |
| `key=value` | Filter by frontmatter or body text. Common keys: `kind`, `org`, `project`, `repo`, `topic`, `tool`, `ticket`, `status`, `q`. |
| `--json` | Emit JSON. |
| `--paths` | Emit only matching paths. |
| `--count` | Emit only the result count. |
| `--limit <n>` | Limit result count. |

## `scripts/recall.sh`

Build a focused context pack for an agent before planning or implementation.

```bash
scripts/recall.sh repo=repo--example--owner--repo
scripts/recall.sh ticket=ACME-123 --json
```

| Flag / Argument | Description |
| --- | --- |
| `key=value` | Same filter style as `find.sh`. |
| `--json` | Emit JSON. |
| `--limit <n>` | Number of `must_read` records. Default `8`. |
| `--stale-days <n>` | Staleness threshold. Default `180`. |

## `scripts/new-record.sh`

Create a dated record from a template.

```bash
scripts/new-record.sh task project--example--memory "ship discussion tab" \
  orgs/org--example/projects/project--example--memory/records
```

Arguments:

1. Record kind: `task`, `review`, `decision`, `learning`, `interaction`,
   `version`, `note`, `summary`, `profile`, or `ticket-stub`.
2. Entity key: project, repo, topic, tool, person, org, or ticket key.
3. Subject.
4. Output directory.
5. Optional filename suffix.

## `scripts/qa-generate.sh`

Generate a strict QA plan from ticket + memory + optional Gather Step evidence.
See [QA Test Planning](/guides/qa-test-planning/).

```bash
scripts/qa-generate.sh \
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
| `--gather-target <target>` | Symbol, route, or event target for Gather Step `qa-evidence`. |
| `--projection-target <target>` | Optional field/contract target for projection impact evidence. |
| `--evidence-pack <path>` | Existing `qa-evidence.v1` manifest. |
| `--budget-tokens <n>` | Default `160000`. |
| `--emit-format <fmt>` | `markdown`, `xray-json`, `testrail-csv`, or `gherkin`. |
| `--output <path>` | Explicit output path. |
| `--output-dir <path>` | Output directory. Defaults to `.test-plans/`. |
| `--repo`, `--project`, `--topic`, `--tool` | Braingent memory filters. |
| `--print` | Print generated output after writing it. |

## `scripts/synthesize.sh`

Generate a source-indexed synthesis page from records.

```bash
scripts/synthesize.sh --topic topic--ai-memory
scripts/synthesize.sh --repo repo--example--owner--repo
scripts/synthesize.sh --project project--example--memory
```

Exactly one of `--topic`, `--repo`, or `--project` is required.

## `scripts/cleanup.sh`

Run report-only cleanup checks.

```bash
scripts/cleanup.sh --daily
scripts/cleanup.sh --weekly
```

Cleanup reports stale generated indexes, unchecked follow-ups, stale records,
raw imports, and live-task hygiene. It does not rewrite records by itself.

## Live Task Scripts

Coordinate optional live `BGT-NNNN` task files under `tasks/`.

| Script | Purpose |
| --- | --- |
| `scripts/task-new.sh "<title>"` | Create a live task. |
| `scripts/task-claim.sh BGT-0001 --as agent--codex-cli` | Claim a task. |
| `scripts/task-comment.sh BGT-0001 "note" --as agent--codex-cli` | Append activity. |
| `scripts/task-status.sh BGT-0001 in-review --as agent--codex-cli` | Change status. |
| `scripts/task-list.sh` | List live and archived tasks. |
| `scripts/task-list.sh --count` | Print status counts. |
| `scripts/task-archive.sh BGT-0001 --resolution completed --as agent--codex-cli` | Close and archive. |

## MCP Server

Expose token-efficient retrieval tools to MCP-aware agents.

```bash
python3 scripts/mcp_server.py
```

Tools:

- `braingent_guide()`
- `braingent_find(query, limit)`
- `braingent_get(path, depth)`

Point your agent's MCP config at `scripts/mcp_server.py` from your copied
memory repo.
