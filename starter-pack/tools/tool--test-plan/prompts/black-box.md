# Black-Box Scenario Prompt

Generate QA scenarios from product intent only.

Inputs:

- Ticket summary and acceptance criteria.
- Product/spec/design sources.
- Braingent memories that describe prior QA misses or repo-specific risks.

Rules:

- Do not use implementation diff or code evidence.
- Produce cases a manual QA reviewer can execute without reading code.
- Include positive, negative, boundary, role/permission, tenant/data-shape, and
  locale/device/browser coverage when the source implies them.
- Mark every scenario with the product source that justifies it.
- If AC or design context is missing, write a gap instead of guessing.

Output:

- Candidate scenarios with title, source AC, priority, steps, expected result,
  data variations, and automation candidate flag.
