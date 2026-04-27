# Workflow: Index A Repository Into Memory

Use this workflow when you want to backfill useful history from a code repository into this memory repo.

Trigger phrases:

- "index this repo to memory"
- "index <specific-repo> to memory"
- "index this repo to braingent"
- "index <specific-repo> to braingent"
- "backfill this repo to memory"
- "scan this repo into memory"
- "create a repo profile"

## Goal

Create a small, durable set of memory records from a repository's local docs, Git history, PRs, tickets, and existing AI notes.

Do not create one record per commit. Cluster related work into useful records.

## Pre-Flight

Before scanning:

1. Confirm the target repository.
2. Confirm the time window.
3. Confirm whether private sources may be summarized.
4. Confirm no secrets or sensitive personal data should be copied.
5. Check whether a repository profile already exists.
6. Estimate scope before doing a large import.

If the trigger names a specific repository, resolve that repo before scanning. If the trigger says "this repo," use the current working directory.

## Sources To Check

### Local Docs

Look for:

- `README.md`
- architecture docs
- planning docs
- design docs
- migration notes
- `AGENTS.md`
- `CLAUDE.md`
- other AI instruction files
- untracked or local notes, if the user explicitly allows it

Classify docs as:

- permanent repo docs to link
- planning docs to summarize
- raw notes to import
- obsolete docs to ignore or mark as superseded

### Git History

Look for:

- authored commits
- merged branches
- ticket IDs
- branch names
- meaningful merge commits
- commit bursts that form one task

Skip:

- branch promotion noise
- routine dependency bumps
- generated changelogs
- version-only release commits
- trivial formatting-only changes, unless they reveal a durable convention

### Pull Requests

If available, capture:

- PR title
- PR URL
- creation and merge dates
- branch and base
- description summary
- linked tickets
- review comments that contain decisions
- files changed summary

Skip routine or trivial PRs unless comments contain a real decision or learning.

### Tickets

If available, capture:

- title
- status
- type
- priority
- description summary
- acceptance criteria
- linked PRs
- resolution
- last meaningful comments

Do not copy sensitive ticket content. Summarize it.

## Synthesis

Always create or update:

- one repository profile
- one import summary

Create task records for meaningful units of work.

Create decision records when an option was chosen over alternatives.

Create learning records when a reusable pattern appears.

Create ticket stubs only for cross-project or cross-repository tickets.

## Import Summary Shape

The import summary should include:

- scope
- sources scanned
- counts
- records created
- skipped noise
- gaps
- follow-ups

## Safety

Before writing records:

- strip secrets
- redact private identifiers when unnecessary
- summarize sensitive comments instead of copying them
- avoid private local paths in public-safe records

## Report Back

End with:

- what was indexed
- records created
- gaps
- follow-ups
- recommended next import
