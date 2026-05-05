# Token-Efficient Agent Access

A Markdown memory repo works best when agents retrieve the smallest useful
memory first and expand only when they need more evidence. This keeps sessions
cheaper, faster, and less noisy without weakening the memory system.

## Plain Explanation

Think of a memory repo like a large documentation site. A good agent should not
print the whole site into its prompt before doing one task. It should start with
the table of contents, search for the few relevant pages, read short summaries,
and open full pages only when it needs proof.

Token-efficient access is that habit turned into a design rule.

## The Access Ladder

Use memory in this order:

1. **Entrypoints:** read the short root files that explain how the repo works.
2. **Search:** query frontmatter, generated indexes, or a local search database.
3. **Compact results:** inspect small result rows with stable identifiers,
   titles, dates, scopes, status, and source links.
4. **Summary reads:** open summary-depth record bodies or generated summaries
   by default.
5. **Full reads:** open full records only when a decision, review, or exact
   evidence matters.
6. **Raw imports:** read raw source material only when curated records are not
   enough.

This ladder does not require a specific database, MCP server, dashboard, or
embedding system. It is a default access pattern: start with cheap retrieval,
then hydrate more context only when the task needs it.

## How To Use This During Setup

When creating a new memory repo:

1. Copy this guide, or copy its rules into your own `WORKFLOW.md` or agent
   entrypoint files.
2. Tell your agent: "Use token-efficient access. Search first, inspect compact
   results, read summaries by default, and open full records only when evidence
   requires it."
3. Start with plain tools such as `rg`, generated Markdown indexes, and short
   record summaries.
4. Add scripts, SQLite, MCP tools, embeddings, or dashboards only after the
   manual retrieval loop is useful.

The first version can be simple. A table of record paths and summaries is
enough to teach agents not to read every file.

## Recommended Defaults

- Prefer `summary` over `full` when an agent opens a record or note.
- Keep compact indexes small enough for first-pass scanning.
- Track token baselines with committed, reproducible fixtures.
- Use deterministic summaries, frontmatter filters, and capped result sets
  before adding more complex processing.
- Preserve critical markers during summary reads: headings, links, repository
  names, issue or ticket IDs, commands, dates, decisions, and source
  references.

## What To Measure

Size reduction alone is not enough. A token-efficient memory layer should prove
both of these:

- **Compactness:** repeated tasks consume fewer tokens than reading the root
  files plus every generated index.
- **Recall:** compact views still point the agent to the same relevant records
  and preserve the facts needed for a correct decision.

A useful test set includes several realistic questions, the expected records,
and the specific facts that must survive summary reads. Keep the fixture data
public-safe and synthetic when publishing an open starter kit.

## Common Pitfalls

- **Making full reads the default.** Agents often omit optional parameters, so
  the default should be the cheaper path.
- **Ignoring baselines.** If the old and new retrieval paths are not
  reproducible, future contributors cannot verify the savings.
- **Testing only length.** A shorter summary can still be wrong if it drops the
  ticket, repo, command, or evidence that made the record useful.
- **Hard-coding one organization's schema.** Public examples should show the
  pattern, not require another team to copy project, ticket, or repository
  names.
- **Treating summarization as redaction.** Summaries are not redaction.
  Sensitive data should never enter the memory repo in the first place.

## Public Starter-Pack Guidance

For a public starter kit, document the pattern rather than shipping private
memory data or private measurements. Example values should use placeholders such
as `repo--github--example--service`, `<scope-id>`, `<ticket-id>`, and
`example.com`.

Private teams can then implement the same pattern with their own scripts,
indexes, MCP tools, or local databases.
