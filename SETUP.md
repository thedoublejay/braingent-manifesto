# Setup Guide

This guide creates a Braingent-style memory repo with Markdown as the source of
truth and the installable Python CLI as the workflow surface.

## Prerequisites

Required:

- Python 3.11+.
- `pipx` or `uv`.
- Git.
- One AI tool, such as Claude, Codex, or ChatGPT.

Optional but useful:

- `rg` or another fast search tool.
- `jq` and `yq` for structured JSON/YAML inspection.
- SQLite if you later build generated indexes.
- GitHub CLI if you later want to index merged PRs.
- Bun and Playwright if you later build or run the optional task dashboard.

## Step 1: Install The CLI

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install braingent
```

`uv` users can run `uv tool install braingent`.

## Step 2: Initialize A Repo

Create a new repository named `braingent` or any name you prefer.

```bash
braingent init <your-memory-repo>
cd <your-memory-repo>
git init
```

Do not hardcode private paths into committed files. Use placeholders or relative
paths where possible.

Your new repo should start with files like:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `CHATGPT_PROJECT_BRIEF.md`
- `INDEX.md`
- `CURRENT_STATE.md`
- `preferences/`
- `templates/`
- `workflows/`
- `repositories/`
- `orgs/`
- `topics/`
- `tools/`
- `people/`
- `tickets/`
- `imports/`
- `inbox/`
- `indexes/`

The optional v3 live-work module also includes `tasks/`,
`preferences/agent-task-protocol.md`, `templates/agent-task.md`, and optional
`dashboard/tasks/` documentation. Keep it if you want active task coordination;
delete it if you only want durable memory records.

If you want the local dashboard app, copy `examples/task-dashboard/` into your
memory repo as `dashboard/tasks/`. The sample app uses synthetic data by default
and supports `BRAINGENT_MEMORY_ROOT=/path/to/your-braingent` for real task files.

## Step 3: Replace Placeholders

Run the first checks:

```bash
braingent doctor
braingent validate
```

Search for placeholder syntax:

```bash
rg "<[^>]+>"
```

Replace values such as:

- `<your-name>`
- `<timezone>`
- `<organization-key>`
- `<project-key>`
- `<repo-key>`
- `<repo-url>`
- `<ticket-id-or-null>`

Keep the examples generic until you are ready to add real private context.

## Step 4: Add Your First Entity Pages

Start small:

1. One organization page.
2. One project page.
3. One repository profile.
4. One topic page for AI memory or your main technology.
5. One task record for the setup itself.

Do not import everything on day one. The first goal is to make the memory usable.

## Step 5: Add Agent Entrypoints

The starter pack includes:

- `AGENTS.md` for Codex-style agents.
- `CLAUDE.md` for Claude-style agents.
- `CHATGPT_PROJECT_BRIEF.md` for ChatGPT projects.

Each file should tell the AI:

- read the repo before planning
- search prior records
- follow the capture policy
- never store secrets
- create records after meaningful work

If your tool supports global instructions, you can copy or symlink these files into that tool's global instruction location. Keep machine-specific paths out of the committed files.

## Step 6: Make The First Commit

```bash
git add .
git commit -m "Initialize Braingent memory repo"
```

After this, use normal Git commits to preserve memory changes.

With the pipx install flow there is no separate setup repo to clean up — `braingent init` generates your memory repo directly from the packaged template. (If you instead cloned `braingent-manifesto` to work on the starter kit itself, keep that checkout separate from your memory repo so agents don't read the public starter kit instead of your real memory.)

## Step 7: Index Your First Codebase

Once setup is committed, point Braingent at a real repo.

If you are inside the codebase you want indexed, tell your agent:

```text
Index this repo to braingent
```

If you are working from another directory, name the target:

```text
Index <specific-repo> to braingent
```

The agent should follow `workflows/index-repo.md`, scan local docs and Git history, use optional sources such as GitHub/Jira/Linear when available, then create durable records and a repository profile in your memory repo.

## Step 8: Use The Loop

For every meaningful task:

1. Search first.
2. Plan from prior evidence.
3. Do the work.
4. Capture outcome, decisions, verification, risks, and follow-ups.
5. Commit the memory update.

If the optional live-work module is enabled:

1. Check `tasks/INDEX.md` or `braingent task-list --count` before starting.
2. Create or claim a `BGT-NNNN` task when coordination matters.
3. Append activity during the work.
4. On completion, create or link the durable record with `agent_task: BGT-NNNN`.
5. Regenerate indexes and archive closed tasks when appropriate.

After setup, ask what the user wants to do next:

- Index a codebase with `Index this repo to braingent`.
- Build a plan for a feature, bug fix, or cleanup.
- Capture a task or decision that already happened.
- Tune preferences, workflows, or capture depth.

## Step 9: Use Token-Efficient Access

As the memory repo grows, teach agents to retrieve in layers instead of reading
everything up front:

```text
Search -> inspect compact results -> read summaries -> open full records only when evidence requires it
```

Use `TOKEN-EFFICIENT-ACCESS.md` as the setup guide. You can copy it into your
memory repo as-is, or fold its rules into `WORKFLOW.md`, `AGENTS.md`,
`CLAUDE.md`, and `CHATGPT_PROJECT_BRIEF.md`.

Start with simple tools:

- `rg` for keyword search;
- generated Markdown indexes for record lists and follow-ups;
- short summaries in durable records;
- explicit full-record reads only when exact evidence matters.

Later, you can add compact JSON indexes, SQLite search, MCP tools, embeddings,
or dashboards. Those tools should implement the same retrieval ladder, not
replace it.

## Step 10: Use The Helper CLI

This manifesto intentionally keeps Markdown as the source of truth. The helper
CLI currently covers:

- validating frontmatter
- generating indexes
- building a local search database
- importing Git history
- summarizing PRs or tickets
- generating traceable QA plans from tickets, memory, and Gather Step evidence
- managing live task files
- serving a read-only local dashboard

The copyable dashboard sample lives at `examples/task-dashboard/`.

For the helper surface, keep the scope intentionally small and make every
mutation visible in Git. The helpers should never become the source of truth;
they should create, validate, search, index, and summarize the Markdown repo.

| Command | Scope |
| --- | --- |
| `braingent doctor` | Check required files, stale placeholders, malformed frontmatter, private path leaks, generated-index drift, and local runtime/tooling gaps. |
| `braingent validate` | Validate record frontmatter and taxonomy values. |
| `braingent reindex` | Rebuild generated indexes and the local derived cache from Markdown records. |
| `braingent find` / `braingent recall` | Search frontmatter and build focused context packs. |
| `braingent init` | Copy the packaged starter template into a new memory repo and rebuild indexes. |
| `braingent update` | Report or apply conservative starter template updates. |
| `braingent qa generate` | Generate strict, reviewable QA plans from tickets, Braingent memory, and Gather Step `qa-evidence`. |
| `braingent mcp serve` | Serve read-only MCP tools for token-efficient agent retrieval. |

`braingent init` is a bootstrap, not a hidden migration:

1. Resolve the target directory and refuse to overwrite non-Braingent repos
   unless the user passes an explicit force flag.
2. Copy the packaged starter template, preserving file modes and leaving generated indexes
   reproducible from Markdown.
3. Write the template manifest used by future updates.
4. Run reindex after copy.
5. Print a concise handoff: files created, optional modules included, first
   commit command, and the next suggested workflow.

`braingent update` is conservative:

1. Read the installed template/version marker and the current packaged template
   manifest.
2. Build a three-way comparison between old template, new template, and the
   user's current files.
3. Auto-apply only files that are unchanged locally or have conflict-free
   mechanical updates.
4. Write conflicts to a review report with exact file paths and reasons.
5. Re-run `braingent doctor`, `braingent validate`, and
   `braingent reindex --check` after any accepted change.

Avoid putting product state in the CLI. The CLI is the moving truck, not the
house: it can copy, validate, and upgrade files, but Markdown remains the source
of truth.

For setup tooling, prefer:

- no required server;
- no required database;
- no hosted account;
- repo-local caches and generated files;
- explicit diffs before overwriting user-edited files;
- CI-friendly `validate`, `reindex --check`, `doctor`, lint, and typecheck
  commands.

Automation should support the memory model, not define it.
