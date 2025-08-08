import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 800  // Slower for better demonstration
  });
  
  const context = await browser.newContext({
    recordVideo: {
      dir: './videos/',
      size: { width: 1920, height: 1080 }  // Higher resolution for analytics
    }
  });
  
  const page = await context.newPage();
  
  console.log('🎬 Starting AITM Advanced Analytics Demo...');
  
  try {
    // Step 1: Navigate to dashboard
    console.log('🏠 Loading main dashboard...');
    await page.goto('http://localhost:41241');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Step 2: Navigate to Analytics page
    console.log('📊 Navigating to Analytics Dashboard...');
    await page.goto('http://localhost:41241/analytics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Step 3: Wait for data to load and explore the overview
    console.log('📈 Exploring threat intelligence overview...');
    await page.waitForTimeout(2000);
    
    // Scroll through the dashboard to show all metrics
    await page.evaluate(() => window.scrollTo(0, 400));
    await page.waitForTimeout(1500);
    await page.evaluate(() => window.scrollTo(0, 800));
    await page.waitForTimeout(1500);
    
    // Step 4: Navigate through different tabs
    console.log('🔍 Exploring threat landscape...');
    const threatsTab = await page.locator('button:has-text("Threat Landscape")').first();
    if (await threatsTab.isVisible()) {
      await threatsTab.click();
      await page.waitForTimeout(2000);
      await page.evaluate(() => window.scrollTo(0, 600));
      await page.waitForTimeout(2000);
    }
    
    console.log('📊 Viewing risk trends...');
    const trendsTab = await page.locator('button:has-text("Risk Trends")').first();
    if (await trendsTab.isVisible()) {
      await trendsTab.click();
      await page.waitForTimeout(2000);
      await page.evaluate(() => window.scrollTo(0, 400));
      await page.waitForTimeout(2000);
    }
    
    console.log('🛡️ Analyzing MITRE coverage...');
    const mitreTab = await page.locator('button:has-text("MITRE Coverage")').first();
    if (await mitreTab.isVisible()) {
      await mitreTab.click();
      await page.waitForTimeout(2000);
      await page.evaluate(() => window.scrollTo(0, 600));
      await page.waitForTimeout(2000);
    }
    
    // Step 5: Return to overview to show complete dashboard
    console.log('🔄 Returning to overview...');
    const overviewTab = await page.locator('button:has-text("Overview")').first();
    if (await overviewTab.isVisible()) {
      await overviewTab.click();
      await page.waitForTimeout(2000);
    }
    
    // Step 6: Interact with the threat intel feed
    console.log('🔍 Examining threat intelligence feed...');
    await page.evaluate(() => window.scrollTo(0, 800));
    await page.waitForTimeout(2000);
    
    // Step 7: Navigate to projects to show integration
    console.log('📁 Navigating to projects for context...');
    await page.goto('http://localhost:41241/projects');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Step 8: Show a project with results
    const completedProject = await page.locator('text=Demo Project with Results').first();
    if (await completedProject.isVisible()) {
      const viewDetailsLink = await page.locator('text=Demo Project with Results').locator('..').locator('text=View Details →').first();
      if (await viewDetailsLink.isVisible()) {
        await viewDetailsLink.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        // Show the analysis results in context
        const resultsTab = await page.locator('button:has-text("Results"), a:has-text("Results")').first();
        if (await resultsTab.isVisible()) {
          await resultsTab.click();
          await page.waitForTimeout(2000);
          await page.evaluate(() => window.scrollTo(0, 600));
          await page.waitForTimeout(2000);
        }
      }
    }
    
    // Step 9: Return to analytics for final overview
    console.log('🎯 Returning to analytics for final overview...');
    await page.goto('http://localhost:41241/analytics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Final scroll through the complete dashboard
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(1000);
    await page.evaluate(() => window.scrollTo(0, 400));
    await page.waitForTimeout(1000);
    await page.evaluate(() => window.scrollTo(0, 800));
    await page.waitForTimeout(1000);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(2000);
    
    console.log('✅ Advanced Analytics Demo completed successfully!');
    
  } catch (error) {
    console.error('❌ Error during analytics demo:', error);
    await page.screenshot({ path: './analytics-error.png', fullPage: true });
  } finally {
    await browser.close();
    console.log('🎥 Analytics demo video saved to ./videos/ directory');
  }
})();
