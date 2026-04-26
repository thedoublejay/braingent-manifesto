# Naming

Naming is optimized for search, automation, Git, and long-term use.

## Entity Keys

Use stable directory keys:

```text
entity-kind--scope-or-system--slug
```

Allowed entity kinds:

- `org`
- `project`
- `repo`
- `ticket`
- `person`
- `tool`
- `topic`

Examples:

```text
org--personal
project--personal--memory
repo--github--owner--repo-name
ticket--github--owner-repo-123
person--first-last
tool--node
topic--testing
```

## Record Filenames

Use this format:

```text
yyyy-mm-dd--record-kind--short-subject.md
```

Rules:

- Date is the capture date.
- Use lowercase ASCII.
- Use `--` between machine-readable segments.
- Use `-` inside slugs.
- Keep the subject short and specific.
- Do not include every ticket, PR, repo, or generated ID in the filename unless needed to disambiguate.
- If a filename collision occurs, append `--2`, `--3`, and so on.

Allowed record kinds:

- `task`
- `review`
- `decision`
- `learning`
- `interaction`
- `version`
- `note`
- `summary`
- `profile`
- `ticket-stub`

## Where Records Go

- Organization/project work: `orgs/<org>/projects/<project>/records/`
- Repository profiles: `repositories/<repo-key>/README.md`
- Topic learnings: `topics/<topic-key>/records/`
- Tool notes: `tools/<tool-key>/records/`
- People interaction notes: `people/<person-key>/records/`
- Cross-cutting tickets: `tickets/<ticket-key>/README.md`
- Unsorted notes: `inbox/`
- Import summaries: `imports/summaries/`

## Frontmatter

Every durable record starts with YAML frontmatter. Frontmatter is the source of truth for metadata; the body is for human context.

