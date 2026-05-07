---
title: Keeping Memory Healthy
description: Daily, weekly, monthly, and quarterly maintenance — keep frontmatter clean, indexes fresh, and stale records archived.
section: Guides
order: 9
---

A Braingent repo accumulates records the way any Git repo accumulates
code. Most of it stays useful. Some drifts: frontmatter goes stale,
indexes fall behind, captures get duplicated, the same lesson gets
written three different ways across three different records.

Maintenance is the cleanup loop. It runs on a schedule, not on a feeling.

## The trigger phrase

```text
clean up braingent
```

Variants the agent recognizes: `cleanup braingent`, `tidy braingent`,
`braingent maintenance`. The agent runs the matching procedure from
`workflows/cleanup-braingent.md`.

## Cadence

| Cadence | What runs | Time |
| --- | --- | --- |
| Daily (optional) | `doctor`, list new records | 1 min |
| Weekly | `validate`, `reindex --check`, archive done tasks | 5–10 min |
| Monthly | Stale record review, dedup pass, link audit | 20–30 min |
| Quarterly | Synthesis pass, broad review, frontmatter migration | 1–2 hours |

You can run any of these out of order. The agent picks based on the
trigger phrase + the time since the last cleanup commit.

## Daily — `braingent doctor`

The fastest health check. Run it as part of your morning ritual or wire
it into `pre-commit`.

```bash
braingent doctor --strict
```

Checks for missing entrypoints, stale placeholders, malformed
frontmatter, broken links, generated-index drift, and tooling gaps.

## Weekly

Three steps:

```bash
# 1. validate frontmatter across all records
braingent validate

# 2. confirm indexes still match records (no diff)
braingent reindex --check

# 3. archive done tasks
braingent task-archive --status done --older-than 7d
```

If any of these report issues, the agent shows you the diff before
fixing.

## Monthly — stale record review

Records the system flags as candidates for review:

- **No `links:`** at all (might be orphaned).
- **`status: open` for >30 days** (probably actually done).
- **Decisions without `superseded_by` whose tags overlap with newer
  decisions** (might already be obsolete).
- **Multiple records with near-identical `title`** (dedup candidates).

`braingent doctor --check stale` produces the list. Review by hand;
update or supersede; never auto-delete.

## Quarterly — synthesis pass

Synthesize what the last quarter taught you. The output is a topic page
with citations.

```bash
braingent synthesize --topic auth --since 2026-01-01 \
  --out topics/auth/2026-q1-synthesis.md
```

After the synthesis lands, review which underlying records are still
the best source of evidence. Mark superseded decisions with
`superseded_by:` pointing at the synthesis or a newer decision.

## What the agent should *not* do during cleanup

- **Never delete records silently.** Stale records can be archived
  (`status: archived`) but the file stays.
- **Never rewrite history.** Cleanup only adds new commits.
- **Never alter `id`.** IDs are forever; cross-references rely on them.
- **Never auto-merge dedup candidates.** Always show the diff and ask.

These rules live in the cleanup workflow itself. If you find an agent
breaking one, fix the workflow.

## Privacy passes

Every cleanup pass should also run a quick check for things that
shouldn't be there:

```bash
braingent doctor --check private-paths
braingent doctor --check forbidden-patterns
```

The first checks for committed paths under `~/private/...`. The second
runs your `forbid_patterns` regex list (AWS keys, GitHub PATs, Anthropic
keys, etc.). See [Configuration → Privacy
knobs](/reference/configuration/#privacy--safety-knobs).

## Wire it into CI (optional)

The whole maintenance check is non-zero-exit-clean:

```yaml
# .github/workflows/braingent-doctor.yml
on: [push, pull_request]
jobs:
  doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v1
      - run: bun install
      - run: braingent doctor --strict
      - run: braingent validate
      - run: braingent reindex --check
```

Three commands, three exit codes, full coverage of the weekly cadence
on every push.

## A cleanup that succeeds is *boring*

The right outcome of a cleanup pass: a small commit with `chore:
cleanup` in the message, a refreshed `indexes/recent.md`, and zero
substantive content changes. If a cleanup ever surfaces a substantive
issue, that's a sign of capture drift — fix the underlying capture
policy, not just the symptom.

## Where to go next

- [The Capture Loop](/guides/capture-loop/) — the cleanest way to keep
  cleanups boring is to capture cleanly in the first place.
- [Configuration](/reference/configuration/) — `forbid_patterns` and
  hooks.
- [CLI Reference](/reference/cli/) — every flag for `doctor`,
  `validate`, `reindex`, `task-archive`.
