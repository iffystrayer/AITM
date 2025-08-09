import { test, expect, TestData } from '../fixtures';

test.describe('Threat Analysis Workflow', () => {
  test.describe.configure({ mode: 'serial' });

  let testProjectName: string;
  
  test.beforeAll(async ({ browser }) => {
    // Create a test project with system inputs for analysis tests
    const context = await browser.newContext();
    const page = await context.newPage();
    
    testProjectName = `Analysis Test Project ${Date.now()}`;
    
    // Create project
    await page.goto('/projects');
    await page.waitForLoadState('networkidle');
    await page.click('text=+ New Project');
    await page.fill('input[placeholder="Enter project name"]', testProjectName);
    await page.fill('textarea[placeholder="Optional project description"]', 'Project for testing analysis workflow');
    await page.click('button:has-text("Create Project")');
    await page.waitForLoadState('networkidle');
    
    // Add system input
    await page.click(`text=${testProjectName}`);
    await page.click('button:has-text("System Inputs")');
    await page.click('button:has-text("+ Add Input")');
    
    await page.fill('input[placeholder*="title"]', TestData.systemInput.title);
    await page.fill('textarea[placeholder*="description"]', TestData.systemInput.description);
    await page.fill('textarea[placeholder*="system description"]', TestData.systemInput.content);
    await page.click('button:has-text("Add System Input")');
    await page.waitForLoadState('networkidle');
    
    await context.close();
  });

  test('should configure and start threat analysis', async ({ projectsPage, projectDetailPage }) => {
    await test.step('Navigate to test project', async () => {
      await projectsPage.goto();
      await projectsPage.page.click(`text=${testProjectName}`);
    });

    await test.step('Navigate to analysis tab', async () => {
      await projectDetailPage.clickTab('analysis');
    });

    await test.step('Verify analysis is available', async () => {
      await expect(projectDetailPage.page.locator('button:has-text("Start Threat Analysis"):not([disabled])')).toBeVisible();
      await expect(projectDetailPage.page.locator('text=Status:').locator('+ span:has-text("idle")')).toBeVisible();
    });

    await test.step('Start analysis configuration', async () => {
      await projectDetailPage.page.click('button:has-text("Start Threat Analysis")');
    });

    await test.step('Configure analysis parameters', async () => {
      // Wait for configuration modal to appear
      await expect(projectDetailPage.page.locator('text=Analysis Configuration, text=Configure Threat Analysis')).toBeVisible({ timeout: 5000 });
      
      // Select LLM provider (test with available option)
      const providerSelect = projectDetailPage.page.locator('select[name="llm_provider"], select:has(option[value="gemini"])', { timeout: 5000 });
      if (await providerSelect.isVisible()) {
        await providerSelect.selectOption('gemini');
      }
      
      // Select analysis depth
      const depthSelect = projectDetailPage.page.locator('select[name="analysis_depth"], select:has(option[value="standard"])');
      if (await depthSelect.isVisible()) {
        await depthSelect.selectOption('standard');
      }
      
      // Enable comprehensive options if available
      const comprehensiveCheck = projectDetailPage.page.locator('input[type="checkbox"][name="comprehensive"], input[type="checkbox"]:near(text*="comprehensive")');
      if (await comprehensiveCheck.isVisible()) {
        await comprehensiveCheck.check();
      }
    });

    await test.step('Submit analysis configuration', async () => {
      await projectDetailPage.page.click('button:has-text("Start Analysis")');
      await projectDetailPage.page.waitForLoadState('networkidle');
    });

    await test.step('Verify analysis started', async () => {
      // Check that analysis status changed to running or processing
      await expect(projectDetailPage.page.locator('text=Status:').locator('+ span')).not.toContainText('idle');
      
      // Should show either running, processing, or completed status
      const statusText = await projectDetailPage.page.locator('text=Status:').locator('+ span').textContent();
      expect(statusText?.toLowerCase()).toMatch(/(running|processing|analyzing|completed)/);
    });
  });

  test('should monitor analysis progress', async ({ projectDetailPage }) => {
    await test.step('Check current analysis status', async () => {
      await projectDetailPage.page.reload();
      await projectDetailPage.clickTab('analysis');
      
      const status = await projectDetailPage.page.locator('text=Status:').locator('+ span').textContent();
      console.log('Current analysis status:', status);
    });

    await test.step('Verify progress indicators exist', async () => {
      const status = await projectDetailPage.page.locator('text=Status:').locator('+ span').textContent();
      
      if (status?.toLowerCase().includes('running')) {
        // Look for progress bar or spinner
        const progressIndicators = projectDetailPage.page.locator('.animate-spin, .progress-bar, [style*="width:"]');
        const hasProgress = await progressIndicators.count() > 0;
        
        if (hasProgress) {
          console.log('✅ Progress indicators found');
        } else {
          console.log('⚠️ No progress indicators visible');
        }
      }
    });

    await test.step('Handle different analysis states', async () => {
      const status = await projectDetailPage.page.locator('text=Status:').locator('+ span').textContent();
      
      if (status?.toLowerCase().includes('completed')) {
        // Analysis completed - should show "View Results" button
        await expect(projectDetailPage.page.locator('button:has-text("View Results")')).toBeVisible();
        console.log('✅ Analysis completed successfully');
      } else if (status?.toLowerCase().includes('running')) {
        // Analysis in progress - should show progress
        console.log('⏳ Analysis in progress...');
      } else if (status?.toLowerCase().includes('failed')) {
        // Analysis failed - should show error message
        console.log('❌ Analysis failed');
        await expect(projectDetailPage.page.locator('text=error, text=failed')).toBeVisible();
      }
    });
  });

  test('should display analysis results when completed', async ({ projectDetailPage }) => {
    await test.step('Check if analysis is completed', async () => {
      await projectDetailPage.page.reload();
      await projectDetailPage.clickTab('analysis');
      
      const status = await projectDetailPage.page.locator('text=Status:').locator('+ span').textContent();
      
      if (!status?.toLowerCase().includes('completed')) {
        test.skip('Analysis not yet completed - skipping results test');
      }
    });

    await test.step('Navigate to results', async () => {
      const viewResultsButton = projectDetailPage.page.locator('button:has-text("View Results")');
      
      if (await viewResultsButton.isVisible()) {
        await viewResultsButton.click();
      } else {
        await projectDetailPage.clickTab('results');
      }
    });

    await test.step('Verify results are displayed', async () => {
      // Look for any results content
      const resultsContent = projectDetailPage.page.locator('[data-testid="analysis-results"], .results-container, text*="Threat", text*="Attack", text*="Risk"');
      const hasResults = await resultsContent.count() > 0;
      
      if (hasResults) {
        console.log('✅ Analysis results displayed');
        
        // Check for common threat modeling elements
        const threats = projectDetailPage.page.locator('text*="threat", text*="attack", text*="technique"');
        if (await threats.count() > 0) {
          console.log('✅ Threat information found in results');
        }
        
        const mitre = projectDetailPage.page.locator('text*="MITRE", text*="ATT&CK", text*="T1", text*="technique"');
        if (await mitre.count() > 0) {
          console.log('✅ MITRE ATT&CK information found in results');
        }
      } else {
        console.log('⚠️ No analysis results content found');
      }
    });

    await test.step('Verify results navigation', async () => {
      // Test different result sections if they exist
      const resultTabs = projectDetailPage.page.locator('button:has-text("Summary"), button:has-text("Attack Paths"), button:has-text("Recommendations")');
      const tabCount = await resultTabs.count();
      
      if (tabCount > 0) {
        console.log(`✅ Found ${tabCount} result section tabs`);
        
        // Click through available tabs
        for (let i = 0; i < tabCount; i++) {
          await resultTabs.nth(i).click();
          await projectDetailPage.page.waitForTimeout(500);
        }
      }
    });
  });

  test('should update project status after analysis', async ({ projectDetailPage }) => {
    await test.step('Check overview for updated status', async () => {
      await projectDetailPage.clickTab('overview');
    });

    await test.step('Verify analysis status in overview', async () => {
      const analysisStatusCard = projectDetailPage.page.locator('text=Analysis Status').locator('..');
      await expect(analysisStatusCard).toBeVisible();
      
      // Should not be "idle" anymore
      await expect(analysisStatusCard.locator('p:has-text("idle")')).not.toBeVisible();
    });

    await test.step('Check for threats found count', async () => {
      const threatsCard = projectDetailPage.page.locator('text=Threats Found').locator('..');
      if (await threatsCard.isVisible()) {
        const threatCount = await threatsCard.locator('p.text-2xl').textContent();
        console.log(`Threats found: ${threatCount}`);
        
        // Should be a number
        expect(threatCount).toMatch(/^\d+$/);
      }
    });
  });

  test('should handle analysis configuration validation', async ({ projectsPage, projectDetailPage }) => {
    await test.step('Create new project for validation testing', async () => {
      await projectsPage.goto();
      const validationProjectName = `Validation Test ${Date.now()}`;
      
      await projectsPage.createProject({
        name: validationProjectName,
        description: 'Project for testing analysis validation'
      });
      
      await projectsPage.page.click(`text=${validationProjectName}`);
    });

    await test.step('Try to start analysis without system inputs', async () => {
      await projectDetailPage.clickTab('analysis');
      
      const startButton = projectDetailPage.page.locator('button:has-text("Start Threat Analysis")');
      await expect(startButton).toBeDisabled();
      await expect(projectDetailPage.page.locator('text=Add system inputs before starting analysis')).toBeVisible();
    });

    await test.step('Add minimal system input', async () => {
      await projectDetailPage.clickTab('inputs');
      await projectDetailPage.page.click('button:has-text("+ Add Input")');
      
      await projectDetailPage.page.fill('input[placeholder*="title"]', 'Minimal System');
      await projectDetailPage.page.fill('textarea[placeholder*="description"]', 'Basic test');
      await projectDetailPage.page.fill('textarea[placeholder*="system description"]', 'Simple web application');
      await projectDetailPage.page.click('button:has-text("Add System Input")');
      await projectDetailPage.page.waitForLoadState('networkidle');
    });

    await test.step('Verify analysis is now enabled', async () => {
      await projectDetailPage.clickTab('analysis');
      await expect(projectDetailPage.page.locator('button:has-text("Start Threat Analysis"):not([disabled])')).toBeVisible();
    });
  });

  test('should handle analysis errors gracefully', async ({ projectDetailPage, page }) => {
    await test.step('Test backend connectivity', async () => {
      // Try to access analysis endpoint directly to test error handling
      const response = await page.request.get('http://127.0.0.1:38527/api/v1/projects/99999/analysis/status');
      expect(response.status()).toBeGreaterThanOrEqual(400); // Should be 404 or other error
    });

    await test.step('Verify UI error handling', async () => {
      await projectDetailPage.goto('99999'); // Non-existent project
      
      // Should show error state
      await expect(projectDetailPage.page.locator('text=Error Loading Project, text=not found')).toBeVisible({ timeout: 10000 });
    });
  });
});
