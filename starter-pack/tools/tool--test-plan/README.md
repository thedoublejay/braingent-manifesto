# test-plan

Braingent-owned manual QA test-plan generator.

The tool reads ticket/spec text, compact Braingent memory, and optional Gather
Step evidence, then writes a human-reviewable Markdown QA reference. Gather Step
stays the code evidence layer; Braingent owns the workflow, prompts, critic
rubric, and capture loop.

## Quick start

```bash
bash scripts/qa-generate.sh \
  --ticket-key SYN-001 \
  --no-diff \
  tools/tool--test-plan/examples/synthetic-ticket.md
```

By default output goes to `.test-plans/<ticket-key>--test-plan.md`.

## Common modes

Pre-implementation planning:

```bash
bash scripts/qa-generate.sh \
  --ticket-key ACME-123 \
  --implementation-state pre-implementation \
  --no-diff \
  --repo repo--example--owner--repo \
  path/to/ticket.md
```

Post-implementation with Gather Step evidence:

```bash
bash scripts/qa-generate.sh \
  --ticket-key ACME-123 \
  --implementation-state post-implementation \
  --diff main..HEAD \
  --gather-workspace /path/to/workspace \
  --gather-target ChangedSymbol \
  --projection-target changedField \
  --repo repo--example--owner--repo \
  path/to/ticket.md
```

Post-implementation with a prebuilt QA evidence pack:

```bash
bash scripts/qa-generate.sh \
  --ticket-key ACME-123 \
  --implementation-state post-implementation \
  --evidence-pack path/to/qa-evidence.json \
  --emit-format markdown \
  --repo repo--example--owner--repo \
  path/to/ticket.md
```

## Current contract

- Requires acceptance criteria by default; `--allow-missing-ac` permits
  product-intent-derived `REQ-*` cases only when the ticket is clear enough.
- Prefers native Gather Step `qa-evidence --json` output when
  `--gather-workspace` and implementation evidence are supplied.
- Accepts `--evidence-pack` for an already generated `qa-evidence.v1` manifest.
- Emits `markdown`, `xray-json`, `testrail-csv`, or `gherkin` from the same
  scenario model via `--emit-format`.
- Defaults to a lenient `--budget-tokens 160000` evidence envelope because QA
  plans are expected to be strict and long; truncation is surfaced as a gap
  instead of silently shortening test cases.
- Keeps black-box scenarios product/source driven.
- Adds white-box scenarios only when implementation evidence is requested and
  collected.
- Uses compact Braingent memory retrieval, not full-index reads.
- Runs Gather Step `status --json` and `doctor --json` before trusting white-box
  evidence.
- Marks `Both`, `AC-only`, and `Code-only` classifications explicitly.
- Emits spec rows, AC coverage, an uncovered-AC section, and a reverse
  traceability index.
- Emits gaps instead of silently filling missing AC, design context, or Gather
  Step evidence.
- Surfaces manifest truncation and unsupported discovery as gaps, never as
  complete coverage.

## Better alternatives already baked in

- Use source registry rows instead of prose-only citations.
- Use `.test-plans/` as ignored local output so generated drafts do not pollute
  durable memory.
- Use deterministic local generation and precheck for the CLI; prompts are
  stored for agent review and optional LLM orchestration.
- Keep evidence command output bounded with `--budget-tokens` or the lower-level
  `--evidence-budget-bytes` override.
- Prefer Gather Step MCP tools for future steady-state orchestration; the local
  CLI uses bounded JSON commands as the first portable V1 surface.

## Integration edges

- Existing-test discovery depends on Gather Step `qa-evidence` rows or direct
  code review naming relevant tests.
- Current-page, screenshot, and Figma/design extraction stay outside Gather Step;
  pass them as sources and mark `--design-context` when supplied.
- LLM critique is represented by `prompts/critic.md`; the local CLI performs the
  deterministic precheck and leaves model-backed critique to agent orchestration.

## Records

Create durable records under `records/` only when the workflow itself changes or
a generated test plan produces a reusable QA learning.
