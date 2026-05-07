# Braingent Website

Astro landing page for `https://braingent.dev`.

This mirrors the Gather Step website setup:

- Bun package manager.
- Astro landing page at `/`.
- Static build output in `dist/`.
- Cloudflare Pages deployment via Wrangler.

## Commands

```bash
bun install
bun run dev
bun run build
```

## Deployment

The Cloudflare Pages build command is:

```bash
bun install --frozen-lockfile && bun run build
```

The output directory is:

```text
website/dist
```

The intended production domain is `https://braingent.dev`.
