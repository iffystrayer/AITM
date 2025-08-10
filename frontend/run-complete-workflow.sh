#!/bin/bash

# 🎬 AITM Complete Workflow Demonstration Script
# This script runs the complete end-to-end workflow test with video recording

set -e  # Exit on any error

echo "🎬 ================================================"
echo "   AITM COMPLETE WORKFLOW DEMONSTRATION"
echo "🎬 ================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
  echo "❌ Error: package.json not found. Please run this script from the frontend directory."
  exit 1
fi

# Check if required services are running
echo "🔍 Checking prerequisites..."

# Check if backend is running (adjust port as needed)
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
  echo "✅ Backend service is running on port 8000"
else
  echo "⚠️  Backend service not detected on port 8000"
  echo "   Please ensure the backend server is running before proceeding"
  echo "   You can start it with: cd ../backend && uvicorn app.main:app --reload --port 8000"
fi

# Check if frontend is running  
if curl -s http://127.0.0.1:59000 >/dev/null 2>&1; then
  echo "✅ Frontend service is running on port 59000"
else
  echo "⚠️  Frontend service not detected on port 59000"
  echo "   Please ensure the frontend server is running before proceeding"
  echo "   You can start it with: npm run dev -- --port 59000"
fi

echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
  echo "📦 Installing dependencies..."
  npm install
fi

# Ensure Playwright browsers are installed
echo "🎭 Ensuring Playwright browsers are installed..."
npx playwright install chromium

# Create screenshots directory
mkdir -p screenshots
mkdir -p videos
mkdir -p test-results

echo ""
echo "🎬 Starting Complete Workflow Demonstration..."
echo ""
echo "📋 This demonstration will cover:"
echo "   1. 🔐 Authentication & Dashboard Overview"
echo "   2. 📁 Project Creation"
echo "   3. 🏗️  System Architecture Definition"
echo "   4. 🔍 AI Threat Analysis Execution"
echo "   5. ⏳ Analysis Progress Monitoring"
echo "   6. 📊 Results Review & Assessment"
echo "   7. 📈 Analytics Dashboard & Insights"
echo "   8. 📋 Executive Report Generation"
echo "   9. 📚 Project Portfolio Management"
echo "   10. 🎉 Workflow Summary"
echo ""
echo "📹 Video recording: ENABLED"
echo "📸 Screenshots: ENABLED"
echo "🎯 Full trace: ENABLED"
echo ""

# Run the complete workflow test with enhanced reporting
echo "🚀 Executing complete workflow test..."

# Update Playwright config to force video recording
cat > playwright-workflow.config.ts << 'EOF'
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
EOF

# Run with custom configuration for comprehensive video recording
npx playwright test tests/e2e/05-complete-workflow.spec.ts \
  --config=playwright-workflow.config.ts \
  --headed \
  --project=chromium

# Check if test passed
if [ $? -eq 0 ]; then
  echo ""
  echo "🎊 ============================================"
  echo "   WORKFLOW DEMONSTRATION COMPLETED!"
  echo "🎊 ============================================"
  echo ""
  echo "✅ Test Results:"
  echo "   📹 Video recordings: test-results/**/*.webm"
  echo "   📸 Screenshots: screenshots/*.png"
  echo "   🔍 Traces: test-results/**/*trace.zip"
  echo "   📋 HTML Report: playwright-report/index.html"
  echo ""
  echo "📊 View the results:"
  echo "   npx playwright show-report"
  echo ""
  echo "🎬 Video files location:"
  find test-results -name "*.webm" -type f | head -5
  echo ""
  
  # Copy videos to a more accessible location
  echo "📁 Copying videos to videos directory..."
  find test-results -name "*.webm" -exec cp {} videos/ \; 2>/dev/null || true
  
  # List generated artifacts
  echo "📋 Generated Artifacts:"
  echo "   Screenshots: $(ls -1 screenshots/*.png 2>/dev/null | wc -l) files"
  echo "   Videos: $(ls -1 videos/*.webm 2>/dev/null | wc -l) files"
  echo "   Traces: $(find test-results -name "*trace.zip" | wc -l) files"
  
else
  echo ""
  echo "❌ ============================================"
  echo "   WORKFLOW TEST ENCOUNTERED ISSUES"
  echo "❌ ============================================"
  echo ""
  echo "📋 Check the test results for details:"
  echo "   npx playwright show-report"
  echo ""
  echo "🔍 Debug information available in:"
  echo "   - test-results/ directory"
  echo "   - screenshots/ directory"
  echo "   - Playwright HTML report"
  echo ""
  exit 1
fi

echo ""
echo "🎓 Next Steps:"
echo "   1. Review the video recording to see the complete workflow"
echo "   2. Check screenshots for detailed step-by-step documentation"
echo "   3. Open the HTML report for interactive test results"
echo "   4. Use traces for detailed debugging if needed"
echo ""
echo "🎯 The demonstration shows how AITM can:"
echo "   ✅ Streamline threat modeling processes"
echo "   ✅ Provide AI-driven security analysis"
echo "   ✅ Generate comprehensive security reports"  
echo "   ✅ Support enterprise security workflows"
echo ""
echo "📺 Open the HTML report now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
  npx playwright show-report
fi

echo ""
echo "🎬 Workflow demonstration complete! 🎉"
