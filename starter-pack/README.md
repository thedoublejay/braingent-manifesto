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
- Raw imports before they are summarized.
- Preferences that guide future AI agents.

## Read First

Agents should start here:

1. `AGENTS.md` or `CLAUDE.md`, depending on the tool.
2. `INDEX.md`.
3. `CURRENT_STATE.md`.
4. `preferences/`.
5. Relevant organization, project, repository, topic, tool, ticket, or person records.

## Core Workflow

Before work:

- Read the root instructions.
- Search memory for relevant context.
- Reuse prior decisions and conventions.

During work:

- Track decisions, versions, commands, failures, fixes, tickets, PRs, branches, and follow-ups.

After work:

- Create or update a durable record.
- Update indexes or current state if needed.
- Commit the memory change.

## Search

Start with free-text search:

```bash
rg -n "<query>" .
```

When you add structured search automation later, use frontmatter fields such as:

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

