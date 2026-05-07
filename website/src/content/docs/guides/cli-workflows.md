---
title: Script Workflows
description: Day-to-day Braingent starter-pack scripts — validate, find, recall, reindex, live tasks, MCP, and QA plans.
section: Guides
order: 6
---

The public starter pack ships runnable scripts under `scripts/`. They remove
friction from the memory loop without hiding state in a binary. Every script
operates on plain Markdown files in a Git repo you control.

Run these examples from the root of your copied memory repo.

## A typical day

```bash
# morning: see what's live
scripts/doctor.sh
scripts/task-list.sh --status in-progress

# during work: search before planning
scripts/recall.sh q="auth session rotation" --limit 8

# after a PR merges: create a record scaffold
scripts/new-record.sh task project--example--memory \
  "fix billing webhook race" orgs/org--example/projects/project--example--memory/records

# end of week: keep memory clean
scripts/doctor.sh --strict
scripts/reindex.sh --check
```

## Bootstrap manually

There is no packaged `init` command yet. The supported public path is still
simple and explicit:

```bash
git clone https://github.com/thedoublejay/braingent-manifesto
mkdir -p ~/Documents/repos/braingent
cp -R braingent-manifesto/starter-pack/. ~/Documents/repos/braingent/
cd ~/Documents/repos/braingent
git init
```

Then replace placeholders, run `scripts/doctor.sh`, and commit.

## Health checks

```bash
scripts/doctor.sh
scripts/doctor.sh --strict
scripts/validate.sh
scripts/reindex.sh --check
```

`doctor` checks required files, stale placeholders, frontmatter, index drift,
tooling gaps, possible private paths, and possible secrets.

## Searching and recall

```bash
# precise frontmatter filters
scripts/find.sh kind=decision topic=ai-memory --limit 10

# focused context pack
scripts/recall.sh repo=repo--example--owner--repo --limit 8

# raw full-text fallback
rg -n "billing webhook idempotency" .
```

Use `key=value` filters. Common keys are `kind`, `org`, `project`, `repo`,
`topic`, `tool`, `ticket`, `status`, and `q`.

## Capturing

Use `scripts/new-record.sh` to create the right filename and frontmatter from a
template, then edit the body by hand or with your agent.

```bash
scripts/new-record.sh decision project--example--memory \
  "prefer markdown source of truth" orgs/org--example/projects/project--example--memory/records
scripts/validate.sh
scripts/reindex.sh
git add . && git commit -m "docs: capture memory decision"
```

## Live tasks

```bash
scripts/task-new.sh "Backfill repo profile for example app" --priority medium
scripts/task-claim.sh BGT-0001 --as agent--codex-cli
scripts/task-comment.sh BGT-0001 "Drafted profile, needs review." --as agent--codex-cli
scripts/task-status.sh BGT-0001 in-review --as agent--codex-cli
scripts/task-list.sh --count
scripts/task-archive.sh BGT-0001 --resolution completed --as agent--codex-cli
```

Each command edits the matching `tasks/active/BGT-NNNN.md` file. Editing by
hand works too.

## Synthesis

Generate source-indexed synthesis from records:

```bash
scripts/synthesize.sh --topic topic--ai-memory
scripts/synthesize.sh --repo repo--example--owner--repo
scripts/synthesize.sh --project project--example--memory
```

## QA plans

The flagship workflow. See [QA Test Planning](/guides/qa-test-planning/) for
the full guide.

```bash
scripts/qa-generate.sh \
  --ticket-key ACME-1492 \
  --evidence-pack ./build/qa-evidence.json \
  --emit-format markdown \
  --output ./qa-plans/ACME-1492.md \
  ./tickets/ACME-1492.md
```

## Indexing

Regenerate `indexes/*.md`, `indexes/*.json`, and `.braingent.db` from records.

```bash
scripts/reindex.sh
scripts/reindex.sh --check
```

`--check` is the right flag for CI; it reports drift without writing.

## MCP server

Start the MCP server for local agent retrieval:

```bash
python3 scripts/mcp_server.py
```

Most users configure this in their agent's MCP config rather than running it by
hand. See [Installation → MCP Server](/guides/installation/#install-the-mcp-server).

## Updates

There is no packaged `update` helper yet. Pull `braingent-manifesto`, compare
your memory repo against `starter-pack/`, and copy only the generic files you
want to adopt.

```bash
git -C ~/Documents/repos/braingent-manifesto pull
diff -ru ~/Documents/repos/braingent ~/Documents/repos/braingent-manifesto/starter-pack
```
