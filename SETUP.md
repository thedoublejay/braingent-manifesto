# Setup Guide

This guide creates a Braingent-style memory repo using only Markdown files.

## Prerequisites

Required:

- A text editor.
- Git, if you want version history.
- One AI tool, such as Claude, Codex, or ChatGPT.

Optional but useful:

- `rg` or another fast search tool.
- `jq` and `yq` for structured JSON/YAML inspection.
- SQLite if you later build generated indexes.
- GitHub CLI if you later want to index merged PRs.
- Bun and Playwright if you later build or run the optional task dashboard.

## Step 1: Create A Repo

Create a new repository named `braingent` or any name you prefer. The public guide is named `braingent-manifesto`; your personal memory repo can have its own name.

```bash
mkdir <your-memory-repo>
cd <your-memory-repo>
git init
```

Do not hardcode private paths into the files. Use placeholders or relative paths.

## Step 2: Copy The Starter Pack

Copy everything under `starter-pack/` into your new repo.

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

Delete or archive the cloned `braingent-manifesto` setup repo after this first commit unless you plan to contribute to the starter kit. Keeping both repos active can confuse future `AGENTS.md` / `CLAUDE.md` searches because agents may read the public starter kit instead of your real memory repo.

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

1. Check `tasks/INDEX.md` or `scripts/task-list.sh --count` before starting.
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

## Step 10: Add Automation Later

This manifesto intentionally starts with Markdown only.

Later, you can add scripts for:

- creating dated record files
- validating frontmatter
- generating indexes
- building a local search database
- importing Git history
- summarizing PRs or tickets
- managing live task files
- serving a read-only local dashboard

The copyable dashboard sample lives at `examples/task-dashboard/`.

Automation should support the memory model, not define it.
