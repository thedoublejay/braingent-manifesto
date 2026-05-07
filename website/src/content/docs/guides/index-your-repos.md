---
title: Index Your Repos
description: Backfill durable memory for an existing codebase from local docs, Git history, and GitHub — one trigger phrase, one workflow.
section: Guides
order: 8
---

After a fresh Braingent setup, your memory is empty. That's fine — you
can start capturing as you ship. But if you have an existing codebase
you'd like the agent to *already know about* on day one, run the
**index-repo** workflow.

It's the closest thing Braingent has to "import everything." It's
deliberately small.

## The trigger phrase

Inside any working repo:

```text
Index this repo to braingent
```

Or, when you're not in the target repo:

```text
Index <repo-slug> to braingent
```

The agent follows `workflows/index-repo.md` from the starter pack and
captures what it can reach.

## What gets captured

| Source | What gets captured |
| --- | --- |
| Local docs | READMEs, architecture notes, planning files, agent instructions, untracked notes |
| Git history | Your authored commits, branch names, merge history, ticket references in commit messages |
| GitHub | Issues and pull requests when `gh` is authenticated |
| External trackers | Jira, Linear, etc. — only when explicitly connected |

The output is a small set of durable records:

- A **repo profile** under `repositories/<repo-slug>/`.
- One or more **task records** for completed work the agent can
  reconstruct.
- **Decision records** when the agent finds non-obvious choices in commit
  messages, ADRs, or RFCs.
- **Learning records** when patterns surface across multiple files.
- **Ticket stubs** under `tickets/` for any tracker IDs it found.

## You don't need every source on day one

Git history + local docs is enough to start. Connect `gh` later. Connect
Jira / Linear later. Indexing is incremental — re-running the workflow
adds new records without overwriting old ones.

## Privacy is enforced during indexing

The same rules that apply to capture apply here:

- **No secrets, tokens, credentials.** Even if they're in a committed
  README, the agent should refuse to put them in records.
- **No raw chat transcripts.** Even if they're in a `.notes/` file.
- **No sensitive personal data.**

If you suspect the source repo has any of these, run `git diff` on the
output before committing the new records. The whole memory repo is
plain text — leaks are visible.

## Time and scope

Expect:

- **Small repos (<100 commits, ~1k lines docs):** 1–3 minutes.
- **Medium repos (1k commits, several READMEs):** 5–15 minutes.
- **Large repos:** chunk it. Index by date range or by directory.

The agent will stop and ask before it tries to index thousands of
commits in one shot. Token budget is finite.

## Re-indexing

Run the trigger phrase again to top off:

```text
Index this repo to braingent — only new since 2026-04-01
```

The agent walks `git log` from the cutoff and produces records only for
work it doesn't already see in the memory repo.

## When *not* to index

- **Repos you don't actually work in.** If it's a dependency you read
  but don't ship, the index will be noise.
- **Repos with frequent rewrites.** If `git log` is mostly squash-merges
  to a 50-commit-per-day branch, the signal-to-noise is too low.
- **Repos that already have an active Braingent profile.** Update the
  profile by hand or create a profile record with `scripts/new-record.sh`; don't
  re-index.

## What you do *after* indexing

Search what the agent wrote. Read the repo profile. Skim the new
records. If anything is wrong, fix it — the records are plain Markdown.

```bash
scripts/find.sh repo=repo--acme--api q=2026-04 --paths
scripts/recall.sh repo=repo--acme--api
```

Then go back to your normal flow. Next session, every time the agent
plans work in `acme/api`, it'll already have the profile in context.

## Where to go next

- [The Capture Loop](/guides/capture-loop/) — the ongoing write half of
  the loop.
- [Search & Recall](/guides/search-and-recall/) — what to do with the
  records the index produced.
- [Repository Shape](/concepts/repository-shape/) — where the repo
  profile lives in the layout.
