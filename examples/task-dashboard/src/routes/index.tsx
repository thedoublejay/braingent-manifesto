import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { createServerFn } from '@tanstack/react-start'
import { useQuery } from '@tanstack/react-query'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import {
  Activity,
  Archive,
  BookOpenText,
  CircleCheck,
  CircleDot,
  ClipboardList,
  GitBranch,
  GitPullRequest,
  Link2,
  ListFilter,
  Lock,
  MessageSquare,
  RefreshCw,
  Search,
  Table2,
  UserRound,
} from 'lucide-react'
import { loadTaskDashboard, type AgentTask, type AgentTaskStatus } from '../lib/task-data.server'

const getDashboardData = createServerFn({ method: 'GET' }).handler(() => loadTaskDashboard())

export const Route = createFileRoute('/')({
  component: TasksDashboard,
})

const statuses: AgentTaskStatus[] = ['triage', 'ready', 'in-progress', 'in-review', 'blocked', 'completed', 'closed']
const activityPageSize = 6

function TasksDashboard() {
  const dashboard = useQuery({
    queryKey: ['task-dashboard'],
    queryFn: () => getDashboardData(),
  })

  const [status, setStatus] = useState<AgentTaskStatus | 'all'>('all')
  const [agent, setAgent] = useState('all')
  const [project, setProject] = useState('all')
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [tab, setTab] = useState<'overview' | 'activity' | 'graph' | 'markdown'>('overview')
  const [activityPage, setActivityPage] = useState(0)

  const data = dashboard.data
  const tasks = data?.tasks ?? []
  const filteredTasks = useMemo(() => {
    const q = query.trim().toLowerCase()
    return tasks.filter((task) => {
      if (status !== 'all' && task.status !== status) return false
      if (agent !== 'all' && ![task.assignee, task.reviewer, task.claimedBy, ...task.observers].includes(agent)) return false
      if (project !== 'all' && task.project !== project) return false
      if (!q) return true
      return [
        task.id,
        task.title,
        task.status,
        task.priority,
        task.assignee,
        task.reviewer,
        task.project,
        task.repositories.join(' '),
        task.description,
      ].join(' ').toLowerCase().includes(q)
    })
  }, [agent, project, query, status, tasks])

  const selectedTask = tasks.find((task) => task.id === selectedId) ?? filteredTasks[0] ?? tasks[0] ?? null

  const columns = useMemo<ColumnDef<AgentTask>[]>(() => [
    {
      accessorKey: 'id',
      header: 'ID',
      cell: ({ row }) => <button className="link-button" onClick={() => setSelectedId(row.original.id)}>{row.original.id}</button>,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => <StatusBadge status={row.original.status} />,
    },
    {
      accessorKey: 'priority',
      header: 'Priority',
      cell: ({ row }) => <PriorityBadge priority={row.original.priority} />,
    },
    {
      accessorKey: 'title',
      header: 'Task',
      cell: ({ row }) => (
        <button className="task-title" onClick={() => setSelectedId(row.original.id)}>
          <span>{row.original.title}</span>
          <small>{row.original.path}</small>
        </button>
      ),
    },
    {
      accessorKey: 'assignee',
      header: 'Assignee',
      cell: ({ row }) => <DisplayValue value={row.original.assignee} />,
    },
    {
      accessorKey: 'reviewer',
      header: 'Reviewer',
      cell: ({ row }) => <DisplayValue value={row.original.reviewer} />,
    },
    {
      accessorKey: 'updated',
      header: 'Updated',
      cell: ({ row }) => <TextValue value={row.original.updated} />,
    },
  ], [])

  const table = useReactTable({
    data: filteredTasks,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (dashboard.isLoading) {
    return <Shell><main className="loading">Loading task files...</main></Shell>
  }

  if (dashboard.isError || !data) {
    return (
      <Shell>
        <main className="error-state">
          <h1>Could not load Braingent tasks</h1>
          <p>{dashboard.error instanceof Error ? dashboard.error.message : 'Unknown error'}</p>
        </main>
      </Shell>
    )
  }

  const recentActivity = tasks
    .flatMap((task) => task.activity.map((item) => ({ ...item, taskId: task.id, taskTitle: task.title })))
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  const activityPageCount = Math.max(1, Math.ceil(recentActivity.length / activityPageSize))
  const currentActivityPage = Math.min(activityPage, activityPageCount - 1)
  const pagedActivity = recentActivity.slice(currentActivityPage * activityPageSize, (currentActivityPage + 1) * activityPageSize)

  return (
    <Shell>
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
          <button className={status === 'all' ? 'active' : ''} onClick={() => setStatus('all')}>
            <Table2 size={16} /> Queue <Count value={tasks.length} />
          </button>
          {statuses.map((item) => (
            <button key={item} className={status === item ? 'active' : ''} onClick={() => setStatus(item)}>
              {iconForStatus(item)} {labelForStatus(item)} <Count value={data.counts[item]} />
            </button>
          ))}
        </nav>
        <div className="sidebar-section">
          <span>Generated</span>
          <code>{new Date(data.generatedAt).toLocaleTimeString()}</code>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>Task Queue</h1>
            <p>{filteredTasks.length} visible of {tasks.length} Markdown tasks</p>
          </div>
          <button className="icon-button" onClick={() => dashboard.refetch()} title="Refresh task files">
            <RefreshCw size={18} />
            Refresh
          </button>
        </header>

        <section className="toolbar" aria-label="Task filters">
          <label className="search-field">
            <Search size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search Tasks, Agents, Repos" />
          </label>
          <Select label="Status" value={status} onChange={(value) => setStatus(value as AgentTaskStatus | 'all')} values={['all', ...statuses]} />
          <Select label="Agent" value={agent} onChange={setAgent} values={['all', ...data.agents]} />
          <Select label="Project" value={project} onChange={setProject} values={['all', ...data.projects]} />
          <button className="secondary-button" onClick={() => { setStatus('all'); setAgent('all'); setProject('all'); setQuery('') }}>
            <ListFilter size={16} />
            Reset Filters
          </button>
        </section>

        <div className="content-grid">
          <section className="queue-panel" aria-label="Task queue table">
            <table>
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr key={row.id} className={selectedTask?.id === row.original.id ? 'selected-row' : ''}>
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <TaskDetail task={selectedTask} tab={tab} setTab={setTab} />
        </div>

        <section className="activity-panel">
          <div className="section-heading">
            <Activity size={17} />
            <h2>Recent Activity</h2>
          </div>
          <div className="activity-list-frame">
            {pagedActivity.length ? (
              <ol className="activity-list">
                {pagedActivity.map((item) => (
                  <li key={`${item.taskId}-${item.timestamp}-${item.event}`}>
                    <time>{item.timestamp}</time>
                    <strong>{item.taskId}</strong>
                    <span>{displayLabel(item.actor)}</span>
                    <em>{displayLabel(item.event)}</em>
                    <p>{item.note}</p>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="empty-copy">No Recent Activity</p>
            )}
          </div>
          <div className="pagination-row" aria-label="Recent activity pages">
            <span>
              Page {currentActivityPage + 1} of {activityPageCount}
            </span>
            <div>
              <button className="secondary-button" disabled={currentActivityPage === 0} onClick={() => setActivityPage((page) => Math.max(0, page - 1))}>
                Previous
              </button>
              <button
                className="secondary-button"
                disabled={currentActivityPage >= activityPageCount - 1}
                onClick={() => setActivityPage((page) => Math.min(activityPageCount - 1, page + 1))}
              >
                Next
              </button>
            </div>
          </div>
        </section>
      </main>
    </Shell>
  )
}

function Shell({ children }: { children: ReactNode }) {
  return <div className="app-shell">{children}</div>
}

function TaskDetail({
  task,
  tab,
  setTab,
}: {
  task: AgentTask | null
  tab: 'overview' | 'activity' | 'graph' | 'markdown'
  setTab: (tab: 'overview' | 'activity' | 'graph' | 'markdown') => void
}) {
  if (!task) {
    return (
      <section className="detail-panel empty">
        <h2>No Tasks</h2>
      </section>
    )
  }

  return (
    <section className="detail-panel" aria-label="Task detail">
      <div className="detail-header">
        <div>
          <span className="eyebrow">{task.id}</span>
          <h2>{task.title}</h2>
        </div>
        <StatusBadge status={task.status} />
      </div>
      <div className="tab-row" role="tablist">
        {(['overview', 'activity', 'graph', 'markdown'] as const).map((item) => (
          <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>{displayLabel(item)}</button>
        ))}
      </div>
      {tab === 'overview' && (
        <div className="detail-scroll">
          <dl className="metadata-grid">
            <Meta label="Assignee" value={task.assignee} icon={<UserRound size={15} />} />
            <Meta label="Reviewer" value={task.reviewer} icon={<MessageSquare size={15} />} />
            <Meta label="Priority" value={task.priority} />
            <Meta label="Project" value={task.project} />
            <Meta label="Visibility" value={task.visibility} icon={<Lock size={15} />} />
            <Meta label="Resolution" value={task.resolution} icon={<CircleCheck size={15} />} />
          </dl>
          <div className="detail-section">
            <h3>Description</h3>
            <p>{task.description || 'No description.'}</p>
          </div>
          <div className="detail-section">
            <h3>Acceptance Criteria</h3>
            <ul>{task.acceptanceCriteria.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
          <div className="detail-section">
            <h3>Linked Evidence</h3>
            <pre>{task.linkedEvidence || 'No linked evidence.'}</pre>
          </div>
        </div>
      )}
      {tab === 'activity' && (
        <ol className="task-activity">
          {task.activity.map((item) => (
            <li key={`${item.timestamp}-${item.event}`}>
              <time>{item.timestamp}</time>
              <strong>{displayLabel(item.actor)}</strong>
              <span>{displayLabel(item.role)}</span>
              <em>{displayLabel(item.event)}</em>
              <p>{item.note}</p>
            </li>
          ))}
        </ol>
      )}
      {tab === 'graph' && (
        <div className="graph-table">
          <GraphRow icon={<GitBranch size={16} />} label="Depends On" values={task.dependsOn} />
          <GraphRow icon={<Link2 size={16} />} label="Blocks" values={task.blocks} />
          <GraphRow icon={<Archive size={16} />} label="Parent" values={task.parent ? [task.parent] : []} />
          <GraphRow icon={<GitPullRequest size={16} />} label="Duplicate Of" values={task.duplicateOf ? [task.duplicateOf] : []} />
        </div>
      )}
      {tab === 'markdown' && <pre className="raw-markdown">{task.rawMarkdown}</pre>}
    </section>
  )
}

function Count({ value }: { value: number }) {
  return <span className="count">{value}</span>
}

function Select({ label, value, values, onChange }: { label: string; value: string; values: string[]; onChange: (value: string) => void }) {
  return (
    <label className="select-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {values.map((item) => <option key={item} value={item}>{displayLabel(item)}</option>)}
      </select>
    </label>
  )
}

function TextValue({ value }: { value: string | null | undefined }) {
  return <span className={value ? 'text-value' : 'muted'}>{value || '-'}</span>
}

function DisplayValue({ value }: { value: string | null | undefined }) {
  return <span className={value ? 'text-value' : 'muted'}>{displayLabel(value)}</span>
}

function Meta({ label, value, icon }: { label: string; value: string | null | undefined; icon?: ReactNode }) {
  return (
    <div>
      <dt>{icon}{label}</dt>
      <dd>{displayLabel(value)}</dd>
    </div>
  )
}

function GraphRow({ icon, label, values }: { icon: ReactNode; label: string; values: string[] }) {
  return (
    <div>
      <span>{icon}{label}</span>
      <strong>{values.length ? values.join(', ') : '-'}</strong>
    </div>
  )
}

function StatusBadge({ status }: { status: AgentTaskStatus }) {
  return <span className={`badge status-${status}`}>{labelForStatus(status)}</span>
}

function PriorityBadge({ priority }: { priority: string }) {
  return <span className={`badge priority-${priority}`}>{displayLabel(priority)}</span>
}

function labelForStatus(status: AgentTaskStatus) {
  if (status === 'in-progress') return 'In Progress'
  if (status === 'in-review') return 'In Review'
  return status[0].toUpperCase() + status.slice(1)
}

function displayLabel(value: string | null | undefined) {
  if (!value) return '-'
  if (value === 'all') return 'All'
  if ((statuses as string[]).includes(value)) return labelForStatus(value as AgentTaskStatus)

  const trimmed = value
    .replace(/^agent--/, '')
    .replace(/^project--/, '')
    .replace(/^org--/, '')
    .replace(/^repo--/, '')
    .replace(/^topic--/, '')
    .replace(/^tool--/, '')

  return trimmed
    .split('--')
    .map((part) => part.split('-').map(titleWord).join(' '))
    .join(' / ')
}

function titleWord(word: string) {
  const uppercaseWords: Record<string, string> = {
    ai: 'AI',
    api: 'API',
    cli: 'CLI',
    css: 'CSS',
    html: 'HTML',
    id: 'ID',
    ids: 'IDs',
    js: 'JS',
    json: 'JSON',
    markdown: 'Markdown',
    pr: 'PR',
    prs: 'PRs',
    ui: 'UI',
    ux: 'UX',
    yaml: 'YAML',
  }
  const normalized = word.toLowerCase()
  return uppercaseWords[normalized] ?? `${normalized.charAt(0).toUpperCase()}${normalized.slice(1)}`
}

function iconForStatus(status: AgentTaskStatus) {
  if (status === 'completed' || status === 'closed') return <CircleCheck size={16} />
  if (status === 'blocked') return <Lock size={16} />
  if (status === 'in-review') return <MessageSquare size={16} />
  return <CircleDot size={16} />
}
