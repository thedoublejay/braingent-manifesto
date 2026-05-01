import { expect, test } from '@playwright/test'

test('dashboard renders tasks and supports core interactions', async ({ page }) => {
  const runtimeErrors: string[] = []
  page.on('pageerror', (error) => runtimeErrors.push(`pageerror: ${error.message}`))
  page.on('console', (message) => {
    if (message.type() === 'error') {
      runtimeErrors.push(`console: ${message.text()}`)
    }
  })

  await page.goto('/')

  await expect(page).toHaveTitle('Braingent Tasks')
  await expect(page.locator('html')).toHaveCSS('color-scheme', 'dark')
  await expect(page.locator('body')).toHaveCSS('background-color', 'rgb(0, 0, 0)')
  await expect(page.getByRole('heading', { name: 'Task Queue' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Guide' })).toBeVisible()
  await expect(page.getByRole('button', { name: /Queue \d+/ })).toBeVisible()

  const rows = page.locator('tbody tr')
  await expect(rows.first()).toBeVisible()
  expect(await rows.count()).toBeGreaterThan(0)

  await expect(page.getByLabel('Status')).toContainText('In Progress')
  await expect(page.getByLabel('Status')).toContainText('All')
  await expect(page.getByLabel('Agent')).toContainText('Codex CLI')
  await expect(page.getByLabel('Project')).toContainText('Example / Memory')

  const search = page.getByPlaceholder('Search Tasks, Agents, Repos')
  await search.fill('smoke')
  await expect(page.getByText(/1 visible of \d+ Markdown tasks/)).toBeVisible()
  await expect(page.locator('tbody').getByRole('button', { name: 'BGT-0004', exact: true })).toBeVisible()

  await page.getByRole('button', { name: 'Reset Filters' }).click()
  await expect(search).toHaveValue('')

  await page.locator('tbody').getByRole('button', { name: 'BGT-0003', exact: true }).click()
  await expect(page.locator('.detail-header .eyebrow')).toHaveText('BGT-0003')
  await expect(page.getByRole('heading', { name: 'Review dashboard documentation' })).toBeVisible()
  await expect(page.locator('.metadata-grid div').filter({ hasText: 'Priority' }).locator('dd')).toHaveText('High')
  await expect(page.locator('.metadata-grid div').filter({ hasText: 'Resolution' }).locator('dd')).toHaveText('-')

  await page.locator('.tab-row').getByRole('button', { name: 'Activity' }).click()
  await expect(page.locator('.task-activity')).toContainText('Owner')
  await expect(page.locator('.task-activity')).toContainText('Reviewed')

  await page.locator('.tab-row').getByRole('button', { name: 'Graph' }).click()
  await expect(page.locator('.graph-table')).toContainText('Depends On')
  await expect(page.locator('.graph-table')).toContainText('Duplicate Of')

  await page.locator('.tab-row').getByRole('button', { name: 'Markdown' }).click()
  await expect(page.locator('.raw-markdown')).toContainText('id: BGT-0003')

  const recentActivity = page.locator('.activity-panel')
  await expect(recentActivity).toHaveCSS('height', '390px')
  await expect(recentActivity).toContainText(/Page 1 of \d+/)
  await recentActivity.getByRole('button', { name: 'Next' }).click()
  await expect(recentActivity).toContainText(/Page 2 of \d+/)
  await recentActivity.getByRole('button', { name: 'Previous' }).click()
  await expect(recentActivity).toContainText(/Page 1 of \d+/)

  await page.getByRole('link', { name: 'Guide' }).click()
  await expect(page).toHaveURL(/\/guide$/)
  await expect(page.getByRole('heading', { name: 'Dashboard Guide' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Braingent Tasks Dashboard User Guide' })).toBeVisible()
  await expect(page.getByRole('link', { name: /Queue \d+/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /Completed \d+/ })).toBeVisible()
  await expect(page.getByRole('complementary').getByText('Generated')).toBeVisible()
  await expect(page.getByText('Live from USER-GUIDE.md')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Current Features' })).toBeVisible()
  await expect(page.getByText('Reads sample task Markdown files')).toBeVisible()
  await page.getByRole('button', { name: 'Refresh Guide' }).click()
  await expect(page.getByRole('heading', { name: 'Braingent Tasks Dashboard User Guide' })).toBeVisible()

  expect(runtimeErrors).toEqual([])
})
