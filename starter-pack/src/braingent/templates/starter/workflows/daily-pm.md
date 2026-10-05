# Daily PM Workflow

Use this when the user says "run the daily PM", "catch me up", "daily standup", or "what did the agents do today".

The PM agent reports on the day. It does not do the work, open tickets, change trackers, or edit `## Goals`. The only file it writes is today's daily log, and only through `braingent daily-log`.

## Steps

1. **Open the day.** Run `braingent daily-status --json`. This creates today's file with carry-over if it does not exist yet. Read today's file and the previous day's file.
   → verify: the JSON `path` exists and `carried` matches the carried items you see.

2. **Check goals.** If `## Goals` is empty, ask the user for up to three goals for today and stop the workflow until they answer or decline. Do not invent goals.

3. **Sweep sources for today** in the `[daily] timezone` window. Use whichever sources are available and skip the rest:
   - GitHub: `gh search prs --author @me --updated ">=YYYY-MM-DD"` and `gh search prs --reviewed-by @me --updated ">=YYYY-MM-DD"`.
   - Issue tracker (Linear, Jira, GitHub Issues) through its MCP server or CLI: issues you created or moved today.
   - Braingent: `braingent find date=YYYY-MM-DD` for records captured today, and `braingent task-list` for live `BGT-*` tasks.
   → verify: every source you used is listed in the report, and every source you skipped is named with the reason.

4. **Backfill the log.** For each item a source shows but the log does not, append one event with your own agent ID and a `sweep:` prefix:

   ```bash
   braingent daily-log spawned "sweep: Flaky checkout test" --ref EX-1240 --as agent--claude-code
   ```

   Match items by `--ref`. Do not duplicate items the log already has. Do not rewrite or delete existing lines.
   → verify: `braingent daily-status` counts rise by exactly the number of events you added.

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
