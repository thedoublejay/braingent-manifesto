# Claude Instructions

This repository is a durable engineering memory. Use it before planning meaningful work and update it after meaningful work.

> Source of truth for agent workflow is `preferences/agent-workflow.md`. Keep this file, `AGENTS.md`, and `CHATGPT_PROJECT_BRIEF.md` aligned with it.

## Read Order

1. `README.md`
2. `INDEX.md`
3. `CURRENT_STATE.md`
4. `preferences/naming.md`
5. `preferences/agent-workflow.md`
6. `preferences/capture-policy.md`
7. `preferences/search-recipes.md`
8. `preferences/taxonomy.md`
9. `preferences/content-style.md`
10. `preferences/note-taking-and-ai-memory.md`
11. `preferences/engineering-defaults.md`
12. `preferences/planning.md`
13. `preferences/code-review.md`
14. `preferences/pr-and-commit.md`
15. `preferences/privacy-and-safety.md`
16. Any relevant org, project, repository, topic, tool, ticket, or person records.

Do not read archives or raw imports by default. Search them only when relevant.

When the user invokes a workflow trigger phrase, follow the matching procedure in `workflows/` exactly. Current workflows include "clean up braingent" → `workflows/cleanup-braingent.md` and "index this repo to braingent" → `workflows/index-repo.md`.

## Core Rules

- Search memory before planning.
- Prefer prior decisions and established conventions when still valid.
- Capture decisions, verification, versions, failures, fixes, and follow-ups.
- Keep root instruction files thin.
- Do not store secrets, credentials, tokens, private keys, or sensitive personal data.
- Use templates from `templates/` for durable records.

## Memory Retrieval Protocol

Before planning or answering from memory:

1. Identify the relevant org, project, repo, ticket, topic, tool, and time window.
2. Run structured search (`scripts/find.sh` or equivalent) with metadata filters first.
3. Use `rg` for body text, error strings, partial names, and exploratory search.
4. Open the smallest useful set of records.
5. Separate current, stale, superseded, and raw-only evidence.
6. Cite file paths when memory affects the answer or plan.

## Subagent Handoff Protocol

When delegating work to subagents:

- Retrieve memory once in the parent agent.
- Pass a focused context pack to subagents — do not ask each subagent to reread the whole repo.
- Subagent outputs should cite the supplied memory and any local files inspected.

## Note Quality Protocol

When capturing a durable record:

- One meaningful event or reusable idea per record.
- Include retrieval cues: repo, project, ticket, topic, tool, error strings, and exact phrases future agents might search.
- Include evidence: commands, commits, PRs, ticket IDs, and source links.
- Link related records.
- Mark inference explicitly. Do not store guesses as facts.
- Mark stale assumptions and superseded decisions explicitly.

## Planning Format

For non-trivial work, include:

- **GOAL**
- **ANALYSIS**
- **APPROACH**
- **RISKS**
- **ELI5:** A plain-but-technical explanation that makes the work easy to understand without dumbing it down.

When writing a plan with a summary and phases or breakdowns, add a short **ELI5** after the summary and after each major phase. Assume the reader is technical, but may not have all local context loaded.

For multi-step plans, give each step a `→ verify: [check]` so progress is observable.

## After Work

When meaningful work is complete:

1. Create or update the appropriate record.
2. Update `CURRENT_STATE.md` or `INDEX.md` if the durable map changed.
3. Mention evidence and verification.
4. Note follow-ups.

## Stuck Protocol

If you hit the same wall twice:

1. State clearly what failed and why.
2. Search memory and the codebase for prior patterns.
3. Say: "I'm stuck on <X>. Tried <Y>. Options are <A> or <B>."
4. Ask which option to take.

Do not silently pivot to a different approach without flagging it.
