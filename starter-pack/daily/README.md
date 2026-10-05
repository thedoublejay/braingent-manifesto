# Daily Log

One file per day, `daily/YYYY-MM-DD.md`, recording what every agent did that day. It answers "what is ongoing, what is todo, what got done, and what did the agents spawn" without reading every ticket and PR.

The date is the date in `[daily] timezone` from `.braingent/config.toml`, or the machine's local timezone when unset.

## File shape

| Section | Owner | Rule |
| --- | --- | --- |
| `## Goals` | Human | Up to three outcomes for the day. Agents never edit it. |
| `## Status` | Generated | Rebuilt from the log on every write. Hand edits are overwritten. |
| `## Log` | Agents | Append-only, one event per line. Never rewrite earlier lines. |

## Logging an event

```bash
braingent daily-log started "Verdict lock fix" --ref EX-1234 --as agent--claude-code
braingent daily-log review "Two findings on the lock PR" --ref app#201 --as agent--codex-cli
braingent daily-log spawned "Flaky checkout test" --ref EX-1240 --as agent--claude-code
braingent daily-log done "Verdict lock merged" --ref EX-1234 --as agent--claude-code
```

Each call appends a line such as `- 09:42 · agent--claude-code · started · EX-1234 · Verdict lock fix` under a file lock, so several CLIs can log at once.

| Kind | Status bucket | Use when |
| --- | --- | --- |
| `todo` | Todo | Work is identified but not started. |
| `started` | Ongoing | An agent begins work. |
| `review` | In review | Work is waiting on review, or a reviewer reports back. |
| `blocked` | Blocked | Work waits on a person, access, or another change. |
| `done` | Done | Work is finished. |
| `dropped` | Done (dropped) | Work is intentionally abandoned. |
| `spawned` | Todo, plus Spawned today | An agent creates a new ticket, PR, or task. |
| `note` | Log only | Context worth keeping that changes no status. |

Events with the same `--ref` are one item, and the latest event decides its bucket. Without `--ref`, the event text is the key.

## Reading the day

```bash
braingent daily-status          # counts and sprawl flag
braingent daily-status --json   # for a PM agent or dashboard
braingent daily-status --path   # today's file path
```

When `Spawned today` reaches `[daily] sprawl_threshold` (default 10), the status block shows a sprawl warning.

## Carry-over

The first event of a new day creates that day's file and copies the previous day's unfinished items (ongoing, in review, blocked, todo) into the log as `carry-over` events. Done, dropped, and note events stay behind. Older files are kept as history.

## PM agent

`workflows/daily-pm.md` is the catch-up procedure: it sweeps the day's PRs, tickets, and records for anything agents forgot to log, regenerates the status, and reports goals against progress.
