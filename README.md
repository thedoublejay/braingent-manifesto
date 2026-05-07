<p align="center">
  <img src="website/public/favicon/favicon-96x96.png" alt="Braingent logo" width="96" />
</p>

<h1 align="center">Braingent</h1>

<p align="center">
  A Markdown-first engineering memory repo for humans and AI coding agents.
</p>

<p align="center">
  Search before planning. Capture after meaningful work. Keep memory in Git.
</p>

<p align="center">
  <a href="https://braingent.dev"><strong>Website</strong></a>
  ·
  <a href="#quick-start"><strong>Quick Start</strong></a>
  ·
  <a href="#what-braingent-gives-you"><strong>Features</strong></a>
  ·
  <a href="#contributing"><strong>Contributing</strong></a>
</p>

<p align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT license" />
  </a>
  <a href="https://braingent.dev">
    <img src="https://img.shields.io/badge/docs-braingent.dev-blue.svg" alt="Documentation" />
  </a>
  <img src="https://img.shields.io/badge/storage-Markdown%20%2B%20Git-222222.svg" alt="Markdown and Git" />
  <img src="https://img.shields.io/badge/server-not%20required-lightgrey.svg" alt="No server required" />
</p>

Braingent is a Markdown-first memory system for software engineers who work
with AI agents. It gives Claude, Codex, ChatGPT, Gemini CLI, and future tools
one durable place to read before planning, one consistent structure for
capturing work, and one searchable history of tasks, reviews, decisions,
learnings, tools, repositories, and projects.

This repository is not a private memory dump. It is a public, open source
starter kit. Copy the Markdown files into your own repo, personalize them, and
let your agents use that repo as shared engineering memory. No database,
server, or required install is needed on day one.

Braingent stays simple: Markdown is the source of truth. Optional scripts,
generated indexes, local search databases, live task files, and dashboards are
helpers built around the Markdown, not replacements for it.

## Why Braingent

Use Braingent when agent sessions keep losing the same context:

- which files, repos, and decisions matter before planning;
- what was already tried in a ticket, review, or incident;
- which conventions should guide future edits;
- what work should be captured after the PR, fix, or decision is done.

It is deliberately plain: clone it, copy the starter pack, personalize the
Markdown, and commit your memory repo like any other project.

## Requirements

Day one only requires Git and a text editor. The starter pack is plain Markdown.

Optional tools unlock more automation:

| Tool | Used for |
| --- | --- |
| `gh` | Importing GitHub PR and issue context when authenticated. |
| `rg` | Fast search across records and preferences. |
| `jq` / SQLite | Querying generated indexes and local search caches. |
| Python / `uv` | Validation, indexing, and helper scripts. |
| Bun | Running the optional dashboard example and website locally. |

---

## Quick Start

1. **Copy the starter pack into a new memory repo.**

```bash
git clone https://github.com/thedoublejay/braingent-manifesto
mkdir my-braingent
cd my-braingent
git init
cp -r ../braingent-manifesto/starter-pack/. .
```

2. **Give the setup prompt to your agent.**

Paste `BOOTSTRAP-PROMPT.md` into Claude, Codex, ChatGPT, or Gemini CLI as the
first message in a new session. The agent will read `INITIALIZE.md` and walk
you through the setup one question at a time.

3. **Commit your initialized memory repo.**

After the agent replaces placeholders, creates your first folders, and writes
the first setup record:

```bash
git add .
git commit -m "Initialize Braingent memory repo"
```

After that first commit, delete or archive the cloned `braingent-manifesto`
setup repo unless you plan to contribute to it. Keeping both repos active can
confuse agent searches because they may read the public starter kit instead of
your real memory repo.

Detailed setup lives in `INITIALIZE.md` and `SETUP.md`.

### Setup Paths

Braingent should keep one manual path and four optional CLI-assisted paths:

| Path | Command or artifact | Purpose |
| --- | --- | --- |
| Manual path | `starter-pack/` + `BOOTSTRAP-PROMPT.md` | Zero-install setup that proves Braingent is still just Markdown. |
| Fast path | future `braingent init` | Optional CLI setup that copies files, replaces placeholders, and asks setup questions once. |
| Health path | future `braingent doctor` | Optional checks for missing files, stale placeholders, invalid frontmatter, path leaks, and stale generated indexes. |
| Upgrade path | future `braingent update` | Optional starter-pack upgrade helper that shows what changed before editing. |
| QA path | future `braingent qa-generate` | Optional QA planning helper that turns tickets, Braingent memory, and Gather Step evidence into traceable Markdown, Xray JSON, TestRail CSV, or Gherkin. |

The product line is: **Braingent is Markdown-first. Automation only removes
setup friction.**

---

## What Braingent Gives You

| Surface | What it does | Source of truth |
| --- | --- | --- |
| Agent entrypoints | Tell each AI tool what to read, how to search, when to capture, and what never to store. | `AGENTS.md`, `CLAUDE.md`, `CHATGPT_PROJECT_BRIEF.md` |
| Durable memory | Stores completed work, decisions, reviews, learnings, repo profiles, tool notes, and summaries. | Markdown records with YAML frontmatter |
| Preferences | Keeps standing rules outside individual chats: naming, capture policy, privacy, planning, review, and workflow defaults. | `preferences/` |
| Workflows | Gives agents repeatable procedures for repo indexing, cleanup, retrieval, and capture. | `workflows/` |
| Generated indexes | Summarize records, follow-ups, stale candidates, and current memory health. | Rebuilt from Markdown |
| Token-efficient access | Keeps agent sessions small by searching first, reading summaries by default, and opening full records only when needed. | `TOKEN-EFFICIENT-ACCESS.md` |
| Live tasks | Coordinates active work with `BGT-NNNN` task files, status, owners, dependencies, and append-only activity. | `tasks/active/*.md` |
| Local dashboard | Shows the live task queue, filters, task detail, dependency graph, activity, raw Markdown, and guide. | Read-only over task Markdown |

You can start with only durable memory and preferences. Add live tasks,
generated indexes, helper scripts, and the dashboard when they solve real
coordination or search problems.

ELI5: the durable records are your engineering notebook. The live task files
are the shared whiteboard for work in progress. The dashboard is a window onto
the whiteboard, not a second notebook.

---

## The Daily Loop

Every useful Braingent session follows the same loop:

1. **Search before planning.** The agent reads the thin entrypoints and searches
   for related tasks, prior decisions, repo profiles, and known risks.
2. **Do the work.** You and the agent work as usual. The agent keeps track of
   decisions, commands, errors, links, versions, and tradeoffs.
3. **Capture the outcome.** At the end, the agent writes a durable record and
   commits it.

The capture habit is the point. A useful memory repo is built from many small,
evidence-backed records, not one giant document.

Common trigger phrases:

| Phrase | What it does |
| --- | --- |
| `"capture this"` | Save what just happened. |
| `"task done"` or `"done thanks"` | End the task and capture it. |
| `"dump this to braingent"` | Explicitly save the current context. |
| `"write to braingent"` | Same idea, different wording. |

Customize trigger phrases in `preferences/capture-policy.md`.

---

## Index Your Repos

After setup, point Braingent at your real codebases:

```text
Index this repo to braingent
```

Run that from inside the codebase you want indexed. If you are somewhere else,
name the target explicitly:

```text
Index <specific-repo> to braingent
```

The agent follows `workflows/index-repo.md` and captures what it can reach:

| Source | What it captures |
| --- | --- |
| Local docs | README files, architecture notes, planning files, agent instructions, and untracked notes |
| Git history | Your authored commits, branch names, merge history, and issue or ticket references already present in commit messages |
| GitHub | Issues and pull requests when `gh` is authenticated |
| External trackers | Jira, Linear, or other systems only when you connect them |

The result is a set of durable task, decision, review, learning, and repository
profile records. Next time you start work in that codebase, the agent can read
the repo's history before writing code.

You do not need every source on day one. Git history and local docs are enough
to start; connected services can be added later.

---

## Live Task Coordination

Durable records describe what happened. Live tasks coordinate what is happening
now.

Use `tasks/` when work spans multiple agents, sessions, or reviews and needs:

- a visible queue;
- status, owner, priority, and dependencies;
- append-only handoff activity;
- a clear closeout path into durable memory.

Live task files use `BGT-NNNN` IDs and `record_kind: agent-task`. When a live
task is completed, important outcomes should still be promoted into normal
durable records with `agent_task: BGT-NNNN` linking back to the live task.

The full task workflow is documented in `AGENT-TASK-COORDINATION.md`,
`starter-pack/tasks/README.md`, and `starter-pack/preferences/agent-task-protocol.md`.

---

## Local Dashboard

The dashboard sample in `examples/task-dashboard/` is a copyable Bun + React
app for inspecting active task files. It includes:

- dark-mode task queue;
- status, priority, owner, and text filters;
- task detail, acceptance criteria, plan, closeout, raw Markdown, and activity;
- dependency graph;
- fixed-height paginated recent activity;
- in-app guide page;
- synthetic sample data for safe public use;
- Playwright e2e coverage.

The dashboard is read-only over Markdown task files. It does not own a separate
schema and does not replace `tasks/active/*.md`.

To try the sample:

```bash
cd examples/task-dashboard
bun install
bun run dev
```

To point it at a real memory repo:

```bash
BRAINGENT_MEMORY_ROOT=/path/to/your-memory-repo bun run dev
```

---

## What This Repo Contains

| File or directory | Purpose |
| --- | --- |
| `INITIALIZE.md` | Guided agent setup prompt. Start here after copying `starter-pack/`. |
| `SETUP.md` | Manual setup guide and optional tooling notes. |
| `MANIFESTO.md` | Philosophy and core principles. |
| `HOW-IT-WORKS.md` | Conceptual model for the memory layers. |
| `STRUCTURE.md` | Recommended directory layout and naming. |
| `WORKFLOW.md` | Day-to-day search, work, capture, and cleanup loop. |
| `AGENT-INTEGRATION.md` | How to connect Claude, Codex, ChatGPT, and Gemini CLI. |
| `TOKEN-EFFICIENT-ACCESS.md` | Retrieval-first guidance for reducing agent token usage without losing recall. |
| `AGENT-TASK-COORDINATION.md` | Optional Markdown-based live task coordination. |
| `PRIVACY-AND-SAFETY.md` | What must never be captured and how to review before publishing. |
| `PUBLISHING-CHECKLIST.md` | Public-release checklist for examples and docs. |
| `FAQ.md` | Practical questions and answers. |
| `starter-pack/` | Files to copy into a new memory repo. |
| `examples/task-dashboard/` | Copyable local dashboard sample with synthetic task data. |

---

## Recommended Memory Repo Shape

```text
your-memory-repo/
├── AGENTS.md
├── CLAUDE.md
├── CHATGPT_PROJECT_BRIEF.md
├── README.md
├── INDEX.md
├── CURRENT_STATE.md
├── preferences/
├── templates/
├── workflows/
├── tasks/                     # optional live task queue
├── dashboard/                 # optional local dashboard
├── orgs/
├── repositories/
├── topics/
├── tools/
├── people/
├── tickets/
├── inbox/
├── imports/
└── indexes/
```

The exact structure can be adapted, but keep the same principles:

- thin root entrypoints;
- stable preferences;
- durable records with YAML frontmatter;
- generated files that can be rebuilt;
- raw imports separated from curated summaries;
- secrets and sensitive personal data kept out.

---

## Optional Tooling

Braingent starts as plain Markdown. Add tools when they help:

| Tool | What it adds |
| --- | --- |
| `rg` | Fast full-text search. |
| `jq` / `yq` | Structured JSON/YAML inspection. |
| Shell scripts | Record creation, validation, reindexing, task helpers. |
| Optional setup CLI | Repeatable `init`, `doctor`, `print-prompts`, and `update` paths without replacing manual setup. |
| SQLite | Rebuildable local search cache for structured queries. |
| Compact indexes | Small generated projections for fast agent scanning before full record reads. |
| GitHub CLI | Import pull requests and issues when authenticated. |
| Bun + React | Local dashboard over active task Markdown. |

Automation should support the memory model, not define it. Markdown remains the
source of truth.

Recent implementation lessons from real Braingent usage:

- exact metadata queries should use generated indexes or SQLite instead of
  reparsing every Markdown record;
- token-efficient MCP/search helpers should return compact records first and
  hydrate full records only when evidence requires it;
- validation, reindex, and doctor checks should be repeatable from CI and local
  scripts;
- helper tooling should keep caches and writes repo-local where possible.

---

## Keeping Memory Healthy

Tell your agent:

```text
clean up braingent
```

The cleanup workflow checks frontmatter, generated indexes, unchecked
follow-ups, stale records, stale live tasks, raw imports, and drift in
entrypoint docs. It should report findings before making structural edits.

Suggested cadence:

| Cadence | What it covers |
| --- | --- |
| Daily | Validate frontmatter, check indexes, scan open follow-ups. |
| Weekly | Review active tasks, blocked work, stale profiles, and raw imports. |
| Monthly | Refresh synthesis pages and check cross-links. |
| Quarterly | Revisit taxonomy, templates, workflows, and agent entrypoints. |

---

## Design Goals

- Keep engineering memory portable across AI tools.
- Make agents search prior context before planning.
- Capture meaningful work before details disappear.
- Keep stable preferences separate from one-time records.
- Make search reliable through frontmatter and consistent naming.
- Preserve why decisions happened, not just what changed.
- Keep secrets, credentials, tokens, and sensitive personal data out.

## Anti-Goals

- Braingent is not a replacement for source control.
- Braingent is not a place to store secrets or credentials.
- Braingent is not a full chat transcript archive.
- Braingent is not a replacement for your team's project management system.
- Braingent is not tied to one AI vendor.
- Braingent does not require automation on day one.

---

## Make It Yours

Everything in the starter pack is a starting point. Change the preference files,
templates, trigger phrases, and workflows to match how you actually work.

The fixed principles are intentionally small:

- Search before planning.
- Capture after meaningful work.
- Keep secrets out.

Everything else is adjustable.

---

## Development

Most changes are Markdown-only. Keep examples public-safe and generic enough
for another user's setup.

For the website:

```bash
cd website
bun install --frozen-lockfile
bun run build
```

For starter-pack or documentation changes, review:

- `PRIVACY-AND-SAFETY.md`
- `PUBLISHING-CHECKLIST.md`
- `CONTRIBUTING.md`

---

## Security And Privacy

Do not put secrets, credentials, tokens, private keys, customer data, or
sensitive personal data in this repository or in examples. Use placeholders for
all private organizations, repositories, people, and tickets.

If you find an example that leaks private context, open a bug report or PR that
removes the data and explains the replacement pattern.

---

## Contributing

Suggestions, fixes, and improvements are welcome.

- **Bug or unclear docs?** [Open a bug report](https://github.com/thedoublejay/braingent-manifesto/issues/new?template=bug_report.md)
- **Have an idea?** [Open a suggestion](https://github.com/thedoublejay/braingent-manifesto/issues/new?template=suggestion.md)
- **Want to contribute directly?** Open a pull request. The PR template includes the privacy checklist.

The main contribution rule: no private data. Examples should use placeholders,
and changes should be generic enough to work for another user's setup. See
`CONTRIBUTING.md` for details.

---

## License

MIT — see `LICENSE`.

---

Created by [JJ Adonis](https://josejai.me/).
