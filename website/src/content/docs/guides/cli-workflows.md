---
title: CLI Workflows
description: Day-to-day Braingent CLI commands — bootstrap, validate, find, recall, capture, update, and ship QA plans.
section: Guides
order: 6
---

The Braingent CLI is small on purpose. Its job is to remove friction from
the loop, not to hide product state in a binary. Every command operates on
plain Markdown files in a Git repo you control.

This page is a tour of the day-to-day commands and the tasks they solve.
For exhaustive flags, see the [CLI Reference](/reference/cli/).

## A typical day

```bash
# morning: see what's live
braingent doctor
braingent task-list --status in_progress

# during work: search before planning
braingent recall "auth session rotation" --max 8

# after a PR merges: capture
braingent capture --kind task \
  --title "Fix billing webhook race" \
  --repo acme/api \
  --tags billing,webhook,fix

# end of week: keep memory clean
braingent doctor --strict
braingent reindex
```

That's most of what you'll ever run. Everything else is a variant.

## Bootstrapping — `braingent init`

Run once per memory repo. Walks you through setup, copies the starter
pack, replaces placeholders, runs an initial `doctor + validate +
reindex` pass.

```bash
braingent init ~/Documents/repos/braingent
```

What it does:

1. Resolves the target directory and detects whether it's empty, already
   a Braingent repo, or unrelated content.
2. Asks the minimum setup questions: repo owner/name, primary AI tools,
   privacy posture, first organization/project, optional live-task and
   dashboard modules.
3. Copies `starter-pack/` into the target with a version marker.
4. Replaces known placeholders from your answers.
5. Runs `doctor`, `validate`, and `reindex --check` if those tools are
   available.
6. Prints the first commit command and the next workflow to run.

The command refuses risky overwrites unless you pass `--force`.

## Health checks — `braingent doctor`

`doctor` is the first command you should run when something feels off.

```bash
braingent doctor                      # checks default memory repo
braingent doctor --path /elsewhere   # different repo
braingent doctor --strict            # warnings become errors
```

It checks for:

- Missing required entrypoint files.
- Stale placeholders (e.g. unmodified `<YOUR_NAME>`).
- Malformed YAML frontmatter.
- Generated-index drift.
- Tooling gaps (`rg`, `jq`, `sqlite`, `gh`).
- Private path leaks (paths under `~/private/...` in committed Markdown).

Exit code is non-zero on any error, so `doctor` is safe to wire into
pre-commit or CI.

## Searching — `braingent find` / `recall` / `search`

Three modes, three depths. See [Search & Recall](/guides/search-and-recall/)
for the full taxonomy. The TL;DR:

```bash
# precise filter on frontmatter
braingent find --kind decision --tag jobs --since 2026-01-01

# graph walk for a single concept
braingent recall "billing webhook idempotency" --max 8

# full-text fallback
braingent search 'temporal AND idempotency' --kind decision
```

## Reading — `braingent get`

Fetch one record by id.

```bash
braingent get DEC-0218 --depth summary
braingent get BGT-0142 --depth full
```

`summary` is cheap; `full` is the whole body. Default is `summary`.

## Capturing — `braingent capture`

The CLI version of *capture this*. Useful when an agent isn't in the
loop.

```bash
braingent capture \
  --kind task \
  --title "Fix billing webhook race" \
  --status done \
  --repo acme/api \
  --tags billing,webhook,fix \
  --body @./notes.md
```

The command picks the right directory, generates frontmatter, validates,
and commits. Run `--dry-run` first if you want to preview the file path
and frontmatter before writing.

## Live tasks — `braingent task-*`

Multi-agent coordination commands. See [Multi-Agent
Coordination](/guides/multi-agent-tasks/).

```bash
braingent task-new "Backfill repo profile for acme/api" --priority P2
braingent task-claim BGT-0142 --as claude
braingent task-status BGT-0142 "drafted profile, 14 sections"
braingent task-question BGT-0142 "include deprecated /v1/login?"
braingent task-close BGT-0142 --status done
braingent task-list --status in_progress
braingent task-archive BGT-0142
```

Each command is a thin wrapper that edits the matching
`tasks/active/BGT-NNNN.md` file. Editing by hand works the same.

## Synthesis — `braingent synthesize`

Generate a synthesis page from records. Every claim cites the record it
came from.

```bash
braingent synthesize \
  --topic auth \
  --repos acme/api,acme/web \
  --since 2026-01-01 \
  --out topics/auth/2026-h1-synthesis.md
```

Output is a `topics/<slug>/<date>-synthesis.md` Markdown file with
inline citations to source records.

## Updates — `braingent update`

Pull starter-pack improvements safely.

```bash
braingent update --path ~/Documents/repos/braingent
```

`update` produces a patch plan first, classifies each change as safe
auto-merge, manual review, or skipped. It never overwrites your edits
without an explicit diff.

## QA plans — `braingent qa-generate`

The flagship workflow. See [QA Test Planning](/guides/qa-test-planning/)
for the full guide.

```bash
braingent qa-generate \
  --ticket ./tickets/ACME-1492.md \
  --evidence ./build/qa-evidence.json \
  --memory ~/Documents/repos/braingent \
  --format markdown \
  --out ./qa-plans/ACME-1492.md
```

## Indexing — `braingent reindex`

Regenerate `indexes/*.md` and search caches from records.

```bash
braingent reindex
braingent reindex --check    # exits non-zero if indexes drifted
```

`--check` is the right flag for CI; it reports drift without writing.

## MCP server — `braingent mcp serve`

Start the MCP server for the configured agent.

```bash
braingent mcp serve --path ~/Documents/repos/braingent
```

Most users configure this in their agent's MCP config rather than
running it by hand. See [Installation → MCP
Server](/guides/installation/#install-the-mcp-server).

## Print agent prompts — `braingent print-prompts`

Useful when you want to set up an agent that can't auto-load a file
(ChatGPT projects, custom GPTs).

```bash
braingent print-prompts --agent chatgpt
braingent print-prompts --agent claude --copy   # copies to clipboard
```

It prints the personalized entrypoint contents for the requested agent.
No file changes.

## Where to go next

- [CLI Reference](/reference/cli/) — every flag, every command.
- [QA Test Planning](/guides/qa-test-planning/) — the flagship workflow.
- [Search & Recall](/guides/search-and-recall/) — when to use which
  query mode.
