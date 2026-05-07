---
title: ChatGPT Integration
description: Use Braingent with a ChatGPT Project or Custom GPT — paste the brief, attach pinned files, capture by hand.
section: Integrations
order: 4
---

ChatGPT doesn't read files from your local machine, so the entrypoint
goes into a Project's "Instructions" field (or a Custom GPT's system
prompt). The contract is the same; only the delivery is different.

## Setup — Project Instructions

1. Create a new ChatGPT Project (or open an existing one).
2. Open the file `~/Documents/repos/braingent/CHATGPT_PROJECT_BRIEF.md`.
3. Copy its contents.
4. Paste into the Project's **Instructions** field.

Done. ChatGPT now treats the brief as standing instructions for every
chat in that Project.

## Optional — attach pinned files

If you want ChatGPT to see specific Braingent files (preferences, the
relevant repo profile, recent decisions), attach them to the Project's
knowledge:

- The Project → Files panel.
- Drop in `preferences/*.md`, `repos/<active-repo>/profile.md`, recent
  decisions.

ChatGPT will reference those files in answers and you'll see citations.

> **Tip:** Don't attach your entire memory repo. ChatGPT's Project
> knowledge is a static snapshot, not live. Pick the small set of files
> a fresh chat actually needs.

## Setup — Custom GPT

If you maintain a personal Custom GPT instead of a Project:

1. Open the GPT's configuration.
2. Paste the brief into the **Instructions** field.
3. Optionally upload pinned files in the **Knowledge** section.
4. Save.

## Capturing from ChatGPT

ChatGPT can't write to your filesystem. Two patterns work:

**Pattern A — copy-paste capture.** When ChatGPT proposes a record, ask
it to format the file (full frontmatter + body), copy the result, paste
into your editor, save under the right path, commit.

**Pattern B — round-trip via Claude or Codex.** Ask ChatGPT for the
content, then in a Claude/Codex session say *"capture this to braingent"*
and paste the proposed body. The local agent writes the file.

Pattern B is more reliable because the local agent runs `validate`
before committing.

## Smoke test

Start a fresh chat in the Project and ask:

> What's the path to my Braingent memory repo, and what should you do
> before planning a non-trivial task?

ChatGPT should answer with the path you set in the brief and restate
the search-before-plan contract.

## Where to go next

- [Wire Up Your Agents](/guides/wire-up-agents/) — generic pattern.
- [The Capture Loop](/guides/capture-loop/) — capture rules that apply
  even when ChatGPT can't write.
