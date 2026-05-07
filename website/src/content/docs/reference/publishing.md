---
title: Publishing
description: How braingent.dev is built and deployed — and how to fork the site for your own docs.
section: Reference
order: 4
---

The Braingent website is a regular Astro site. It builds locally with
Bun, deploys static output to a CDN, and uses a content collection for
docs. There's nothing exotic.

## Stack

- **Astro** — site framework.
- **Bun** — runtime + package manager.
- **`@astrojs/sitemap`** — sitemap generation.
- **Markdown** — every doc page in `src/content/docs/`.

No Tailwind, no React runtime, no CMS. The CSS is hand-written; the JS
is `<script is:inline>` for the few interactive bits.

## Build

```bash
cd website
bun install --frozen-lockfile
bun run build
```

Output:

```text
website/dist/
```

You can preview the production build locally:

```bash
bun run preview
```

## Dev server

```bash
bun run dev
```

Opens on `http://localhost:4321`. Hot-reload for `.astro`, `.md`, and
CSS changes.

## Deploying

The site is designed to deploy to any static host. The reference deploy
is **Cloudflare Pages** with the project root pointed at `website/`:

- Build command: `bun install --frozen-lockfile && bun run build`
- Build output: `website/dist`
- Node/Bun version: pinned via `package.json` `packageManager`.

Other hosts (Netlify, Vercel, GitHub Pages, S3 + CloudFront) work
identically — feed them `website/dist`.

## Content authoring

Docs live in `src/content/docs/`, organized by section:

```
src/content/docs/
├── intro/
├── guides/
├── concepts/
├── integrations/
├── reference/
├── about.md
└── changelog.md
```

Each Markdown file has standard frontmatter:

```yaml
---
title: My Page Title
description: One-sentence summary for SEO and social cards.
section: Guides
order: 5
badge: Optional badge text
---
```

The sidebar nav is defined in `src/lib/nav.ts`. Add new pages there.

## Forking the site for your own docs

The site is MIT-licensed along with the rest of the manifesto. To fork:

1. Copy `website/` into your own repo.
2. Update `astro.config.mjs` with your domain.
3. Replace `src/content/docs/**` with your content.
4. Edit `src/lib/nav.ts` to match your IA.
5. Update `src/pages/index.astro` for your landing.
6. Update favicons in `public/favicon/`.
7. Build and deploy.

The parchment design system in `src/styles/landing.css` and
`src/styles/docs.css` is yours to keep, modify, or replace.

## Where to go next

- [About](/about/) — what the project is.
- [Changelog](/changelog/) — what shipped recently.
