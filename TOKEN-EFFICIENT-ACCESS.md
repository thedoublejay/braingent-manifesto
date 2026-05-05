# Token-Efficient Agent Access

Braingent works best when agents retrieve the smallest useful memory first and
only expand when they need more evidence. This keeps sessions cheaper, faster,
and less noisy without weakening the memory system.

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
3. **Compact results:** inspect small result rows with path, title, kind, date,
   project, repository, ticket, and status.
4. **Summary reads:** open summary-depth record bodies by default.
5. **Full reads:** open full records only when a decision, review, or exact
   evidence matters.
6. **Raw imports:** read raw source material only when curated records are not
   enough.

This is the same retrieval ladder as normal Braingent usage, with stricter
defaults around how much text an agent should hydrate at once.

## Recommended Defaults

- Prefer `summary` over `full` when an agent opens a record.
- Keep compact indexes small enough to scan quickly.
- Track token baselines with committed, reproducible fixtures.
- Treat lossy compression as optional and off by default.
- Preserve critical markers during compression: headings, links, repository
  keys, ticket IDs, commands, dates, and source references.

## What To Measure

Size reduction alone is not enough. A token-efficient memory layer should prove
both of these:

- **Compactness:** repeated tasks consume fewer tokens than reading the root
  files and every generated index.
- **Recall:** compressed summaries still preserve the facts an agent needs to
  make a correct decision.

A useful test set includes several realistic questions, the expected records,
and the specific facts that must survive summary or compression.

## Common Pitfalls

- **Making full reads the default.** Agents often omit optional parameters, so
  the default should be the cheaper path.
- **Ignoring baselines.** If the pre-compression baseline is not committed or
  reproducible, future contributors cannot verify the savings.
- **Testing only length.** A shorter summary can still be wrong if it drops the
  ticket, repo, command, or evidence that made the record useful.
- **Compressing secrets.** Compression is not redaction. Sensitive data should
  never enter the memory repo in the first place.

## Public Starter-Pack Guidance

For a public starter kit, document the pattern rather than shipping private
memory data or private measurements. Example values should use placeholders such
as `repo--github--example--service`, `<ticket-id>`, and `example.com`.

Private teams can then implement the same pattern with their own scripts,
indexes, MCP tools, or local databases.
