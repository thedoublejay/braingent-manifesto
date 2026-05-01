# Privacy And Safety

Braingent is useful only if it stays safe to search, commit, and share within the intended audience.

## Never Capture

- Passwords.
- API keys.
- Access tokens.
- Refresh tokens.
- SSH private keys.
- Cloud credentials.
- Database credentials.
- Session cookies.
- Customer secrets.
- Private URLs that should not leave their context.
- Sensitive personal data.
- Full private chat transcripts unless temporarily retained with a clear reason.

## Be Careful With

- Real name~s.
- Email addresses.
- Phone numbers.
- Employee IDs.
- Customer IDs.
- Internal domains.
- Screenshots.
- Logs.
- Ticket comments.
- PR comments.
- Stack traces.
- Live task activity copied from private work.
- Dashboard screenshots that reveal private task titles, people, repos, or tickets.

When in doubt, summarize rather than copy.

## Redaction Pattern

Use clear placeholders:

```text
<redacted-token>
<redacted-email>
<redacted-customer>
<internal-url-redacted>
```

Do not replace sensitive values with fake values that look real. Fake credentials can still confuse future agents.

## Public Repo Rule

The `braingent-manifesto` repo should contain only public-safe instructions, examples, and templates.

It may say "created by JJ Adonis" because that attribution is intentional.

It should not include:

- local workspace paths
- private repository names
- private organization names
- customer references
- real ticket IDs from private systems
- private commit hashes
- private PR links
- machine-specific config
- real live task queues
- dashboard exports or screenshots from private memory repos

## Personal Memory Repo Rule

Your private Braingent repo can contain private engineering context if that is appropriate for your work, but it should still avoid secrets and sensitive personal data.

If a record needs evidence from a private source, link to the private source instead of copying sensitive content.

## Before Publishing

Run a manual sweep:

```bash
rg -n "token|secret|password|apikey|api_key|private key|BEGIN .* PRIVATE KEY" .
rg -n "@|http|https|customer|client|internal" .
rg -n "/Users/|/home/|C:\\\\" .
rg -n "REG-[0-9]+|JIRA|Linear|customer|internal|private" .
```

Review matches manually. These commands are not proof of safety, but they catch common mistakes.
