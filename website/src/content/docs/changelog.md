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
  `--gatherstep`.

### `2026-04-15` — Live multi-agent tasks

- `tasks/active/BGT-NNNN.md` convention for parallel agent coordination.
- `task-*` CLI commands for create, claim, status, question, block,
  close, list, archive.
- Optional local Bun + Astro dashboard renders the live queue.

### `2026-04-01` — Source-indexed synthesis

- `braingent synthesize` produces synthesis pages with inline citations
  back to source records.
- Topic / repo / project synthesis modes.

### `2026-03-15` — MCP server

- `braingent mcp serve` exposes `braingent_guide`, `braingent_find`, and
  `braingent_get` over MCP.
- Token-efficient retrieval for Claude, Codex, and any MCP-aware agent.

### `2026-03-01` — CLI v3

- `braingent doctor` health checks (entrypoints, placeholders,
  frontmatter, indexes, tooling).
- `braingent find` / `recall` / `search` / `get`.
- `braingent capture` / `validate` / `reindex`.

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

Run `braingent update --path <your-memory-repo>` to apply starter-pack
changes. The command always shows a plan before mutating files; local
edits win unless you explicitly accept a template change.
