# Maintenance

Braingent stays useful when it is maintained lightly and regularly.

The starter pack includes a complete cleanup workflow at
`starter-pack/workflows/cleanup-braingent.md`. Trigger it by telling your agent:

> "clean up braingent"

The workflow covers daily, weekly, monthly, and quarterly cadences. Below is a
summary.

## Cadence Summary

### Daily: 5-10 Minutes

- Normalize or explicitly defer new `inbox/` items.
- Validate frontmatter and check indexes.
- Capture any meaningful completed work.
- Scan for unchecked follow-ups and obvious TODOs.

```bash
git status --short
scripts/validate.sh
scripts/reindex.sh --check
rg -n "^- \[ \]" --type md orgs repositories topics tools tickets inbox imports
```

### Weekly: 30-45 Minutes

- Review `CURRENT_STATE.md`.
- Promote useful inbox notes into records.
- Link new important records from `INDEX.md`.
- Mark blocked or superseded records.
- Move repeated lessons into `topics/`.
- Remove stale raw imports if summaries exist.
- Check repo profiles for old `last_reviewed` dates.

### Monthly: 60-90 Minutes

- Create or update derived synthesis pages only when every claim cites source
  records.
- Run a drift check: claims without source paths, accepted decisions that
  conflict, profiles not linking important recent records.
- Sample real tasks as recall-eval cases.

### Quarterly: 2-3 Hours

- Review taxonomy fields and templates.
- Check validation coverage and generated index shape.
- Review global agent entrypoint drift between Claude, Codex, and ChatGPT.
- Evaluate whether any workflow should be promoted, simplified, or archived.

## After A Task

- Capture the outcome.
- Add verification evidence.
- Record decisions and alternatives.
- Add follow-ups.
- Link related records.
- Commit the memory update.

## After A Review

- Capture findings.
- Capture missing tests.
- Capture security or privacy risks.
- Promote reusable review lessons.
- Link the PR or diff.

## After A Tool Upgrade

- Add a version record.
- Note compatibility issues.
- Note verification commands.
- Link affected repositories.

## When Records Become Wrong

Do not silently rewrite history.

Instead:

1. Add a new record.
2. Mark the old record `superseded`.
3. Link both records.
4. Update indexes and profiles.

## When The Repo Gets Noisy

Common symptoms:

- too many vague notes
- raw transcripts piling up
- unclear filenames
- no current state updates
- root instruction files too large
- duplicated preferences

Fixes:

- summarize raw imports
- delete stale inbox notes
- move detailed rules into focused preference files
- keep root entrypoints thin
- update `INDEX.md`
- create topic records for repeated patterns

See `starter-pack/workflows/cleanup-braingent.md` for the full structured
cleanup procedure including deep cleanup and quarterly review.
