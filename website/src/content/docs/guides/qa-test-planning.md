---
title: QA Test Planning
description: Generate strict, reviewable QA plans from tickets, Braingent memory, and engineering evidence — output Markdown, Xray JSON, TestRail CSV, or Gherkin.
section: Guides
order: 5
badge: Flagship
---

Most QA planning today happens in a chat window with no traceability —
you paste a ticket, you get a list of test cases, you hope the LLM didn't
hallucinate the acceptance criteria. There's no link back to the engineering
evidence, no link back to prior decisions, and no way to tell why a test
was included.

`scripts/qa-generate.sh` is built differently. It produces a strict,
reviewable QA plan from three real inputs: the ticket, your Braingent
memory, and concrete implementation evidence. Every test case is traceable
back to the source that produced it.

This is Braingent's flagship workflow.

## What it produces

`scripts/qa-generate.sh` emits a single QA plan in your chosen format. All
formats share the same case model:

- **Markdown** — for human review, PR comments, and Confluence pastes.
- **Xray JSON** — direct import into Jira/Xray test repositories.
- **TestRail CSV** — direct import into TestRail.
- **Gherkin** — `.feature` files for BDD frameworks.

Same cases, four exports. Pick whichever your team's QA tool wants.

## Why it's different

- **Acceptance criteria are required.** No silent fallback to
  hallucinated AC. If they're missing, the command refuses unless you
  pass `--allow-missing-ac` for clear product-intent-derived cases.
- **Memory-grounded.** It pulls compact Braingent memory for prior
  decisions, known misses, and repo context — so test plans inherit the
  team's accumulated knowledge.
- **Evidence-aware.** It accepts a `qa-evidence.v1` manifest from your
  build, or collects it natively from [Gather Step](/integrations/gather-step/).
  Tests cite the implementation they're verifying.
- **Deterministic precheck.** Before the LLM writes a single case, a
  precheck runs against the inputs: missing coverage of stated AC,
  duplicate scenarios, weak expected results, unsurfaced evidence
  truncation. Failures are reported, not papered over.
- **Lossy generation is surfaced, not hidden.** If the evidence
  envelope is too large to include verbatim, the plan flags the
  truncation as a review gap — it never silently shortens.

## The flow

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  Ticket / spec  │    │  Braingent memory    │    │  qa-evidence    │
│  (Jira / docs)  │    │  (decisions, repos,  │    │  v1 manifest    │
│                 │    │   prior tasks)       │    │  + Gather Step  │
└────────┬────────┘    └──────────┬───────────┘    └────────┬────────┘
         │                        │                         │
         └────────────────┬───────┴─────────────────────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Deterministic    │  ← precheck:
                 │ precheck         │     • AC coverage
                 │                  │     • duplicates
                 └────────┬─────────┘     • weak expected
                          │               • truncation flags
                          ▼
                 ┌──────────────────┐
                 │ Strict QA plan   │
                 │ generation       │
                 └────────┬─────────┘
                          │
            ┌─────────────┼─────────────┬─────────────┐
            ▼             ▼             ▼             ▼
        Markdown     Xray JSON     TestRail CSV    Gherkin
```

## Quickstart

You'll need:

- A ticket (file path, URL, or pasted text).
- A connected Braingent memory repo.
- Optional but recommended: a `qa-evidence.v1` manifest from your build,
  or [Gather Step](/integrations/gather-step/) connected.

Then run:

```bash
scripts/qa-generate.sh \
  --ticket-key ACME-1492 \
  --evidence-pack ./build/qa-evidence.json \
  --emit-format markdown \
  --output ./qa-plans/ACME-1492.md \
  ./tickets/ACME-1492.md
```

Open the output. Every test case will look like this:

```markdown
### TC-001 — Webhook handler is idempotent on duplicate event

**AC:** AC-2 — "Duplicate webhook deliveries must not create duplicate
billing rows."

**Steps:**
1. Send a `payment.succeeded` webhook with idempotency key `idem-X`.
2. Replay the same payload immediately.
3. Query `billing_events` for rows where `idempotency_key = 'idem-X'`.

**Expected:**
- Step 1 returns 200 and inserts one row.
- Step 2 returns 200 with `Idempotent-Replay: true` header.
- Step 3 returns exactly one row.

**Evidence:**
- `apps/api/src/billing/webhook.ts:42-78` (handler with idempotency key)
- `apps/api/src/billing/migrations/0042_idempotency_keys.sql`
- DEC-0218 — moved jobs runtime; idempotency mandatory under Temporal

**Risk surfaced:** if `Idempotent-Replay` header is missing,
observability dashboards will undercount. See LRN-2026-04-bullmq-process-churn.
```

Each case carries:

- **AC trace** — which acceptance criterion it covers.
- **Steps + Expected** — the actual test, written for execution.
- **Evidence** — file paths, line ranges, decisions, learnings.
- **Risk surfaced** — what the precheck noticed.

## Flags worth knowing

| Flag | What it does |
| --- | --- |
| `<ticket-path-or-inline-ticket-text>` | Source ticket text or path. Required. |
| `--ticket-key <key>` | Ticket key used in the output title and filename. |
| `--allow-missing-ac` | Allow product-intent-derived `REQ-*` cases when explicit AC is missing. |
| `--source <path-or-text>` | Supporting spec, PRD, note, design source, or pasted text. Repeatable. |
| `--evidence-pack <path>` | Existing `qa-evidence.v1` manifest from Gather Step or your build. |
| `--gather-workspace <path>` | Workspace where Gather Step should run. |
| `--gather-target <target>` | Symbol, route, or event target for Gather Step `qa-evidence`. |
| `--budget-tokens <n>` | Evidence envelope budget. Default `160000`. |
| `--emit-format <markdown\|xray-json\|testrail-csv\|gherkin>` | Output format. |
| `--output <path>` | Explicit output path. |
| `--output-dir <path>` | Output directory. Defaults to `.test-plans/`. |

## How the precheck works

The precheck is deterministic — it runs before the LLM and runs in the
same way every time. It checks:

1. **AC coverage.** Every stated acceptance criterion has at least one
   test case mapped to it. Missing → error.
2. **Duplicate scenarios.** Two cases with the same steps + expected →
   warning.
3. **Weak expected results.** Cases where the expected result is
   tautological ("expected: it works") → warning.
4. **Unsurfaced truncation.** Evidence was clipped to fit the budget,
   but the truncation isn't flagged in the plan → error.
5. **Orphan evidence.** Evidence rows that no case references → warning,
   often a sign of missed coverage.

Input errors fail the command before output is written. Warnings and evidence
gaps are rendered in the plan for review.

## Integration with Gather Step

[Gather Step](https://gatherstep.dev) is QA-evidence-aware by design.
When `--gather-workspace` and `--gather-target` are supplied,
`qa-generate` calls Gather Step's `qa-evidence --json` to collect native
evidence rows: which tests have already been written, which have been run,
which have flaked.

The result is a QA plan that knows what's already covered, so it can
focus generation on the gaps.

See [Gather Step Integration](/integrations/gather-step/) for the full
picture.

## Why this exists

Test plans written from a ticket alone repeat the team's mistakes.
They miss the regression that bit you last quarter. They re-introduce
the antipattern you decided against. They lack the context that lives in
your decisions and learnings — because the LLM has never seen them.

`scripts/qa-generate.sh` reads that context for you and uses it to ground every test
case. The output is a plan a senior engineer would write — because it's
informed by the same evidence a senior engineer would have.

## Where to go next

- [Gather Step Integration](/integrations/gather-step/) — pair Braingent
  + Gather Step for end-to-end QA.
- [CLI Reference](/reference/cli/#qa-generate) — full flag table.
- [Search & Recall](/guides/search-and-recall/) — what kinds of memory
  the precheck pulls from.
