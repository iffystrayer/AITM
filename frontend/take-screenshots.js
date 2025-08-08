import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  console.log('📸 Taking screenshots of AITM application...');
  
  // Dashboard
  await page.goto('http://localhost:41241');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: './screenshots/dashboard.png', fullPage: true });
  console.log('✅ Dashboard screenshot saved');
  
  // Projects page
  await page.goto('http://localhost:41241/projects');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: './screenshots/projects-list.png', fullPage: true });
  console.log('✅ Projects list screenshot saved');
  
  // Project detail page (completed project with results)
  await page.goto('http://localhost:41241/projects/2');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: './screenshots/project-detail.png', fullPage: true });
  console.log('✅ Project detail screenshot saved');
  
  await browser.close();
  console.log('📸 All screenshots saved to ./screenshots/ directory');
})();
