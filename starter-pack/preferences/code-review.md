# Code Review

Use code review records for PR reviews, design reviews, and important diffs.

## Review Priorities

Order findings by impact:

1. Correctness.
2. Security.
3. Performance.
4. Memory or resource use.
5. Tests.
6. Readability.
7. Observability.

## Findings Format

Each finding should include:

- severity
- file or area
- evidence
- recommended fix
- issue ELI5: plain-but-technical explanation of what is wrong and why it matters
- fix ELI5: plain-but-technical explanation of how the proposed fix addresses the root problem

Use `templates/code-review-record.md`.

## Security Checks

Look for:

- hardcoded secrets
- unsafe input handling
- authentication gaps
- authorization gaps
- weak crypto
- sensitive data in logs
- dependency risk
- overly broad permissions
- missing rate limits on public endpoints

If something looks risky, stop and flag it.

## Test Checks

Look for:

- missing regression coverage
- untested edge cases
- tests that assert implementation details instead of behavior
- flaky time, network, or ordering assumptions
- fixtures that do not match real data shape

## Capture Outputs

After every meaningful review, capture:

- review target
- method
- verdict
- findings with severity, file or area, evidence, recommendation, issue ELI5, and fix ELI5
- verification
- follow-ups
- reusable learnings
