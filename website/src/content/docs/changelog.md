---
title: Changelog
description: What shipped, when. Newest first.
section: Resources
order: 2
---

Braingent versions the starter pack and the CLI together. Both follow
SemVer. Records you wrote in one version will always read correctly in
the next — frontmatter additions are backwards-compatible, removals are
versioned migrations.

## Latest

### `2026-05-07` — Documentation, public site

- Public docs site at [braingent.dev](https://braingent.dev) — full
  Introduction, Concepts, Guides, Integrations, and Reference sections.
- [QA Test Planning](/guides/qa-test-planning/) flagship workflow
  documented end-to-end.
- [Gather Step partner integration](/integrations/gather-step/) explained
  and recommended.
- Parchment-style docs UI matching the landing aesthetic.

### `2026-04-30` — `qa-generate` v4

- Strict, reviewable QA plans from ticket + memory + evidence.
- Output formats: Markdown, Xray JSON, TestRail CSV, Gherkin.
- Deterministic precheck for AC coverage, duplicates, weak expected
  results, evidence truncation.
- Native [Gather Step](https://gatherstep.dev) integration via
  `--gather-workspace` and `--gather-target`.

### `2026-04-15` — Live multi-agent tasks

- `tasks/active/BGT-NNNN.md` convention for parallel agent coordination.
- `scripts/task-*.sh` helpers for create, claim, comment, status, list,
  and archive.
- Optional local Bun + Astro dashboard renders the live queue.

### `2026-04-01` — Source-indexed synthesis

- `scripts/synthesize.sh` produces synthesis pages with inline citations
  back to source records.
- Topic / repo / project synthesis modes.

### `2026-03-15` — MCP server

- `python3 scripts/mcp_server.py` exposes `braingent_guide`,
  `braingent_find`, and `braingent_get` over MCP.
- Token-efficient retrieval for Claude, Codex, and any MCP-aware agent.

### `2026-03-01` — Helper scripts v3

- `scripts/doctor.sh` health checks (entrypoints, placeholders,
  frontmatter, indexes, tooling).
- `scripts/find.sh` / `scripts/recall.sh`.
- `scripts/new-record.sh` / `scripts/validate.sh` / `scripts/reindex.sh`.

### `2026-02-15` — Starter pack v1.0

- Eight record kinds (task, decision, review, learning, repo, project,
  topic, tool).
- Five memory surfaces formalized.
- Agent entrypoints for Claude, Codex, ChatGPT, Gemini CLI.
- Workflows for index-repo, cleanup-braingent, retrieve-context.

### `2026-01-10` — Public manifesto

- First public release of the Braingent manifesto repo.
- Markdown-only. CLI optional.

## Upgrade notes

Until a packaged update helper exists, compare your memory repo against the
latest `starter-pack/` and copy only the files you want. Always review the Git
diff, then run `scripts/doctor.sh`, `scripts/validate.sh`, and
`scripts/reindex.sh --check`.
