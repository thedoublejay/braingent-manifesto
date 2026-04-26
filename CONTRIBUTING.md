# Contributing

Braingent Manifesto is a Markdown-only public guide. Contributions should improve the clarity, safety, portability, or usefulness of the setup.

## Good Contributions

- clearer setup instructions
- better templates
- safer privacy guidance
- more tool-agnostic agent instructions
- practical workflows
- public-safe examples
- corrections to naming or taxonomy guidance

## Keep It Public-Safe

Do not add:

- secrets
- credentials
- tokens
- private repository names
- private organization names
- customer data
- sensitive personal data
- local workspace paths
- internal ticket links
- private PR links

Use placeholders instead.

## Style

- Use Markdown.
- Use ASCII text.
- Prefer concise sections and tables.
- Keep examples generic.
- Explain why a convention exists.
- Keep root docs useful for first-time readers.

## Before Opening A PR

Run a manual safety sweep:

```bash
rg -n "token|secret|password|api_key|apikey|private key" .
rg -n "/Users/|/home/|C:\\\\" .
rg -n "@|http|https|customer|client|internal" .
```

Review matches manually.

