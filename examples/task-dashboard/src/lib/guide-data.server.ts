import { promises as fs } from 'node:fs'
import path from 'node:path'

const packageRoot = path.resolve(process.cwd())
const guidePath = path.join(packageRoot, 'USER-GUIDE.md')

export type DashboardGuide = {
  markdown: string
  path: string
  updatedAt: string
}

export async function loadDashboardGuide(): Promise<DashboardGuide> {
  const [markdown, stat] = await Promise.all([
    fs.readFile(guidePath, 'utf-8'),
    fs.stat(guidePath),
  ])

  return {
    markdown,
    path: path.relative(packageRoot, guidePath),
    updatedAt: stat.mtime.toISOString(),
  }
}
