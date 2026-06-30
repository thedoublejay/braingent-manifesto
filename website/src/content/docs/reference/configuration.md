---
title: Configuration
description: Optional configuration knobs for the braingent CLI — most users never need them. Defaults are designed to be right.
section: Reference
order: 3
---

Braingent works with no configuration. The defaults are the smallest set that
makes search, capture, and validation work out of the box, and the built-in
secret checks below are always on. If you want to tune behavior, the CLI reads
an optional `config.toml`.

## Configuration sources, in priority order

Higher in this list wins.

1. **Command flags** (`--limit`, `--stale-days`, etc.).
2. **Repo-local config** — `.braingent/config.toml` inside the memory repo.
3. **User-level config** — `~/.braingent/config.toml`.
4. **Built-in defaults**.

Scalar values (like `stale_days`) follow this precedence directly. List values
under `[safety]` and the `[factcheck]` domain lists are **additive**: repo and
user entries are appended to the built-in defaults, never replacing them.

Selecting *which* repo to operate on is separate from the config file: use the
`--root` flag or the `BRAINGENT_ROOT` environment variable.

`braingent doctor` parses both config files and reports any problems (malformed
TOML, wrong types, invalid regex) under its **Config issues** section; `doctor
--strict` exits non-zero when there are any.

## Example `config.toml`

Everything is optional — include only the sections you want to change.

```toml
# .braingent/config.toml  (or ~/.braingent/config.toml)

[safety]
# Extra regexes flagged as a hard failure by `braingent doctor`.
# Added to the always-on built-ins (AWS/GitHub/Google/OpenAI keys, PEM blocks).
forbid_patterns = [
  "ACME-INTERNAL-[0-9]+",
]
# Literal strings that must never appear in committed Markdown
# (e.g. a private absolute path on your machine).
forbid_paths = [
  "/Users/alice/secrets",
]

[doctor]
# Age threshold (days) for the stale-record check. Default: 180.
stale_days = 180

[recall]
# Defaults for `braingent recall` (flags still override).
limit = 8
stale_days = 180

[task_ids]
# Format for new agent-task IDs. Default: BGT-NNNN, zero-padded to 4.
# Set this BEFORE creating tasks — changing it later orphans existing IDs.
prefix = "BGT"
pad = 4

[factcheck]
# Topics that opt a record into `braingent factcheck` when it has no
# `verification` field. A record with a `verification` field is always in scope.
scope_topics = ["company-research", "deep-research"]
# Source-credibility tiers. Domain lists are additive to sensible defaults
# (PR-wire and tier-1-2 press ship pre-filled; slop starts empty).
slop_domains = ["contentfarm.example", "ai-rewrite-mill.example"]
prwire_domains = ["myindustrywire.example"]
tier12_domains = ["mytrustedjournal.example"]
```

## What each section does

| Section / key | Effect |
| --- | --- |
| `[safety] forbid_patterns` | Extra regexes scanned across record bodies by `doctor`. Matches are hard failures. Added to the built-ins. |
| `[safety] forbid_paths` | Literal substrings that must not appear in committed Markdown. Matches are hard failures. |
| `[doctor] stale_days` | Default age threshold for the stale-record warning. |
| `[recall] limit` | Default number of must-read records `recall` returns. |
| `[recall] stale_days` | Default age threshold `recall` uses to classify stale records. |
| `[task_ids] prefix` / `pad` | Prefix and zero-pad width for generated task IDs (and the matching validation). |
| `[factcheck] scope_topics` | Topics that opt a record into `factcheck` when it has no `verification` field. Additive. |
| `[factcheck] slop_domains` / `prwire_domains` / `tier12_domains` | Source-credibility tiers used by `factcheck`. Additive to the built-in defaults. |

The built-in `[safety]` patterns are always active even with no config file, so
`doctor` flags common secret formats out of the box.

## What is NOT configured here

Some behavior lives in the memory repo's Markdown, not in `config.toml`:

- **Capture trigger phrases** — `preferences/capture-policy.md`. Capture is
  driven by your AI agent reading that file, not by the CLI.
- **Taxonomy / allowed status values** — `preferences/taxonomy.yml`, which
  `braingent validate` checks against.
- **Repository layout** — see [Repository Shape](/concepts/repository-shape/).

## MCP server

The MCP server reads its repo path from CLI args, not a config file. See
[Installation → Enable MCP Retrieval](/guides/installation/#enable-mcp-retrieval).

## Where to go next

- [CLI Reference](/reference/cli/) — every flag for every command.
- [Frontmatter Schema](/concepts/frontmatter-schema/) — what `validate` checks.
- [Repository Shape](/concepts/repository-shape/) — the layout defaults assume.
