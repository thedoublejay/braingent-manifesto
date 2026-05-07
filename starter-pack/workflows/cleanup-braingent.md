# Workflow: Clean Up Braingent

Run recurring maintenance on Braingent without drifting away from the core model:
Markdown records are canonical, frontmatter drives retrieval, generated artifacts
are disposable, and derived synthesis must cite durable source records.
Optional live task files are coordination state, not durable source records.

## Trigger Phrases

Run this workflow when the user says any of:

- "clean up braingent"
- "cleanup braingent"
- "tidy braingent"
- "run braingent maintenance"
- "daily braingent cleanup"
- "weekly braingent cleanup"
- "deep clean braingent"

If the user does not specify depth, run **standard cleanup**: daily checks plus
weekly review, report findings, and ask before any destructive or broad rewrite.

## Research Basis

This workflow combines these practices:

- Docs-as-code: treat documentation like software with Git, review, linting,
  link checks, and CI-style quality gates.
  Source: <https://docs.gitlab.com/development/documentation/testing/>
- Markdown structure linting: use markdownlint-style checks to keep Markdown
  predictable.
  Source: <https://docs.gitlab.com/development/documentation/testing/markdownlint/>
- Prose/style linting: use Vale-style checks for consistent terms and tone.
  Source: <https://www.elastic.co/docs/contribute-docs/vale-linter>
- Link checking: use a tool such as lychee for Markdown and web links.
  Source: <https://github.com/lycheeverse/lychee>
- Spell checking: use CSpell or an equivalent with a project dictionary, not
  blind manual edits.
  Source: <https://cspell.org/docs/getting-started>
- Technical writing style: prefer clarity, consistency, descriptive links,
  active voice, accessible structure, and unambiguous dates.
  Source: <https://developers.google.com/style/highlights>
- Knowledge-base governance: assign ownership, review on a cadence, archive
  outdated material, and track versions.
  Source: <https://support.zendesk.com/hc/en-us/articles/4408831743258-Best-practices-Developing-content-for-your-knowledge-base>
- Karpathy LLM Wiki pattern: keep raw sources immutable, maintain a Markdown
  synthesis layer, run query and lint operations, and keep a parseable log.
  Source: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>

## Operating Rules

- **Report first.** Cleanup starts by producing findings. Only edit when the fix
  is clearly mechanical or the user approves.
- **Do not rewrite historical records.** Immutable task, review, decision,
  learning, and interaction records can receive typo/link fixes, but not
  narrative rewrites.
- **Do not delete raw imports silently.** Raw import removal needs an explicit
  retention check and a linked curated summary.
- **Do not make generated synthesis canonical.** Compiled pages and recall packs
  are derived aids. Durable records remain source of truth.
- **Do not make live tasks canonical.** Completed `agent-task` files should link
  durable records with `agent_task: BGT-NNNN`.
- **Keep diffs small.** Separate mechanical fixes, content reorganization,
  schema changes, and generated index updates.
- **Do not capture secrets.** If cleanup finds secrets, stop and report without
  quoting the secret value.

## Schedule

### Daily Cleanup: 5-10 Minutes

Purpose: keep the repo healthy after normal work.

Run:

```bash
git status --short
scripts/validate.sh
scripts/reindex.sh --check
scripts/find.sh status=active
test ! -f scripts/task-list.sh || scripts/task-list.sh --count
rg -n "^- \[ \]" --type md orgs repositories topics tools tickets inbox imports
rg -n "TODO|FIXME|PLACEHOLDER|TBD|XXX" --type md .
```

Optional local tools if installed:

```bash
markdownlint "**/*.md"
vale .
cspell lint "**/*.md"
lychee --no-progress README.md INDEX.md CURRENT_STATE.md preferences workflows orgs repositories topics tools tickets
```

Daily output:

- validation status;
- stale generated-index status;
- live task counts if the optional task module is enabled;
- active records needing attention;
- unchecked follow-ups;
- obvious placeholders or TODOs;
- optional style/spell/link findings.

Daily edit policy:

- Safe to fix typos, broken relative links, stale generated indexes, and obvious
  formatting issues.
- Ask before moving files, changing frontmatter semantics, archiving records, or
  rewriting summaries.

**ELI5:** Daily cleanup is a quick sweep: check the floor, empty obvious trash,
and write down anything that needs deeper work.

### Weekly Cleanup: 30-45 Minutes

Purpose: prevent memory decay and retrieval drift.

Run the daily checks, then add:

```bash
scripts/find.sh kind=decision status=accepted
scripts/find.sh kind=summary
rg -n "^last_reviewed:|^last_revalidated:|^raw_retained_until:" .
rg -n "record_kind: agent-task|status: blocked|status: in-progress|status: triage" tasks indexes 2>/dev/null
rg -n "agent_task: BGT-[0-9]{4}" orgs repositories topics tools tickets 2>/dev/null
rg -n "source_location: /Users/|local_path: /Users/" .
rg -n "<your-org-name>|<your-github-username>|<workspace-root>" . 2>/dev/null
```

Review:

- import summaries missing organization/project/repository metadata;
- repo profiles with old `last_reviewed`;
- learnings with old `last_revalidated`;
- active tasks that should now be completed, blocked, or superseded;
- live tasks that are stale: triage over 30 days, blocked over 30 days, or in-progress with no activity for 14 days;
- completed live tasks missing durable `agent_task: BGT-NNNN` links;
- raw imports past `raw_retained_until`;
- private/local names in public-facing material;
- duplicated records that should be linked or superseded;
- records that need backlinks from repo/project/topic pages.

Weekly output:

- one short cleanup report in the response;
- a list of safe fixes applied;
- a list of edits needing user approval;
- suggested captures, synthesis updates, or follow-up tasks.
- a task hygiene summary if `tasks/` exists.

**ELI5:** Weekly cleanup checks whether the memory map still points to the right
places and whether old notes need labels like "verified", "superseded", or
"needs review".

### Monthly Cleanup: 60-90 Minutes

Purpose: keep Braingent useful as a compounding memory system.

Run daily and weekly checks, then add a synthesis pass:

1. Pick 1-3 high-value areas:
   - a project with many active records;
   - a repo used often;
   - a topic with repeated decisions or learnings.
2. Create or update a derived synthesis page only if the repo has a `compiled/`
   or `synthesis/` convention.
3. Every synthesis claim must cite source records by path.
4. Mark generated or derived pages clearly:

   ```markdown
   <!-- Derived synthesis. Durable records remain source of truth. -->
   ```

5. Run a drift check:
   - claims without source paths;
   - source paths that no longer exist;
   - accepted decisions that appear to conflict;
   - profiles not linking important recent records;
   - summaries no longer discoverable through structured search.

Monthly output:

- a synthesis freshness report;
- suggested new `compiled/` or `synthesis/` pages;
- stale or conflicting durable records needing human judgment;
- recall-eval candidates from real tasks.

**ELI5:** Monthly cleanup turns scattered receipts into a cited study guide, but
the receipts still remain the truth.

### Quarterly Cleanup: 2-3 Hours

Purpose: prevent structural drift.

Review:

- taxonomy fields and templates;
- `scripts/new-record.sh` or successor capture tooling;
- validation coverage;
- generated index shape;
- raw import retention policy;
- active workflows;
- global agent entrypoint drift between Claude, Codex, and ChatGPT;
- task protocol drift between `tasks/CLAUDE.md`, `preferences/agent-task-protocol.md`, and generated indexes;
- dashboard schema-drift checks if a dashboard exists;
- recall quality against real tasks;
- whether any workflow should be promoted, simplified, or archived.

Quarterly output:

- one decision or task record if a structural change is made;
- a small maintenance backlog;
- any rejected cleanup ideas with rationale;
- updated `CURRENT_STATE.md` if the repo operating model changed.

**ELI5:** Quarterly cleanup checks whether the filing system itself still fits
how the work is actually being done.

## Roadmap: Recall And Synthesis Automation

The following capabilities are planned, not yet implemented. Document them as
optional or future work.

### Phase 1: Stabilize Maintenance Checks

Add or run a first-class health helper such as `scripts/doctor.sh` that reports:

- validation failures;
- stale indexes;
- summaries missing retrieval metadata;
- profiles with old `last_reviewed`;
- learnings with old `last_revalidated`;
- expired `raw_retained_until`;
- broken source paths in derived synthesis;
- draft/quarantined records that would be served by recall;
- public-safety leaks in public-facing packages.
- live task staleness and missing promotion links.

**ELI5:** Put the recurring checklist into one command so cleanup is repeatable,
not dependent on memory.

### Phase 2: Add Recall Packs

Add or run `scripts/recall.sh --json` so agents can retrieve:

- `must_read`;
- `supporting`;
- `stale_or_verify`;
- `do_not_use`;
- `capture_target`.

Daily cleanup should only verify recall tooling health. Weekly cleanup should
sample one or two recent tasks to see whether recall finds the right records.

**ELI5:** Recall is the briefing packet. Cleanup checks whether the packet still
pulls the right pages.

### Phase 3: Add Derived Synthesis

Create `compiled/` or `synthesis/` only after recall and doctor checks exist.
Synthesis pages must cite durable source records and must never become the only
home for a fact.

Recommended structure:

```text
compiled/
  projects/
  repositories/
  topics/
  maintenance-log.md
```

Monthly cleanup updates these pages. Daily cleanup does not.

**ELI5:** The compiled layer is a set of cited summaries. It is faster to read,
but it is not allowed to invent or silently replace history.

### Phase 4: Add Maintenance Scheduling

Preferred order:

1. Manual trigger with "clean up braingent".
2. Local script wrapper, for example `scripts/cleanup.sh --daily`.
3. Local scheduler after the script is stable.

Example local cron entry:

```cron
15 8 * * * cd /path/to/braingent && scripts/cleanup.sh --daily >> /tmp/braingent-cleanup.log 2>&1
```

Example macOS `launchd` direction:

- create a user LaunchAgent that runs `scripts/cleanup.sh --daily`;
- log to `/tmp/braingent-cleanup.log`;
- keep the job report-only unless the user explicitly enables auto-fix.

Do not enable auto-commit by default.

**ELI5:** Start by running cleanup by hand. Schedule it only after the command is
boring and safe.

## Standard Cleanup Procedure

Use this when the user says "clean up braingent" without a mode.

1. Pre-flight:
   ```bash
   git status --short
   ```
   If there are unrelated changes, report them and avoid staging or rewriting
   those files.

2. Run mechanical checks:
   ```bash
   scripts/validate.sh
   scripts/reindex.sh --check
   test ! -f scripts/task-list.sh || scripts/task-list.sh --count
   ```

3. Scan for maintenance signals:
   ```bash
   scripts/find.sh status=active
   rg -n "record_kind: agent-task|status: blocked|status: in-progress|status: triage" tasks indexes 2>/dev/null
   rg -n "^- \[ \]" --type md orgs repositories topics tools tickets inbox imports
   rg -n "^last_reviewed: 202" .
   rg -n "^raw_retained_until:" imports orgs topics repositories tools tickets inbox
   rg -n "TODO|FIXME|PLACEHOLDER|TBD|XXX" --type md .
   ```

4. Run optional installed tools:
   ```bash
   command -v markdownlint >/dev/null 2>&1 && markdownlint "**/*.md"
   command -v vale >/dev/null 2>&1 && vale .
   command -v cspell >/dev/null 2>&1 && cspell lint "**/*.md"
   command -v lychee >/dev/null 2>&1 && lychee --no-progress README.md INDEX.md CURRENT_STATE.md preferences workflows
   ```

5. Apply safe fixes only:
   - generated indexes stale: run `scripts/reindex.sh`;
   - obvious typo in mutable docs: fix with a minimal patch;
   - broken relative link with one clear target: fix with a minimal patch;
   - placeholder in public-facing docs: replace or report.

6. Report before larger work:
   - moving records;
   - changing taxonomy;
   - editing historical narrative;
   - closing or archiving live tasks;
   - deleting raw imports;
   - rewriting summaries;
   - committing while unrelated changes are present.

7. If meaningful cleanup was completed, capture a task record unless the cleanup
   was purely generated-index refresh with no decisions.

## Deep Cleanup Procedure

Use this when the user says "deep clean braingent" or asks for monthly or
quarterly maintenance.

1. Run standard cleanup.
2. Review all active task records.
3. Review optional live tasks for stale status, blockers, dependencies, missing closeout, and missing durable promotion.
4. Review all accepted decisions for supersession candidates.
5. Review all summaries for retrieval completeness.
6. Review repo profiles for important-record backlinks.
7. Review topic pages for repeated patterns that deserve synthesis.
8. Propose a small backlog instead of doing broad rewrites immediately.

Deep cleanup should end with one of:

- no changes, report only;
- small mechanical commit;
- one planned task record for the backlog;
- one decision record if the operating model changed.

## Outputs

Every cleanup run should produce:

- mode: daily, weekly, monthly, quarterly, standard, or deep;
- commands run;
- pass/fail status;
- safe fixes applied;
- findings needing approval;
- live task hygiene if `tasks/` exists;
- suggested follow-ups;
- whether a capture record was created.

## Cost And Limits

- Daily: 5-10 minutes.
- Weekly: 30-45 minutes.
- Monthly: 60-90 minutes.
- Quarterly: 2-3 hours.
- Link checking external URLs can be slow or flaky. Do not block cleanup solely
  on transient external-link failures.
- Grammar and style tools produce false positives. Treat them as suggestions,
  especially in record bodies that preserve historical wording.

## Failure Modes And Recovery

- **Dirty worktree:** avoid staging unrelated files. Report what is already
  modified before cleanup.
- **Validation failure:** fix validation before style or synthesis work.
- **Stale indexes:** run `scripts/reindex.sh`, then `scripts/reindex.sh --check`.
- **Task schema drift:** fix task frontmatter or dashboard parsing, then rerun reindex and dashboard checks if present.
- **Optional tools missing:** report skipped checks and continue.
- **Possible secret found:** stop, report file path and line number only, do not
  quote secret value.
- **Large rewrite temptation:** stop and create a planned task record instead.

## Anti-Goals

- Do not make cleanup an excuse for broad refactors.
- Do not auto-delete raw imports.
- Do not let LLM-generated synthesis replace durable records.
- Do not let live task files replace durable records.
- Do not auto-commit unless the user explicitly asks for it.
- Do not optimize for perfect grammar at the cost of preserving evidence.
- Do not add cloud memory tools as part of routine maintenance.
