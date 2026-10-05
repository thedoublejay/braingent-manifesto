# Daily PM Workflow

Use this when the user says "run the daily PM", "catch me up", "daily standup", or "what did the agents do today".

The PM agent reports on the day. It does not do the work, open tickets, change trackers, or edit `## Goals`. The only file it writes is today's daily log, and only through `braingent daily-log`.

## Steps

1. **Open the day.** Run `braingent daily-status --json`. This creates today's file with carry-over if it does not exist yet. Read today's file and yesterday's file when it exists. Carry-over may come from the most recent earlier log if there was a gap.
   → verify: the JSON `path` exists and `carried` matches the carried items you see.

2. **Check goals.** If `## Goals` is empty, ask the user for up to three goals for today and stop the workflow until they answer or decline. Do not invent goals.

3. **Sweep sources for today** in the `[daily] timezone` window. Use whichever sources are available and skip the rest:
   - GitHub: calculate the start of today and tomorrow in `[daily] timezone`, then convert both boundaries to ISO 8601 UTC timestamps. Search authored and reviewed PRs with `gh search prs --author @me --updated "$start..$end" --limit 1000` and `gh search prs --reviewed-by @me --updated "$start..$end" --limit 1000`. Filter returned timestamps to the half-open interval `start <= updatedAt < end`; a date-only query uses the wrong midnight outside UTC. If the limit is reached, narrow by repository or time and report any incomplete coverage. Also fetch the live state of every unfinished PR already in today's log, including carried items, using `gh pr view <number> --repo <owner>/<repo> --json state,createdAt,closedAt,mergedAt,url,title`. Confirm the authenticated account covers the intended repositories.
   - Issue tracker (Linear, Jira, GitHub Issues) through its MCP server or CLI: issues you created or moved today.
   - Braingent: `braingent find date=YYYY-MM-DD` for records captured today, and `braingent task-list` for live `BGT-*` tasks.
   → verify: every source you used is listed in the report, and every source you skipped is named with the reason.

4. **Reconcile the log.** Match each source item by its canonical `--ref` and compare its live state with the latest logged state. For PRs, use `repo#number` as the key and retain its real URL when citing it in the report. For each verified missing event or state transition, append an event with your own agent ID and a `sweep:` prefix:

   ```bash
   braingent daily-log spawned "sweep: Flaky checkout test" --ref EX-1240 --as agent--claude-code
   braingent daily-log done "sweep: Checkout fix merged" --ref app#201 --as agent--claude-code
   ```

   - Use `spawned` only when the source proves the item was created within today's local window and no creation event for that ref is already logged. This keeps the sprawl count about new work.
   - Record the current state separately when needed: `review` for an open PR, `done` for a merged PR or completed task, `dropped` for an abandoned or unmerged closed item, and `started`, `blocked`, or `todo` for matching tracker states. Older items first discovered today get their current state without a `spawned` event.
   - An existing ref is not a reason to skip a state change. A carried PR that merged today needs a `done` event. Unchanged states need no event, even when the title changed. For ambiguous tracker states, report uncertainty instead of guessing.
   - Deduplicate source results and compare against events added during this sweep so rerunning the workflow adds nothing when sources are unchanged. Do not rewrite or delete existing lines.
   → verify: the Log gains exactly the events added, status buckets match the verified states, and the spawned count rises only by newly discovered creations. A second sweep with unchanged sources adds zero events.

5. **Report** to the user, short and scannable:
   - Goals: each goal with progress and the items that serve it.
   - Ongoing and in review: what is moving, and who is reviewing.
   - Blocked: each blocker and the single decision or input it needs.
   - Spawned today: count, untouched count, and the sprawl flag. If the flag is up, suggest which spawned items to defer, merge, or close. Do not act on them.
   - Carry-over: what will roll into tomorrow if nothing changes.
   - Sources used and skipped.

## Boundaries

- Read-only everywhere except today's daily log.
- Never edit `## Goals` or the generated `## Status` block by hand.
- Never notify, assign, or mention anyone.
- Never store secrets or ticket content that should not live in the memory repo. Titles and keys are enough.
