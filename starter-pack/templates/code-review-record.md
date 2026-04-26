---
title: <title>
record_kind: review
status: draft
date: <yyyy-mm-dd>
timezone: <timezone>
organization: <org-key-or-null>
project: <project-key-or-null>
ticket: <ticket-id-or-null>
review_target: <PR | branch | commit | diff | design-doc>
repositories: []
reviewer: <person-key-or-tool>
people: []
prs: []
topics: []
tools: []
---

# Code Review Record: <title>

## Review Target

<What was reviewed?>

## Method

<How the review was performed: files inspected, tests run, tools used.>

## Verdict

<High-level result.>

## Findings

| Severity | File/Area | Finding | Evidence | Recommendation | Issue ELI5 | Fix ELI5 |
| --- | --- | --- | --- | --- | --- | --- |
| <critical/high/medium/low> | <path> | <issue> | <evidence> | <fix> | <plain-but-technical why this is a problem> | <plain-but-technical how the fix solves it> |

## Positive Notes

- <Useful patterns to preserve>

## Verification

| Command or Evidence | Result | Notes |
| --- | --- | --- |
| `<command>` | <passed/failed/not run> | <notes> |

## Decisions Or Follow-Ups

- [ ] <Follow-up>

## Reusable Learnings

- <Learning to promote to topics/>

## Related Records

- <links>
