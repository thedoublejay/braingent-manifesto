import { defineConfig, devices } from '@playwright/test'

const port = Number(process.env.BRAINGENT_DASHBOARD_PORT ?? 4321)
const baseURL = process.env.BRAINGENT_DASHBOARD_URL ?? `http://127.0.0.1:${port}`

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  reporter: process.env.CI ? 'github' : 'line',
  use: {
    baseURL,
    trace: 'on-first-retry',
  },
  webServer: {
    command: `bun run dev --host 127.0.0.1 --port ${port}`,
    url: baseURL,
    reuseExistingServer: true,
    timeout: 30_000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 1000 },
      },
    },
  ],
})
