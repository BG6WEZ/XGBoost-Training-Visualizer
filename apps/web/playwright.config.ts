import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for frontend E2E tests.
 * 
 * Usage:
 *   npx playwright test
 * 
 * Prerequisites:
 *   1. API server running at http://127.0.0.1:8000
 *   2. PostgreSQL running at localhost:5432
 *   3. Redis running at localhost:6379
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: process.env.WEB_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  /* Auto-start Vite dev server */
  webServer: {
    command: 'npx vite --port 3000',
    url: process.env.WEB_BASE_URL || 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});