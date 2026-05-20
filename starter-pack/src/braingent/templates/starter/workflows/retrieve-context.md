# Workflow: Retrieve Braingent Context

Build a focused context pack from Braingent before planning, reviewing, or
delegating work. Search structured metadata first, then free-text, then open
only the smallest set of records that directly apply.

## Trigger Phrases

Run this workflow when the user says any of:

- "retrieve braingent context"
- "build a braingent context pack"
- "prepare braingent context"
- "search braingent for this task"
- "what should I read from braingent"
- "check braingent before planning"

Also use this workflow automatically before non-trivial planning, code review,
or implementation when Braingent memory is relevant.

## Pre-Flight

1. Identify likely retrieval keys:
   - organization
   - project
   - repository
   - ticket
   - topic
   - tool
   - person
   - date window
   - exact error strings, APIs, branches, commits, or PRs
2. Read the thin entrypoints:
   - `README.md`
   - `INDEX.md`
   - `CURRENT_STATE.md`
   - `preferences/agent-workflow.md`
   - `preferences/search-recipes.md`
3. Do not read raw imports or archives unless curated records are insufficient.

## Retrieval Steps

1. If you have `scripts/find.sh`, run structured metadata searches first:

   ```bash
   scripts/find.sh ticket=<TICKET>
   scripts/find.sh repo=<repo-slug>
   scripts/find.sh project=<project-slug>
   scripts/find.sh topic=<topic-slug>
   scripts/find.sh kind=decision status=accepted
   ```

   If you do not have `scripts/find.sh`, use `rg` with frontmatter patterns:

   ```bash
   rg "repositories:.*<repo-slug>" --type md
   rg "ticket: <TICKET>" --type md
   rg "record_kind: decision" --type md
   ```

2. Run free-text searches for terms that are not reliable frontmatter:

   ```bash
   rg -n "<error|string|api|branch|feature>" orgs repositories topics tools tickets
   ```

3. Open candidate records in this order:
   - current project/repo profile
   - active or recent task records
   - accepted decisions
   - reusable learnings
   - import summaries
   - raw imports only when the curated record points there and the detail is
     still required

4. Classify the results:
   - `must_read`: records that directly affect the plan or answer
   - `supporting`: useful background, but not required line-by-line
   - `stale_or_verify`: records with old dates, superseded status, or
     assumptions that must be checked
   - `do_not_use`: superseded, draft, raw-only, or otherwise unsafe context
   - `capture_target`: where the completed task should be recorded

5. Produce a compact context pack in the response or handoff:

   ```markdown
   ## Context Pack

   must_read:
   - <path>: <why it matters>

   supporting:
   - <path>: <why it may help>

   stale_or_verify:
   - <path>: <what must be checked>

   do_not_use:
   - <path>: <why not>

   capture_target:
   - <path or suggested directory>
   ```

6. If subagents are used, pass only the context pack plus the specific task.
   Subagents should not independently reread the whole memory repo unless
   their assignment is explicitly to audit memory coverage.

## Output Rules

- Cite file paths when memory affects a recommendation or plan.
- Distinguish fact from inference.
- Keep the context pack short enough to be useful in an agent handoff.
- Prefer current durable records over raw transcripts.
- If evidence conflicts, report the conflict instead of silently picking one.

## Failure Modes

- **No structured hit:** use `rg`, then propose a new record if the context
  should exist.
- **Too many hits:** narrow by project, repo, ticket, status, or date window.
- **Only raw imports found:** summarize the useful fact into a durable record
  before relying on it repeatedly.
- **Conflicting records:** prefer current accepted decisions and active
  profiles, but cite the conflict and create a follow-up if human judgment is
  needed.
- **Likely secret or private data:** stop and report file path and line number
  only; do not quote the sensitive value.
