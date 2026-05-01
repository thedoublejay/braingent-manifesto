---
id: BGT-0004
record_kind: agent-task
title: "Fix dashboard smoke test data"
status: completed
priority: medium
owner: agent--codex-cli
reviewer: agent--claude-code
observers: []
created: 2026-01-04
updated: 2026-01-05
organization: org--example
project: project--example--memory
repositories: [repo--github--example--starter]
topics: [topic--dashboard]
depends_on: [BGT-0002]
blocked_by: []
external_links: []
resolution: completed
visibility: public-example
---

# BGT-0004: Fix Dashboard Smoke Test Data

## Description

Keep one synthetic task searchable by the word smoke so e2e tests can verify filtering.

## Acceptance Criteria

- [x] Searching for smoke returns this task.
- [x] The task has completed closeout metadata.
- [x] Raw Markdown contains public-safe sample content.

## Plan

1. Add smoke-specific sample text.
2. Mark task completed.
3. Link a synthetic durable record path.

## Linked Evidence

- Durable record: `orgs/org--example/projects/project--example--memory/records/2026-01-05--task--fix-dashboard-smoke-test-data.md`
- Verification: `bun run test:e2e`

## Activity

- 2026-01-04T14:00:00Z | agent--codex-cli | role:owner | event:claimed |
  Claimed smoke test data update.
- 2026-01-04T14:20:00Z | agent--codex-cli | role:owner | event:updated |
  Added sample search terms and closeout evidence.
- 2026-01-05T10:00:00Z | agent--claude-code | role:reviewer | event:approved |
  Approved synthetic smoke test data.
- 2026-01-05T10:15:00Z | agent--codex-cli | role:owner | event:closed |
  Completed task with synthetic durable record link.

## Closeout

- Resolution: completed
- Durable record: `orgs/org--example/projects/project--example--memory/records/2026-01-05--task--fix-dashboard-smoke-test-data.md`
- Verification: `bun run test:e2e`
