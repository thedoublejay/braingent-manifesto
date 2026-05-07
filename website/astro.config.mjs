// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const siteUrl = 'https://braingent.dev';

// https://astro.build/config
export default defineConfig({
  site: siteUrl,
  integrations: [sitemap()],
});
