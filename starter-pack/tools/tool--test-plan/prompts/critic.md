# Critic Prompt

Review a generated manual QA test plan.

Check for:

- Missing AC coverage.
- Missing design/page coverage.
- Duplicated cases.
- Weak expected results.
- Untestable wording.
- Developer bias.
- Missing integration impact.
- Missing negative or boundary cases.
- Missing data matrix dimensions.
- Missing source links.
- Code-only behavior presented as product truth.

Required fixes:

- Add a gap or follow-up question for every missing source.
- Rewrite vague expected results into observable outcomes.
- Keep source citations attached to every case.
