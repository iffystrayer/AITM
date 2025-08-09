import { test, expect } from '../fixtures';

test.describe('AITM Application Smoke Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test('should load the dashboard successfully', async ({ dashboardPage }) => {
    await test.step('Navigate to dashboard', async () => {
      await dashboardPage.goto();
    });

    await test.step('Verify page title', async () => {
      await expect(dashboardPage.page).toHaveTitle(/AITM - Threat Intelligence Dashboard/);
    });

    await test.step('Verify main heading is present', async () => {
      await expect(dashboardPage.page.locator('h1:has-text("Threat Intelligence Dashboard")')).toBeVisible();
    });

    await test.step('Verify analytics dashboard elements', async () => {
      // Wait for dashboard data to load
      await dashboardPage.page.waitForTimeout(2000);
      
      // Check for key analytics elements
      await expect(dashboardPage.page.locator('text=Real-time analytics and insights')).toBeVisible();
      await expect(dashboardPage.page.locator('select')).toBeVisible(); // Time range selector
      await expect(dashboardPage.page.locator('button:has-text("Refresh")')).toBeVisible();
    });
  });

  test('should verify backend connectivity', async ({ dashboardPage }) => {
    await test.step('Navigate to dashboard', async () => {
      await dashboardPage.goto();
    });

    await test.step('Wait for dashboard to load analytics data', async () => {
      // Wait for the dashboard to load data (not showing loading spinner)
      await dashboardPage.page.waitForFunction(
        () => {
          const loadingSpinner = document.querySelector('[class*="animate-spin"]');
          return !loadingSpinner || loadingSpinner.offsetParent === null;
        },
        { timeout: 15000 }
      );
    });

    await test.step('Verify analytics dashboard loads successfully', async () => {
      // Check that we have metric cards loaded (indicating successful backend connection)
      await expect(dashboardPage.page.locator('text=Total Projects')).toBeVisible({ timeout: 10000 });
      await expect(dashboardPage.page.locator('text=Average Risk Score')).toBeVisible();
      await expect(dashboardPage.page.locator('text=Analysis Confidence')).toBeVisible();
    });
  });

  test.skip('should have working quick access links', async ({ dashboardPage, page }) => {
    // Skip this test as the new AnalyticsDashboard doesn't have quick access links
    // TODO: Re-implement when quick access links are added to the new dashboard
    await test.step('Navigate to dashboard', async () => {
      await dashboardPage.goto();
    });

    await test.step('Test API Documentation link', async () => {
      // Open link in new tab and verify it loads
      const [newPage] = await Promise.all([
        page.context().waitForEvent('page'),
        dashboardPage.clickAPIDocumentation()
      ]);

      await newPage.waitForLoadState('networkidle');
      expect(newPage.url()).toContain('127.0.0.1:38527/docs');
      await expect(newPage.locator('#swagger-ui')).toBeVisible({ timeout: 10000 });
      await newPage.close();
    });

    await test.step('Test Health Check link', async () => {
      const [newPage] = await Promise.all([
        page.context().waitForEvent('page'),
        dashboardPage.clickHealthCheck()
      ]);

      await newPage.waitForLoadState('networkidle');
      expect(newPage.url()).toContain('127.0.0.1:38527/health');
      
      const healthContent = await newPage.textContent('body');
      expect(healthContent).toMatch(/(healthy|status)/);
      await newPage.close();
    });
  });

  test('should load projects page', async ({ projectsPage }) => {
    await test.step('Navigate to projects', async () => {
      await projectsPage.goto();
    });

    await test.step('Verify projects page loads', async () => {
      await expect(projectsPage.page).toHaveTitle(/Projects - AITM/);
      await projectsPage.waitForProjectsLoad();
    });

    await test.step('Verify page elements', async () => {
      await expect(projectsPage.page.locator('h2')).toContainText('Threat Modeling Projects');
      await expect(projectsPage.page.locator('text=+ New Project')).toBeVisible();
    });
  });

  test('should navigate between pages', async ({ page }) => {
    await test.step('Start from dashboard', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      expect(page.url()).toBe('http://127.0.0.1:59000/');
    });

    await test.step('Navigate to Projects', async () => {
      await page.goto('/projects');
      await page.waitForLoadState('networkidle');
      expect(page.url()).toContain('/projects');
      await expect(page.locator('h2:has-text("Threat Modeling Projects")')).toBeVisible();
    });

    await test.step('Navigate to Analysis', async () => {
      await page.goto('/analysis');
      await page.waitForLoadState('networkidle');
      expect(page.url()).toContain('/analysis');
    });

    await test.step('Navigate to Assets', async () => {
      await page.goto('/assets');
      await page.waitForLoadState('networkidle');
      expect(page.url()).toContain('/assets');
    });

    await test.step('Navigate to Reports', async () => {
      await page.goto('/reports');
      await page.waitForLoadState('networkidle');
      expect(page.url()).toContain('/reports');
    });

    await test.step('Navigate back to Dashboard', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      expect(page.url()).toBe('http://127.0.0.1:59000/');
    });
  });

  test('should handle responsive design', async ({ page }) => {
    await test.step('Load dashboard on desktop', async () => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    await test.step('Verify desktop layout', async () => {
      // Verify that metric cards are laid out in a grid on desktop
      const metricGrid = page.locator('.grid.grid-cols-1.md\\:grid-cols-2.lg\\:grid-cols-4');
      await expect(metricGrid).toBeVisible();
    });

    await test.step('Test tablet viewport', async () => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(500); // Allow layout to adjust
      
      // Elements should still be visible
      await expect(page.locator('h1:has-text("Threat Intelligence Dashboard")')).toBeVisible();
    });

    await test.step('Test mobile viewport', async () => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      
      // Elements should stack vertically on mobile
      await expect(page.locator('h1:has-text("Threat Intelligence Dashboard")')).toBeVisible();
    });
  });
});
