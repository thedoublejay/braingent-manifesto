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
