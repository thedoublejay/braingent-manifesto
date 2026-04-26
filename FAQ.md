# FAQ

## Is Braingent A Tool Or A Folder Structure?

It starts as a folder structure and workflow. Automation can come later.

The core idea is durable, searchable Markdown memory with consistent frontmatter and AI-readable instructions.

## Why Not Just Use Chat History?

Chat history is hard to search, fragmented across tools, and full of noise. Braingent keeps the durable parts:

- decisions
- verification
- risks
- lessons
- repo conventions
- review findings
- tool versions

## Why YAML Frontmatter?

Frontmatter lets humans write normal Markdown while agents and scripts can still filter by kind, status, repo, ticket, tool, person, or topic.

## Do I Need Scripts?

No.

Scripts are useful later for validation, indexing, and search, but the public starter kit is Markdown-only. Start manually, then automate what becomes repetitive.

## Should Every Task Get A Record?

No.

Capture meaningful work:

- non-obvious decisions
- completed tickets
- opened PRs
- finished reviews
- surprising bugs
- reusable lessons
- setup changes that future agents need

Tiny one-off edits do not need a permanent record unless they teach something.

## Should I Store Raw Chat Logs?

Usually no.

If a raw transcript is useful, store it under `imports/raw/` temporarily and create a curated summary. The summary should become the durable source.

## Can This Work For Non-Code Projects?

Yes, but the templates are optimized for software engineering. You can adapt record kinds and preferences for writing, research, operations, design, or personal knowledge work.

## How Big Should The Repo Get?

Big enough to answer future questions, small enough that search stays useful.

Prefer one concise record per meaningful event. Promote repeated patterns into topic records. Update indexes and current state as the memory grows.

## What Is The Most Important Habit?

Search before planning. Capture after meaningful work.

That loop is the system.

