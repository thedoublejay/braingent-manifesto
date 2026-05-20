# Agent Workflow

Use this workflow for Claude, Codex, ChatGPT, and other AI tools.

## Before Planning

1. Read root instructions and `INDEX.md`.
2. Read `CURRENT_STATE.md`.
3. Read relevant files under `preferences/`.
4. If live tasks are enabled, check `tasks/INDEX.md` or `indexes/agent-task-queue.md`.
5. Search for relevant org, ticket, repo, topic, tool, and person names.
6. Reuse prior decisions and preferences when still valid.

Use free-text search first:

```bash
rg -n "<query>" .
```

Examples:

```bash
rg -n "auth|authentication|login" .
rg -n "repo--github--owner--repo-name" .
rg -n "record_kind: decision" .
rg -n "BGT-[0-9]{4}|record_kind: agent-task" tasks indexes
```

## During Work

Capture durable facts as they emerge:

- decisions and tradeoffs
- commands and verification evidence
- tool, framework, library, runtime, and model versions
- PR comments and review findings
- ticket numbers, commits, branch names, and PR links
- people involved and what was decided with them
- surprising failures and the fix
- live task activity when work is tracked by `BGT-NNNN`

## After Work

Create or update a record when:

- a PR is opened
- a ticket is completed or moved
- a code review is finished
- a key decision was made
- a reusable learning surfaced
- a surprising failure or bug was diagnosed
- the user explicitly asks to capture memory
- the user closes out a substantive task
- a live `BGT-NNNN` task reaches `completed`

For active coordination, use `record_kind: agent-task` under `tasks/active/`.
For durable memory, use the normal record templates outside `tasks/`.

## Handoff Checklist

Completed task records should include:

- current status
- repositories touched
- ticket, PR, branch, commit, and command evidence
- what changed
- what was verified
- key decisions
- follow-ups and risks
- links to related records
- `agent_task: BGT-NNNN` when produced from a completed live task

## Memory Hygiene

- Prefer one durable record per meaningful event.
- Promote repeated patterns to `topics/`.
- Promote stable repo facts to `repositories/`.
- Keep raw imports separate from curated notes.
- Keep live task files separate from durable records.
- Do not rewrite immutable records except for typo cleanup.
- Update `INDEX.md` and `CURRENT_STATE.md` when the durable map changes.
- Regenerate task indexes when live task state changes, if automation exists.
