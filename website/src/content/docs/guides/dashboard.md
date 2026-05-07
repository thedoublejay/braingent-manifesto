---
title: Local Dashboard
description: A read-only Bun + React + TanStack dashboard over your live tasks — runs locally, never writes to your memory repo.
section: Guides
order: 7
---

The Braingent dashboard is a small local web app that gives humans a
read-only view of multi-agent work in progress. It reads the same
Markdown files agents write to (`tasks/active/*.md` and `indexes/*`) and
renders them as a queue you can scan in a browser.

It's optional. If you only ever read raw Markdown and `git log`, you'll
never need it. But once you have several agents working in parallel, the
dashboard makes the live state easy to see at a glance.

## What it shows

- **Live queue** of `tasks/active/*.md` with status, priority, and owner.
- **Filters** by status, priority, owner, and free-text search.
- **Task detail** view with goal, acceptance criteria, plan, closeout,
  raw Markdown, and an append-only activity log.
- **Dependency graph** between tasks.
- **Recent activity** — fixed-height paginated feed across all tasks.
- **In-app guide** explaining the contract.
- **Synthetic sample data** when no real memory repo is connected, so
  you can demo the UI safely.

The dashboard is **strictly read-only**. Agents and humans still capture
through their normal flow; the dashboard is just a window onto the
files.

## Stack

- **Bun** — package manager and runtime.
- **TanStack Start, Router, Query, Table** — app framework + data layer.
- **React 19, TypeScript 6, Vite 8**.
- **lucide-react** for icons.
- **Playwright** for end-to-end tests.

Same files. Same Git history. Same agent contract. The dashboard adds no
schema and no service.

## Run the example in place

The manifesto repo ships a runnable example with synthetic data.

```bash
cd ~/Documents/repos/braingent-manifesto/examples/task-dashboard
bun install
bun run dev
```

Open the printed URL (typically `http://localhost:3000`). The synthetic
data is deliberately public-safe — feel free to demo it.

## Point it at your real memory repo

Set `BRAINGENT_MEMORY_ROOT` to your memory repo's absolute path:

```bash
BRAINGENT_MEMORY_ROOT=~/Documents/repos/braingent bun run dev
```

The dashboard will read live `tasks/active/*.md` and the relevant
`indexes/*` files from that path. It still never writes.

## Copy it into your memory repo

If you want the dashboard to live alongside your memory (so multiple
machines can run it without recloning the manifesto), copy the
`dashboard/` directory from the starter pack into your memory repo:

```bash
# from the manifesto repo
cp -R examples/task-dashboard ~/Documents/repos/braingent/dashboard

# then
cd ~/Documents/repos/braingent/dashboard
bun install
bun run dev
```

The starter pack already includes a `dashboard/` placeholder so the
target path works out of the box.

## When to use it

- **Multiple agents in parallel.** Two Claude sessions plus a Codex run —
  the dashboard shows their hands-offs in real time.
- **Onboarding a teammate.** "Open the dashboard" beats "let me explain
  what's in flight."
- **End-of-day scan.** Glance at active tasks and recent activity before
  closing the laptop.

If your typical day is a single agent on a single task, you can skip the
dashboard entirely and read the Markdown.

## Verifying it loads

The first thing you should see when the dashboard starts:

- A queue of tasks (synthetic or real, depending on
  `BRAINGENT_MEMORY_ROOT`).
- Filters at the top.
- A "Recent activity" feed in the sidebar.

If the queue is empty *and* `BRAINGENT_MEMORY_ROOT` is set, check that
`tasks/active/` actually has files. The dashboard ignores
`tasks/archive/` and `tasks/done/` — those are deliberately out of
scope for the live view.

## Limitations on purpose

The dashboard intentionally does *not*:

- Write to the memory repo.
- Trigger captures or commits.
- Keep its own state outside the file system.
- Replace the CLI or the agent contract.

Those choices keep the dashboard cheap to build, easy to trust, and
harmless to run alongside any agent.

## Where to go next

- [Multi-Agent Coordination](/guides/multi-agent-tasks/) — the contract
  the dashboard renders.
- [Memory Model](/concepts/memory-model/) — how the dashboard fits in
  the five surfaces.
- [Installation](/guides/installation/#install-the-optional-dashboard) —
  setup as part of the broader Braingent install.
