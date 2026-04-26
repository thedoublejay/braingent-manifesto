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

## Manual Search

```bash
rg -n "token|secret|password|api_key|apikey|private key" .
rg -n "/Users/|/home/|C:\\\\" .
rg -n "@|customer|client|internal" .
```

Review every match before publishing.

