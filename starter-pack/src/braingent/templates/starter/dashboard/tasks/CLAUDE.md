# Dashboard Task Instructions

These instructions apply when editing an optional local task dashboard.

## Contract

- The dashboard reads `tasks/active/` and generated indexes.
- Task Markdown remains the source of truth.
- Do not store task state in browser-only data, a separate API database, or generated fixtures.
- Keep demo data synthetic when publishing.

## Recommended Stack

- Bun for package/runtime commands.
- React for UI.
- TanStack Router or equivalent for local routes.
- Tailwind or a comparable utility layer for styling.
- Playwright for end-to-end checks.

## Required Views

- Queue and filters.
- Task detail.
- Recent activity with pagination or fixed-height scrolling.
- Dependency graph.
- Raw Markdown.
- Guide page.

## Verification

After task schema changes:

1. Reindex the memory repo.
2. Run dashboard end-to-end tests if they exist.
3. Confirm the UI still reads Markdown-derived state only.
