---
title: Daily Log
description: One Markdown file per day of what every agent did, so you can catch up on ongoing, todo, done, and spawned work in one read.
section: Guides
order: 5
---

A normal day with AI agents looks like this: Claude Code implements a
change, Codex reviews it, another session picks up a follow-up, and each
of them opens tickets and PRs as it goes. By the afternoon the work has
spread across a dozen tickets and you have lost the thread.

The daily log is one file per day that every agent appends to. Braingent
turns those lines into a status view (ongoing, in review, blocked, todo,
done, and what was spawned today), so you or a PM agent can catch up in
one read.

## The problem

- **Sprawl.** Agents create tickets and PRs faster than a person can
  follow them.
- **Scattered evidence.** What happened today is split across the issue
  tracker, GitHub, and several terminal sessions.
- **No end of day.** Unfinished work silently drops off when a session
  closes.

Live [multi-agent tasks](/guides/multi-agent-tasks/) coordinate one piece
of work. The daily log is the layer above them: a timeline of everything
that happened today.

## The file: `daily/YYYY-MM-DD.md`

```markdown
# Daily log: 6 October 2026

## Goals                         ← you write these, agents never touch them
- Ship the verdict lock fix

<!-- braingent:daily-status:start -->
## Status                        ← generated from the log on every write
Spawned today: 1 (1 untouched) · Carried over: 2
### Ongoing (1)
- [EX-1234] Verdict lock fix · agent--claude-code · 09:42
### In review (1)
- [app#201] Two findings on the lock PR · agent--codex-cli · 10:15
...
<!-- braingent:daily-status:end -->

## Log                           ← append-only, one line per event
- 00:00 · carry-over · blocked · EX-1100 · Waiting on infra access
- 09:42 · agent--claude-code · started · EX-1234 · Verdict lock fix
- 10:15 · agent--codex-cli · review · app#201 · Two findings on the lock PR
- 10:20 · agent--claude-code · spawned · EX-1240 · Flaky checkout test
```

The date is the date in your configured timezone, not UTC, so "today"
matches your clock.

## Why append-only

Several CLIs write to the same file at the same time. If each agent
edited the status sections directly, they would overwrite each other.

Instead, agents only **append one line** to `## Log`, under a file lock.
The status block is **derived** from the log and regenerated on every
write. This is the same pattern GitHub activity feeds and Linear's Pulse
use: writers record events, and the readable view is computed from them.

- Events with the same `--ref` are one item. The latest event decides
  its bucket.
- `## Goals` is human-owned and preserved byte for byte.
- Hand edits to `## Status` are overwritten, so make changes by logging
  an event instead.

## Logging from an agent

```bash
braingent daily-log started "Verdict lock fix" --ref EX-1234 --as agent--claude-code
braingent daily-log review "Two findings on the lock PR" --ref app#201 --as agent--codex-cli
braingent daily-log spawned "Flaky checkout test" --ref EX-1240 --as agent--claude-code
braingent daily-log blocked "Waiting on infra access" --ref EX-1100 --as agent--claude-code
braingent daily-log done "Verdict lock merged" --ref EX-1234 --as agent--claude-code
```

| Kind | Bucket | Use when |
| --- | --- | --- |
| `todo` | Todo | Work is identified but not started. |
| `started` | Ongoing | An agent begins work. |
| `review` | In review | Work waits on review, or a reviewer reports back. |
| `blocked` | Blocked | Work waits on a person, access, or another change. |
| `done` | Done | Work is finished. |
| `dropped` | Done (dropped) | Work is intentionally abandoned. |
| `spawned` | Todo, plus Spawned today | An agent creates a new ticket, PR, or task. |
| `note` | Log only | Context that changes no status. |

The starter `AGENTS.md` tells agents to log when they start, finish, hand
off for review, get blocked, or spawn something. Add the same line to your
global agent instructions so every CLI logs, not just sessions opened
inside the memory repo.

## Sprawl warning

When the number of tickets and PRs spawned today reaches
`[daily] sprawl_threshold` (default 10), the status block shows:

```text
> Sprawl: 10 tickets or PRs spawned today (threshold 10). Triage these before starting new work.
```

It is a limit on new work in progress, borrowed from Kanban: the fix for
sprawl is to notice it early, not to track more.

## Carry-over

The first event of a new day creates that day's file and copies the
previous day's unfinished items (ongoing, in review, blocked, todo) into
the log as `carry-over` events. Gap days such as weekends are skipped, so
Monday picks up from Friday. Old files stay in Git as history. A PM agent
only needs today and yesterday, so its context stays small.

## The PM agent

Agents forget to log. `workflows/daily-pm.md` covers the gap. Open any
agent once a day and say **"run the daily PM"** or **"catch me up"**. It:

1. Runs `braingent daily-status --json` and reads today and yesterday.
2. Asks for up to three goals if `## Goals` is empty.
3. Sweeps today's PRs (`gh search prs`), issue-tracker activity, and new
   Braingent records.
4. Backfills anything missing from the log with `sweep:` events, never
   rewriting existing lines.
5. Reports goals against progress, blockers and the decision each one
   needs, the spawned count with triage suggestions, and what will carry
   over.

The PM agent writes only today's log. It does not open tickets, change
trackers, or notify anyone.

## Reading the day

```bash
braingent daily-status            # one-line counts plus the sprawl flag
braingent daily-status --json     # for a PM agent or a dashboard
braingent daily-status --path     # today's file, to open in your editor
```

## Configuration

```toml
# .braingent/config.toml
[daily]
timezone = "Asia/Singapore"   # IANA name; defaults to the machine's local zone
sprawl_threshold = 10         # spawned items per day before the warning
```

## Where to go next

- [Multi-Agent Coordination](/guides/multi-agent-tasks/) for live task files.
- [CLI Reference](/reference/cli/#daily-log-commands) for every flag.
- [Configuration](/reference/configuration/) for the `[daily]` section.
