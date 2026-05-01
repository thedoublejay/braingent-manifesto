# Task Dashboard

This optional directory documents a local dashboard for live `BGT-NNNN` tasks.

The starter pack does not require a dashboard. The public manifesto repo includes
a copyable sample app at `examples/task-dashboard/`; copy it here when you want
a working Bun/React UI.

If you build or copy one, keep this contract:

- read task state from `tasks/active/` and generated indexes;
- do not store a second copy of task state;
- keep task Markdown canonical;
- run dashboard checks after reindexing when schema changes;
- keep screenshots, fixtures, and demo data synthetic if publishing.

## Recommended Views

- queue grouped by status and priority;
- filters for status, owner, priority, and text search;
- task detail with goal, plan, acceptance criteria, closeout, and raw Markdown;
- dependency graph;
- paginated recent activity;
- guide page explaining the live task workflow.

## Suggested Stack

Use whatever fits your repo. A proven local setup is Bun, React, TanStack Router,
Tailwind, and Playwright end-to-end tests.
