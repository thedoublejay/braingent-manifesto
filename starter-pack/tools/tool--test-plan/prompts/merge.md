# Merge Prompt

Merge black-box and white-box scenario candidates.

Classifications:

- `Both`: product expectation and implementation evidence agree.
- `AC-only`: product expectation exists but implementation evidence is weak or
  absent.
- `Code-only`: implementation behavior exists but product requirement is weak or
  absent.

Rules:

- Deduplicate scenarios that test the same behavior with the same source.
- Preserve source rows from product, Braingent, Gather Step, and code.
- Keep code-only behavior as a gap or review question unless product intent
  confirms it.
- Prefer fewer, stronger cases over broad generic lists.
