---
id: BGT-0002
record_kind: agent-task
title: "Build dashboard sample app"
status: in-progress
priority: high
owner: agent--codex-cli
reviewer: agent--claude-code
observers: [human--example-owner]
created: 2026-01-02
updated: 2026-01-03
organization: org--example
project: project--example--memory
repositories: [repo--github--example--starter]
topics: [topic--ai-memory, topic--dashboard]
depends_on: [BGT-0001]
blocked_by: []
external_links: []
visibility: public-example
---

# BGT-0002: Build Dashboard Sample App

## Description

Provide a copyable local dashboard example that reads synthetic Markdown tasks.

## Acceptance Criteria

- [ ] The app runs with Bun.
- [ ] The default data source is `sample-memory/tasks/`.
- [ ] `BRAINGENT_MEMORY_ROOT` can point to a real memory repo.

## Plan

1. Copy the working dashboard implementation.
2. Replace private data with synthetic tasks.
3. Verify typecheck and build.

## Linked Evidence

- `examples/task-dashboard/README.md`

## Activity

- 2026-01-02T10:00:00Z | agent--codex-cli | role:owner | event:claimed |
  Claimed dashboard sample implementation.
- 2026-01-02T10:30:00Z | agent--codex-cli | role:owner | event:copied |
  Copied the dashboard app into a public example path.
- 2026-01-02T11:15:00Z | agent--codex-cli | role:owner | event:sanitized |
  Pointed the dashboard at synthetic task data by default.
- 2026-01-03T08:45:00Z | agent--claude-code | role:reviewer | event:review-note |
  Requested docs explaining how to use `BRAINGENT_MEMORY_ROOT`.
