# Capture Policy

Capture enough detail that a future agent can understand what happened without rereading a full chat transcript.

## Capture These

- Task plans, execution records, and completions.
- Code reviews and review outcomes.
- Architecture and implementation decisions.
- Learnings reusable across tasks or projects.
- Tool, dependency, framework, runtime, model, and platform versions.
- Bugs fixed, root causes, and verification commands.
- Ticket, PR, branch, commit, and release details.
- Important professional conversations or decisions.
- User preferences that affect future work.

## Do Not Capture

- Secrets, credentials, API keys, tokens, private keys, or passwords.
- Sensitive personal data that is not needed for engineering memory.
- Full chat transcripts unless temporarily stored under `imports/raw/`.
- Large generated artifacts that can be reproduced.

## Record Type Selection

- Use `task` for planned or completed execution work.
- Use `review` for code reviews, PR reviews, and design reviews.
- Use `decision` for choices that should guide future work.
- Use `learning` for reusable technical lessons.
- Use `version` for dependency, framework, runtime, model, or tool versions.
- Use `interaction` for meaningful people or stakeholder exchanges.
- Use `summary` for imported historical baselines.
- Use `note` for temporary or mixed context that does not fit yet.
- Use `ticket-stub` for cross-cutting tickets that link related records.

## Common Frontmatter Shape

```yaml
---
title: <human title>
record_kind: task | review | decision | learning | interaction | version | summary | profile | note | ticket-stub
status: <kind-specific>
date: <yyyy-mm-dd>
timezone: <timezone>
organization: <org-key-or-null>
project: <project-key-or-null>
ticket: <ticket-id-or-null>
repositories: []
prs: []
commits: []
ai_tools: []
people: []
topics: []
tools: []
---
```

## Capture Triggers

Always capture when:

- a PR is opened
- a ticket is completed or moved
- a code review is finished
- a key decision was made
- a surprising failure or bug was diagnosed
- a reusable learning surfaced
- a new tool, framework, library, or version was adopted

Explicit phrases that should trigger capture:

- "capture this"
- "save this to memory"
- "write this to memory"
- "task done"
- "done thanks"

A casual "thanks" without task context is not enough.

## Quick Capture Vs Full Capture

- Use `templates/task-record-minimal.md` for quick end-of-task captures.
- Use `templates/task-record.md` for substantial work.
- Minimal records can be expanded later.

## Raw Imports

For old chats, PRs, tickets, or local notes:

1. Store raw exports in `imports/raw/` only if needed.
2. Create curated records from the raw material.
3. Link curated records to raw imports if retained.
4. Prefer summaries over transcript dumps.

