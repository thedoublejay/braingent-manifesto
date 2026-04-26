# Claude Instructions

This repository is a durable engineering memory. Use it before planning meaningful work and update it after meaningful work.

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
10. `preferences/engineering-defaults.md`
11. `preferences/planning.md`
12. `preferences/code-review.md`
13. `preferences/pr-and-commit.md`
14. `preferences/privacy-and-safety.md`
15. Any relevant org, project, repository, topic, tool, ticket, or person records.

Do not read archives or raw imports by default. Search them only when relevant.

## Core Rules

- Search memory before planning.
- Prefer prior decisions and established conventions when still valid.
- Capture decisions, verification, versions, failures, fixes, and follow-ups.
- Keep root instruction files thin.
- Do not store secrets, credentials, tokens, private keys, or sensitive personal data.
- Use templates from `templates/` for durable records.

## Planning Format

For non-trivial work, include:

- **GOAL**
- **ANALYSIS**
- **APPROACH**
- **RISKS**
- **ELI5:** A plain-but-technical explanation that makes the work easy to understand without dumbing it down.

When writing a plan with a summary and phases or breakdowns, add a short **ELI5** after the summary and after each major phase. Assume the reader is technical, but may not have all local context loaded.

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
