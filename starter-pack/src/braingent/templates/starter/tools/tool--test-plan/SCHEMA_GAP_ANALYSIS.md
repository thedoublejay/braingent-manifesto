# QA Evidence Schema Gap Analysis

Status: accepted for native Gather Step `qa-evidence.v1` ingestion.

## Current Adapter Scope

Braingent normalizes native Gather Step `qa-evidence --json` output into the
internal row model used by the manual QA generator. Older bounded Gather Step
commands remain a fallback for checkouts that do not expose `qa-evidence`.

Current sources:

| Source | Current adapter behavior | Gap |
| --- | --- | --- |
| `status --json` | Collected for trust checks only; not converted into evidence rows. | No test-case evidence expected. |
| `doctor --json` | Collected for trust checks only; not converted into evidence rows. | No test-case evidence expected. |
| `qa-evidence --json` | Preferred source. Canonical rows are normalized from `qa-evidence.v1` into the internal pack model. | Real-ticket validation should continue, but schema ingestion is active. |
| `pr-review --format json` | Legacy fallback converted to low-confidence command-cited rows when present. | Field-level file spans, changed symbols, and edge IDs are not parsed from fallback rows. |
| `search --json` | Legacy fallback converted to low-confidence command-cited rows. | Exact source kind and symbol resolution are heuristic. |
| `pack --mode review --json` | Legacy fallback converted to low-confidence command-cited rows. | Caller/consumer row IDs are not extracted from fallback pack payloads. |
| `impact --json` | Legacy fallback converted to low-confidence command-cited rows. | Downstream edges are summarized from text only. |
| `projection-impact --json` | Legacy fallback converted to low-confidence `projection` rows. | Field spans and projection graph IDs are not parsed from fallback rows. |

## Required Before Stable Workflow Use

- Continue real-ticket validation passes against merged Gather Step v4.0 evidence.
- Expand deterministic precheck rules as new QA misses appear.
- Prefer direct Gather Step MCP calls once this workflow runs inside an
  MCP-aware agent.

## Gather Step Boundary

Gather Step work is no longer blocked on the schema draft. It should continue
improving deterministic review, change-impact, citation, and graph evidence
surfaces without interpreting Jira, Figma, ACs, or QA heuristics.
