---
id: BGT-0001
record_kind: agent-task
title: Example review task
status: triage
status_category: triage
resolution: null
type: task
priority: medium
visibility: public
assignee: null
reviewer: null
observers: []
claimed_by: null
claimed_at: null
date: 2026-01-01
timezone: UTC
created: 2026-01-01
updated: 2026-01-01
closed: null
organization: org--example
project: project--example--memory
repositories: [repo--example--owner--repo]
ticket: null
prs: []
commits: []
ai_tools: [Codex]
people: []
topics: [topic--ai-memory]
tools: []
parent: null
depends_on: []
duplicate_of: null
related_records: []
---

# BGT-0001: Example Review Task

## Description

Show the live task format with synthetic, public-safe content. This example
demonstrates how an agent can claim work, leave handoff notes, and later link a
durable record. Replace or delete it during initialization.

## Acceptance Criteria

- [ ] The task file has valid `agent-task` frontmatter.
- [ ] Activity entries are attributed to concrete actors.
- [ ] Closeout explains whether durable memory was created.

## Plan

1. Review the starter pack documentation.
2. Confirm whether live tasks are needed.
3. Delete this example or replace it with real, privacy-safe work.

## Dependencies

- Depends on: none
- Derived blockers: none

## Activity

- 2026-01-01T00:00:00Z | agent--codex-cli | role:assignee | event:visibility |
  Marked the synthetic example public because it contains no private context.
- 2026-01-01T00:01:00Z | agent--codex-cli | role:assignee | event:created |
  Created synthetic example task for the starter pack.

## Linked Evidence

- Durable records: none
- PRs: none
- Commits: none
- Commands: `scripts/validate.sh`

## Closeout

- Resolution: null
- Durable record: null
- Verification: starter example only
