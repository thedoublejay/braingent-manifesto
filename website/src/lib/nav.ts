export interface NavItem {
  title: string;
  slug: string;
  badge?: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const docsNav: NavSection[] = [
  {
    title: 'Introduction',
    items: [
      { title: 'What is Braingent', slug: 'intro/what-is-braingent' },
      { title: 'Why Braingent is Different', slug: 'intro/why-different' },
      { title: 'The Manifesto', slug: 'intro/manifesto' },
    ],
  },
  {
    title: 'Get Started',
    items: [
      { title: 'Quickstart', slug: 'guides/getting-started', badge: '10 min' },
      { title: 'Installation', slug: 'guides/installation' },
      { title: 'Wire Up Your Agents', slug: 'guides/wire-up-agents' },
    ],
  },
  {
    title: 'Core Concepts',
    items: [
      { title: 'Memory Model', slug: 'concepts/memory-model' },
      { title: 'Repository Shape', slug: 'concepts/repository-shape' },
      { title: 'Record Kinds', slug: 'concepts/record-kinds' },
      { title: 'Frontmatter Schema', slug: 'concepts/frontmatter-schema' },
    ],
  },
  {
    title: 'Guides',
    items: [
      { title: 'Agent Workflows', slug: 'guides/agent-workflows' },
      { title: 'The Capture Loop', slug: 'guides/capture-loop' },
      { title: 'Search & Recall', slug: 'guides/search-and-recall' },
      { title: 'Multi-Agent Coordination', slug: 'guides/multi-agent-tasks' },
      { title: 'Index Your Repos', slug: 'guides/index-your-repos' },
      { title: 'QA Test Planning', slug: 'guides/qa-test-planning', badge: 'Flagship' },
      { title: 'Local Dashboard', slug: 'guides/dashboard' },
      { title: 'Keeping Memory Healthy', slug: 'guides/maintenance' },
      { title: 'CLI Workflows', slug: 'guides/cli-workflows' },
    ],
  },
  {
    title: 'Integrations',
    items: [
      { title: 'Overview', slug: 'integrations/overview' },
      { title: 'Claude', slug: 'integrations/claude' },
      { title: 'Codex', slug: 'integrations/codex' },
      { title: 'ChatGPT', slug: 'integrations/chatgpt' },
      { title: 'Gemini CLI', slug: 'integrations/gemini-cli' },
      { title: 'Gather Step', slug: 'integrations/gather-step', badge: 'Partner' },
    ],
  },
  {
    title: 'Reference',
    items: [
      { title: 'CLI Commands', slug: 'reference/cli' },
      { title: 'MCP Tools', slug: 'reference/mcp-tools' },
      { title: 'Configuration', slug: 'reference/configuration' },
      { title: 'Publishing', slug: 'reference/publishing' },
    ],
  },
  {
    title: 'Resources',
    items: [
      { title: 'About', slug: 'about' },
      { title: 'Changelog', slug: 'changelog' },
    ],
  },
];

export function flatNav(): NavItem[] {
  return docsNav.flatMap((s) => s.items);
}

export function findAdjacent(slug: string) {
  const flat = flatNav();
  const i = flat.findIndex((n) => n.slug === slug);
  return {
    prev: i > 0 ? flat[i - 1] : null,
    next: i >= 0 && i < flat.length - 1 ? flat[i + 1] : null,
  };
}

export function findSectionFor(slug: string): NavSection | undefined {
  return docsNav.find((s) => s.items.some((i) => i.slug === slug));
}
