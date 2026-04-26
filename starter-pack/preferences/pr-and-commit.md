# PR And Commit Hygiene

Use this checklist before committing memory or code changes.

## Pre-Commit Checklist

1. Simplify the diff.
2. Remove dead code, stale comments, debug logs, and unused imports.
3. Scan for secrets.
4. Scan for sensitive personal data.
5. Avoid local machine paths unless the record is private and the path is necessary.
6. Keep unrelated changes out of the commit.
7. Use a clear commit message.

## PR Description Shape

When writing PR descriptions, include:

- Summary.
- Motivation.
- Approach.
- Tradeoffs or alternatives.
- Verification.
- Migration or rollout notes, when relevant.
- Follow-ups.

## Memory Commits

For memory-only commits, use messages like:

```text
Capture <short subject>
Add <repo> profile
Record <decision subject>
Update memory current state
```

Do not add `Co-Authored-By` trailers unless you explicitly want them.

