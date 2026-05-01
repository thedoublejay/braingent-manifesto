# Publishing Checklist

Use this before publishing a Braingent-style repo or example.

## Content

- [ ] README explains what Braingent is.
- [ ] Setup guide can be followed by a new user.
- [ ] File tree is accurate.
- [ ] Starter pack is Markdown-only.
- [ ] Agent instructions exist for Codex and Claude.
- [ ] ChatGPT project brief exists.
- [ ] Templates cover task, review, decision, learning, profile, version, interaction, ticket, and import summary records.
- [ ] Optional live-work docs explain `agent-task`, `BGT-NNNN`, closeout, stale rules, and dashboard boundaries.
- [ ] Generated index docs cover records, follow-ups, memory summary, stale candidates, task queue, and task graph.
- [ ] Privacy guidance is clear.
- [ ] License file exists.

## Safety

- [ ] No secrets.
- [ ] No tokens.
- [ ] No private keys.
- [ ] No local workspace paths.
- [ ] No private organization names.
- [ ] No private repository names.
- [ ] No real private tickets.
- [ ] No sensitive personal data.
- [ ] Examples use placeholders.
- [ ] Live task examples are synthetic.
- [ ] Dashboard screenshots or fixtures, if any, are synthetic.

## Manual Search

```bash
rg -n "token|secret|password|api_key|apikey|private key" .
rg -n "/Users/|/home/|C:\\\\" .
rg -n "@|customer|client|internal|private" .
rg -n "REG-[0-9]+|JIRA|Linear" .
```

Review every match before publishing.
