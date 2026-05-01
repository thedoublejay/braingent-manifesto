# Privacy And Safety

This memory repo must be safe to search and commit.

## Never Store

- passwords
- API keys
- access tokens
- refresh tokens
- SSH private keys
- cloud credentials
- database credentials
- session cookies
- customer secrets
- sensitive personal data
- real private task queues or dashboard screenshots

## Prefer Links And Summaries

If evidence lives in a private ticket, PR, log, or chat:

- summarize the relevant point
- link to the source if appropriate
- do not copy sensitive content

## Public-Safe Placeholder Style

Use:

```text
<repo-url>
<ticket-id>
<redacted-token>
<redacted-email>
<internal-url-redacted>
```

Do not invent realistic fake secrets.

## Safety Sweep

Before publishing or sharing:

```bash
rg -n "token|secret|password|api_key|apikey|private key" .
rg -n "/Users/|/home/|C:\\\\" .
rg -n "@|http|https|customer|client|internal|private" .
rg -n "Jira|Linear" .
```

Review matches manually.
