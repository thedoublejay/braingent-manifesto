---
title: Agent Workflows
description: How an agent uses Braingent — the contract for searching before planning and capturing after work.
section: Guides
order: 1
---

Once your agents are wired up, they all follow the same contract. This
page describes that contract from the agent's point of view: what it does
at session start, while it works, and after work is done.

If you've used `CLAUDE.md`-style instruction files before, this will feel
familiar. The difference is that Braingent gives every agent the *same*
instructions and the *same* memory — so the contract is consistent across
tools.

## The contract

```
1. Read pinned context (entrypoints, preferences, workflows).
2. Search Braingent for relevant prior memory before planning.
3. State what you found and what you're still assuming.
4. Work the task with the human.
5. After meaningful work, capture a durable record.
6. Commit the record to Git.
```

Every step is observable. You can ask the agent at any time: *what did
you read, what did you find, what are you assuming?*

## I. Session start — pinned context

The agent reads, in order:

1. The agent-specific entrypoint at the repo root (`CLAUDE.md`,
   `AGENTS.md`, etc.).
2. Any standing preferences in `preferences/`.
3. Workflows that match recent user input (e.g. *"index this repo to
   braingent"* triggers `workflows/index-repo.md`).

This load is fast and cheap. Most pinned files are short by design.

> **Tip:** If your agent skips this step, it usually means the entrypoint
> isn't loading. Smoke-test by asking *"what's the path to my Braingent
> memory repo?"* — a wired agent answers with the absolute path.

## II. Before planning — search

Before proposing a plan or touching code, the agent searches Braingent
for relevant prior context. Concretely, it does some combination of:

- **MCP tools** (preferred when available): `braingent_guide()`,
  `braingent_find(repos=..., topics=..., kind=...)`,
  `braingent_get(id, depth='summary')`.
- **Script fallbacks**: `scripts/find.sh repo=repo--acme--api kind=decision`,
  `scripts/recall.sh q=session-token-rotation`.
- **Direct grep / ripgrep** when the user asks for free-text body search.
- **Reading the relevant repo profile** at `repos/<repo-slug>/profile.md`.

The agent prefers `depth='summary'` first to keep context small, and only
fetches `depth='full'` when it needs exact evidence.

## III. State what you found

Before writing code, the agent surfaces a brief context summary:

> *I read the `acme/api` profile and three decision records (DEC-0218,
> DEC-0091, DEC-0205). Last quarter we moved to Temporal; the migration
> is done for billing but not for webhooks. Assuming we're touching
> webhooks now — confirm or correct?*

This is the most underrated benefit of Braingent. It catches half the
mistakes before they happen.

## IV. Work the task

Normal engineering. The agent edits files, runs tests, opens PRs. Memory
isn't in the way; it's just the floor everything stands on.

If the agent realizes mid-task that it needs more memory, it searches
again. There's no penalty for repeated lookups — it's all local files.

## V. After meaningful work — capture

The agent captures when:

- The user says *capture this*, *task done*, *save to braingent*, *write
  to braingent*.
- A PR opens or merges.
- A ticket closes.
- A non-obvious decision is made.
- A reusable lesson is identified.
- A code review surfaces durable signal.

The agent picks the right kind (task / decision / review / learning),
copies the matching template, fills in the body and frontmatter, runs
`scripts/validate.sh`, and commits.

See [The Capture Loop](/guides/capture-loop/) for the full ruleset.

## VI. Commit

The capture step ends in a Git commit. Conventional message format:

```
capture: <slug>
capture: 2026-04-12-jobs-runtime-decision
capture: BGT-0142-task
```

If the user is in a working repo (not the memory repo), the agent commits
to *both* — the task record goes into the memory repo, and any code
changes go into the working repo. They're separate commits in separate
repos.

## What the agent never does

The contract is also negative: a Braingent-wired agent **never** stores:

- Secrets, tokens, API keys, credentials.
- Raw chat transcripts.
- Sensitive personal data (anything you wouldn't push to a code repo).
- Speculative roadmap content the user hasn't actually decided on.

If you see any of those slipping into a record, that's a bug in the
prompt or the agent — not a feature of Braingent.

## When agents disagree with each other

Two agents working in parallel may capture overlapping records. That's
fine. They're plain Markdown — `git diff` shows the difference, the
human reconciles, and you keep the better version. There's no
synchronization layer to get out of sync.

For *active* multi-agent work — where two agents are operating on the
same task at the same time — see [Multi-Agent
Coordination](/guides/multi-agent-tasks/).

## Where to go next

- [The Capture Loop](/guides/capture-loop/) — when to capture, what to
  skip.
- [Search & Recall](/guides/search-and-recall/) — how agents (and you)
  query memory.
- [Multi-Agent Coordination](/guides/multi-agent-tasks/) — live tasks
  across agents.
