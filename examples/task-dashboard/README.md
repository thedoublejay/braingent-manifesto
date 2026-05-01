# Braingent Task Dashboard Example

Copyable local web UI for the optional Braingent v3 live-task layer.

This example is public-safe. It ships with synthetic task Markdown under
`sample-memory/tasks/` and reads that sample data by default.

## Copy Into A Memory Repo

From the `braingent-manifesto` repo:

```bash
mkdir -p /path/to/your-braingent/dashboard
cp -R examples/task-dashboard /path/to/your-braingent/dashboard/tasks
```

Then from your memory repo:

```bash
cd dashboard/tasks
bun install
BRAINGENT_MEMORY_ROOT="$(pwd)/../.." bun run dev
```

Open:

```text
http://127.0.0.1:4321/
```

## Run The Example In Place

```bash
cd examples/task-dashboard
bun install
bun run dev
```

Without `BRAINGENT_MEMORY_ROOT`, the dashboard reads `sample-memory/tasks/`.

## Commands

```bash
bun install
bun run dev
bun run typecheck
bun run build
bunx playwright install chromium
bun run test:e2e
```

## Scope

- Reads Markdown task files from `tasks/`.
- Defaults to synthetic sample data.
- Uses `BRAINGENT_MEMORY_ROOT` to point at a real memory repo.
- Derives blockers and activity in-process.
- Uses the same task files as the CLI; no separate database.
- Current slice is read-only: queue, filters, detail, graph, activity, guide, and raw Markdown.

## Stack

- Bun package manager/runtime.
- TanStack Start, Router, Query, and Table.
- React 19, TypeScript 6, Vite 8.
- lucide-react icons.
- Playwright e2e tests.
