# Test Plan Generator

Use this skill when the user asks for `/test-plan`, QA reference generation,
manual test-plan generation from a ticket, or a Braingent-owned QA workflow.

## Workflow

1. Read the ticket, acceptance criteria, specs, design/page context, and related
   Braingent records.
2. Decide whether the request is pre-implementation, in progress, or
   post-implementation.
3. For pre-implementation work, run the generator with `--no-diff`.
4. For post-implementation work, prefer a supplied `--evidence-pack` when one
   exists. Otherwise collect native Gather Step `qa-evidence --json` rows with
   `--diff`, `--gather-workspace`, and one or more `--gather-target` values
   when known.
5. Review the generated output before sharing it. Fix gaps, weak expected
   results, duplicate cases, missing negative paths, and missing source rows.
6. Capture reusable QA misses or decisions in Braingent after the task finishes.

## Command

```bash
bash tools/tool--test-plan/test-plan.sh --ticket-key <KEY> [options] <ticket.md>
```

Important options:

- `--no-diff` for AC/product-only planning.
- `--allow-missing-ac` only when the ticket has clear product intent but no
  explicit AC; generated cases are tagged as `REQ-*` instead of `AC-*`.
- `--design-context` when page, screenshot, or Figma evidence was supplied.
- `--repo`, `--project`, `--topic`, `--tool`, and `--memory-query` for compact
  Braingent retrieval.
- `--evidence-pack` for an already-normalized `qa-evidence.json` manifest.
- `--emit-format markdown|xray-json|testrail-csv|gherkin` for downstream QA
  tools. Markdown remains the default human review format.
- `--budget-tokens` to tune the evidence envelope. Keep this lenient for QA;
  truncation must be reviewed as a gap.
- `--gather-workspace`, `--gather-target`, `--projection-target`, and `--diff`
  for white-box evidence.

## Guardrails

- Do not invent product requirements.
- Do not hide missing AC or design context.
- Do not treat code-only behavior as product intent.
- Do not generate executable test code; Gherkin output is an exchange format,
  not an automated step implementation.
- Do not claim complete coverage when the QA evidence pack reports truncation or
  unsupported surfaces.
- Prefer a short useful plan with explicit gaps over a long generic checklist.
