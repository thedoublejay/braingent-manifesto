---
title: Weekly Plan
description: One human-written file per week of what matters, so you do not forget it and your agents know what to prioritise.
section: Guides
order: 5
---

The [daily log](/guides/daily-log/) records what agents did. It does not say
what you wanted them to do. By Wednesday the priorities you had on Monday
live only in your head, and an agent picking between three open tickets has
nothing to go on.

The weekly plan is one Markdown file per ISO week that you write. Agents read
it before choosing work, and the daily PM reports against it.

## The file

`weekly/2026-W42.md`:

```markdown
# Weekly plan: 2026-W42 (12 to 18 October 2026)

Timezone: Asia/Singapore

## Priorities

- [ ] Compliance M1 evidence packs
- [ ] Finish database locking (from 2026-W41)

## Notes

- [ ] Staging certificate renews in December

## Not this week

- Dashboard redesign

<!-- braingent:weekly-progress:start -->
## Progress

Done: 4 · Spawned: 6 · Open now: 3 ongoing, 1 in review, 1 blocked, 2 todo
...
<!-- braingent:weekly-progress:end -->
```

| Section | Owner | Rule |
| --- | --- | --- |
| `## Priorities` | You | Ordered, most important first. Tick with `[x]` when done. |
| `## Notes` | You | Reminders, context, deadlines, anything you might forget. |
| `## Not this week` | You | Work agents must not start this week without asking. |
| `## Progress` | Generated | Rolled up from the week's daily logs. Hand edits are overwritten. |

Weeks start on Monday, in `[daily] timezone`.

## Writing to it

Edit the file directly, or have an agent add a line when you ask it to:

```bash
braingent weekly-add "Compliance M1 evidence packs" --section priorities
braingent weekly-add "Staging certificate renews in December"   # notes is the default
braingent weekly-add "Dashboard redesign" --section not-this-week
```

## Reading it

```bash
braingent weekly          # priorities, notes, not-this-week, progress counts
braingent weekly --json   # for an agent or a dashboard
braingent weekly --path   # this week's file path
```

`--date YYYY-MM-DD` picks the week that contains that day.

## How agents use it

- They read it at the start of non-trivial work, and whenever choosing between tasks, and prefer work that serves a priority, in order.
- They do not start anything under `## Not this week` without asking.
- They edit your sections only through `braingent weekly-add`, and only when you ask. They never tick, reorder or delete your items.
- `workflows/daily-pm.md` suggests open priorities when today's goals are empty, and reports which priorities moved and which nothing touched.

## Carry-over

The first read or write of a new week creates its file and copies last week's
unticked priorities and notes into it, suffixed `(from YYYY-Www)`. Ticked
items and `## Not this week` stay behind, and older files remain as history.
