# Note Taking And AI Memory

Use this preference when capturing, normalizing, reviewing, or retrieving
Braingent notes. The goal is not more notes. The goal is higher-signal records
that future agents can retrieve, trust, and cite without drifting.

## Research Basis

These practices are adapted for Braingent's Git-backed Markdown model:

- Cornell note-taking separates capture, cue questions, reflection, and weekly
  review. Applied here: every useful record should make future retrieval easy,
  not just preserve what happened.
  Source: <https://lsc.cornell.edu/notes.html>
- Evergreen / Zettelkasten practice favors atomic, concept-oriented, densely
  linked notes that accumulate across projects. Applied here: use one durable
  record per meaningful event or reusable idea, then link it to projects,
  repos, topics, tools, tickets, and related records.
  Source: <https://notes.andymatuschak.org/About_these_notes?stackedNotes=Evergreen_note-writing_as_fundamental_unit_of_knowledge_work&stackedNotes=Evergreen_notes&stackedNotes=Evergreen_notes_should_be_atomic>
- PARA organizes by actionability: projects, areas, resources, and archives.
  Applied here: active execution belongs under org/project records; stable
  responsibilities live in profiles and `CURRENT_STATE.md`; reusable reference
  material belongs under topics/tools; inactive material is summarized or
  archived.
  Source: <https://every.to/forte-labs/the-para-method-a-universal-system-540221>
- Dendron uses schemas and hierarchies as a type system for notes. Applied
  here: frontmatter, taxonomy, templates, validation, and generated indexes are
  Braingent's type system.
  Sources: <https://wiki.dendron.so/notes/c5e5adde-5459-409b-b34d-a0d75cbb1052/>,
  <https://wiki.dendron.so/notes/f3a41725-c5e5-4851-a6ed-5f541054d409/>
- Foam emphasizes wikilinks, backlinks, tags, and placeholders. Applied here:
  use explicit Markdown links for important relationships, frontmatter for
  structured tags, and unchecked follow-ups for unresolved links or missing
  records.
  Sources: <https://foamnotes.com/user/features/wikilinks.html>,
  <https://foamnotes.com/user/features/backlinking.html>,
  <https://docs.foamnotes.com/user/features/tags.html>
- Letta / MemGPT separates pinned in-context memory from retrieved archival
  memory. Applied here: root instructions and `CURRENT_STATE.md` are the small
  always-read layer; durable records are archival memory; generated recall
  packs are temporary context.
  Sources: <https://docs.letta.com/guides/agents/memory>,
  <https://docs.letta.com/guides/core-concepts/memory/archival-memory/>
- Mem0, Zep, and GraphRAG show that entities, relationships, time, and source
  claims matter for AI retrieval. Applied here: capture who/what/when/where in
  frontmatter and cite source records from any synthesis.
  Sources: <https://docs.mem0.ai/open-source/features/graph-memory>,
  <https://help.getzep.com/concepts>,
  <https://microsoft.github.io/graphrag/index/overview/>
- Retrieval systems work better when content has searchable attributes and
  recall quality is evaluated. Applied here: frontmatter is required metadata,
  and future `recall` / `doctor` tooling should include recall-eval samples.
  Sources: <https://developers.openai.com/api/docs/guides/retrieval>,
  <https://developers.openai.com/api/docs/guides/evaluation-best-practices>

## Memory Layers

Treat Braingent as three layers:

1. **Pinned context:** root entry files, `CURRENT_STATE.md`, and stable
   preferences. Keep this small and current.
2. **Durable memory:** task, review, decision, learning, summary, interaction,
   version, profile, and ticket-stub records. These are canonical.
3. **Derived retrieval:** generated indexes, optional local databases, future
   recall packs, and future synthesis pages. These are aids, not source of
   truth.

**ELI5:** The pinned layer is the short briefing, durable records are the
receipts, and derived retrieval is the search assistant that pulls the right
receipts.

## Capture Funnel

Use this funnel for messy information:

1. **Capture fast:** put rough material in `inbox/` or `imports/raw/` only when
   it is not ready for a durable record.
2. **Classify:** choose the record kind before polishing the prose.
3. **Normalize:** add frontmatter, exact identifiers, dates, timezone, related
   repos/projects/topics/tools, and source links.
4. **Summarize:** write the shortest useful durable summary in your own words.
5. **Link:** add related records and promote repeated ideas to topics/tools.
6. **Validate:** run `scripts/validate.sh` if available.
7. **Index:** run `scripts/reindex.sh` if available.
8. **Review later:** stale, active, raw, and unchecked items are handled by the
   cleanup workflow.

Do not let `inbox/` become permanent storage. If a note is still useful after
cleanup, normalize it or link it from a follow-up.

## What Good Records Contain

Every durable record should answer:

- **Why this exists:** original goal, question, bug, review, or decision.
- **What happened:** actual outcome, not just the intended plan.
- **Why it matters:** future consequence or reusable lesson.
- **Evidence:** commands, files, commits, PRs, tickets, source URLs, or logs.
- **Retrieval cues:** repo, project, ticket, topic, tool, names, error strings,
  API names, versions, and exact user phrases future agents might search.
- **Trust state:** status, date, timezone, stale assumptions, and what should be
  revalidated.
- **Next action:** follow-ups, risks, or "none".

Prefer short records over transcript dumps. Long records should have a top
summary and sections that can be scanned independently.

## Atomic But Not Microscopic

Create one durable record per meaningful event or reusable idea:

- One ticket completion, PR, code review, incident, decision, reusable learning,
  or import batch usually deserves one record.
- Split a record only when the parts have different lifecycles, statuses,
  projects, repos, or future retrieval paths.
- Merge or link tiny fragments when they only make sense together.
- Promote stable facts to repository/project/topic/tool profiles instead of
  repeatedly copying them into task records.

**ELI5:** A good record is like a well-named function: focused enough to reuse,
but not split so small that nobody knows what it is for.

## Organization Rules

Use actionability first, then topic:

- Active execution work goes under `orgs/<org>/projects/<project>/records/`.
- Repository-specific facts go in `repositories/<repo-key>/`.
- Reusable technical lessons go in `topics/<topic-key>/records/`.
- Tool, framework, model, runtime, or version facts go in `tools/<tool-key>/`.
- Cross-cutting tickets get `tickets/<ticket-key>/` only when they span multiple
  projects or repos.
- Raw exports stay under `imports/raw/` only until summarized.
- Unsorted notes stay under `inbox/` only until normalized.

Avoid folder taxonomy fights. If a note could live in multiple places, choose
the most actionable home and use frontmatter plus links for the other access
paths.

## Optional Authoring Tools

Braingent's source of truth stays plain Markdown plus Git. Editor tools can help
authoring, but they should not become required infrastructure.

- Foam is the closest optional editor layer because it works over Markdown files
  and emphasizes wikilinks, backlinks, tags, and graph navigation.
- Dendron has useful ideas for schemas, hierarchies, and refactors, but do not
  depend on it as required tooling; its GitHub repository states that active
  development has ceased.
- Logseq can be useful as a private block/journal scratchpad, but it should stay
  a sidecar unless its notes are normalized into Braingent records.
- Zettelkasten, Evergreen Notes, Cornell notes, and PARA are operating lenses,
  not replacement taxonomies. Braingent's taxonomy remains the source of truth.

Sources:

- <https://docs.foamnotes.com/>
- <https://github.com/foambubble/foam>
- <https://github.com/dendronhq/dendron>
- <https://github.com/logseq/logseq>

## Retrieval Protocol

Before planning or answering from memory:

1. Identify likely org, project, repo, ticket, topic, tool, people, and time
   window.
2. Run structured search (`scripts/find.sh` or equivalent) with metadata filters
   first.
3. Use `rg` for body text, error strings, partial names, and exploratory search.
4. Open the smallest useful set of records.
5. Separate current, stale, superseded, and raw-only evidence.
6. Cite file paths when memory affects the answer or plan.
7. If subagents are used, pass them a focused context pack instead of asking
   each subagent to reread the whole repo.

## Anti-Drift Rules

- Do not store guesses as facts. Mark inference explicitly.
- Do not make generated synthesis canonical. Cite durable source records.
- Do not rewrite immutable historical records except typo, link, or metadata
  hygiene. Add a superseding record when facts change.
- Do not let semantic/vector retrieval outrank explicit metadata for known
  repos, tickets, projects, or dates.
- Do not store secrets, tokens, private keys, or sensitive personal data.
- Do not keep local paths or private names in public-facing material.
- Do not let stale active tasks remain active after cleanup finds they are done,
  blocked, or superseded.

## Maintenance Cadence

Daily:

- Normalize or explicitly defer new `inbox/` items.
- Validate and check indexes.
- Capture any meaningful completed work.

Weekly:

- Review active tasks, unchecked follow-ups, stale profiles, and raw imports.
- Promote repeated findings to topics/tools.
- Add backlinks from repo/project/topic pages when useful.

Monthly:

- Create or refresh derived synthesis only when every claim cites source
  records.
- Sample real tasks as recall-eval cases: did search find the right records?

Quarterly:

- Review taxonomy, templates, validation, global agent entrypoints, and cleanup
  workflow drift.
