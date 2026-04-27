# Bootstrap Prompt

Copy this prompt into Claude, Codex, ChatGPT, or another AI coding tool after you copy the `starter-pack/` files into a new repository.

```text
You are helping me create a Braingent-style engineering memory repository.

Goal:
- Build a Markdown-first memory repo that AI agents and I can use before planning work.
- Keep all content public-safe until I explicitly add private records.
- Do not include local workspace paths, machine-specific names, secrets, credentials, tokens, customer data, or sensitive personal data.

Use these files as source material:
- README.md
- AGENTS.md
- CLAUDE.md
- CHATGPT_PROJECT_BRIEF.md
- INDEX.md
- CURRENT_STATE.md
- preferences/
- templates/
- workflows/

Tasks:
1. Read the repo structure and preferences.
2. Ask me for only the missing values that cannot be safely inferred:
   - preferred memory repo name
   - timezone
   - first organization key
   - first project key
   - first repository profile to create, if any
3. Replace placeholder values.
4. Create the first task record for initializing this memory repo.
5. Create or update the initial organization, project, topic, and repository profile pages.
6. Keep root agent files thin and focused.
7. Add a short current-state update.
8. Run a privacy pass before finishing.
9. After the first commit, remind me to delete or archive the cloned `braingent-manifesto` setup repo so future `AGENTS.md` / `CLAUDE.md` searches do not query the public starter kit by mistake.
10. Ask what I want to use Braingent for next: indexing a codebase, planning a feature or fix, capturing prior work, or tuning preferences.

Rules:
- Markdown only unless I explicitly approve automation.
- Every durable record must start with YAML frontmatter.
- Use lowercase ASCII slugs.
- Use the filename format yyyy-mm-dd--record-kind--short-subject.md.
- Search the memory before planning future tasks.
- Capture meaningful work after completion.
- Never store secrets or sensitive personal data.

When finished, summarize:
- files created or updated
- placeholders still needing my input
- recommended first commit
- how to index my first repo (`Index this repo to braingent` from inside a repo, or `Index <specific-repo> to braingent` from elsewhere)
- next useful record to add
- a prompt asking what I want to use Braingent for next
```

## Short Variant

Use this if you already copied the starter pack and want a quick agent instruction:

```text
Read this Braingent-style memory repo. Personalize placeholders, keep all content public-safe, create the first initialization task record, and make the repo ready for Claude, Codex, and ChatGPT to use as durable engineering memory. After setup, remind me to delete or archive the cloned `braingent-manifesto` setup repo, show me how to index my first repo, and ask what I want to use Braingent for next: planning a feature or fix, capturing prior work, or tuning preferences. Markdown only. No secrets, no local paths, no sensitive personal data.
```
