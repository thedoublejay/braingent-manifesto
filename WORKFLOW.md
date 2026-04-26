# Workflow

Braingent is a work loop, not just a folder layout.

## The Daily Loop

### 1. Start With Context

Before planning meaningful work, read:

1. `README.md`
2. `INDEX.md`
3. `CURRENT_STATE.md`
4. `preferences/`
5. Relevant organization, project, repository, topic, tool, ticket, or person records

Then search:

```bash
rg -n "<ticket-or-topic-or-repo-name>" .
```

If you later add a structured search script, use that first and `rg` second.

### 2. Frame The Task

For non-trivial work, state:

- **GOAL:** What problem is being solved.
- **ANALYSIS:** What context matters.
- **APPROACH:** What will be done and why.
- **RISKS:** What could go wrong.
- **ELI5:** A plain-but-technical explanation that makes the work easy to understand without dumbing it down.

When a plan has a summary and phases or breakdowns, add a short **ELI5** after the summary and after each major phase. Assume the reader is technical, but may not have all local context loaded.

Keep this short unless the task needs a full plan.

### 3. Work From Existing Patterns

Use repository profiles, topic records, and prior decisions as defaults.

Do not invent a new convention if the memory already records a working one.

### 4. Capture During Work

Notice facts worth preserving:

- commands that verified the work
- versions
- errors and root causes
- tradeoffs
- rejected options
- PR links
- ticket links
- branch names
- commit hashes
- review findings
- deployment notes
- follow-up risks

### 5. Capture At The End

Create or update a record when:

- a task completes
- a PR opens
- a review finishes
- a ticket moves
- a decision is made
- a surprising bug is diagnosed
- a reusable learning appears
- the user says "capture this" or "task done"

Use the smallest record that preserves the important evidence.

### 6. Commit The Memory

Commit after each meaningful memory update:

```bash
git add .
git commit -m "Capture <short subject>"
```

Keep commits focused. Do not bundle unrelated memory updates.

## Record Selection

| Need | Use |
| --- | --- |
| Planned or completed work | `task` |
| Quick end-of-task capture | `task` minimal |
| Code or design review | `review` |
| Chosen tradeoff | `decision` |
| Reusable lesson | `learning` |
| Tool/framework/model version | `version` |
| Repository facts | `profile` |
| Historical import | `summary` |
| Mixed temporary context | `note` |
| Cross-repo ticket | `ticket-stub` |

## Review Loop

When reviewing code, capture:

- target PR, branch, commit, or diff
- files inspected
- tools or tests run
- findings by severity
- missing tests
- security or privacy risks
- verdict
- follow-ups

Promote reusable review lessons to `topics/`.

## Import Loop

When importing older history:

1. Scan local docs.
2. Scan Git history.
3. Scan PRs if available.
4. Scan tickets if available.
5. Cluster related work.
6. Create summaries, tasks, decisions, and learnings.
7. Do not create one record per commit.
8. Keep raw imports separate from curated records.

## Stuck Protocol

If the same approach fails twice:

1. Stop.
2. State what failed and why.
3. Search memory for related failures.
4. Present two or three options.
5. Ask which path to take.

This prevents silent thrashing and makes the problem visible.
