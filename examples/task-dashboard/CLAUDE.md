# Tasks Dashboard Instructions

Use this file when editing the copyable dashboard example or a copied
`dashboard/tasks/` app.

## Stack

- Bun is the package manager and runtime.
- The app uses React, TypeScript, Vite, TanStack Router, TanStack Query, TanStack Table, Tailwind-style CSS, and lucide-react icons.
- The visual mode is AMOLED-style dark UI. Keep contrast high and avoid green as the dominant palette.

## Contract

- The dashboard is read-only.
- Markdown files under `tasks/` are the source of truth.
- The public example defaults to `sample-memory/tasks/`.
- Real memory repos can be selected with `BRAINGENT_MEMORY_ROOT`.
- Do not add a dashboard database, write API, or divergent task schema.
- Keep the loader aligned with `templates/agent-task.md` and `preferences/taxonomy.md`.
- Derived data such as blockers, activity entries, labels, and counts should be computed from the task files.

## Commands

```bash
bun install
bun run dev
bun run typecheck
bun run build
bun run test:e2e
```

## E2E Expectations

- Playwright tests live under `e2e/`.
- E2E must cover dashboard load, Guide navigation, filters, task detail, activity, graph, raw Markdown, and runtime console/page errors.
- In a full memory repo, reindex checks can run the dashboard e2e gate after task schema changes.
- If task frontmatter or Markdown section parsing changes, update the dashboard loader and e2e in the same change.

## Anti-Patterns

- Do not hardcode sample tasks in React components.
- Do not hide schema drift by catching and ignoring malformed task files without a visible test.
- Do not make closed durable records the dashboard's primary data source; closed task files remain queryable, but durable memory lives in the wiki layer.
