# Planning

Use a plan when the task has unclear scope, touches several files, changes architecture, or may span sessions.

## Plan Format

Include:

- **GOAL:** What problem is being solved.
- **ANALYSIS:** What context matters, what is known, and what still needs checking.
- **APPROACH:** The plan and why it fits.
- **RISKS:** What could go wrong.
- **ELI5:** A plain-but-technical explanation that makes the work easy to understand without dumbing it down.

When writing a plan with a summary and phases or breakdowns, add a short **ELI5** after the summary and after each major phase. Assume the reader is technical, but may not have all local context loaded.

## Options

For non-trivial plans:

1. Consider two or three reasonable options.
2. List tradeoffs.
3. Recommend one option with rationale.
4. State what evidence would change the recommendation.
5. Include the ELI5 bullet for one-shot non-trivial plans.

## Plan Files

Create a plan file when work spans multiple sessions or needs review checkpoints.

Suggested locations:

- `docs/planning/`
- `docs/research/`
- `docs/decisions/`
- `orgs/<org>/projects/<project>/records/`

Keep planning docs organized. Do not scatter root-level Markdown files.

## Capture

After meaningful work, create a record. Do not wait for explicit instruction when a decision, surprise, reusable learning, or completed task should be remembered.
