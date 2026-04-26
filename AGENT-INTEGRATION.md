# Agent Integration

Braingent works because the AI tools are told to use it before they act.

The exact integration depends on the tool, but the idea is the same:

1. Give the tool a small entrypoint file.
2. Tell it to read the memory repo before planning.
3. Tell it to search relevant records before implementation or review.
4. Tell it to capture meaningful outcomes after work.
5. Tell it never to store secrets or sensitive data.

## Codex

Use `AGENTS.md` as the Codex entrypoint.

Recommended behavior:

- Read `README.md`, `INDEX.md`, `CURRENT_STATE.md`, and `preferences/`.
- Search the memory before non-trivial planning.
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

## Tool-Agnostic Rule

Any AI tool using Braingent should follow this loop:

```text
Read entrypoints -> search relevant memory -> plan -> execute -> verify -> capture -> commit
```

## What Not To Do

- Do not paste private memory into public prompts.
- Do not include secrets in global agent instructions.
- Do not make every agent read every record for every task.
- Do not let root instruction files become a giant archive.
- Do not capture raw chat logs as final memory when a summary would work.

