import { FullConfig, chromium } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global setup for AITM tests...');
  
  // Check if backend is running
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Wait for backend to be ready
    console.log('🔍 Checking backend health...');
    await page.goto('http://127.0.0.1:38527/health');
    const healthResponse = await page.textContent('body');
    console.log('✅ Backend health check:', healthResponse);
    
    // Verify API endpoints are accessible
    await page.goto('http://127.0.0.1:38527/docs');
    console.log('✅ API documentation is accessible');
    
  } catch (error) {
    console.error('❌ Backend is not accessible:', error);
    throw new Error('Backend services are not running. Please start them before running tests.');
  } finally {
    await browser.close();
  }
  
  console.log('✅ Global setup completed successfully');
}

export default globalSetup;
