---
title: Changelog
description: What shipped, when. Newest first.
section: Resources
order: 2
---

Braingent versions the starter template and the CLI together. Both follow
SemVer. Records you wrote in one version will always read correctly in the
next; frontmatter additions are backwards-compatible and removals are versioned
migrations.

## Latest

### `12 November 2026`: `1.8.0`

- **`keywords` field.** A record may carry `keywords: [...]`: other words someone would search by, such as the everyday name for an internal term. Search indexes them above body text. Do not repeat words already in the title. The decision and learning templates include the field; add it to `allowed_fields` and `list_fields` in your own `preferences/taxonomy.yml` when you upgrade.
- **Merged rewordings.** `braingent search "<question>" --also "<another wording>"` (repeatable), and `also` on `braingent_search`, run each wording and merge the results into one ranked list by reciprocal rank. Use it when a question may share no words with its record.
- **Decisions and learnings rank above work logs.** Search weights `decision` and `learning` records 1.5 times, so a ruling is not buried under the tasks and reviews that mention the same words. Every match is now ranked before the list is cut, where 1.6.0 ranked only the first few dozen. Exact ticket and PR matches still come first.
- **Default timezone is no longer hardcoded.** `new-record.sh` falls back to `TZ` and then `UTC`. `CURRENT_STATE.md` and `task-new` use `[daily] timezone` from the config, then `UTC`. Set `BRAINGENT_TIMEZONE` or `[daily] timezone` to keep your own zone.
- **`daily-status` counts work with no epic.** The JSON output gains `no_epic: {spawned, untouched}`, and the By epic list ends with a `no epic` line when there is any.
- The search index gains a column, so `.braingent.db` rebuilds itself on the first search after the upgrade.
- **`braingent capture`.** Creates a record through `scripts/new-record.sh` after three checks. The same `--source` at the same `--revision` is already recorded: it reports that record and writes nothing. Similar records exist: it lists them. For a decision, live decisions on a similar subject exist: it stops with exit 3 until you pass `--supersedes <path>`, `--coexists-with <path>` or `--unrelated`. Only `--supersedes` changes another record, marking it superseded and linking both ways. `--check` reports without writing.
- **`coexists_with` and `source_revision` fields.** A decision that names another in `coexists_with` no longer raises the implicit-conflict warning for that pair. Add both fields to `allowed_fields`, and `coexists_with` to `list_fields`, in your own `preferences/taxonomy.yml`.
- **Validation baseline.** `braingent validate --update-baseline` records today's warnings in `.braingent/validation-baseline.json`. After that, `validate` prints a count per warning class and lists only warnings that are new since the baseline. `--verbose` lists everything. Without a baseline file nothing changes. Errors fail as before.
- **Safe record updates.** Capture stays inside indexed memory folders, serialises retries of the same source and checks all matching decisions even without full-text search. Existing records are backed up before replacement. Consolidation proposals expire when their target changes; competing or cyclic successors need a manual decision, and a failed batch restores earlier writes.
- **Concurrent daily work.** Stale-queue updates preserve other agents' items, notes reactivate old work without counting it as newly spawned, and inherited weekly priorities protect their items before the new weekly file exists.
- **Reconciliation previews change no files.** Apply respects the requested day and preserves events added during a lookup. Ambiguous repository owners remain unknown until an explicit owner is supplied. Warning baselines track individual warnings, so replacing an old warning with a different one is reported as new.
- **Merged is not done.** The daily log gains `merged`, `deployed` and `verified`. Merged and deployed items sit under "Merged, not yet verified", stay open and are carried over; `verified` or `done` closes them.
- **Stale queue, off by default.** With `[daily] stale_after_days` set, unfinished items nobody has touched for that long leave the daily log for `daily/stale.md`. They are never closed by age, blocked items and items under a weekly priority's epic stay, and any new event brings an item back.
- **`braingent dream`.** Lists consolidation proposals and changes nothing: a record whose `superseded_by` is set but whose status is not `superseded`, a superseding record its target does not point back to, a link that resolves to no record, two records of the same source and revision, and live decisions on one subject with no stated relation. `--apply <id>` makes the stated frontmatter change for the mechanical ones, after regenerating the proposal so a record edited since is never overwritten. `--reject <id>` hides one for good.
- **`braingent daily-reconcile`.** Looks up the pull request behind each open daily item. With `--apply`, an item whose pull request has merged is logged as `merged`, which stays open until `verified` or `done`. Nothing is closed, a failed lookup is reported as unknown and leaves the item alone, and items beyond `--limit` are counted, not skipped silently.
- **Weekly priorities can name epics.** Write `epic:<slug>` in a priority line, or use `weekly-add --epic <slug>`. The weekly plan then shows done, open and spawned per priority and how much was spawned outside them. The daily status line gains closed today, net, and spawned outside weekly priorities.

### `12 November 2026`: `1.7.1`

- **Equal-status config entries preserve page edits.** When a page and PR have the same status, the page's conflicting field values win, including `dormant` and `not-needed`. Missing fields are still filled from the PR. Distinct statuses retain their existing precedence.

### `12 November 2026`: `1.7.0`

- **Search a second corpus.** `[[search.corpus]]` in `.braingent/config.toml` names a read-only Markdown folder, such as a plans repository, that `search` and `braingent_search` include beside the records. Hits say which corpus they came from, have class `reference`, and give the file's absolute path. A ticket key in a document's file name or title gets the same exact-identifier boost as one in a record's metadata.
- **Noise stays out.** Hidden folders, `raw/`, backup copies, `node_modules`, `site-packages`, folders holding a code project and files over `max_bytes` are not indexed. Add your own globs with `exclude`.
- **Deleted and renamed files.** The index stores a hash of each document and rebuilds when the set of files changes, and every hit is checked on disk, so a deleted document is never returned.
- **Search hits carry `corpus`.** Record hits say `records`.

### `12 November 2026`: `1.6.0`

- **`braingent search`.** Ranked full-text search over titles, identifiers, metadata and bodies, with the same `key=value` filters as `find`. Any word may match. A ticket key or PR reference in a record's metadata outranks a mention in a body. Each hit says whether it is a `candidate`, `stale_or_verify` or `do_not_use`, and superseded records rank lower without being hidden. Also available over MCP as `braingent_search`.
- **Unknown filters fail.** `find`, `recall`, `search` and `braingent_find` now reject a filter key that is not a known field, with the nearest valid key, and exit 2. Before, a typo such as `tickets=EX-1` returned zero results. Scripts that passed a field outside `allowed_fields` must add it to `preferences/taxonomy.yml`.
- **Ambiguous short names fail.** `repo=<name>` or `project=<name>` matching more than one entry is an error that lists the candidates. Before, it searched for a name that did not exist and returned nothing.
- **Hints on empty results.** When nothing matches and a filter names an organisation, person, topic, tool or repository with no directory, similar names are printed to stderr.
- **The SQLite index is replaced atomically** and gains a full-text table. `.braingent.db` stays a disposable cache: delete it and the next `search` or `reindex` rebuilds it.

### `12 November 2026`: `1.5.0`

- **Epic pages are `record_kind: epic`.** New pages carry `record_kind: epic` and an `epic:` list holding their own id. Pages written by 1.2.0 to 1.4.0 (`record_kind: profile`, scalar `epic`) still validate, with a deprecation warning; change those two lines to clear it.
- **`labels` and `parent_epic` are epic-only.** The taxonomy gains `kind_allowed_fields`, and these two fields now warn on any record that is not an epic page. Move them off other records, or add them back under `allowed_fields` in your own `preferences/taxonomy.yml`.
- **Daily-log epic position.** `--epic` is now written after the ref: `- HH:MM · agent · kind · ref · epic:<slug> · text`. Lines with ` · epic:<slug>` at the end still parse, so existing logs keep their per-epic counts.
- **Config-ledger owners and search size.** `[config_ledger] owners` sets the default `--owner` list. The labelled-PR search asks for up to 1,000 results, GitHub search's ceiling, instead of 100; an epic with 1,000 or more labelled PRs still refuses to sync rather than miss items.
- **Ledger precedence, stated.** When an epic page and a PR body hold the same item, the side whose status is further along (`pending`, `pr-open`, `applied`, `verified`) supplies the whole item, and the other side only fills blank fields. On equal status the page wins, so a PR body corrected after its first sync does not change the page; edit the page instead. `not-needed` and `dormant` override only a `pending` item.
- **`new-record.sh` fills its own templates.** Titles of interaction, version and ticket-stub records, and `ticket_system`, are now filled instead of left as placeholders.
- **Wrappers.** `scripts/daily-log.sh` and `scripts/daily-status.sh` join `weekly.sh`.

### `28 October 2026`: `1.4.0`

- **Epic goals.** `braingent new epic --goal "<one line>"` writes the goal into the new epic page.
- **Config-ledger limits.** `default`, `target` and `verify` accept up to 2,000 characters, so a full verification command fits. Identifier fields keep the 300-character cap, and errors name the item and field.
- **Skipped PRs fail loudly.** `config-ledger` still syncs every PR that parses, then lists each skipped PR with the reason and exits 1, so a dropped config item cannot go unnoticed.
- **Website dependencies.** Patched `undici`, `vite` and `zod` for high-severity advisories.

### `12 October 2026`: `1.3.0`

- **Weekly plan.** `braingent weekly` and `braingent weekly-add` keep one human-written `weekly/YYYY-Www.md` per ISO week with Priorities, Notes and Not this week, plus a Progress block rolled up from the week's daily logs. Unticked priorities and notes carry into the next week. Agents read it before choosing work, and `workflows/daily-pm.md` reports against it.
- **Carry-over and agent entry points.** Plain notes survive carry-over alongside unticked checklists. Claude and ChatGPT starter instructions also load the weekly plan before choosing work.

### `7 October 2026`: `1.2.0`

- **Epics.** An epic is an ad hoc anchor for work that spans many tickets and repositories. It has a page at `orgs/<org>/epics/epic--<org>--<slug>/`, an optional `epic:` list on records, a tracker and PR label `epic:<slug>`, and `braingent new epic` to scaffold it. Dangling epic references fail validation.
- **Config-to-enable ledger.** A `config-to-enable/v1` YAML block records each setting that must be set before work is live, where it lives and its status. `braingent config-ledger` merges the blocks in labelled PR bodies with the epic page and can `--sync` the page.
- **Config drift.** `braingent config-drift --contracts <dir> --deployed <dir>` reports environment keys present in one place and missing from the other.
- **Epic indexes and queries.** `reindex` writes `indexes/epics.md` and `indexes/config-ledger.md`, adds an Active epics section to `CURRENT_STATE.md`, and fills `record_epics` and `config_items` in the SQLite cache. `find`, `recall`, `synthesize` and MCP `braingent_find` accept `--epic`.
- **Daily log.** `braingent daily-log --epic` tags events, the status block rolls up spawned work per epic, and the sprawl warning names the epics behind it. Lines without an epic are unchanged.
- **Fix.** `braingent --root <dir> reindex` writes the SQLite cache under the selected root instead of the directory the package was imported from.

### `6 October 2026`: `1.1.0`

- **Daily log.** `braingent daily-log` and `braingent daily-status` keep one append-only `daily/YYYY-MM-DD.md` per day across every agent, with a generated ongoing/review/blocked/todo/done view, carry-over of unfinished work, and a sprawl warning at `[daily] sprawl_threshold`. `workflows/daily-pm.md` adds a PM catch-up agent that reconciles GitHub, the issue tracker, and Braingent records.
- **Reliable concurrent logging.** Readers and writers share file locks, human Goals are preserved, and only Log entries affect status. Windows uses its native locking backend.
- **Deterministic indexes.** `CURRENT_STATE.md` reports the latest source-record date, so unchanged indexes remain current across midnight.
- **CLI version string.** `braingent --version` reports the package version instead of a leftover `0.1.0`.
- **Dependencies.** Refreshed Python tooling, MCP, website and example dashboard packages; Python 3.14 joins the supported CI matrix.


### `17 September 2026`: `1.0.1`

- **PyPI republish.** `1.0.0` is already on PyPI (26 June 2026) and cannot be replaced. This patch ships the post-1.0 work: MCP SDK 2.2 (`MCPServer`), `braingent factcheck`, token-efficient retrieval, and hatchling metadata 2.5 with a matching publish action.

### `2026-06-26` — `1.0.0`

- **Stable package metadata.** The `braingent` Python package is now versioned
  as `1.0.0` and marked `Production/Stable` on PyPI.
- **Stable starter-template baseline.** The packaged starter template manifest
  now reports `1.0.0`, making the current memory repo shape the first stable
  baseline for `braingent init` and `braingent update`.
- **Release baseline.** This release includes the hardened publishing pipeline,
  optional `config.toml`, built-in secret scanning, MCP retrieval tools, QA test
  planning, and the refreshed Node 24 website/example dependency baseline.

### `2026-06-16` — `0.1.1`

- **Optional `config.toml`.** `braingent` now reads `.braingent/config.toml`
  (repo-local) and `~/.braingent/config.toml` (user-level). Supports
  `[safety]` forbid patterns/paths enforced by `doctor`, `[doctor]`/`[recall]`
  default knobs, and `[task_ids]` prefix/pad. See
  [Configuration](/reference/configuration/).
- **Built-in secret scanning in `doctor`.** Always-on patterns for AWS,
  GitHub, Google, and OpenAI/Anthropic keys plus PEM private keys; config can
  add more.
- **Hardening.** `braingent_get` (MCP) is restricted to Markdown records;
  release tooling pins all GitHub Actions by SHA and verifies build provenance
  before publishing.

### `2026-05-20` — Python package flow

- `pipx install braingent` is the primary install path.
- `braingent init` creates a private memory repo from the packaged template.
- `braingent update` reports add/update/conflict status before applying
  starter-template changes.
- `braingent qa generate` ships the QA plan generator with Markdown, Xray JSON,
  TestRail CSV, and Gherkin outputs.
- `braingent mcp serve --path <repo>` starts MCP retrieval tools for agents.
- Release checks now include package build, wheel smoke, metadata validation,
  and extracted-artifact safety scanning.

### `2026-05-07` — Documentation, public site

- Public docs site at [braingent.dev](https://braingent.dev) with Introduction,
  Concepts, Guides, Integrations, and Reference sections.
- [QA Test Planning](/guides/qa-test-planning/) flagship workflow documented
  end-to-end.
- [Gather Step partner integration](/integrations/gather-step/) explained and
  recommended.
- Parchment-style docs UI matching the landing aesthetic.

### `2026-04-30` — QA generation v4

- Strict, reviewable QA plans from ticket + memory + evidence.
- Output formats: Markdown, Xray JSON, TestRail CSV, Gherkin.
- Deterministic precheck for AC coverage, duplicates, weak expected results,
  and evidence truncation.
- Native [Gather Step](https://gatherstep.dev) integration via
  `--gather-workspace` and `--gather-target`.

### `2026-04-15` — Live multi-agent tasks

- `tasks/active/BGT-NNNN.md` convention for parallel agent coordination.
- `braingent task-*` commands for create, claim, comment, status, list, and
  archive.
- Optional local Bun + Astro dashboard renders the live queue.

### `2026-04-01` — Source-indexed synthesis

- `braingent synthesize` produces synthesis pages with inline citations back to
  source records.
- Topic / repo / project synthesis modes.

### `2026-03-15` — MCP server

- `braingent mcp serve` exposes `braingent_guide`, `braingent_find`, and
  `braingent_get` over MCP.
- Token-efficient retrieval for Claude, Codex, and any MCP-aware agent.

### `2026-03-01` — Core memory commands

- `braingent doctor` health checks.
- `braingent find` / `braingent recall`.
- `braingent validate` / `braingent reindex`.

### `2026-02-15` — Starter template

- Eight record kinds: task, decision, review, learning, repo, project, topic,
  tool.
- Five memory surfaces formalized.
- Agent entrypoints for Claude, Codex, ChatGPT, Gemini CLI.
- Workflows for index-repo, cleanup-braingent, retrieve-context.

### `2026-01-10` — Public manifesto

- First public release of the Braingent manifesto repo.

## Upgrade Notes

Check available starter-template updates with:

```bash
braingent update ~/Documents/repos/braingent --dry-run
```

Apply non-conflicting updates with:

```bash
braingent update ~/Documents/repos/braingent --write
braingent doctor
braingent validate
braingent reindex --check
```
