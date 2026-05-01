# Initialize Your Braingent Memory Repo

This file is a guided initialization script for your AI agent. Paste this into Claude, Codex, or ChatGPT after copying the starter pack into your new repo, and the agent will walk you through setup interactively.

---

## How To Use This File

1. Copy `starter-pack/` into a new empty Git repo.
2. Open a new session with your AI agent.
3. Paste the prompt below as your first message.
4. Answer each question. The agent personalizes the files as you go.
5. At the end, commit.

---

## Initialization Prompt (Paste This)

> Copy everything below this line and paste it into your AI agent.

---

I have copied the Braingent starter pack into a new Git repository. I need you to initialize it by walking me through a series of short questions. After each answer, update the relevant files immediately before asking the next question. Do not ask multiple questions at once. Work through them one at a time.

Here is the initialization checklist. Work through it in order:

---

### Step 1: Identity

Ask me:

> What is your name or handle? (This will appear in record authors and the README.)

Replace `<your-name>` everywhere in the repo with my answer.

---

### Step 2: Timezone

Ask me:

> What is your timezone? (Examples: UTC, America/New_York, Asia/Singapore, Europe/London)

Replace `<timezone>` everywhere in the repo with my answer.

---

### Step 3: Memory Repo Name

Ask me:

> What do you want to call this memory repo? (Default: `braingent`. This is the name used in trigger phrases like "dump this to braingent".)

Update the trigger phrases in `preferences/capture-policy.md` and the agent entrypoints (`CLAUDE.md`, `AGENTS.md`, `CHATGPT_PROJECT_BRIEF.md`) to use this name.

---

### Step 4: AI Tools

Ask me:

> Which AI tools will read this memory repo? Select all that apply: Claude, Codex, ChatGPT, Gemini, other.

Based on the answer:
- If Claude: confirm `CLAUDE.md` is present and complete.
- If Codex: confirm `AGENTS.md` is present and complete.
- If ChatGPT: confirm `CHATGPT_PROJECT_BRIEF.md` is present and remind me to paste it into my ChatGPT project instructions.
- If Gemini CLI: create a `GEMINI.md` at the repo root with the same read order and workflow triggers as `CLAUDE.md`. Remind me to place it where Gemini CLI will pick it up. See `AGENT-INTEGRATION.md` for details.
- If other: note which tools in `CURRENT_STATE.md` under "AI Tools In Use".

---

### Step 5: Organizations

Ask me:

> Do you have any organizations, clients, or teams to track? Give me their names or slugs, separated by commas. (Example: personal, acme-corp, freelance. Press Enter to skip.)

For each answer:
- Create a folder `orgs/org--<slug>/` with a `README.md` inside.
- Create a subfolder `orgs/org--<slug>/projects/` with a placeholder `README.md`.
- Replace `org--example` in any example files with the first real org key.

---

### Step 6: Repositories

Ask me:

> Which code repositories do you work in most? Give me up to 5 as `owner/repo-name` pairs. (Example: myname/api-service, myname/web-frontend. Press Enter to skip.)

For each answer:
- Create `repositories/repo--github--<owner>--<repo-name>/README.md` from `templates/repository-profile.md`.
- Fill in the repo name and URL. Leave stack, conventions, and commands as placeholders for me to fill in later.

---

### Step 7: Capture Preferences

Ask me:

> How do you prefer to capture work? Choose one:
> 1. Automatic — capture at end of every task without asking
> 2. Prompted — agent asks "capture this?" after each task
> 3. Manual — I say the trigger phrase when I want to capture

Update `preferences/capture-policy.md` to reflect this preference.

---

### Step 8: Default Capture Depth

Ask me:

> What should the default capture depth be?
> 1. Minimal — just the task name, outcome, and one key decision
> 2. Full — full context, decisions, errors, follow-ups, and links

Update `preferences/capture-policy.md` to set this as the default template.

---

### Step 9: Privacy Level

Ask me:

> Is this memory repo private (personal use only) or will it be shared with a team?
> 1. Private — I can include internal project names, ticket IDs, and org details
> 2. Shared/public — keep everything generic and anonymizable

Update `preferences/privacy-and-safety.md` with a note reflecting the answer.

---

### Step 10: First Topic

Ask me:

> What is the main technology or theme you want to track? (Example: backend, typescript, rust, ai-agents, mobile. This becomes your first topic record.)

Create `topics/topic--<slug>/README.md` with a short description of the topic.

---

### Step 11: CURRENT_STATE.md

Update `CURRENT_STATE.md` with:
- Today's date as "Last reviewed"
- The timezone from Step 2
- A summary of what was just initialized
- Active initiatives: personalize remaining placeholders, add first task record

---

### Step 12: First Task Record

Tell me:

> I am going to create your first task record documenting this initialization. This gives future agents evidence that the repo was set up intentionally.

Create `<today's-date>--task--initialize-memory-repo.md` in the first org/project folder (or at root if no org was given) using `templates/task-record-minimal.md`. Fill it in with what was just done.

---

### Step 13: Optional Live Tasks

Ask me:

> Do you want to keep the optional live task module? Use it if multiple agents or long-running work need a shared `BGT-NNNN` queue. Skip it if you only want durable memory records for now.

If I keep it, leave `tasks/`, `templates/agent-task.md`,
`preferences/agent-task-protocol.md`, and `dashboard/tasks/` documentation in
place. Explain that live tasks use `record_kind: agent-task`, can be viewed by
optional helper scripts or the dashboard, and completed work should still be
promoted into durable records with `agent_task: BGT-NNNN`.

If I skip it, remove those optional live-task and dashboard-task files before
the first commit. Durable memory records still work without them.

---

### Step 14: Commit

Tell me:

> Your memory repo is initialized. Here is the commit to make:

```bash
git add .
git commit -m "Initialize Braingent memory repo"
```

Then summarize what was set up: which files were updated, which folders were
created, whether the optional live-task layer was kept, and what still needs to
be filled in manually.

---

### Step 15: Cleanup Reminder

Tell me:

> Your memory repo is committed. If the cloned `braingent-manifesto` setup repo is still on disk, delete or archive it now unless you plan to contribute to the starter kit. Keeping it around can confuse future `AGENTS.md` / `CLAUDE.md` searches because agents may query the public starter repo instead of your real memory repo.

Do not delete anything automatically. Ask me to confirm the path first.

---

## What To Do Next

After initialization:

1. **Remove the setup repo from your active workspace.** Delete or archive `braingent-manifesto` after confirming your memory repo is committed.
2. **Index your first repo.** See below — this is the highest-value next step.
3. **Add your first real task record.** Next time you finish a piece of work, say `"capture this"` (or your chosen trigger phrase).
4. **Fill in repository profiles.** Open `repositories/repo--github--<owner>--<name>/README.md` and add the stack, common commands, and conventions.
5. **Customize preferences.** Read through `preferences/` and adjust anything that does not match how you work.
6. **Use live tasks only when coordination matters.** Start with `tasks/README.md` and `AGENT-TASK-COORDINATION.md`.
7. **Add optional tooling.** See `SETUP.md` for ripgrep, SQLite, task scripts, dashboard, and generated indexes if you want faster search later.

The memory gets better with use. The first record is the hardest — everything after that is just the loop.

End setup by asking me:

> What do you want to use Braingent for next?
>
> - Index a codebase so future planning has repo context.
> - Build a plan for a feature, bug fix, or cleanup.
> - Capture a task or decision that already happened.
> - Tune preferences, workflows, or capture depth.

---

## Ready To Index Your First Repo?

Your memory repo is set up. Now give it real history to work from.

Tell your agent:

> **"Index this repo to braingent"**

Use it from inside the codebase you want indexed. If you are in a different directory, name the target repo instead:

> **"Index `<specific-repo>` to braingent"**

The agent will:

1. Scan local docs, planning files, and untracked notes.
2. Pull your authored commits from Git history.
3. Import merged pull requests from GitHub (if `gh` is authenticated).
4. Pull tickets from Jira or Linear (if connected and configured).
5. Write durable records — tasks, decisions, learnings, a repo profile.
6. Commit everything to your memory repo.

**You do not need all sources.** Git and local docs always work. GitHub, Jira, and Linear are optional — the agent skips what it cannot reach and tells you what was missed.

### Connecting external sources

| Source | What to do |
| --- | --- |
| GitHub Issues + PRs | Run `gh auth login` in your terminal before indexing |
| Jira | Ask your agent: `"connect Jira to braingent"` — it will guide you through the MCP or API key setup |
| Linear | Ask your agent: `"connect Linear to braingent"` — same flow |

Once connected, those sources are available for every future indexing run.

### After indexing

Your agent now knows the repo's full history before you write a single line of new code. Next time you start work on a ticket, it will search memory first and surface relevant past decisions, known risks, and prior fixes automatically.
