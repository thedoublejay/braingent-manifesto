---
id: BGT-0005
record_kind: agent-task
title: "Unblock index regeneration"
status: blocked
priority: low
owner: agent--gemini-cli
reviewer: agent--codex-cli
observers: [human--example-owner]
created: 2026-01-05
updated: 2026-01-06
organization: org--example
project: project--example--memory
repositories: [repo--github--example--starter]
topics: [topic--ai-memory]
depends_on: [BGT-0002]
blocked_by: [human--example-owner]
external_links: []
visibility: public-example
---

# BGT-0005: Unblock Index Regeneration

## Description

Demonstrate blocked work in the sample dashboard.

## Acceptance Criteria

- [ ] The blocked status appears in the queue.
- [ ] The dependency graph shows the task depends on `BGT-0002`.
- [ ] The activity panel includes a blocker note.

## Plan

1. Wait for the example owner to choose generated index filenames.
2. Update sample index references.
3. Move the task back to ready.

## Linked Evidence

- `indexes/agent-task-queue.md`
- `indexes/agent-task-graph.md`

## Activity

- 2026-01-05T15:00:00Z | agent--gemini-cli | role:owner | event:created |
  Created blocked sample task.
- 2026-01-06T09:00:00Z | human--example-owner | role:blocker | event:blocked |
  Waiting on a naming decision for generated task indexes.
