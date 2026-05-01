# Braingent Tasks Dashboard User Guide

The Braingent Tasks Dashboard is a local, read-only web app for inspecting the v3 agent-task Markdown files under `tasks/`.

It is a view over the repository, not a separate task system. Markdown remains the source of truth.

## Start The App

In the public example:

```bash
cd examples/task-dashboard
bun install
bun run dev
```

To point the copied dashboard at a real memory repo:

```bash
BRAINGENT_MEMORY_ROOT=/path/to/your-braingent bun run dev
```

Open:

```text
http://127.0.0.1:4321/
```

When copied into a memory repo at `dashboard/tasks`, run:

```bash
cd dashboard/tasks
bun install
BRAINGENT_MEMORY_ROOT="$(pwd)/../.." bun run dev
```

## What You Can Do

### In-App Guide

Open `Guide` in the sidebar to read this document inside the dashboard.

The guide is loaded from `USER-GUIDE.md`, so edits to this file are reflected in the app after refreshing the guide page.

### Queue Navigation

Use the left sidebar to switch between task queues:

- `Queue` shows all parsed task files.
- `Triage`, `Ready`, `In Progress`, `In Review`, `Blocked`, `Completed`, and `Closed` filter by task status.
- Each queue shows a count badge based on the current Markdown files.
- `Generated` shows when the dashboard last loaded task data.

### Search And Filters

Use the top toolbar to narrow the task table:

- Search matches task ID, title, status, priority, agents, project, repositories, and description.
- `Status` filters by task lifecycle state.
- `Agent` filters tasks where the selected agent is assignee, reviewer, claimant, or observer.
- `Project` filters by task project.
- `Reset Filters` clears all filters and search text.

### Task Table

The table shows the main task queue fields:

- ID
- Status
- Priority
- Task title and source path
- Assignee
- Reviewer
- Updated date

Click a task ID or title to open it in the detail panel.

### Task Detail

The detail panel has four tabs:

- `Overview` shows assignee, reviewer, priority, project, visibility, resolution, description, acceptance criteria, and linked evidence.
- `Activity` shows the selected task's parsed activity log.
- `Graph` shows dependency and relationship fields: depends on, blocks, parent, and duplicate of.
- `Markdown` shows the raw task file content exactly as stored.

### Recent Activity

The Recent Activity panel shows activity entries across all tasks, newest first.

- The panel has a fixed height so the page layout stays stable.
- Activity is paginated in groups of 6.
- Use `Previous` and `Next` to move between activity pages.

### Refresh

Click `Refresh` after editing task Markdown files outside the dashboard.

The dashboard rereads the task files from disk. It does not mutate files itself.

## Current Features

- Local-only Bun/TanStack web app.
- Reads sample task Markdown files from `sample-memory/tasks/` by default.
- Reads real task Markdown files when `BRAINGENT_MEMORY_ROOT` is set.
- Parses task frontmatter and body sections.
- Derives blocker relationships from `depends_on`.
- Displays queue counts by status.
- Provides search and structured filters.
- Provides task detail, graph, activity, and raw Markdown views.
- Uses an AMOLED-style dark palette.
- Includes Playwright end-to-end coverage for the core workflow.

## Current Limitations

- Read-only: no create, claim, status change, close, archive, or comment actions in the UI yet.
- No separate database: every displayed task comes from Markdown.
- No authentication or remote hosting flow.
- No multi-repo task ingestion beyond files present in this repository.

Write-capable UI actions should use the same mutation path as the task CLI when added later.

## Test The UI

Install Playwright's Chromium runtime once:

```bash
cd dashboard/tasks
bunx playwright install chromium
```

Run the browser test:

```bash
bun run test:e2e
```

The E2E test verifies:

- The dashboard loads.
- Dark mode uses an AMOLED black page background.
- The task table renders.
- Filters and search work.
- Task detail opens.
- Overview, Activity, Graph, and Markdown tabs work.
- Recent Activity pagination works.
- No browser console errors or page errors occur.

Run the regular checks before committing UI changes:

```bash
bun run typecheck
bun run build
bun run test:e2e
```

## Troubleshooting

If the browser still shows old styles or labels after a code change, restart the dev server:

```bash
bun run dev
```

If `bun run test:e2e` fails on macOS with a browser launch permission error, run it from an environment that can launch Chromium. In this repo's sandboxed agent sessions, Playwright needs browser execution outside the sandbox.

If the dashboard shows fewer tasks than expected, verify the files:

- Live task files must be under `tasks/`.
- Task filenames must start with `BGT-` and end with `.md`.
- Files must have valid YAML frontmatter.
