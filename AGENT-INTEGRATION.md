# Agent Integration

Braingent works because the AI tools are told to use it before they act.

The exact integration depends on the tool, but the idea is the same:

1. Give the tool a small entrypoint file.
2. Tell it to read the memory repo before planning.
3. Tell it to search relevant records before implementation or review.
4. Tell it to capture meaningful outcomes after work.
5. Tell it never to store secrets or sensitive data.
6. If live tasks are enabled, tell it to check `tasks/INDEX.md` before starting overlapping work.

## Codex

Use `AGENTS.md` as the Codex entrypoint.

Recommended behavior:

- Read `README.md`, `INDEX.md`, `CURRENT_STATE.md`, and `preferences/`.
- Search the memory before non-trivial planning.
- Check live tasks before creating duplicate active work.
- Prefer existing repo and topic records over guessing.
- Capture completed work using the templates.
- Keep changes small and commit meaningful updates.
- Never add `Co-Authored-By` trailers unless you explicitly want them.

If your Codex setup supports global instructions, copy the root `AGENTS.md` content into that global location, or make the global file point to your memory repo.

## Claude

Use `CLAUDE.md` as the Claude entrypoint.

Recommended behavior:

- Treat the memory repo as source material.
- Read root instructions and preferences before plans.
- Search durable records for prior decisions, bugs, and conventions.
- Use `tasks/CLAUDE.md` only when working inside `tasks/` or touching `BGT-NNNN` files.
- Use the capture policy when the task ends.
- Keep long transcripts out of permanent records unless there is a retention reason.

If Claude supports project instructions, add a short pointer to the memory repo and ask it to read the root files.

## ChatGPT

Use `CHATGPT_PROJECT_BRIEF.md` as the ChatGPT project brief.

Recommended behavior:

- Paste the brief into the Project Instructions field.
- Add key memory files as project knowledge if your ChatGPT plan supports that.
- Keep the brief short and focused on workflow.
- Use the same taxonomy and templates as Claude and Codex.

## Gemini CLI

Use `GEMINI.md` as the Gemini CLI entrypoint.

Gemini CLI reads `GEMINI.md` from the project root when starting a session in that directory. Place a `GEMINI.md` in your memory repo pointing to the same read order and workflow instructions as `CLAUDE.md`.

Recommended behavior:

- Read `README.md`, `INDEX.md`, `CURRENT_STATE.md`, and `preferences/` before planning.
- Search durable records for prior decisions, bugs, and conventions.
- Follow the capture policy when the task ends.
- Keep the file thin — route into focused memory rather than duplicating instructions.

Gemini CLI skills (if configured) can activate workflows automatically. Wire the same trigger phrases (`"index this repo to braingent"`, `"clean up braingent"`, etc.) so the behavior stays consistent across tools.

If your Gemini setup supports global instructions, copy or symlink the `GEMINI.md` content into that global location.

## Tool-Agnostic Rule

Any AI tool using Braingent should follow this loop:

```text
Read entrypoints -> search relevant memory -> check live tasks -> plan -> execute -> verify -> capture -> commit
```

For larger memory repos, make this loop token-efficient:

```text
Read entrypoints -> search -> inspect compact results -> read summaries -> open full records only when evidence requires it
```

See `TOKEN-EFFICIENT-ACCESS.md` for a tool-agnostic retrieval ladder and
summary-read guardrails.

If a tool is working on a live task, append attributed activity with a concrete
actor such as `agent--codex-cli` or `agent--claude-code`. Do not use vague
authors like "AI" or "assistant" in the task log.

## What Not To Do

- Do not paste private memory into public prompts.
- Do not include secrets in global agent instructions.
- Do not make every agent read every record for every task.
- Do not let root instruction files become a giant archive.
- Do not put the full task protocol in the root entrypoint; keep it in `tasks/CLAUDE.md` or a focused preference file.
- Do not let the local dashboard become a second source of truth.
- Do not capture raw chat logs as final memory when a summary would work.
