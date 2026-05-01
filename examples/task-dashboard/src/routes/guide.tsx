import type { ReactNode } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { createServerFn } from '@tanstack/react-start'
import { useQuery } from '@tanstack/react-query'
import {
  BookOpenText,
  ClipboardList,
  CircleCheck,
  CircleDot,
  RefreshCw,
  Lock,
  MessageSquare,
  Table2,
} from 'lucide-react'
import { loadDashboardGuide } from '../lib/guide-data.server'
import { loadTaskDashboard, type AgentTaskStatus, type TaskDashboardData } from '../lib/task-data.server'

const getGuideData = createServerFn({ method: 'GET' }).handler(() => loadDashboardGuide())
const getDashboardData = createServerFn({ method: 'GET' }).handler(() => loadTaskDashboard())

const statuses: AgentTaskStatus[] = ['triage', 'ready', 'in-progress', 'in-review', 'blocked', 'completed', 'closed']

export const Route = createFileRoute('/guide')({
  component: GuidePage,
})

function GuidePage() {
  const guide = useQuery({
    queryKey: ['dashboard-guide'],
    queryFn: () => getGuideData(),
  })
  const dashboard = useQuery({
    queryKey: ['task-dashboard'],
    queryFn: () => getDashboardData(),
  })

  if (guide.isLoading) {
    return (
      <GuideShell dashboard={dashboard.data}>
        <main className="loading">Loading guide...</main>
      </GuideShell>
    )
  }

  if (guide.isError || !guide.data) {
    return (
      <GuideShell dashboard={dashboard.data}>
        <main className="error-state">
          <h1>Could not load dashboard guide</h1>
          <p>{guide.error instanceof Error ? guide.error.message : 'Unknown error'}</p>
        </main>
      </GuideShell>
    )
  }

  return (
    <GuideShell dashboard={dashboard.data}>
      <main className="workspace guide-workspace">
        <header className="topbar">
          <div>
            <h1>Dashboard Guide</h1>
            <p>Live from {guide.data.path}, updated {new Date(guide.data.updatedAt).toLocaleString()}</p>
          </div>
          <button className="icon-button" onClick={() => guide.refetch()} title="Reload guide Markdown">
            <RefreshCw size={18} />
            Refresh Guide
          </button>
        </header>
        <article className="guide-document">
          <MarkdownDocument markdown={guide.data.markdown} />
        </article>
      </main>
    </GuideShell>
  )
}

function GuideShell({ children, dashboard }: { children: ReactNode; dashboard: TaskDashboardData | undefined }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <ClipboardList size={22} />
          <div>
            <strong>Braingent Tasks</strong>
            <span>Markdown source</span>
          </div>
        </div>
        <nav aria-label="Task queues">
          <Link to="/guide" className="sidebar-link">
            <BookOpenText size={16} /> Guide
          </Link>
          <Link to="/" className="sidebar-link">
            <Table2 size={16} /> Queue <Count value={dashboard?.tasks.length ?? 0} />
          </Link>
          {statuses.map((item) => (
            <Link key={item} to="/" className="sidebar-link">
              {iconForStatus(item)} {labelForStatus(item)} <Count value={dashboard?.counts[item] ?? 0} />
            </Link>
          ))}
        </nav>
        <div className="sidebar-section">
          <span>Generated</span>
          <code>{dashboard ? new Date(dashboard.generatedAt).toLocaleTimeString() : 'Loading...'}</code>
        </div>
      </aside>
      {children}
    </div>
  )
}

type MarkdownBlock =
  | { type: 'heading'; level: 1 | 2 | 3; text: string }
  | { type: 'paragraph'; text: string }
  | { type: 'list'; items: string[] }
  | { type: 'code'; code: string; language: string }

function MarkdownDocument({ markdown }: { markdown: string }) {
  return <>{parseMarkdown(markdown).map(renderBlock)}</>
}

function parseMarkdown(markdown: string): MarkdownBlock[] {
  const blocks: MarkdownBlock[] = []
  const lines = markdown.split('\n')
  let index = 0

  while (index < lines.length) {
    const line = lines[index]
    const trimmed = line.trim()

    if (!trimmed) {
      index += 1
      continue
    }

    if (trimmed.startsWith('```')) {
      const language = trimmed.slice(3).trim()
      const code: string[] = []
      index += 1
      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        code.push(lines[index])
        index += 1
      }
      blocks.push({ type: 'code', code: code.join('\n'), language })
      index += 1
      continue
    }

    if (trimmed.startsWith('### ')) {
      blocks.push({ type: 'heading', level: 3, text: trimmed.slice(4) })
      index += 1
      continue
    }

    if (trimmed.startsWith('## ')) {
      blocks.push({ type: 'heading', level: 2, text: trimmed.slice(3) })
      index += 1
      continue
    }

    if (trimmed.startsWith('# ')) {
      blocks.push({ type: 'heading', level: 1, text: trimmed.slice(2) })
      index += 1
      continue
    }

    if (trimmed.startsWith('- ')) {
      const items: string[] = []
      while (index < lines.length && lines[index].trim().startsWith('- ')) {
        items.push(lines[index].trim().slice(2))
        index += 1
      }
      blocks.push({ type: 'list', items })
      continue
    }

    const paragraph: string[] = []
    while (index < lines.length) {
      const current = lines[index].trim()
      if (!current || current.startsWith('# ') || current.startsWith('## ') || current.startsWith('### ') || current.startsWith('- ') || current.startsWith('```')) {
        break
      }
      paragraph.push(current)
      index += 1
    }
    blocks.push({ type: 'paragraph', text: paragraph.join(' ') })
  }

  return blocks
}

function renderBlock(block: MarkdownBlock, index: number) {
  if (block.type === 'heading') {
    if (block.level === 1) return <h1 key={index}>{renderInline(block.text)}</h1>
    if (block.level === 2) return <h2 key={index}>{renderInline(block.text)}</h2>
    return <h3 key={index}>{renderInline(block.text)}</h3>
  }

  if (block.type === 'list') {
    return (
      <ul key={index}>
        {block.items.map((item) => <li key={item}>{renderInline(item)}</li>)}
      </ul>
    )
  }

  if (block.type === 'code') {
    return (
      <pre key={index} data-language={block.language}>
        <code>{block.code}</code>
      </pre>
    )
  }

  return <p key={index}>{renderInline(block.text)}</p>
}

function Count({ value }: { value: number }) {
  return <span className="count">{value}</span>
}

function labelForStatus(status: AgentTaskStatus) {
  if (status === 'in-progress') return 'In Progress'
  if (status === 'in-review') return 'In Review'
  return status[0].toUpperCase() + status.slice(1)
}

function iconForStatus(status: AgentTaskStatus) {
  if (status === 'completed' || status === 'closed') return <CircleCheck size={16} />
  if (status === 'blocked') return <Lock size={16} />
  if (status === 'in-review') return <MessageSquare size={16} />
  return <CircleDot size={16} />
}

function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(`[^`]+`)/g)
  return parts.map((part, index) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index}>{part.slice(1, -1)}</code>
    }
    return part
  })
}
