# Project Conventions

Cross-cutting conventions that apply to all your projects.

Use this file to record standing rules that agents should follow across every task — things that don't belong in a single repository profile or task record because they span multiple projects or repos.

## How To Use This File

Replace the placeholder examples below with your own conventions. Delete sections that don't apply. Add new sections as you discover patterns you want to repeat or mistakes you want to prevent.

---

## Example Convention: Database Migrations Before Release

<!-- Replace this with your own rule or delete it. -->

For projects that have not yet shipped to production:

- Do not write migrations. Reset and reseed the database on each schema change instead.
- Once the project has real production users, switch on migrations and treat the schema as immutable history.

---

## Example Convention: Phase and Milestone Numbering

<!-- Replace this with your own rule or delete it. -->

Within any project, phase and milestone numbers must be unique across all tasks to avoid ambiguity.

- Use scope-prefixed labels: `auth-phase-1`, `export-phase-1`.
- When starting a new "Phase 1" without a scope qualifier, stop and ask which scope it belongs to.

---

## Add Your Own Conventions

Useful sections to consider:

- Branching and commit rules your tools do not enforce
- Code style choices that override default agent behavior
- Review requirements before merging certain types of changes
- Naming conventions for projects, tickets, or branches
- Release gate requirements or deployment rules
- Privacy or compliance rules that apply to all projects
