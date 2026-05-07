# Braingent Memory Repo

This is a Markdown-first engineering memory repository based on Braingent, created by JJ Adonis.

Use it as a durable memory layer for AI-assisted software engineering work. Claude, Codex, ChatGPT, and other tools should read this repo before planning meaningful work and should capture important outcomes after the work is done.

## What Goes Here

- Project and repository profiles.
- Task records.
- Code review records.
- Decision records.
- Reusable learnings.
- Tool and version notes.
- Ticket stubs for cross-cutting work.
- Optional live `BGT-NNNN` agent tasks for active coordination.
- Optional dashboard docs for a read-only live task UI.
- Runnable helper scripts for search, validation, reindexing, task files, MCP retrieval, and QA generation.
- The `tools/tool--test-plan/` QA generator for Markdown, Xray JSON, TestRail CSV, and Gherkin outputs.
- Raw imports before they are summarized.
- Preferences that guide future AI agents.

## Read First

Agents should start here:

1. `AGENTS.md` or `CLAUDE.md`, depending on the tool.
2. `INDEX.md`.
3. `CURRENT_STATE.md`.
4. `preferences/`.
5. `tasks/INDEX.md` if live tasks are enabled and the work may already be active.
6. Relevant organization, project, repository, topic, tool, ticket, or person records.

## Core Workflow

Before work:

- Read the root instructions.
- Search memory for relevant context.
- Check live tasks before creating overlapping active work.
- Reuse prior decisions and conventions.

During work:

- Track decisions, versions, commands, failures, fixes, tickets, PRs, branches, and follow-ups.
- Append activity to a live `BGT-NNNN` task when coordination or handoff matters.

After work:

- Create or update a durable record.
- Link completed live tasks to durable records with `agent_task: BGT-NNNN`.
- Update indexes or current state if needed.
- Commit the memory change.

## Search

Start with free-text search:

```bash
rg -n "<query>" .
```

With Python available, use the included structured search helper:

```bash
scripts/find.sh kind=decision
scripts/recall.sh repo=repo--example--owner--repo
```

You can also search frontmatter fields directly:

- `record_kind`
- `status`
- `organization`
- `project`
- `repositories`
- `ticket`
- `topics`
- `tools`
- `people`
- `ai_tools`

## Safety

Never store secrets, credentials, tokens, private keys, customer secrets, or sensitive personal data in this repo.

Use placeholders and links instead of copying sensitive evidence.
