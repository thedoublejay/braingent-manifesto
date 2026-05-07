---
title: The Braingent Manifesto
description: Engineering memory should be structured enough for machines, readable enough for humans, and boring enough to trust.
section: Introduction
order: 3
---

> Engineering memory should be structured enough for machines, readable
> enough for humans, and boring enough to trust.

Braingent is a working agreement between you and your AI agents. These are
the principles it bets on.

## I. Markdown is the source of truth

Plain files. YAML frontmatter for search. Git for history. No database is
allowed to know more about your engineering decisions than your filesystem
does. Indexes, search caches, and dashboards are downstream artifacts —
they regenerate from the Markdown.

If a record disappears from the filesystem, it is gone. If a record is in
the filesystem, it is real. Nothing in between.

## II. Retrieve before you plan

Agents that plan before searching invent the same wheel every session.
Before an agent proposes architecture, files to touch, or migration steps,
it should:

- Read the pinned entrypoint files at the root of the memory repo.
- Search for relevant decisions, reviews, and learnings.
- Check the relevant repository profile for local conventions.
- State what it found and what it's still assuming.

Plans built on retrieved memory beat plans built on cold prompts every
single time.

## III. Capture is non-negotiable

Work that doesn't end in a record is work the next session can't inherit.
Capture happens when:

- A pull request opens or closes.
- A ticket is resolved or rejected.
- A code review surfaces a non-obvious tradeoff.
- A decision rules out a path that future-you might re-propose.
- A learning is reusable across more than one repository.
- The user says: *capture this*, *save to braingent*, *task done*.

The bar is low. Capture small and often.

## IV. Frontmatter is the index

Every durable record carries structured frontmatter: `id`, `title`,
`status`, `kind`, `tags`, `topics`, `repos`, `tools`, `links`, `date`.
Search filters that frontmatter directly. Agents and humans both read the
same fields. The body is for narrative; the frontmatter is for retrieval.

A record without frontmatter is a private note. A record with frontmatter
is part of memory.

## V. Privacy is structural, not aspirational

Braingent never stores:

- Secrets, API keys, or credentials.
- Raw chat transcripts.
- Sensitive personal data.
- Anything that wouldn't pass a casual code review for inclusion in a Git
  repo.

This is a default in the starter pack — and a default in every entrypoint
file. The system is designed so that *nothing private should ever land
here*. If something does, the leak is visible in `git diff`.

## VI. Tools are conveniences, files are essential

The CLI helps. The MCP tools help. The dashboard helps. None of them are
required.

Delete every script in `scripts/` tomorrow and your memory still works.
Replace the CLI with a different language tomorrow and your memory still
works. Switch from Claude to whatever-comes-next tomorrow and your memory
still works.

This is what we mean by *boring*. Boring is what you trust five years from
now.

## VII. Memory belongs to the engineer, not the vendor

You should be able to:

- Read your memory in any text editor.
- Search it without an internet connection.
- Diff it against last quarter's version.
- Move it to a different host without an export step.
- Outlive the AI tool you happen to be using this year.

If a vendor's memory feature fails any of those tests, it is not memory.
It is rented attention.

## VIII. Less is more — until it isn't

Start with the smallest record that captures the decision. Add fields when
you actually need to filter on them. Add scripts when you actually do the
thing more than three times. Add a dashboard only when reading the files
isn't enough.

Premature schema, premature automation, and premature dashboards are how
memory systems die. Markdown is how they survive.

---

*Mischief managed — for the engineers who'd rather their agents remembered.*
