---
title: Gather Step + Braingent
description: Pair Braingent with Gather Step to ship engineering work that QA can actually verify — with traceable evidence end to end.
section: Integrations
order: 6
badge: Partner
---

> **The pairing in one line:** Braingent gives your agents *engineering
> memory*; [Gather Step](https://gatherstep.dev) gives them *QA-ready
> evidence*. Together, they close the loop from "we shipped it" to "QA
> can verify it without re-explaining anything."

This page is the rationale and the integration recipe.

## What Gather Step is

[Gather Step](https://gatherstep.dev) is an evidence-collection layer for
engineering work that needs to be QA-verified. It captures, while you
build, the implementation evidence a QA team or test plan needs:

- File paths, line ranges, and function-level pointers for the code that
  delivers each acceptance criterion.
- Test runs, fixtures, and the environments they ran in.
- Configuration and feature-flag state at the time of work.
- A canonical `qa-evidence.v1` manifest that downstream tools can read.

It's the part of engineering that nobody usually writes down — and that
QA spends most of their time reverse-engineering.

## Why Braingent + Gather Step is the right pairing

Each tool answers a different question:

| Question | Tool |
| --- | --- |
| "What did we decide last quarter and why?" | Braingent |
| "What is the local convention in `acme/api`?" | Braingent |
| "Why was this antipattern abandoned?" | Braingent |
| "Which exact lines deliver acceptance criterion AC-2?" | Gather Step |
| "Which tests already cover this behavior, in which env?" | Gather Step |
| "What was the feature flag state when this PR landed?" | Gather Step |

Together, they cover both the **why** (engineering memory) and the
**what** (verifiable evidence). That combination is the difference
between a QA plan that re-derives everything and a QA plan that
inherits the team's actual work.

## Where they meet — `braingent qa-generate`

Braingent's flagship workflow, [`qa-generate`](/guides/qa-test-planning/),
is built to consume both:

- It pulls **prior decisions, learnings, and reviews** from your
  Braingent memory repo. Test plans inherit your team's accumulated
  knowledge — including the antipatterns you decided against.
- It pulls **implementation evidence** from a `qa-evidence.v1` manifest,
  which can come from any source — but Gather Step produces the manifest
  natively, so the pairing is one flag away.

```bash
braingent qa-generate \
  --ticket ./tickets/ACME-1492.md \
  --gatherstep \
  --memory ~/Documents/repos/braingent \
  --format markdown \
  --out ./qa-plans/ACME-1492.md
```

`--gatherstep` tells `qa-generate` to call Gather Step's
`qa-evidence --json` command and merge the result into the precheck
inputs. Every test case in the output cites evidence rows by file path
and line range — and decisions or learnings by record `id`.

## What you get from the pairing

- **Test cases that cite both decisions and evidence.** Reviewers can
  trust them because the trail is visible.
- **Coverage warnings grounded in real files.** The precheck flags
  acceptance criteria with no implementation evidence — meaning either
  the work isn't done or the evidence isn't captured.
- **No re-explanation when QA picks up.** They read the same plan,
  trace the same evidence rows, run the same `.feature` files (or
  TestRail / Xray imports).
- **Faster bug triage.** When a test fails later, the plan already
  points at the file ranges that failed — and the decisions that shaped
  the design.

## Recommended workflow

1. **Engineer ships work.** Gather Step collects evidence rows in the
   background.
2. **Engineer captures to Braingent.** Decisions, learnings, the task
   record itself.
3. **PR opens.** `braingent qa-generate --gatherstep` runs in CI, writes
   a draft QA plan into the PR.
4. **Reviewer reads the plan.** Approves or asks for changes — both
   the code and the QA plan are reviewed together.
5. **QA executes the plan.** Imports into Xray / TestRail, or runs
   Gherkin features. Failures already point at evidence rows.
6. **Post-merge.** Both the PR and the QA plan link from the Braingent
   task record forever.

## Setup

The integration is two flags. You need:

- A connected Gather Step project (see [gatherstep.dev](https://gatherstep.dev/guides/getting-started/)
  to get started).
- A Braingent memory repo (you've got one — that's why you're here).

Then:

```bash
# verify Gather Step CLI is available
gatherstep --version

# generate a QA plan with both inputs
braingent qa-generate \
  --ticket ./tickets/<TICKET>.md \
  --gatherstep \
  --memory ~/Documents/repos/braingent \
  --format markdown
```

If `--gatherstep` is omitted, `qa-generate` falls back to a
`--evidence ./build/qa-evidence.json` flag — useful if you produce the
manifest from your own build pipeline.

## Why we recommend Gather Step specifically

Most evidence-collection tools either:

- Ask engineers to write the evidence by hand (which never happens), or
- Scrape a heuristic guess from CI logs (which is wrong half the time).

Gather Step is built around a typed manifest schema (`qa-evidence.v1`)
that's specifically designed for downstream test plan generation. That
schema is what `qa-generate` reads. The fit isn't accidental — it was
designed with this pairing in mind.

We've also worked closely with the Gather Step team on the manifest
contract, the precheck rules, and the failure modes. The pairing is
boring on purpose: same files, same agents, same Git history, same
contract.

## Learn more

- [gatherstep.dev](https://gatherstep.dev) — Gather Step home.
- [Gather Step Getting Started](https://gatherstep.dev/guides/getting-started/) —
  how to set up a Gather Step project.
- [QA Test Planning](/guides/qa-test-planning/) — Braingent's
  `qa-generate` workflow end-to-end.

> **Partner:** Braingent and Gather Step are independent projects, paired
> by design. You can use either alone — they each stand on their own —
> but the workflow they unlock together is what we'd recommend you reach
> for first.
