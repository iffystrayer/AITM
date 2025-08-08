import { chromium } from 'playwright';

(async () => {
  // Launch browser with video recording
  const browser = await chromium.launch({ 
    headless: false,  // Show the browser for demo
    slowMo: 500       // Slow down actions for video
  });
  
  const context = await browser.newContext({
    recordVideo: {
      dir: './videos/',
      size: { width: 1280, height: 720 }
    }
  });
  
  const page = await context.newPage();
  
  console.log('🎬 Starting AITM Demo Workflow...');
  
  try {
    // Step 1: Navigate to the application
    console.log('📱 Navigating to AITM application...');
    await page.goto('http://localhost:41241');
    await page.waitForTimeout(2000);
    
    // Step 2: Go to Projects page
    console.log('📁 Navigating to Projects page...');
    await page.click('a[href="/projects"]');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Step 3: Create a new project
    console.log('➕ Creating a new project...');
    await page.click('text=+ New Project');
    await page.waitForSelector('.fixed.inset-0'); // Wait for modal
    
    await page.fill('input[placeholder="Enter project name"]', 'Demo Banking Application');
    await page.fill('textarea[placeholder="Optional project description"]', 
      'A comprehensive mobile banking application with user authentication, account management, fund transfers, and payment processing.');
    
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Step 4: Navigate to the newly created project
    console.log('🔍 Opening project details...');
    await page.click('text=Demo Banking Application');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // If we're not on the project detail page, try clicking "View Details"
    if (!(await page.url().includes('/projects/'))) {
      await page.click('text=View Details →');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    }
    
    // Step 5: Add system inputs
    console.log('📝 Adding system inputs...');
    
    // Check if there's an "Add Input" button or form
    const addInputButton = await page.locator('text=Add System Input').first();
    if (await addInputButton.isVisible()) {
      await addInputButton.click();
      await page.waitForTimeout(500);
      
      // Fill out the system input form
      await page.fill('textarea[placeholder*="system"]', 
        'Mobile banking application built with Flutter for mobile clients, Spring Boot backend, PostgreSQL database, and AWS cloud infrastructure. Features include user authentication via OAuth2, account balance inquiries, fund transfers between accounts, bill payments, and push notifications.');
      
      const submitButton = await page.locator('button:has-text("Add Input")').first();
      if (await submitButton.isVisible()) {
        await submitButton.click();
        await page.waitForLoadState('networkidle');
      }
    }
    
    await page.waitForTimeout(1000);
    
    // Step 6: Start threat analysis
    console.log('🔬 Starting threat analysis...');
    
    // Look for "Start Analysis" button
    const startAnalysisButton = await page.locator('button:has-text("Start Analysis")').first();
    if (await startAnalysisButton.isVisible()) {
      await startAnalysisButton.click();
      await page.waitForTimeout(2000);
      
      // If there's a configuration modal, fill it out
      if (await page.locator('.modal, .fixed.inset-0').isVisible()) {
        // Select analysis options if available
        const standardDepth = await page.locator('input[value="standard"]').first();
        if (await standardDepth.isVisible()) {
          await standardDepth.click();
        }
        
        const confirmButton = await page.locator('button:has-text("Start")').first();
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
          await page.waitForLoadState('networkidle');
        }
      }
    }
    
    await page.waitForTimeout(2000);
    
    // Step 7: Navigate to a completed project to show results
    console.log('📊 Viewing analysis results...');
    await page.goto('http://localhost:41241/projects');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Find and click on the "Demo Project with Results" (project 2)
    const completedProject = await page.locator('text=Demo Project with Results').first();
    if (await completedProject.isVisible()) {
      // Try to click the project name or view details
      const viewDetailsLink = await page.locator('text=Demo Project with Results').locator('..').locator('text=View Details →').first();
      if (await viewDetailsLink.isVisible()) {
        await viewDetailsLink.click();
      } else {
        await completedProject.click();
      }
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Navigate through the tabs to show different sections
      console.log('📈 Exploring analysis results...');
      
      // Click on Results tab if available
      const resultsTab = await page.locator('button:has-text("Results"), a:has-text("Results")').first();
      if (await resultsTab.isVisible()) {
        await resultsTab.click();
        await page.waitForTimeout(2000);
        
        // Scroll through the results
        await page.evaluate(() => window.scrollTo(0, 400));
        await page.waitForTimeout(1000);
        await page.evaluate(() => window.scrollTo(0, 800));
        await page.waitForTimeout(1000);
        await page.evaluate(() => window.scrollTo(0, 0));
      }
      
      // Check attack paths
      const attackPathsTab = await page.locator('button:has-text("Attack Paths"), a:has-text("Attack Paths")').first();
      if (await attackPathsTab.isVisible()) {
        await attackPathsTab.click();
        await page.waitForTimeout(2000);
      }
      
      // Check recommendations
      const recommendationsTab = await page.locator('button:has-text("Recommendations"), a:has-text("Recommendations")').first();
      if (await recommendationsTab.isVisible()) {
        await recommendationsTab.click();
        await page.waitForTimeout(2000);
      }
    }
    
    // Step 8: Show the dashboard
    console.log('🏠 Returning to dashboard...');
    await page.goto('http://localhost:41241');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    console.log('✅ Demo workflow completed successfully!');
    
  } catch (error) {
    console.error('❌ Error during demo:', error);
    
    // Take a screenshot of the current state
    await page.screenshot({ path: './error-screenshot.png', fullPage: true });
  } finally {
    // Close the browser
    await browser.close();
    console.log('🎥 Video saved to ./videos/ directory');
  }
})();
