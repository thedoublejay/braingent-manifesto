---
title: Keeping Memory Healthy
description: Daily, weekly, monthly, and quarterly maintenance — keep frontmatter clean, indexes fresh, and stale records archived.
section: Guides
order: 9
---

A Braingent repo accumulates records the way any Git repo accumulates code.
Most of it stays useful. Some drifts: frontmatter goes stale, indexes fall
behind, captures get duplicated, and the same lesson gets written in several
places.

Maintenance is the cleanup loop. It runs on a schedule, not on a feeling.

## The trigger phrase

```text
clean up braingent
```

Variants the agent recognizes: `cleanup braingent`, `tidy braingent`, and
`braingent maintenance`. The agent runs the matching procedure from
`workflows/cleanup-braingent.md`.

## Cadence

| Cadence | What runs | Time |
| --- | --- | --- |
| Daily (optional) | `scripts/doctor.sh`, list new records | 1 min |
| Weekly | `scripts/validate.sh`, `scripts/reindex.sh --check`, archive closed tasks | 5-10 min |
| Monthly | Stale record review, dedup pass, link audit | 20-30 min |
| Quarterly | Synthesis pass, broad review, frontmatter migration | 1-2 hours |

You can run any of these out of order. The agent picks based on the trigger
phrase and the time since the last cleanup commit.

## Daily — `scripts/doctor.sh`

The fastest health check. Run it as part of your morning ritual or wire it
into pre-commit.

```bash
scripts/doctor.sh
```

Checks for missing entrypoints, stale placeholders, malformed frontmatter,
broken links, generated-index drift, and tooling gaps.

## Weekly

Three steps:

```bash
# 1. validate frontmatter across all records
scripts/validate.sh

# 2. confirm indexes still match records
scripts/reindex.sh --check

# 3. archive closed tasks
scripts/task-archive.sh BGT-0142 --as agent--codex-cli --resolution completed
```

If any command reports issues, review the diff before fixing.

## Monthly — stale record review

Records the system flags as candidates for review:

- **No `links:`** at all, which may mean the record is orphaned.
- **Long-lived active work**, which may actually be completed or blocked.
- **Decisions without `superseded_by`** whose topics overlap newer decisions.
- **Multiple records with near-identical `title`**, which may be dedup candidates.

Use `scripts/doctor.sh` plus targeted `scripts/find.sh` and `rg` queries to
produce the list. Review by hand; update or supersede; never auto-delete.

## Quarterly — synthesis pass

Synthesize what the last quarter taught you. The output is a topic, repo, or
project synthesis page with citations.

```bash
scripts/synthesize.sh --topic auth
```

After the synthesis lands, review which underlying records are still the best
source of evidence. Mark superseded decisions with `superseded_by:` pointing at
the synthesis or a newer decision.

## What the agent should not do during cleanup

- **Never delete records silently.** Stale records can be superseded or archived, but the file stays.
- **Never rewrite history.** Cleanup only adds new commits.
- **Never alter durable IDs.** Cross-references rely on them.
- **Never auto-merge dedup candidates.** Always show the diff and ask.

These rules live in the cleanup workflow itself. If an agent breaks one, fix
the workflow.

## Privacy passes

Every cleanup pass should also run a quick check for things that should not be
there:

```bash
scripts/doctor.sh
rg -n '/Users/|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{40,}' .
```

The first checks the Braingent-specific health rules. The second is a simple
defense-in-depth scan for private local paths and common token patterns. See
[Configuration → Privacy knobs](/reference/configuration/#privacy--safety-knobs).

## Wire it into CI (optional)

The weekly maintenance checks are clean CI gates:

```yaml
# .github/workflows/braingent-doctor.yml
on: [push, pull_request]
jobs:
  doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v6
        with:
          python-version-file: .python-version
      - run: pip install -r requirements.txt
      - run: scripts/doctor.sh
      - run: scripts/validate.sh
      - run: scripts/reindex.sh --check
```

Three commands, three exit codes, full coverage of the weekly cadence on every
push.

## A cleanup that succeeds is boring

The right outcome of a cleanup pass is a small commit, refreshed derived
indexes, and zero unrelated content changes. If cleanup surfaces a substantive
issue, fix the underlying capture policy, not just the symptom.

## Where to go next

- [The Capture Loop](/guides/capture-loop/) — the cleanest way to keep cleanups boring.
- [Configuration](/reference/configuration/) — privacy patterns and hooks.
- [CLI Reference](/reference/cli/) — shipped helper scripts and flags.
