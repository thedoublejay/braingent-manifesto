# Agent Task Protocol

This protocol applies only to optional live task files under `tasks/`. Durable records still use `preferences/capture-policy.md` and the normal templates.

## When To Use A Live Task

Use a live task when work needs coordination:

- more than one agent or session may touch it;
- status, priority, owner, or blockers matter;
- dependencies need to be visible;
- handoff activity should be preserved while the work is active;
- a local dashboard or queue view would help review the work.

Do not create live tasks for tiny edits that can be completed and captured directly.

## Identity

Use concrete actor IDs in live task fields and activity:

- `agent--codex-cli`
- `agent--claude-code`
- `agent--chatgpt`
- `agent--gemini-cli`
- `human--<handle>`

Do not use vague actors such as `ai`, `assistant`, or `agent`.

## Statuses

| Status | Meaning |
| --- | --- |
| `triage` | Captured but not accepted or assigned. |
| `ready` | Clear enough to start. |
| `in-progress` | Actively being worked. |
| `blocked` | Waiting on a dependency or decision. |
| `in-review` | Ready for review. |
| `completed` | Work is done and durable memory was updated when needed. |
| `closed` | Closed without completion. |

Every status change should add an activity entry explaining why.

## Activity Format

Append activity entries. Do not rewrite the task history except for typo fixes.

```markdown
- 2026-01-01T10:00:00Z agent--codex-cli: Claimed task and checked existing records.
```

Keep entries short and useful for handoff.

## Closeout

When a task completes:

1. Create or update the durable record.
2. Add `agent_task: BGT-NNNN` to that record.
3. Add the durable record path to the live task closeout.
4. Regenerate indexes.
5. Archive the task when it no longer needs active visibility.

## Stale Rules

Surface these in `indexes/stale-candidates.md`:

- `triage` older than 30 days;
- `blocked` older than 30 days;
- `in-progress` with no activity for 14 days;
- `completed` with no durable record link.

## Anti-Patterns

- Treating `tasks/active/` as permanent memory.
- Mixing `record_kind: agent-task` and `record_kind: task`.
- Closing completed work without durable capture.
- Letting a dashboard store separate state.
- Copying private task logs into public examples.
