# Agent Workflow

Use this workflow for Claude, Codex, ChatGPT, and other AI tools.

## Before Planning

1. Read root instructions and `INDEX.md`.
2. Read `CURRENT_STATE.md`.
3. Read relevant files under `preferences/`.
4. Search for relevant org, ticket, repo, topic, tool, and person names.
5. Reuse prior decisions and preferences when still valid.

Use free-text search first:

```bash
rg -n "<query>" .
```

Examples:

```bash
rg -n "auth|authentication|login" .
rg -n "repo--github--owner--repo-name" .
rg -n "record_kind: decision" .
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

## Memory Hygiene

- Prefer one durable record per meaningful event.
- Promote repeated patterns to `topics/`.
- Promote stable repo facts to `repositories/`.
- Keep raw imports separate from curated notes.
- Do not rewrite immutable records except for typo cleanup.
- Update `INDEX.md` and `CURRENT_STATE.md` when the durable map changes.

