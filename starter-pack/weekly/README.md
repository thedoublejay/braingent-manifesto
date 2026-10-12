# Weekly Plan

One file per ISO week, `weekly/YYYY-Www.md`, holding what matters this week in the human's own words. It is the place to write things down so they are not forgotten, and the first thing an agent reads when deciding what to work on next.

Weeks start on Monday. The week is the one containing today in `[daily] timezone` from `.braingent/config.toml`.

## File shape

| Section | Owner | Rule |
| --- | --- | --- |
| `## Priorities` | Human | Ordered, most important first. `- [ ]` open, `- [x]` done. |
| `## Notes` | Human | Reminders, context, deadlines, anything you might forget. |
| `## Not this week` | Human | Work agents must not start this week without asking. |
| `## Progress` | Generated | Rolled up from this week's `daily/` logs on every read or write. Hand edits are overwritten. |

Write in the file directly, or ask an agent to add a line for you:

```bash
braingent weekly-add "Compliance M1 evidence packs" --section priorities
braingent weekly-add "Staging cert renews in December" --section notes
braingent weekly-add "Dashboard redesign" --section not-this-week
```

`--section` defaults to `notes`. Priorities and notes are added as unticked `- [ ]` items, at the end of the section. Reorder them by hand.

## Reading the week

```bash
braingent weekly          # priorities, notes, not-this-week, progress counts
braingent weekly --json   # for an agent or dashboard
braingent weekly --path   # this week's file path
```

`--date YYYY-MM-DD` on any command selects the week containing that day.

## How agents use it

- Read it at the start of non-trivial work, and whenever choosing between tasks. Prefer work that serves a priority, in order.
- Do not start anything listed under `## Not this week` without asking.
- Edit the human sections only through `braingent weekly-add`, and only when the human asks. Never tick, reorder, or delete their items.
- The daily PM reports today against the week's priorities.

## Carry-over

The first read or write of a new week creates its file and copies last week's unticked priorities and notes into it, suffixed `(from YYYY-Www)`. Ticked items and `## Not this week` stay behind. Older files are kept as history.
