import { defineConfig, devices } from '@playwright/test';

/**
 * Frontend-only Playwright configuration for UI testing without backend dependencies
 * 
 * This config bypasses the global setup that checks for backend services,
 * allowing pure frontend UI testing and demonstration.
 */
export default defineConfig({
  testDir: './tests/e2e',
  /* Run tests in files in parallel */
  fullyParallel: false,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html'],
    ['list'],
    ['junit', { outputFile: 'test-results/junit-report.xml' }]
  ],

  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:59000',
    
    /* Enable full recording for frontend demo */
    trace: 'on',
    screenshot: 'on', 
    video: 'on',
    
    /* Ignore HTTPS errors */
    ignoreHTTPSErrors: true,
    
    /* Timeout for each action */
    actionTimeout: 30000,
    
    /* Timeout for navigation */
    navigationTimeout: 30000,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Test against mobile viewports. */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /* Test against branded browsers. */
    {
      name: 'Microsoft Edge',
      use: { ...devices['Desktop Edge'], channel: 'msedge' },
    },
    {
      name: 'Google Chrome',
      use: { ...devices['Desktop Chrome'], channel: 'chrome' },
    },
  ],

  /* Output directory for test artifacts */
  outputDir: 'test-results/',
  
  /* Timeout for each test */
  timeout: 60000,
  
  /* Timeout for the entire test run */
  globalTimeout: 300000, // 5 minutes
  
  /* Expect timeout */
  expect: {
    timeout: 10000
  },

  /* NO GLOBAL SETUP - This allows frontend-only testing */
  // globalSetup: undefined,  // Explicitly disable global setup
  // globalTeardown: undefined, // Explicitly disable global teardown
});
