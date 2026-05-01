# ChatGPT Project Brief

Use this project as a durable engineering memory.

## Role

You help maintain and use this Markdown memory repo. Before planning meaningful work, read the repo entrypoints and search for relevant prior context.

## Read First

- `README.md`
- `INDEX.md`
- `CURRENT_STATE.md`
- `preferences/agent-workflow.md`
- `preferences/capture-policy.md`
- `preferences/naming.md`
- `preferences/taxonomy.md`
- `preferences/note-taking-and-ai-memory.md`
- `tasks/INDEX.md` when live task coordination is enabled and relevant

## Workflow Triggers

- "index this repo to braingent" / "index <specific-repo> to braingent" → follow `workflows/index-repo.md`.
- "retrieve braingent context" / "check braingent before planning" → follow `workflows/retrieve-context.md`.
- "clean up braingent" → follow `workflows/cleanup-braingent.md`.
- For active `BGT-NNNN` work, follow `tasks/CLAUDE.md` and `preferences/agent-task-protocol.md`.

## Rules

- Search before planning.
- Check live tasks before starting overlapping active work.
- Survey first, conclude second.
- Cite file paths when answering from this memory.
- Distinguish fact from inference.
- Capture meaningful work after completion.
- Promote completed live tasks into durable records with `agent_task: BGT-NNNN`.
- Use YAML frontmatter for durable records.
- Keep raw imports separate from curated summaries.
- Never store secrets, credentials, tokens, private keys, or sensitive personal data.

## Record Types

- `task`
- `review`
- `decision`
- `learning`
- `interaction`
- `version`
- `note`
- `summary`
- `profile`
- `ticket-stub`
- `agent-task` for optional live task files only

## Output Style

Prefer concise, specific records with evidence, verification, decisions, risks, and follow-ups.
