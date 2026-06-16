# Engineering Defaults

Standing rules for tech choices. Apply unless a project-level decision overrides them.

## Dependency And Runtime Versions

- **New / evergreen projects:** use the latest stable version of every dependency, package manager, runtime (Node, Bun, Python, Rust, etc.), and build tool. No reflexive "pin to last LTS" out of habit.
- **Existing projects:** read the lockfile / `package.json` / `Cargo.toml` / `pyproject.toml` first. Do not propose a bump unless the new version is materially beneficial (security fix, needed feature, dropped peer dep, deprecation deadline). Flag major-version bumps as separate work, not bundled with the current task.
- When suggesting a new dependency, **state the exact version** to pin and why.
- Before recommending the latest, do a quick check for known regressions in the most recent release. If a `.0` major just dropped, default to `.x` minor on a stable previous major unless the user wants the bleeding edge.

## Library Selection

Prefer **proven, actively maintained** libraries:

- Maintenance signals: recent commits (within ~6 months), open issues being triaged, releases on a regular cadence, more than one maintainer.
- Adoption signals: weekly downloads (npm/PyPI/crates.io), GitHub stars, mentions in mainstream docs, presence in popular frameworks' ecosystems.
- **Confirm before suggesting:** if a library has low downloads, no recent releases, single-maintainer risk, or no published changelog, flag the risk explicitly and ask before adopting it. Do not silently introduce risky deps.
- For trivial functionality already available in the standard library or an existing dependency, use that. Do not pull in a new package for a 10-line helper.
- Combined rule: pick a *proven* library, then use its *latest stable* version.

## Architecture And Reuse

Before writing new code:

1. **Read the surrounding architecture** — folder structure, naming, boundaries between layers, where similar features already live.
2. **Match the existing style** — but only when it makes sense. If the project's convention is poor for the task at hand, flag it; don't blindly inherit it.
3. **Reuse first, recreate last** — if a component, hook, helper, util, or service already exists in this project (or a standard library) that solves the problem, use it. Do not recreate.
4. **Use the project's own building blocks before pulling in a new dependency.**

## CI And GitHub Actions

- New workflows: use the **latest stable** versions of every action (`actions/checkout@v4`, `actions/setup-node@v4`, `actions/setup-python@v5`, etc.).
- When editing existing workflows, **report any actions still pinned to old majors** as a follow-up. Don't bundle the upgrade into an unrelated task unless explicitly asked.
- Pin to a major version (`@v4`) for evergreen actions; pin to a SHA only when supply-chain hardening is the explicit goal.
- Treat outdated runner images, node versions in matrix configs, and deprecated commands the same way: report as follow-up.
