# Braingent Manifesto

Braingent is a Markdown-first memory system for software engineers who work with AI agents. It gives Claude, Codex, ChatGPT, and future tools one durable place to read before planning, one consistent structure for capturing work, and one searchable history of decisions, tasks, reviews, lessons, projects, tools, and repositories.

This repository is not a private memory dump. It is a public, open source setup guide and starter kit. Copy the Markdown files into a new repo and personalize them. No database, server, or install required.

Braingent v3 keeps the core Markdown memory model and adds an optional live-work layer for active agent tasks, generated health indexes, and a read-only local dashboard contract. The source of truth is still Markdown; automation only helps agents find and maintain it.

---

## Get Started in 3 Steps

**1. Clone this repo and copy the starter pack into a new empty repo.**

```bash
git clone https://github.com/thedoublejay/braingent-manifesto
mkdir my-braingent && cd my-braingent && git init
cp -r ../braingent-manifesto/starter-pack/. .
```

**2. Feed it to your agent.**

Paste the contents of `BOOTSTRAP-PROMPT.md` into Claude, Codex, ChatGPT, or Gemini CLI as the first message in a new session (or as your project/system instructions).

**3. Let it initialize.**

The agent will read `INITIALIZE.md` and walk you through replacing every placeholder — your name, timezone, organizations, repos, and preferences — step by step. Answer the questions. It commits when done.

That's it. Your memory repo is live.

After the first commit, delete or archive the cloned `braingent-manifesto` setup repo if you do not need it anymore. This keeps future `AGENTS.md` / `CLAUDE.md` searches from accidentally reading the public starter kit instead of your real memory repo.

> Full manual setup: see `SETUP.md`. Interactive initialization script: see `INITIALIZE.md`.

---

## The Daily Loop

Every use of your memory follows the same rhythm:

**1. Before work:** Agent reads memory entrypoints and searches for prior context on the task.

**2. During work:** Agent notices commands, decisions, errors, versions, PR links, tradeoffs.

**3. After work:** Agent writes a durable record. This is the **CAPTURE** step — the core habit that makes everything else possible.

---

## CAPTURE: The One Daily Habit That Matters

**You tell your AI agent to save its work using a trigger phrase.** The agent writes a short record to your memory repo. No manual filing. No overhead. Just "I'm done" → memory updated.

### Trigger Phrases (Customize These)

Type any of these into your chat:

| Phrase | What it does |
| --- | --- |
| `"capture this"` | Save whatever just happened |
| `"task done"` or `"done thanks"` | End of task, save automatically |
| `"dump this to braingent"` | Explicit save request |
| `"write to braingent"` | Same as above |

The agent reads your capture policy and knows which template to use and where to file the record. Add your own phrases in `preferences/capture-policy.md`.

### Two Capture Modes

**Quick** — uses `templates/task-record-minimal.md`
- Task name, outcome, one key decision, done
- Perfect for small fixes and incremental changes

**Full** — uses `templates/task-record.md`
- Full context, decisions, errors, follow-ups, links
- For complex work, architecture changes, debugging sessions

### Command Phrases

Use plain chat phrases. These work anywhere the agent can read your memory repo:

- `"capture this"`
- `"task done"` or `"done thanks"`
- `"dump this to braingent"`
- `"write to braingent"`

Tool-specific shortcuts can wrap these phrases later, but they are not part of this starter kit.

---

## Day-to-Day in Practice

### Before You Start

Agent reads the root instructions (`CLAUDE.md`, `AGENTS.md`), then searches memory for related tasks, prior decisions, and known risks. Takes seconds. Prevents duplicated work and surfaces old decisions that still apply.

### Do the Work

You and the agent work as usual. The agent notices edge cases, errors, version bumps, and tradeoffs. No extra friction.

### Task Done → Capture

Say: `"capture this"` or any trigger phrase from your policy.

Agent writes to memory automatically:

- What was accomplished
- Why decisions were made
- What didn't work and why
- Links to PRs, issues, and commits
- Follow-up items and risks

Record is committed to Git. Done.

Next time the same problem appears, your agent reads the record first.

---

## Then: Index Your Repos

Once Braingent is initialized, the next step is pointing it at your actual codebases. Tell your agent:

> **"Index this repo to braingent"**

Run that from inside the codebase you want indexed. If you are not in that repo, name the target explicitly:

> **"Index `<specific-repo>` to braingent"**

The agent runs the `workflows/index-repo.md` procedure and pulls in context from every source it can reach:

| Source | What it captures |
| --- | --- |
| Local docs | `README.md`, architecture docs, planning files, `CLAUDE.md`, `AGENTS.md`, untracked notes |
| Git history | Your authored commits, branch names, merge history, ticket IDs in commit messages |
| GitHub Issues | Open and closed issues assigned to you or linked to your work |
| Pull Requests | Merged PRs — decisions made, what changed, review findings |
| **Jira** | Tickets, epics, sprint history — if your org uses Jira and you have access |
| **Linear** | Issues and cycles — if your team uses Linear |

The result is a set of durable records in your memory repo: task records for completed work, decision records for architectural choices, a repository profile with the stack and common commands, and learning records for anything worth remembering.

**You do not need all sources on day one.** Git history and local docs are always available. GitHub, Jira, and Linear are optional — the agent notes what it could not reach and skips it cleanly.

### What indexing looks like

```
You:   "index this repo to braingent"
Agent: Found 34 merged PRs, 12 months of commits, 3 local planning docs.
       Estimated 8–12 records. Proceed?
You:   yes
Agent: [creates records, repo profile, and import summary]
       Done. 9 records written. Committed.
```

After indexing, your agent knows the repo's history before you write a single line of new code.

### Supported trigger phrases

- `"index this repo to braingent"`
- `"index <specific-repo> to braingent"`
- `"backfill this repo to braingent"`
- `"scan this repo into braingent"`
- `"create a repo profile for this"`

---

## Quick Start

1. **Create a new Git repository** for your memory.
2. **Copy `starter-pack/`** contents into it.
3. **Open `INITIALIZE.md`** and paste the prompt inside into your AI agent.
4. **Answer the questions.** The agent replaces all placeholders and sets up your config.
5. **Commit.** The agent tells you exactly what to run.

No database. No server. No install. Just Git and Markdown.

Optional tools to add later: ripgrep, jq, yq, SQLite. Day one, plain Markdown is enough.

---

## What This Repo Contains

| File or directory | Purpose |
| --- | --- |
| `INITIALIZE.md` | **Start here.** Interactive agent-guided setup — paste into your AI tool and answer questions. |
| `MANIFESTO.md` | Philosophy and core principles. |
| `SETUP.md` | Full manual setup guide. |
| `STRUCTURE.md` | Recommended directory structure and naming. |
| `AGENT-INTEGRATION.md` | How to connect to Claude, Codex, ChatGPT, and Gemini CLI. |
| `AGENT-TASK-COORDINATION.md` | Optional v3 module for Markdown-based multi-agent task coordination. |
| `WORKFLOW.md` | Detailed day-to-day usage loop. |
| `BOOTSTRAP-PROMPT.md` | Short copyable prompt to give your agent context about this repo. |
| `PRIVACY-AND-SAFETY.md` | What must never be captured and how to redact. |
| `FAQ.md` | Practical questions answered. |
| `starter-pack/` | Markdown files to copy into your new memory repo. |
| `examples/task-dashboard/` | Copyable Bun/React dashboard sample with synthetic task data. |

---

## How It Works

Braingent turns engineering memory into a searchable, Git-backed knowledge base:

- **Root instructions** tell agents how to use the memory.
- **Preference files** define durable rules: naming, capture policy, privacy, search.
- **YAML frontmatter** makes records machine-searchable.
- **Markdown bodies** keep records readable by humans.
- **Templates** make capture consistent and fast.
- **Index files** give humans and agents a map of what's recorded.
- **Workflows** define repeatable procedures like onboarding a new repo.
- **Raw imports** stay separate from curated summaries.
- **Optional live task files** coordinate active work without replacing durable records.
- **Optional dashboard views** make the live task queue easier to inspect while staying read-only over Markdown.

---

## Braingent V3 Feature Map

Braingent v3 has five practical surfaces:

| Surface | What it does | Source of truth |
| --- | --- | --- |
| Root entrypoints | Keep agent instructions thin and current. | `AGENTS.md`, `CLAUDE.md`, `CHATGPT_PROJECT_BRIEF.md`, `README.md`, `INDEX.md`, `CURRENT_STATE.md` |
| Durable memory | Stores completed work, decisions, reviews, learnings, tool versions, profiles, and ticket stubs. | Markdown records with YAML frontmatter |
| Retrieval indexes | Summarize records, follow-ups, stale candidates, and current memory health. | Generated from Markdown |
| Live work | Coordinates active agent tasks with `BGT-NNNN` files, status, owners, dependencies, and append-only activity. | `tasks/active/*.md` |
| Local dashboard | Shows the live task queue, filters, detail, graph, activity, raw Markdown, and guide. | Read-only over task Markdown and generated indexes |

The live-work layer is optional. A small personal memory repo can start with only durable records and add `tasks/` later when multiple agents or long-running work need coordination.

ELI5: the durable memory is your engineering notebook. The live task layer is the whiteboard beside it. The dashboard is a window onto the whiteboard, not a second notebook.

The public dashboard sample lives in `examples/task-dashboard/`. It uses
synthetic `BGT-NNNN` data by default and can be copied into `dashboard/tasks/`
inside a real memory repo.

---

## Architecture

Braingent is a layered folder structure. No magic — just Markdown files organized so agents can navigate them predictably.

```text
your-memory-repo/
├── CLAUDE.md                  ← Claude reads this first
├── AGENTS.md                  ← Codex/other agents read this first
├── CHATGPT_PROJECT_BRIEF.md   ← Paste into ChatGPT project instructions
├── README.md                  ← Human overview
├── INDEX.md                   ← Hand-curated map of important records
├── CURRENT_STATE.md           ← Active context: what's in flight right now
│
├── preferences/               ← Standing rules agents apply before every task
│   ├── agent-workflow.md      ← The search → plan → work → capture loop
│   ├── capture-policy.md      ← What to save and when (trigger phrases live here)
│   ├── naming.md              ← File and key naming conventions
│   ├── taxonomy.md            ← Allowed record kinds, statuses, prefixes
│   ├── note-taking-and-ai-memory.md ← Memory layers, capture funnel, anti-drift rules
│   ├── engineering-defaults.md← Tech choices: deps, libs, CI, architecture
│   ├── planning.md            ← How to frame tasks (GOAL/ANALYSIS/APPROACH/RISKS)
│   ├── code-review.md         ← Review focus and output format
│   ├── pr-and-commit.md       ← Commit and PR hygiene
│   ├── content-style.md       ← How records should be written
│   ├── search-recipes.md      ← How to search the memory
│   └── privacy-and-safety.md  ← What must never be captured
│
├── templates/                 ← Copyable record starters
│   ├── task-record.md         ← Full task capture
│   ├── task-record-minimal.md ← Quick end-of-task capture
│   ├── decision-record.md
│   ├── learning-record.md
│   ├── code-review-record.md
│   ├── repository-profile.md
│   ├── tool-version-record.md
│   ├── ticket-stub.md
│   └── ...
│
├── workflows/                 ← Step-by-step procedures triggered by phrase
│   ├── index-repo.md          ← "index this repo to braingent"
│   └── cleanup-braingent.md   ← "clean up braingent" (daily/weekly/monthly/quarterly)
│
├── tasks/                     ← Optional live agent-task queue
│   ├── CLAUDE.md              ← Scoped rules for task files
│   ├── INDEX.md               ← Generated task index
│   ├── active/                ← Mutable BGT-NNNN task files
│   └── archive/               ← Closed task files by month
│
├── dashboard/
│   └── tasks/                 ← Optional read-only local task dashboard
│
├── orgs/                      ← One folder per org, client, or team
│   └── org--<slug>/
│       └── projects/
│           └── project--<slug>/
│               └── records/   ← Task, decision, review records for this project
│
├── repositories/              ← One profile per codebase you work in
│   └── repo--github--<owner>--<name>/
│
├── topics/                    ← Reusable learnings grouped by technology or theme
├── tools/                     ← Framework, runtime, and model version records
├── people/                    ← Optional: collaboration context
├── tickets/                   ← Cross-cutting ticket stubs
├── inbox/                     ← Temp drop zone — empty regularly
├── imports/
│   ├── raw/                   ← Unprocessed exports (chat dumps, PR lists)
│   └── summaries/             ← Curated summaries of raw imports
└── indexes/                   ← Generated or hand-maintained indexes
```

### Optional Automation Layer

Braingent starts as plain Markdown. You can add tooling incrementally without changing the structure:

| Tool | What it adds |
| --- | --- |
| `ripgrep` | Fast full-text search across all records |
| `jq` / `yq` | Parse and query YAML frontmatter from the terminal |
| Shell scripts | `new-record.sh` to create dated files, `validate.sh` for frontmatter checks |
| **SQLite** | Local search cache — generated from frontmatter by a `reindex.sh` script. Lets you query records by status, date, repo, topic, or record kind without grepping files. Useful once you have hundreds of records. |
| GitHub CLI | Import merged PRs as records automatically |
| Task helper scripts | Create, claim, comment on, count, close, archive, and list `BGT-NNNN` live task files |
| Bun + React dashboard | Optional local UI for inspecting `tasks/active/` without changing the Markdown source of truth. See `examples/task-dashboard/`. |

**SQLite specifically** — it's an optional read cache, not a source of truth. The Markdown files are always the source. SQLite is regenerated from them on demand. You add it when `rg` queries get slow or you want structured queries like `SELECT * FROM records WHERE record_kind = 'decision' AND status = 'active'`.

---

## Keeping Memory Healthy

Braingent compounds only if records stay trustworthy. Tell your agent to run
maintenance using a trigger phrase:

> **"clean up braingent"**

The agent runs the `workflows/cleanup-braingent.md` procedure and reports
findings before making any changes.

| Cadence | Time | What it covers |
| --- | --- | --- |
| **Daily** | 5-10 min | Validate frontmatter, check indexes, scan for unchecked follow-ups and TODOs |
| **Weekly** | 30-45 min | Review active tasks, blocked/stale work, stale profiles, raw imports, and backlink gaps |
| **Monthly** | 60-90 min | Create or refresh cited synthesis pages, check for drift |
| **Quarterly** | 2-3 hrs | Review taxonomy, templates, agent entrypoints, and workflow relevance |

The cleanup workflow is report-first: it always shows findings before editing
anything. You approve structural changes before they happen.

---

## Design Goals

- Keep knowledge portable across AI tools — no vendor lock-in.
- Keep instructions small enough that agents read them at task start.
- Separate stable preferences from one-time records.
- Make search reliable through frontmatter and consistent naming.
- Preserve *why* a decision happened, not just *what* changed.
- Capture enough evidence that future agents don't need old chat transcripts.
- Keep secrets, credentials, tokens, and sensitive personal data out of memory.

## Anti-Goals

- Braingent is not a replacement for source control.
- Braingent is not a place to store secrets or credentials.
- Braingent is not a full chat transcript archive.
- Braingent is not a replacement for your team's project management system.
- Braingent is not tied to one AI vendor.
- Braingent does not require automation on day one.

---

## Make It Yours

Everything in the starter pack is a starting point, not a contract.

**Change the preference files** to match how you actually work. Rename sections. Drop things you won't use. Add what's missing. The structure is a suggestion — your real usage will tell you what to keep.

The only fixed principles (from `MANIFESTO.md`):

- Search before planning.
- Capture after meaningful work.
- Keep secrets out.

Everything else is adjustable — trigger phrases, templates, directory layout, naming conventions.

---

## First Commit

After copying the starter pack and personalizing the placeholders:

```bash
git add .
git commit -m "Initialize Braingent memory repo"
```

Then use it for real work. The value compounds from the loop: **search → work → capture → better context next time.**

---

## Contributing

Suggestions, fixes, and improvements are welcome.

- **Bug or unclear docs?** [Open a bug report](../../issues/new?template=bug_report.md)
- **Have an idea?** [Open a suggestion](../../issues/new?template=suggestion.md)
- **Want to contribute directly?** Open a pull request — the PR template will walk you through the checklist.

The main things to keep in mind for contributions: no private data, examples use placeholders, and changes should be generic enough to work for any user's setup. See `CONTRIBUTING.md` for details.

---

## License

MIT — see `LICENSE`.

---

*Created by JJ Adonis.*
