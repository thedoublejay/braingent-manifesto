# Files Needed

This guide separates the minimum viable Braingent setup from the recommended full setup.

## Minimum Viable Setup

You can start with only these files:

```text
README.md
AGENTS.md
INDEX.md
CURRENT_STATE.md
preferences/agent-workflow.md
preferences/capture-policy.md
preferences/naming.md
preferences/privacy-and-safety.md
templates/task-record.md
templates/decision-record.md
templates/learning-record.md
```

This is enough to:

- tell agents how to use the repo
- define naming
- define capture rules
- create task, decision, and learning records
- avoid unsafe capture

## Recommended Setup

The starter pack includes the broader structure:

```text
README.md
AGENTS.md
CLAUDE.md
CHATGPT_PROJECT_BRIEF.md
INDEX.md
CURRENT_STATE.md
preferences/
templates/
workflows/
orgs/
repositories/
topics/
tools/
people/
tickets/
inbox/
imports/
indexes/
```

Use this if you want the memory to work across multiple AI tools and projects.

## File Purpose Summary

| File | Required? | Why it exists |
| --- | --- | --- |
| `README.md` | Yes | Explains the memory repo. |
| `AGENTS.md` | Yes for Codex | Gives Codex-style agents instructions. |
| `CLAUDE.md` | Yes for Claude | Gives Claude-style agents instructions. |
| `CHATGPT_PROJECT_BRIEF.md` | Optional | Copyable ChatGPT project setup. |
| `INDEX.md` | Yes | Manual map of the memory. |
| `CURRENT_STATE.md` | Yes | Current context and active defaults. |
| `preferences/naming.md` | Yes | Prevents naming drift. |
| `preferences/agent-workflow.md` | Yes | Defines search, plan, work, capture loop. |
| `preferences/capture-policy.md` | Yes | Defines what to capture and when. |
| `preferences/taxonomy.md` | Recommended | Defines allowed record kinds, statuses, and prefixes. |
| `preferences/search-recipes.md` | Recommended | Helps humans and agents find records. |
| `preferences/content-style.md` | Recommended | Keeps notes useful and concise. |
| `preferences/planning.md` | Recommended | Standardizes plans. |
| `preferences/code-review.md` | Recommended | Standardizes review output. |
| `preferences/pr-and-commit.md` | Recommended | Keeps commits and PRs clean. |
| `preferences/privacy-and-safety.md` | Yes | Prevents unsafe capture. |
| `templates/*.md` | Yes | Makes record creation consistent. |
| `workflows/*.md` | Optional | Encodes repeatable procedures. |

## Installation Needed

For the Markdown-only version:

- no installation required

Recommended:

- Git for version history
- ripgrep for fast search
- an AI coding assistant that can read local files

Optional later:

- YAML tooling for frontmatter validation
- JSON tooling for generated indexes
- SQLite for local search cache
- GitHub CLI for PR imports
- issue tracker access for ticket imports

## What To Customize First

1. Repo name.
2. Timezone.
3. Organization keys.
4. Project keys.
5. Repository profiles.
6. AI tool entrypoints.
7. Capture triggers.
8. Required metadata fields.
9. Privacy policy.

## What To Leave Generic

If you plan to publish your setup:

- keep examples generic
- avoid local paths
- avoid private organization names
- avoid private tickets
- avoid real PR links
- avoid customer data
- avoid internal domains

