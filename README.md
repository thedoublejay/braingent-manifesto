# Braingent Manifesto

Created by JJ Adonis.

Braingent is a Markdown-first memory system for software engineers who work with AI agents. It gives Claude, Codex, ChatGPT, and future tools one durable place to read before planning, one consistent structure for capturing work, and one searchable history of decisions, tasks, reviews, lessons, projects, tools, and repositories.

This repository is not a private memory dump. It is a public, open source setup guide and starter kit. Copy the Markdown files into a new repo and personalize them. No database, server, or install required.

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

### Custom Commands (Optional)

Wire your trigger phrases as slash commands in Claude Projects, Codex, or ChatGPT:

- `/save` → prefixes your message with `"dump this to braingent"`
- `/done` → appends `"task done"`
- `/capture` → explicit capture request

The `BOOTSTRAP-PROMPT.md` has ready-to-paste setup prompts for each tool.

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

## Quick Start

1. **Create a new Git repository** for your memory.
2. **Copy `starter-pack/`** contents into it.
3. **Replace placeholders:** `<your-name>`, `<organization-key>`, `<repo-key>`, `<timezone>`.
4. **Paste `BOOTSTRAP-PROMPT.md`** into Claude, Codex, or ChatGPT. Ask it to finish personalizing the repo.
5. **Add your first task record** and commit.

No database. No server. No install. Just Git and Markdown.

Optional tools to add later: ripgrep, jq, yq, SQLite. Day one, plain Markdown is enough.

---

## What This Repo Contains

| File or directory | Purpose |
| --- | --- |
| `MANIFESTO.md` | Philosophy and core principles. |
| `SETUP.md` | Step-by-step setup for your own memory repo. |
| `STRUCTURE.md` | Recommended directory structure and naming. |
| `AGENT-INTEGRATION.md` | How to connect to Claude, Codex, and ChatGPT. |
| `WORKFLOW.md` | Detailed day-to-day usage loop. |
| `BOOTSTRAP-PROMPT.md` | Copyable prompts to paste into your AI tool. |
| `PRIVACY-AND-SAFETY.md` | What must never be captured and how to redact. |
| `FAQ.md` | Practical questions answered. |
| `starter-pack/` | Markdown files to copy into your new memory repo. |

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
- Braingent is not a project management system.
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
