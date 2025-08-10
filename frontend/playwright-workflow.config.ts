import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['html'], ['line']],
  use: {
    baseURL: 'http://127.0.0.1:59000',
    trace: 'on',
    screenshot: 'on',
    video: 'on',
    actionTimeout: 15000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  timeout: 300 * 1000,
  expect: {
    timeout: 10 * 1000
  },
});
