# Manifesto

Braingent exists because AI tools are useful, but isolated sessions forget too much. A strong agent can still waste time if it has no durable memory of past decisions, repo conventions, user preferences, mistakes, review findings, or tool versions.

The answer is not to paste giant chat logs into every prompt. The answer is a small, structured, searchable memory repo that both humans and agents can maintain.

## Core Belief

Software work improves when future planning starts from accumulated evidence.

Every repeated task should get easier. Every hard-won decision should become reusable context. Every bug that took hours to diagnose should become a short warning future agents can find in seconds.

## Principles

### 1. Markdown First

Markdown is portable, readable, diffable, and AI-friendly. It works in GitHub, local editors, Claude, Codex, ChatGPT, and almost every documentation system.

Use Markdown for both human context and agent instructions. Add automation only after the structure proves useful.

### 2. Frontmatter For Retrieval

Every durable record should start with YAML frontmatter. The body explains the story; the frontmatter makes the record searchable.

The frontmatter should answer:

- What kind of record is this?
- What is its status?
- What date was it captured?
- Which organization, project, repo, ticket, PR, branch, person, tool, or topic does it involve?
- Which AI tools helped?

### 3. Thin Entrypoints

Agent entry files should stay small. Files such as `AGENTS.md`, `CLAUDE.md`, and `CHATGPT_PROJECT_BRIEF.md` should tell the agent where to look and what rules cannot be ignored.

They should not become huge archives. Detailed context belongs in focused files under `preferences/`, `repositories/`, `topics/`, `orgs/`, `tools/`, and `records/`.

### 4. Search Before Planning

Before starting meaningful work, agents should search the memory for prior decisions, known risks, repo conventions, and reusable learnings.

This changes the default behavior from "start fresh" to "continue from what we already know."

### 5. Capture After Work

The end of a task is the best time to write memory. Context is still fresh, evidence is nearby, and decisions can be summarized before they disappear into chat history.

Good records are not long. They are specific.

### 6. Curated Records Beat Raw Transcripts

Raw chats are noisy. They are useful temporarily, but poor long-term memory.

Braingent prefers concise summaries:

- goal
- context
- what changed
- why decisions were made
- evidence
- verification
- risks
- follow-ups

Raw imports can exist briefly, but curated records should become the source of truth.

### 7. Immutable Events, Mutable Indexes

Task records, review records, decision records, and learning records should be treated as historical evidence. Do not rewrite history to make it cleaner, except for typo cleanup.

If a fact changes, add a new record and link it as superseding the old one.

Indexes, current-state files, and repository profiles are different. They are living documents and should be updated as reality changes.

### 8. Privacy Is A Feature

A memory system that stores secrets is a liability.

Braingent should never contain:

- passwords
- API keys
- tokens
- private keys
- customer secrets
- personal addresses
- sensitive personal data
- full private transcripts unless explicitly and temporarily retained

The public version should use placeholders and examples, not local names or private workspace paths.

## What Good Memory Feels Like

Good Braingent memory lets a future agent answer:

- What happened last time we touched this repo?
- Which command verifies this kind of change?
- Which decision should we not reopen without new evidence?
- What naming convention does this project use?
- Which prior bug looked like this one?
- Which tools and versions were used?
- What should not be captured?

The result is not a perfect encyclopedia. It is a practical engineering memory that compounds.

