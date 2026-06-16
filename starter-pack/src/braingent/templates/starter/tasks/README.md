# Live Agent Tasks

This optional directory is for active `BGT-NNNN` work that needs coordination across agents or sessions.

Use it only when a live queue is useful. Durable memory still belongs in normal records under `orgs/`, `topics/`, `tools/`, `repositories/`, or another canonical location.

## Files

- `CLAUDE.md` - scoped instructions for agents editing task files.
- `INDEX.md` - generated or hand-maintained task index.
- `active/` - current mutable task files.
- `archive/` - closed tasks organized by month.

## Basic Loop

1. Check `tasks/INDEX.md` before starting overlapping work.
2. Create a task from `templates/agent-task.md` if coordination matters.
3. Claim it with a concrete actor such as `agent--codex-cli`.
4. Append activity while working.
5. Move to `in-review` when ready.
6. On completion, create or link durable memory with `agent_task: BGT-NNNN`.
7. Archive closed tasks after they no longer need active visibility.

## Source Of Truth

Task Markdown is the source of truth. Generated indexes and dashboards are read surfaces.
