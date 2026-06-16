# Task Dashboard User Guide

The dashboard is a read-only view over live task Markdown.

To install the public sample, copy `examples/task-dashboard/` from the
manifesto repo into this directory.

## What You Can Inspect

- active task counts;
- task status, owner, priority, and blockers;
- recent activity;
- dependencies between tasks;
- raw Markdown for the selected task;
- closeout links to durable records.

## What You Should Not Do

- Do not treat the dashboard as the source of truth.
- Do not edit task state in a separate database.
- Do not publish real task data or screenshots from a private memory repo.

## Normal Loop

1. Reindex the memory repo.
2. Open the dashboard.
3. Review blocked, in-review, and stale work.
4. Make task changes in Markdown or task scripts.
5. Reindex and rerun dashboard checks.
