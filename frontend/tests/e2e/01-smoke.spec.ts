import { test, expect } from '../fixtures';

test.describe('AITM Application Smoke Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test('should load the dashboard successfully', async ({ dashboardPage }) => {
    await test.step('Navigate to dashboard', async () => {
      await dashboardPage.goto();
    });

    await test.step('Verify page title', async () => {
      await expect(dashboardPage.page).toHaveTitle(/AITM - AI-Powered Threat Modeler/);
    });

    await test.step('Verify main heading is present', async () => {
      await expect(dashboardPage.page.locator('main h1')).toContainText('AITM');
    });

    await test.step('Verify feature list is displayed', async () => {
      await expect(dashboardPage.page.locator('text=MVP Features Ready')).toBeVisible();
      await expect(dashboardPage.page.locator('h4:has-text("Multi-Agent System")')).toBeVisible();
      await expect(dashboardPage.page.locator('h4:has-text("LLM Integration")')).toBeVisible();
      await expect(dashboardPage.page.locator('h4:has-text("MITRE ATT&CK")')).toBeVisible();
      await expect(dashboardPage.page.locator('h4:has-text("REST API")')).toBeVisible();
    });
  });

  test('should verify backend connectivity', async ({ dashboardPage }) => {
    await test.step('Navigate to dashboard', async () => {
      await dashboardPage.goto();
    });

    await test.step('Wait for backend status check', async () => {
      // Wait for the backend status to be updated
      await dashboardPage.page.waitForFunction(
        () => {
          const statusElement = document.querySelector('dd');
          return statusElement && !statusElement.textContent?.includes('checking...');
        },
        { timeout: 15000 }
      );
    });

    await test.step('Verify backend is online', async () => {
      const backendStatus = await dashboardPage.page.locator('[data-testid="backend-status"] dd, dd:has-text("Backend Online"), dd:has-text("✅")').first().textContent();
      expect(backendStatus).toMatch(/(✅ Backend Online|Backend Online|healthy)/);
    });
  });

  test('should have working quick access links', async ({ dashboardPage, page }) => {
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

  test('should navigate between pages', async ({ navigation, page }) => {
    await test.step('Start from dashboard', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    });

    await test.step('Navigate to Projects', async () => {
      await navigation.navigateToProjects();
      expect(page.url()).toContain('/projects');
      await expect(page.locator('h2:has-text("Threat Modeling Projects")')).toBeVisible();
    });

    await test.step('Navigate to Analysis', async () => {
      await navigation.navigateToAnalysis();
      expect(page.url()).toContain('/analysis');
    });

    await test.step('Navigate to Assets', async () => {
      await navigation.navigateToAssets();
      expect(page.url()).toContain('/assets');
    });

    await test.step('Navigate to Reports', async () => {
      await navigation.navigateToReports();
      expect(page.url()).toContain('/reports');
    });

    await test.step('Navigate back to Dashboard', async () => {
      await navigation.navigateToDashboard();
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
      // Verify that elements are laid out horizontally on desktop
      const statusCards = page.locator('.grid-cols-1.gap-6.sm\\:grid-cols-2.lg\\:grid-cols-3');
      await expect(statusCards).toBeVisible();
    });

    await test.step('Test tablet viewport', async () => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(500); // Allow layout to adjust
      
      // Elements should still be visible
      await expect(page.locator('h1:has-text("AITM")')).toBeVisible();
    });

    await test.step('Test mobile viewport', async () => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      
      // Elements should stack vertically on mobile
      await expect(page.locator('h1:has-text("AITM")')).toBeVisible();
    });
  });
});
