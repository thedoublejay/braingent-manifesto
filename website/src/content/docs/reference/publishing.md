---
title: Publishing
description: Draft publishing reference for braingent.dev.
---

The website is intended to deploy to Cloudflare Pages at `https://braingent.dev`.

## Build

```bash
bun install --frozen-lockfile
bun run build
```

## Output

```text
website/dist
```

## Notes

The workflow scaffold follows the Gather Step website deployment pattern.
