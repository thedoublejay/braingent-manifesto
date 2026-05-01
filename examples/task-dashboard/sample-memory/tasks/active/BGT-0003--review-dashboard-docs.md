---
id: BGT-0003
record_kind: agent-task
title: "Review dashboard documentation"
status: in-review
priority: high
owner: agent--claude-code
reviewer: agent--codex-cli
observers: []
created: 2026-01-03
updated: 2026-01-04
organization: org--example
project: project--example--memory
repositories: [repo--github--example--starter]
topics: [topic--dashboard]
depends_on: [BGT-0002]
blocked_by: []
external_links: []
visibility: public-example
---

# BGT-0003: Review Dashboard Documentation

## Description

Check that dashboard docs explain the read-only contract and copy workflow.

## Acceptance Criteria

- [ ] README names the dashboard as optional.
- [ ] USER-GUIDE explains queue, filters, graph, activity, and raw Markdown.
- [ ] Docs warn that Markdown remains source of truth.

## Plan

1. Read the dashboard README.
2. Read the user guide.
3. Confirm no private data appears in examples.

## Linked Evidence

- `README.md`
- `USER-GUIDE.md`

## Activity

- 2026-01-03T12:00:00Z | agent--claude-code | role:owner | event:opened-review |
  Started documentation review.
- 2026-01-04T09:00:00Z | agent--codex-cli | role:reviewer | event:reviewed |
  Verified the guide references synthetic task files.
