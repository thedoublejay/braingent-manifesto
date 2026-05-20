---
title: CLI Workflows
description: Day-to-day Braingent CLI workflows for health checks, search, recall, live tasks, MCP, and QA plans.
section: Guides
order: 6
---

The `braingent` command is the public workflow surface. It operates on plain
Markdown files in a Git repo you control.

Run these examples from the root of your memory repo, or pass
`--root /path/to/braingent`.

## A Typical Day

```bash
# morning: see what is live
braingent doctor
braingent task-list --status in-progress

# during work: search before planning
braingent recall q="auth session rotation" --limit 8

# coordinate live work
braingent task-new "Backfill repo profile for example app" --priority medium
braingent task-claim BGT-0001 --as agent--codex-cli

# end of week: keep memory clean
braingent doctor --strict
braingent reindex --check
```

## Bootstrap

```bash
braingent init ~/Documents/repos/braingent
cd ~/Documents/repos/braingent
git init
git add .
git commit -m "feat: initialize braingent memory"
```

## Health Checks

```bash
braingent doctor
braingent doctor --strict
braingent validate
braingent reindex --check
```

`doctor` checks required files, stale placeholders, frontmatter, index drift,
tooling gaps, private path leaks, and possible secrets.

## Searching And Recall

```bash
# precise frontmatter filters
braingent find kind=decision topic=ai-memory --limit 10

# focused context pack
braingent recall repo=repo--example--owner--repo --limit 8

# path-only or JSON output
braingent find kind=task status=completed --paths
braingent recall ticket=ACME-123 --json
```

Common filter keys are `kind`, `org`, `project`, `repo`, `topic`, `tool`,
`ticket`, `status`, and `q`.

## Live Tasks

```bash
braingent task-new "Backfill repo profile for example app" --priority medium
braingent task-claim BGT-0001 --as agent--codex-cli
braingent task-comment BGT-0001 "Drafted profile, needs review." --as agent--codex-cli
braingent task-status BGT-0001 in-review --as agent--codex-cli --note "Ready for review"
braingent task-list --count
braingent task-archive BGT-0001 --resolution completed --as agent--codex-cli
```

Each command edits the matching `tasks/active/BGT-NNNN.md` file and leaves the
change visible in Git.

## Synthesis

Generate source-indexed synthesis from records:

```bash
braingent synthesize --topic topic--ai-memory
braingent synthesize --repo repo--example--owner--repo
braingent synthesize --project project--example--memory
```

## QA Plans

```bash
braingent qa generate \
  --ticket-key ACME-1492 \
  --evidence-pack ./build/qa-evidence.json \
  --emit-format markdown \
  --output ./qa-plans/ACME-1492.md \
  ./tickets/ACME-1492.md
```

See [QA Test Planning](/guides/qa-test-planning/) for the full workflow.

## MCP Server

```bash
braingent mcp serve --path ~/Documents/repos/braingent
```

Most users configure this in their agent's MCP config rather than running it by
hand. See [MCP Tools Reference](/reference/mcp-tools/).

## Updates

```bash
braingent update ~/Documents/repos/braingent --dry-run
braingent update ~/Documents/repos/braingent --write
```

The update command reports adds, clean updates, unchanged files, and conflicts.
It does not overwrite local edits unless you explicitly pass `--force`.
