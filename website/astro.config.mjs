// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const siteUrl = 'https://braingent.dev';
const siteTitle = 'Braingent';
const siteDescription =
  'Git-backed engineering memory for humans and AI agents. Capture decisions, retrieve context, and start future work from evidence instead of scattered chat history.';
const socialImage = `${siteUrl}/og-card.svg`;

// https://astro.build/config
export default defineConfig({
  site: siteUrl,
  integrations: [
    starlight({
      title: siteTitle,
      description: siteDescription,
      favicon: '/favicon/favicon.svg',
      head: [
        {
          tag: 'meta',
          attrs: {
            name: 'theme-color',
            content: '#3a3221',
          },
        },
        {
          tag: 'meta',
          attrs: {
            name: 'robots',
            content: 'index,follow',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'icon',
            type: 'image/svg+xml',
            href: '/favicon/favicon.svg',
          },
        },
        {
          tag: 'link',
          attrs: {
            rel: 'manifest',
            href: '/favicon/site.webmanifest',
          },
        },
        {
          tag: 'meta',
          attrs: {
            property: 'og:image',
            content: socialImage,
          },
        },
        {
          tag: 'meta',
          attrs: {
            property: 'og:image:alt',
            content: `${siteTitle} social preview card`,
          },
        },
        {
          tag: 'meta',
          attrs: {
            name: 'twitter:image',
            content: socialImage,
          },
        },
        {
          tag: 'meta',
          attrs: {
            name: 'twitter:image:alt',
            content: `${siteTitle} social preview card`,
          },
        },
      ],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/thedoublejay/braingent-manifesto',
        },
      ],
      editLink: {
        baseUrl: 'https://github.com/thedoublejay/braingent-manifesto/edit/main/website/',
      },
      disable404Route: true,
      lastUpdated: true,
      pagination: true,
      sidebar: [
        {
          label: 'Overview',
          items: [
            { slug: 'guides/getting-started' },
            { slug: 'about' },
          ],
        },
        {
          label: 'Concepts',
          items: [
            { slug: 'concepts/manifesto' },
            { slug: 'concepts/memory-model' },
            { slug: 'concepts/repository-shape' },
          ],
        },
        {
          label: 'Setup',
          items: [
            { slug: 'guides/installation' },
            { slug: 'guides/cli-workflows' },
            { slug: 'guides/agent-workflows' },
          ],
        },
        {
          label: 'Reference',
          items: [
            { slug: 'reference/configuration' },
            { slug: 'reference/mcp-tools' },
            { slug: 'reference/publishing' },
            { slug: 'changelog' },
          ],
        },
      ],
      customCss: ['./src/styles/custom.css'],
    }),
  ],
});
