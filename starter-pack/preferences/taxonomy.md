# Taxonomy

This file defines the controlled vocabulary for durable records.

## Record Kinds

| Kind | Purpose |
| --- | --- |
| `task` | Planned, active, or completed execution work. |
| `review` | Code reviews, PR reviews, and design reviews. |
| `decision` | Choices that should guide future work. |
| `learning` | Reusable technical lessons. |
| `interaction` | Meaningful professional exchanges. |
| `version` | Tool, dependency, framework, runtime, model, or platform versions. |
| `note` | Temporary or mixed context. |
| `summary` | Imported historical baselines. |
| `profile` | Repository or durable entity profiles. |
| `ticket-stub` | Cross-cutting tickets linking related records. |

## Status Values

| Record Kind | Allowed Statuses |
| --- | --- |
| `task` | `planned`, `active`, `blocked`, `completed`, `superseded` |
| `review` | `draft`, `completed`, `superseded` |
| `decision` | `proposed`, `accepted`, `superseded`, `rejected` |
| `learning` | `active`, `superseded` |
| `interaction` | `active`, `superseded` |
| `version` | `active`, `superseded` |
| `note` | `draft`, `active`, `completed`, `superseded` |
| `summary` | `draft`, `completed` |
| `profile` | `active`, `archived`, `superseded` |
| `ticket-stub` | `active`, `completed`, `abandoned` |

## Entity Key Prefixes

| Field | Prefix | Directory |
| --- | --- | --- |
| `organization` | `org--` | `orgs/` |
| `project`, `projects` | `project--` | `orgs/*/projects/` |
| `repo`, `repositories` | `repo--` | `repositories/` |
| `person`, `people` | `person--` | `people/` |
| `topic`, `topics` | `topic--` | `topics/` |
| `tool`, `tools` | `tool--` | `tools/` |

## AI Tools

Use consistent names:

- `ChatGPT`
- `Claude`
- `Codex`
- `Cursor`
- `Gemini`
- `GitHub Copilot`

Add new tools here before using them in frontmatter.

## Ticket IDs

Use a scalar `ticket` field for the primary ticket. If one record needs to mention related tickets, add them in the body or add an explicit `related_tickets` field only after you define that convention.

## Required Common Fields

Recommended common fields:

- `title`
- `record_kind`
- `status`
- `date`
- `timezone`

Add stricter validation later if the repo grows.

