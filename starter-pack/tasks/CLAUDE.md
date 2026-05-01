# Task Instructions

These instructions apply when working inside `tasks/` or editing `BGT-NNNN` files.

## Read First

1. `tasks/README.md`
2. `preferences/agent-task-protocol.md`
3. `preferences/taxonomy.md`
4. `preferences/capture-policy.md`
5. Related durable records cited by the task

## Rules

- Use `record_kind: agent-task` for live task files.
- Keep IDs in the `BGT-NNNN` format.
- Use concrete actor IDs such as `agent--codex-cli`, `agent--claude-code`, or `human--<handle>`.
- Append activity entries; do not erase task history.
- Keep private data out of task files.
- Do not treat live task files as durable memory.
- When completing a task, create or link a durable record with `agent_task: BGT-NNNN`.
- Regenerate indexes after changing task state if scripts exist.

## Dashboard Contract

If this repo has a local task dashboard, it must read task Markdown and generated indexes. It must not store a second copy of task state.
