# 🤝 AITM Collaboration Features E2E Testing

This document describes the end-to-end testing setup for AITM's collaboration system.

## 🎯 Test Coverage

The collaboration E2E tests validate:

### Core Features
- **Team Management**: Creation, listing, member management
- **Project Access Control**: Permission levels, sharing, access validation
- **Activity Tracking**: Activity feeds, logging, history
- **User Authentication**: Login, session management, authorization

### Technical Integration
- **API Integration**: Backend collaboration endpoints
- **Full-Stack Communication**: Frontend ↔ Backend data flow
- **Error Handling**: Graceful failure modes
- **Responsive Design**: Mobile and desktop layouts

## 🚀 Running Tests

### Prerequisites
1. **Backend**: Must be running on `http://127.0.0.1:38527`
2. **Frontend**: Must be running on `http://127.0.0.1:41241`  
3. **Database**: SQLite database with collaboration tables migrated
4. **Admin User**: `admin@aitm.com` with password `SecureAdmin123!`

### Quick Start
```bash
# Ensure both backend and frontend are running
cd /Users/ifiokmoses/code/AITM

# Start backend (in one terminal)
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 38527

# Start frontend (in another terminal) 
cd frontend && npm run dev -- --port 41241

# Run collaboration tests (in a third terminal)
cd frontend && npx playwright test 08-collaboration-features.spec.ts
```

### Test Commands

```bash
# Run all collaboration tests
npx playwright test 08-collaboration-features.spec.ts

# Run specific test suite
npx playwright test 08-collaboration-features.spec.ts --grep "Team Management"

# Run with headed browser (visual)
npx playwright test 08-collaboration-features.spec.ts --headed

# Generate test report
npx playwright test 08-collaboration-features.spec.ts --reporter=html

# Run on specific browser
npx playwright test 08-collaboration-features.spec.ts --project=chromium
```

## 🧪 Test Structure

### Test Organization
```
08-collaboration-features.spec.ts
├── 🔐 Authentication & Authorization
│   ├── Login and dashboard access
│   └── Session persistence across pages
├── 👥 Team Management  
│   ├── Team creation via API
│   └── Team listing and validation
├── 📊 Project Access Control
│   └── Access level verification
├── 📈 Activity Tracking
│   └── Activity feed retrieval
├── 🌐 Full-Stack Integration
│   ├── Complete workflow validation
│   └── Error handling tests
└── 📱 Responsive Design
    └── Mobile layout verification
```

### Helper Functions
- `loginAsAdmin()`: Authenticates as admin user
- `createTestTeam()`: Creates teams through UI
- `directAPICall()`: Makes direct backend API calls

## 📊 Expected Results

### Successful Test Run
```
🤝 AITM Collaboration Features
  🔐 Authentication & Authorization
    ✓ should login successfully and access dashboard
    ✓ should maintain session across page navigations
  👥 Team Management
    ✓ should create teams via API integration  
    ✓ should list user teams
  📊 Project Access Control
    ✓ should check project access levels
  📈 Activity Tracking
    ✓ should retrieve activity feed
  🌐 Full-Stack Integration
    ✓ should demonstrate complete collaboration workflow
    ✓ should handle error states gracefully
  📱 Responsive Design
    ✓ should work on mobile devices

8 passed (45s)
```

### Generated Artifacts
- **Screenshots**: `frontend/screenshots/collaboration-*.png`
- **Test Reports**: `playwright-report/index.html`
- **Trace Files**: For debugging failed tests

## ⚠️ Troubleshooting

### Common Issues

#### Backend Not Running
```
⚠️ API test failed: fetch failed
```
**Solution**: Ensure backend is running on port 38527

#### Database Not Migrated
```
⚠️ no such table: teams
```
**Solution**: Run collaboration migrations
```bash
cd backend && python -m app.database.migrate_collaboration
```

#### Frontend Not Running
```
⚠️ page navigation failed
```
**Solution**: Ensure frontend is running on port 41241

#### Authentication Issues
```
⚠️ No auth token found
```
**Solution**: Verify admin user exists and login form works

### Debug Mode
```bash
# Run with debug output
DEBUG=pw:api npx playwright test 08-collaboration-features.spec.ts

# Record test execution
npx playwright test --trace on 08-collaboration-features.spec.ts

# Show browser while testing
npx playwright test --headed --slow-mo=1000 08-collaboration-features.spec.ts
```

## 🔧 Configuration

### Test Configuration
Tests use these constants (defined in the spec file):
```typescript
const BASE_URL = 'http://127.0.0.1:41241';      // Frontend
const API_BASE_URL = 'http://127.0.0.1:38527/api/v1'; // Backend API
```

### Viewport Settings
- **Desktop**: Default Playwright viewport
- **Mobile**: 375x667 (iPhone-like)

## 📈 Extending Tests

### Adding New Test Cases
```typescript
test('should do something new', async ({ page }) => {
  await loginAsAdmin(page);
  
  // Your test logic here
  await expect(page.locator('selector')).toBeVisible();
});
```

### Adding New Helper Functions
```typescript
async function newHelperFunction(page: Page, param: string): Promise<void> {
  // Helper logic
}

// Export for reuse
export { loginAsAdmin, createTestTeam, directAPICall, newHelperFunction };
```

## 📋 Test Checklist

Before running tests, ensure:

- [ ] Backend server is running and healthy
- [ ] Frontend development server is running  
- [ ] Database has collaboration tables migrated
- [ ] Admin user account exists
- [ ] Network ports are not blocked
- [ ] No other processes using the same ports

## 🎉 Next Steps

After successful test runs:

1. **Review Screenshots**: Check UI renders correctly
2. **Analyze Test Reports**: Look for performance insights
3. **Add More Tests**: Extend coverage as features grow
4. **CI/CD Integration**: Add tests to deployment pipeline
5. **Load Testing**: Consider performance testing for collaboration features

## 📞 Support

For test-related issues:
1. Check troubleshooting section above
2. Verify backend collaboration endpoints work manually
3. Ensure frontend pages load correctly in browser
4. Review Playwright documentation for advanced debugging

---

**Note**: These tests validate the integration between frontend UI and backend collaboration APIs. They are designed to be robust and handle various environment conditions gracefully.
