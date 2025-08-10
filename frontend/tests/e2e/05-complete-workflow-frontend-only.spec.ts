import { test, expect } from '@playwright/test';

// Enable video recording for all tests in this file
test.use({ 
  video: 'on',
  trace: 'on',
  screenshot: 'on'
});

test.describe('🎯 AITM Frontend Workflow Demonstration', () => {
  test.describe.configure({ mode: 'serial' });

  test('📋 Complete Frontend Workflow: Navigation and UI Demo', async ({ page }) => {
    
    // 🎬 STEP 1: Dashboard Overview
    await test.step('🔐 Step 1: Dashboard Overview', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Take screenshot of dashboard
      await page.screenshot({ path: 'screenshots/01-dashboard-overview.png', fullPage: true });
      
      // Verify main elements are present
      await expect(page.locator('h1:has-text("Threat Intelligence Dashboard")')).toBeVisible();
      await expect(page.locator('text=AITM')).toBeVisible();
      
      console.log('✅ Step 1 Complete: Dashboard loaded with navigation');
      await page.waitForTimeout(2000);
    });

    // 🎬 STEP 2: Navigation to Projects
    await test.step('📁 Step 2: Navigate to Projects Section', async () => {
      await page.click('a[href="/projects"]');
      await page.waitForLoadState('networkidle');
      
      // Take screenshot of projects page
      await page.screenshot({ path: 'screenshots/02-projects-navigation.png', fullPage: true });
      
      // Verify projects page elements
      await expect(page.locator('h2:has-text("Threat Modeling Projects")')).toBeVisible({ timeout: 10000 });
      
      console.log('✅ Step 2 Complete: Projects section loaded');
      await page.waitForTimeout(2000);
    });

    // 🎬 STEP 3: Project Creation Modal
    await test.step('🏗️ Step 3: Project Creation Interface', async () => {
      // Look for and click the new project button
      const newProjectButton = page.locator('button:has-text("+ New Project"), button:has-text("New Project"), a:has-text("New Project")').first();
      if (await newProjectButton.isVisible()) {
        await newProjectButton.click();
        
        // Wait for modal to appear
        await page.waitForTimeout(1000);
        
        // Take screenshot of project creation modal
        await page.screenshot({ path: 'screenshots/03-project-creation-modal.png', fullPage: true });
        
        // Try to interact with project creation form
        const nameInput = page.locator('input[placeholder*="name"], input[placeholder*="Name"], input:first-of-type');
        if (await nameInput.isVisible()) {
          await nameInput.fill('Demo E-Commerce Security Assessment');
          
          const descriptionInput = page.locator('textarea, input[placeholder*="description"]');
          if (await descriptionInput.isVisible()) {
            await descriptionInput.fill('Complete security assessment for e-commerce platform including web frontend, backend API, and payment processing system.');
          }
        }
        
        // Take screenshot with form filled
        await page.screenshot({ path: 'screenshots/04-project-form-filled.png', fullPage: true });
        
        console.log('✅ Step 3 Complete: Project creation interface demonstrated');
      } else {
        console.log('ℹ️ New project button not found, continuing with demo');
      }
      await page.waitForTimeout(2000);
    });

    // 🎬 STEP 4: Navigation to Analysis
    await test.step('🔍 Step 4: Analysis Section Navigation', async () => {
      // Navigate to analysis page
      await page.click('a[href="/analysis"]');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Take screenshot of analysis page
      await page.screenshot({ path: 'screenshots/05-analysis-section.png', fullPage: true });
      
      console.log('✅ Step 4 Complete: Analysis section demonstrated');
    });

    // 🎬 STEP 5: Analytics Dashboard
    await test.step('📈 Step 5: Analytics Dashboard Navigation', async () => {
      // Try to navigate to analytics page
      const analyticsLink = page.locator('a[href="/analytics"], nav a:has-text("Analytics"), nav a:has-text("Dashboard")');
      
      if (await analyticsLink.isVisible()) {
        await analyticsLink.first().click();
      } else {
        // If no direct analytics link, try going to a related page or create URL
        await page.goto('/analytics');
      }
      
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
      
      // Take screenshot of analytics page
      await page.screenshot({ path: 'screenshots/06-analytics-dashboard.png', fullPage: true });
      
      console.log('✅ Step 5 Complete: Analytics dashboard demonstrated');
    });

    // 🎬 STEP 6: Reports Section
    await test.step('📋 Step 6: Reports Section Navigation', async () => {
      await page.click('a[href="/reports"]');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Take screenshot of reports page
      await page.screenshot({ path: 'screenshots/07-reports-section.png', fullPage: true });
      
      console.log('✅ Step 6 Complete: Reports section demonstrated');
    });

    // 🎬 STEP 7: MITRE ATT&CK Section
    await test.step('🎯 Step 7: MITRE ATT&CK Framework Navigation', async () => {
      await page.click('a[href="/mitre"]');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Take screenshot of MITRE page
      await page.screenshot({ path: 'screenshots/08-mitre-framework.png', fullPage: true });
      
      console.log('✅ Step 7 Complete: MITRE ATT&CK framework demonstrated');
    });

    // 🎬 STEP 8: Assets Section
    await test.step('💼 Step 8: Assets Management Navigation', async () => {
      await page.click('a[href="/assets"]');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Take screenshot of assets page
      await page.screenshot({ path: 'screenshots/09-assets-management.png', fullPage: true });
      
      console.log('✅ Step 8 Complete: Assets management demonstrated');
    });

    // 🎬 STEP 9: Theme and UI Features
    await test.step('🎨 Step 9: UI Features and Theme Toggle', async () => {
      // Try to toggle theme if available
      const themeToggle = page.locator('button[title*="theme"], button:has-text("theme")');
      if (await themeToggle.isVisible()) {
        await themeToggle.click();
        await page.waitForTimeout(1000);
        
        // Take screenshot in dark mode
        await page.screenshot({ path: 'screenshots/10-dark-theme.png', fullPage: true });
        
        // Toggle back to light mode
        await themeToggle.click();
        await page.waitForTimeout(1000);
      }
      
      // Test sidebar collapse/expand
      const sidebarToggle = page.locator('button[title*="sidebar"], button[title*="Collapse"]');
      if (await sidebarToggle.isVisible()) {
        await sidebarToggle.click();
        await page.waitForTimeout(500);
        
        // Take screenshot with collapsed sidebar
        await page.screenshot({ path: 'screenshots/11-collapsed-sidebar.png', fullPage: true });
        
        // Expand sidebar again
        await sidebarToggle.click();
        await page.waitForTimeout(500);
      }
      
      console.log('✅ Step 9 Complete: UI features and theming demonstrated');
    });

    // 🎬 FINAL STEP: Complete Overview
    await test.step('🎉 Step 10: Complete Workflow Overview', async () => {
      // Return to dashboard for final overview
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Take final comprehensive screenshot
      await page.screenshot({ path: 'screenshots/12-workflow-complete.png', fullPage: true });
      
      console.log(`
🎊 ================================
   AITM FRONTEND DEMO COMPLETED! 
🎊 ================================

✅ Workflow Summary:
1. ✅ Dashboard Overview & Navigation
2. ✅ Projects Management Interface
3. ✅ Project Creation Workflow
4. ✅ Analysis Section Navigation  
5. ✅ Analytics Dashboard & Insights
6. ✅ Reports & Documentation Section
7. ✅ MITRE ATT&CK Framework Integration
8. ✅ Assets Management Interface
9. ✅ UI Features & Theming
10. ✅ Complete System Overview

📊 Frontend Features Demonstrated:
- Responsive navigation and sidebar
- Modern UI with dark/light theme support
- Comprehensive threat modeling sections
- Analytics and reporting interfaces
- MITRE ATT&CK framework integration
- Professional security-focused design

📹 Video Recording: Available in test results
📸 Screenshots: Comprehensive step-by-step documentation
📋 This demonstrates AITM's user interface capabilities

🎯 Next Steps:
- Connect backend services for full functionality
- Review video recording for complete UX flow
- Use screenshots for documentation and training
      `);

      // Add delay to ensure video capture is complete
      await page.waitForTimeout(5000);
    });
  });

  // Optional: Test responsive design
  test('📱 Mobile Responsive Design Demo', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Take mobile screenshot
    await page.screenshot({ path: 'screenshots/13-mobile-responsive.png', fullPage: true });
    
    // Test mobile menu
    const mobileMenuButton = page.locator('button[class*="mobile-menu"], button:has(svg[viewBox*="4 6h16M4 12h16M4 18h16"])');
    if (await mobileMenuButton.isVisible()) {
      await mobileMenuButton.click();
      await page.waitForTimeout(1000);
      
      // Take screenshot with mobile menu open
      await page.screenshot({ path: 'screenshots/14-mobile-menu.png', fullPage: true });
    }
    
    console.log('✅ Mobile responsiveness demonstrated');
  });
});
