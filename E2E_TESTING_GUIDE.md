# AITM End-to-End Testing Guide

## 📋 Overview

This guide covers the comprehensive end-to-end (E2E) testing setup for the AI-Powered Threat Modeler (AITM) application. The E2E tests validate the complete user workflow from frontend to backend integration.

## 🏗️ Test Architecture

### Test Structure
```
frontend/
├── tests/
│   ├── e2e/                    # E2E test files
│   │   ├── 01-smoke.spec.ts    # Basic application functionality
│   │   ├── 02-projects.spec.ts # Project management workflow
│   │   ├── 03-threat-analysis.spec.ts # Threat modeling workflow
│   │   └── 04-api-integration.spec.ts # API integration tests
│   ├── fixtures.ts             # Test helpers and page objects
│   ├── global-setup.ts         # Test environment setup
│   └── global-teardown.ts      # Test environment cleanup
├── playwright.config.ts        # Playwright configuration
└── package.json               # Test scripts
```

### Test Categories

1. **Smoke Tests** (`01-smoke.spec.ts`)
   - Basic application loading
   - Backend connectivity
   - Navigation functionality
   - Responsive design
   - Quick access links

2. **Project Management** (`02-projects.spec.ts`)
   - Project CRUD operations
   - System input management
   - Form validation
   - Empty states handling
   - Error handling

3. **Threat Analysis Workflow** (`03-threat-analysis.spec.ts`)
   - Analysis configuration
   - Progress monitoring
   - Results display
   - Status updates
   - Error scenarios

4. **API Integration** (`04-api-integration.spec.ts`)
   - Direct API testing
   - CRUD operations
   - Error response handling
   - Schema validation
   - Concurrent requests

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Node.js 18+ (for frontend dependencies)
- AITM system with backend and frontend

### 1. Run All Tests (Easiest)
```bash
# Run the comprehensive test suite
./run-e2e-tests.sh

# Run specific test categories
./run-e2e-tests.sh --test-type smoke
./run-e2e-tests.sh --test-type projects
./run-e2e-tests.sh --test-type analysis
./run-e2e-tests.sh --test-type api
```

### 2. Manual Test Execution
```bash
# Start the AITM system first
docker-compose up -d

# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install
npx playwright install

# Run tests
npm run test:e2e           # All tests
npm run test:e2e:smoke     # Smoke tests only
npm run test:e2e:projects  # Project management tests
npm run test:e2e:analysis  # Threat analysis tests
npm run test:e2e:api       # API integration tests

# Interactive modes
npm run test:e2e:ui        # Visual test runner
npm run test:e2e:debug     # Debug mode
npm run test:e2e:headed    # Show browser during tests
```

## 🧪 Test Scenarios

### Smoke Tests
✅ **Application Loading**
- Dashboard loads successfully
- Backend connectivity verified
- Feature list displayed
- Navigation works

✅ **System Health**
- Backend API accessible
- Health endpoint responds
- API documentation loads
- Frontend responsive design

### Project Management Tests
✅ **Project Lifecycle**
- Create new project with validation
- Display project in list
- Navigate to project details
- View project tabs (Overview, Inputs, Analysis, Results)

✅ **System Inputs**
- Add system descriptions
- Form validation
- Input display and management
- Empty states handling

✅ **Error Handling**
- Non-existent project handling
- Form validation errors
- Network error recovery

### Threat Analysis Tests
✅ **Analysis Workflow**
- Configure analysis parameters
- Start threat analysis
- Monitor progress indicators
- View completed results

✅ **Status Management**
- Analysis state transitions
- Progress tracking
- Result navigation
- Error state handling

✅ **Configuration Validation**
- Required system inputs
- LLM provider selection
- Analysis depth settings
- Comprehensive options

### API Integration Tests
✅ **CRUD Operations**
- Create, read, update, delete projects
- System input management
- Response schema validation
- Error response handling

✅ **Advanced Scenarios**
- Concurrent request handling
- Threat modeling endpoints
- Health and status checks
- API documentation accessibility

## 📊 Test Coverage

### Frontend Coverage
- **Pages**: Dashboard, Projects, Project Details, Analysis, Assets, Reports
- **Components**: Navigation, Forms, Modals, Status Indicators
- **User Flows**: Complete project creation to threat analysis
- **Error States**: Network errors, validation errors, empty states

### Backend Coverage
- **API Endpoints**: Projects, System Inputs, Analysis, Health
- **Error Handling**: 404s, validation errors, server errors
- **Data Validation**: Request/response schema validation
- **Concurrency**: Multiple simultaneous requests

### Integration Coverage
- **Frontend-Backend Communication**: API calls, error handling
- **Real-world Scenarios**: Complete user workflows
- **Cross-browser Testing**: Chromium, Firefox, Safari
- **Mobile Testing**: Responsive design validation

## 🔧 Configuration

### Playwright Configuration (`playwright.config.ts`)
```typescript
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://127.0.0.1:41241',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
```

### Environment Settings
- **Frontend URL**: `http://127.0.0.1:41241`
- **Backend URL**: `http://127.0.0.1:38527`
- **Test Timeout**: 30 seconds
- **Retry Policy**: 2 retries on CI, 0 locally
- **Browser Support**: Chromium, Firefox, Safari, Mobile Chrome/Safari

## 🎯 Page Object Pattern

### Example Page Object
```typescript
export class ProjectsPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/projects');
    await this.page.waitForLoadState('networkidle');
  }

  async createProject(projectData: ProjectData) {
    await this.page.click('text=+ New Project');
    await this.page.fill('input[placeholder="Enter project name"]', projectData.name);
    await this.page.click('button:has-text("Create Project")');
  }
}
```

### Test Fixtures
```typescript
export const test = base.extend<{
  projectsPage: ProjectsPage;
  projectDetailPage: ProjectDetailPage;
}>({
  projectsPage: async ({ page }, use) => {
    await use(new ProjectsPage(page));
  },
});
```

## 📈 Best Practices

### Test Design
- **Independent Tests**: Each test can run in isolation
- **Descriptive Names**: Clear test and step descriptions
- **Proper Setup/Teardown**: Clean state between tests
- **Error Recovery**: Graceful handling of failures

### Data Management
- **Dynamic Test Data**: Timestamps to avoid conflicts
- **Test Isolation**: No shared state between tests
- **Cleanup**: Remove test data after completion
- **Realistic Data**: Representative system descriptions

### Assertions
- **Explicit Waits**: Wait for elements to be ready
- **Multiple Checks**: Verify different aspects
- **Error Messages**: Clear failure descriptions
- **State Validation**: Confirm expected state changes

## 🐛 Debugging

### Visual Debugging
```bash
# Run tests with visible browser
npm run test:e2e:headed

# Interactive test runner with live debugging
npm run test:e2e:ui

# Step-by-step debugging
npm run test:e2e:debug
```

### Trace Analysis
- Screenshots captured on failure
- Video recordings for failed tests
- Network logs and requests
- Console logs and errors

### Common Issues
1. **Timing Issues**: Add proper waits for dynamic content
2. **Selector Problems**: Use stable, unique selectors
3. **Test Data Conflicts**: Use unique test data
4. **Network Flakiness**: Implement proper retry logic

## 📊 Reporting

### Test Reports
- **HTML Report**: Visual test results with screenshots
- **JUnit XML**: For CI/CD integration
- **JSON Report**: Programmatic result processing
- **Trace Viewer**: Interactive debugging tool

### Metrics
- **Test Execution Time**: Performance tracking
- **Pass/Fail Rates**: Reliability metrics
- **Browser Coverage**: Cross-browser validation
- **Feature Coverage**: Workflow validation

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start AITM system
        run: docker-compose up -d
      - name: Run E2E tests
        run: ./run-e2e-tests.sh --cleanup
```

## 📚 Resources

### Playwright Documentation
- [Playwright Test](https://playwright.dev/docs/intro)
- [Page Object Model](https://playwright.dev/docs/pom)
- [Test Fixtures](https://playwright.dev/docs/test-fixtures)

### AITM Specific
- [API Documentation](http://127.0.0.1:38527/docs)
- [Frontend Components](./frontend/src/lib/components/)
- [Backend Endpoints](./backend/app/api/)

---

## ✅ Test Execution Checklist

Before running tests:
- [ ] Docker and Docker Compose installed
- [ ] AITM system ports available (38527, 41241)
- [ ] Node.js 18+ installed
- [ ] Internet connection for Playwright installation

Running tests:
- [ ] Use `./run-e2e-tests.sh` for automated setup
- [ ] Check system health before manual runs
- [ ] Review test results in HTML report
- [ ] Check logs for any failures

After tests:
- [ ] Review failed test screenshots
- [ ] Check system logs if needed
- [ ] Stop services with `docker-compose down`
- [ ] Update test documentation if needed

**🎉 Happy Testing! The E2E test suite provides comprehensive validation of the AITM system's functionality and user experience.**
