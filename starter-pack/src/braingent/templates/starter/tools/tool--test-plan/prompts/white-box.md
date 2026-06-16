# White-Box Scenario Prompt

Generate QA scenarios from implementation evidence.

Inputs:

- Gather Step review/change-impact/planning packs.
- Diff summary, changed files, routes, APIs, events, contracts, projections,
  shared DTOs, callers, consumers, and existing tests.
- Direct code readings when Gather Step evidence is incomplete.

Rules:

- Cite code paths, Gather Step edges, existing tests, or explicit inferences.
- Do not promote implementation-only behavior into product requirements.
- Surface upstream/downstream impact and missing test coverage.
- Prefer code evidence that reveals integration, contract, permission, data, or
  deployment risk.

Output:

- Candidate code-evidence scenarios, each tagged `Code-only` until merged with a
  matching product requirement.
