---
title: CLI Workflows
description: Planned v4 CLI workflow reference for Braingent.
---

Braingent remains Markdown-first. The v4 CLI should remove setup friction
without hiding product state in a binary, service, or database.

## Command Shape

| Command | Purpose |
| --- | --- |
| `braingent init` | Bootstrap a new memory repo from the starter pack. |
| `braingent doctor` | Check required files, stale placeholders, private path leaks, invalid frontmatter, generated-index drift, and tooling gaps. |
| `braingent print-prompts` | Print setup snippets for Codex, Claude, ChatGPT, and Gemini without changing files. |
| `braingent update` | Compare starter-pack changes against local edits and produce a patch plan before mutating files. |

## `braingent init`

`braingent init` should walk the user through setup once, then leave them with a
normal Git repo they can inspect and commit.

Flow:

1. Resolve the target directory and detect whether it is empty, already a
   Braingent repo, or unrelated content.
2. Ask the minimum setup questions: repo owner/name, primary AI tools, privacy
   posture, first organization/project, and optional live-task/dashboard
   modules.
3. Copy `starter-pack/` into the target repo with a starter-pack version marker.
4. Replace known placeholders from the answers.
5. Run local checks when available: `doctor`, `validate`, and `reindex --check`.
6. Print the first commit command and the next workflow to run.

The command should refuse risky overwrites unless the user opts in explicitly.

## `braingent update`

`braingent update` should treat user-edited Markdown as more important than the
latest template.

Flow:

1. Read the installed starter-pack version marker.
2. Compare old template, new template, and current local files.
3. Classify each change as safe auto-merge, manual review, or skipped.
4. Show the patch plan before applying changes.
5. Apply only accepted safe changes.
6. Run `doctor`, `validate`, and `reindex --check` after updates.

This keeps upgrades boring: users see exactly what changed, and local memory
remains the source of truth.

## Content Source

This plan is synthesized from `README.md`, `SETUP.md`, `WORKFLOW.md`, and the
helper-script docs in the manifesto repository.
