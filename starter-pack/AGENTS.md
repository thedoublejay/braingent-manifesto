# Agent Instructions

This repository is a durable engineering memory. Treat it as source material for planning, code review, handoffs, retrospectives, and future task execution.

## Read Order

For every non-trivial task that uses this memory repo, read in this order:

1. `README.md`
2. `INDEX.md`
3. `CURRENT_STATE.md`
4. `preferences/naming.md`
5. `preferences/agent-workflow.md`
6. `preferences/capture-policy.md`
7. `preferences/search-recipes.md`
8. `preferences/taxonomy.md`
9. `preferences/content-style.md`
10. `preferences/engineering-defaults.md`
11. `preferences/planning.md`
12. `preferences/code-review.md`
13. `preferences/pr-and-commit.md`
14. `preferences/privacy-and-safety.md`
15. Any relevant org, project, repository, topic, tool, ticket, or person records.

Do not read archives or raw imports by default. Search them only when relevant.

## Operating Rules

- Search this repo before planning, reviewing code, or starting implementation.
- Use frontmatter and filenames for structured discovery.
- Use `rg` for free-text body search.
- Prefer durable summaries over chat transcripts.
- Record decisions, versions, evidence, and follow-up work explicitly.
- Every durable record begins with a YAML frontmatter block.
- Keep immutable records immutable. If facts change, add a new record and link it as superseding the old one.
- Keep mutable truth in indexes, profiles, and `CURRENT_STATE.md`.
- Use lowercase ASCII slugs.
- Do not create vague filenames like `notes.md`, `todo.md`, or `review.md`.
- When a task is completed, create or update a task record before considering memory capture done.
- Never store secrets, credentials, tokens, or sensitive personal data.

## Problem Framing

Before tackling a non-trivial task, briefly state:

- **GOAL:** What problem is being solved.
- **ANALYSIS:** What context matters and what still needs checking.
- **APPROACH:** The plan and why it fits.
- **RISKS:** What could go wrong.
- **ELI5:** A plain-but-technical explanation that makes the work easy to understand without dumbing it down.

Skip this for simple, clear tasks.

When writing a plan with a summary and phases or breakdowns, add a short **ELI5** after the summary and after each major phase. Assume the reader is technical, but may not have all local context loaded.

## Capture Triggers

Create or update a record when:

- a PR is opened
- a ticket is completed or moved
- a code review is finished
- a key decision is made
- a surprising failure or bug is diagnosed
- a reusable learning surfaces
- the user explicitly says "capture this", "save this to memory", or "task done"

## Stuck Protocol

If you hit the same wall twice:

1. State clearly what failed and why.
2. Search memory and the codebase for prior patterns.
3. Say: "I'm stuck on <X>. Tried <Y>. Options are <A> or <B>."
4. Ask which option to take.

Do not silently pivot to a different approach without flagging it.
