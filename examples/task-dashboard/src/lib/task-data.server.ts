import { promises as fs } from 'node:fs'
import path from 'node:path'
import YAML from 'yaml'
import { z } from 'zod'

const packageRoot = process.cwd()
const repoRoot = path.resolve(process.env.BRAINGENT_MEMORY_ROOT ?? path.join(packageRoot, 'sample-memory'))
const tasksRoot = path.join(repoRoot, 'tasks')

const taskStatusSchema = z.enum(['triage', 'ready', 'todo', 'in-progress', 'in-review', 'blocked', 'completed', 'closed'])
const taskPrioritySchema = z.enum(['critical', 'high', 'medium', 'low'])

const frontmatterSchema = z.object({
  id: z.string(),
  record_kind: z.string().optional(),
  title: z.string(),
  status: taskStatusSchema,
  status_category: z.string().nullable().optional(),
  resolution: z.string().nullable().optional(),
  type: z.string().nullable().optional(),
  priority: taskPrioritySchema.catch('medium'),
  owner: z.string().nullable().optional(),
  assignee: z.string().nullable().optional(),
  reviewer: z.string().nullable().optional(),
  observers: z.array(z.string()).catch([]).default([]),
  claimed_by: z.string().nullable().optional(),
  claimed_at: z.string().nullable().optional(),
  created: z.string().nullable().optional(),
  updated: z.string().nullable().optional(),
  date: z.string().nullable().optional(),
  organization: z.string().nullable().optional(),
  project: z.string().nullable().optional(),
  repositories: z.array(z.string()).catch([]).default([]),
  ticket: z.string().nullable().optional(),
  prs: z.array(z.string()).catch([]).default([]),
  commits: z.array(z.string()).catch([]).default([]),
  ai_tools: z.array(z.string()).catch([]).default([]),
  people: z.array(z.string()).catch([]).default([]),
  topics: z.array(z.string()).catch([]).default([]),
  tools: z.array(z.string()).catch([]).default([]),
  parent: z.string().nullable().optional(),
  depends_on: z.array(z.string()).catch([]).default([]),
  duplicate_of: z.string().nullable().optional(),
  closed: z.string().nullable().optional(),
  visibility: z.string().nullable().optional(),
})

export type AgentTaskStatus = z.infer<typeof taskStatusSchema>
export type AgentTaskPriority = z.infer<typeof taskPrioritySchema>

export type AgentTaskActivity = {
  timestamp: string
  actor: string
  role: string
  event: string
  note: string
}

export type AgentTask = {
  id: string
  title: string
  status: AgentTaskStatus
  statusCategory: string
  resolution: string | null
  type: string
  priority: AgentTaskPriority
  assignee: string | null
  reviewer: string | null
  observers: string[]
  claimedBy: string | null
  claimedAt: string | null
  created: string | null
  updated: string | null
  organization: string | null
  project: string | null
  repositories: string[]
  ticket: string | null
  prs: string[]
  commits: string[]
  topics: string[]
  parent: string | null
  dependsOn: string[]
  blocks: string[]
  duplicateOf: string | null
  closed: string | null
  visibility: string
  path: string
  archiveState: 'active' | 'archived'
  description: string
  acceptanceCriteria: string[]
  plan: string
  linkedEvidence: string
  activity: AgentTaskActivity[]
  rawMarkdown: string
}

export type TaskDashboardData = {
  generatedAt: string
  repoRoot: string
  tasks: AgentTask[]
  agents: string[]
  projects: string[]
  repositories: string[]
  counts: Record<AgentTaskStatus, number>
}

type ParsedMarkdown = {
  frontmatter: unknown
  body: string
  rawMarkdown: string
}

async function walkMarkdownFiles(dir: string): Promise<string[]> {
  const entries = await fs.readdir(dir, { withFileTypes: true }).catch(() => [])
  const files = await Promise.all(entries.map(async (entry) => {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      return walkMarkdownFiles(fullPath)
    }
    if (entry.isFile() && entry.name.endsWith('.md') && entry.name.startsWith('BGT-')) {
      return [fullPath]
    }
    return []
  }))
  return files.flat().sort()
}

function splitMarkdown(rawMarkdown: string): ParsedMarkdown | null {
  if (!rawMarkdown.startsWith('---\n')) {
    return null
  }
  const end = rawMarkdown.indexOf('\n---\n', 4)
  if (end === -1) {
    return null
  }
  const rawFrontmatter = rawMarkdown.slice(4, end)
  const body = rawMarkdown.slice(end + '\n---\n'.length)
  return {
    frontmatter: YAML.parse(rawFrontmatter),
    body,
    rawMarkdown,
  }
}

function section(body: string, heading: string): string {
  const pattern = new RegExp(`^## ${heading}\\n`, 'm')
  const match = pattern.exec(body)
  if (!match) {
    return ''
  }
  const start = match.index + match[0].length
  const rest = body.slice(start)
  const next = rest.search(/^## /m)
  return (next === -1 ? rest : rest.slice(0, next)).trim()
}

function listLines(text: string): string[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('- '))
    .map((line) => line.replace(/^- \[[ x]\]\s*/i, '').replace(/^- /, '').trim())
}

function parseActivity(body: string): AgentTaskActivity[] {
  const activity = section(body, 'Activity').split('\n')
  const entries: AgentTaskActivity[] = []
  const entryPattern = /^- ([^|]+) \| ([^|]+) \| role:([^|]+) \| event:([^|]+) \|$/

  for (const line of activity) {
    const match = entryPattern.exec(line.trim())
    if (match) {
      entries.push({
        timestamp: match[1].trim(),
        actor: match[2].trim(),
        role: match[3].trim(),
        event: match[4].trim(),
        note: '',
      })
      continue
    }
    const latest = entries.at(-1)
    if (latest && line.trim()) {
      latest.note = `${latest.note}${latest.note ? '\n' : ''}${line.trim()}`
    }
  }

  return entries
}

function statusCategory(status: AgentTaskStatus): string {
  if (status === 'triage') return 'triage'
  if (status === 'completed' || status === 'closed') return 'closed'
  return 'active'
}

function sortTasks(a: AgentTask, b: AgentTask): number {
  const priorityRank: Record<AgentTaskPriority, number> = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3,
  }
  const statusRank: Record<AgentTaskStatus, number> = {
    triage: 0,
    ready: 1,
    blocked: 2,
    'in-review': 3,
    'in-progress': 4,
    todo: 5,
    completed: 6,
    closed: 7,
  }
  return (
    statusRank[a.status] - statusRank[b.status] ||
    priorityRank[a.priority] - priorityRank[b.priority] ||
    b.updated?.localeCompare(a.updated ?? '') ||
    a.id.localeCompare(b.id)
  )
}

export async function loadTaskDashboard(): Promise<TaskDashboardData> {
  const files = await walkMarkdownFiles(tasksRoot)
  const parsedTasks = await Promise.all(files.map(async (file): Promise<AgentTask | null> => {
    const raw = await fs.readFile(file, 'utf-8')
    const parsed = splitMarkdown(raw)
    if (!parsed) {
      return null
    }
    const result = frontmatterSchema.safeParse(parsed.frontmatter)
    if (!result.success) {
      return null
    }
    const fm = result.data
    const relativePath = path.relative(repoRoot, file).split(path.sep).join('/')
    return {
      id: fm.id,
      title: fm.title,
      status: fm.status,
      statusCategory: fm.status_category ?? statusCategory(fm.status),
      resolution: fm.resolution ?? null,
      type: fm.type ?? 'task',
      priority: fm.priority,
      assignee: fm.assignee ?? fm.owner ?? null,
      reviewer: fm.reviewer ?? null,
      observers: fm.observers,
      claimedBy: fm.claimed_by ?? null,
      claimedAt: fm.claimed_at ?? null,
      created: fm.created ?? fm.date ?? null,
      updated: fm.updated ?? fm.date ?? null,
      organization: fm.organization ?? null,
      project: fm.project ?? null,
      repositories: fm.repositories,
      ticket: fm.ticket ?? null,
      prs: fm.prs,
      commits: fm.commits,
      topics: fm.topics,
      parent: fm.parent ?? null,
      dependsOn: fm.depends_on,
      blocks: [],
      duplicateOf: fm.duplicate_of ?? null,
      closed: fm.closed ?? (fm.status === 'completed' ? fm.updated ?? null : null),
      visibility: fm.visibility ?? 'private',
      path: relativePath,
      archiveState: relativePath.includes('/archive/') ? 'archived' : 'active',
      description: section(parsed.body, 'Description') || section(parsed.body, 'Goal') || section(parsed.body, 'Context'),
      acceptanceCriteria: listLines(section(parsed.body, 'Acceptance Criteria')),
      plan: section(parsed.body, 'Plan'),
      linkedEvidence: section(parsed.body, 'Linked Evidence') || section(parsed.body, 'Closeout'),
      activity: parseActivity(parsed.body),
      rawMarkdown: parsed.rawMarkdown,
    }
  }))

  const tasks = parsedTasks.filter((task): task is AgentTask => task !== null)
  const blocks = new Map<string, string[]>()
  for (const task of tasks) {
    for (const dependency of task.dependsOn) {
      blocks.set(dependency, [...(blocks.get(dependency) ?? []), task.id])
    }
  }
  for (const task of tasks) {
    task.blocks = blocks.get(task.id) ?? []
  }

  const counts: Record<AgentTaskStatus, number> = {
    triage: 0,
    ready: 0,
    todo: 0,
    'in-progress': 0,
    'in-review': 0,
    blocked: 0,
    completed: 0,
    closed: 0,
  }
  for (const task of tasks) {
    counts[task.status] += 1
  }

  return {
    generatedAt: new Date().toISOString(),
    repoRoot,
    tasks: tasks.sort(sortTasks),
    agents: Array.from(new Set(tasks.flatMap((task) => [task.assignee, task.reviewer, task.claimedBy, ...task.observers]).filter(Boolean) as string[])).sort(),
    projects: Array.from(new Set(tasks.map((task) => task.project).filter(Boolean) as string[])).sort(),
    repositories: Array.from(new Set(tasks.flatMap((task) => task.repositories))).sort(),
    counts,
  }
}
