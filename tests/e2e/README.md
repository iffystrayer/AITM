# Comprehensive End-to-End Authorization Tests

This directory contains comprehensive end-to-end (E2E) authorization tests for the AITM platform. These tests validate the complete authorization flow with real HTTP requests, actual JWT tokens, and database interactions in a production-like environment.

## 🎯 Requirements Tested

The E2E tests validate all authorization requirements:

### 1.1-1.4: API Endpoints Enforce Proper Authorization
- ✅ All API endpoints require valid authentication
- ✅ Invalid tokens are properly rejected
- ✅ Missing authorization headers return 401 errors
- ✅ Expired tokens are handled correctly

### 2.1-2.4: Project Data Isolation with Ownership Validation
- ✅ Users can only access projects they own
- ✅ Admin users can access all projects
- ✅ Unauthorized users cannot access projects they don't own
- ✅ Project lists are filtered by ownership

### 3.1-3.4: Robust and Explicit Permission Checking System
- ✅ Uses explicit user object passing instead of fragile decorator logic
- ✅ Clear user context identification without implicit parameter discovery
- ✅ Clear error messages for insufficient permissions
- ✅ Authorization checks implemented by default for new API endpoints

### 4.1-4.4: Secure JWT Secret Key Handling in Production
- ✅ SECRET_KEY validation in production environment
- ✅ Proper error handling for missing or weak keys
- ✅ Secure token generation and validation
- ✅ Production configuration validation on startup

### 5.1-5.4: Multi-layer Authorization with Defense in Depth
- ✅ API layer authorization checks
- ✅ Service layer permission validation
- ✅ Data layer access control
- ✅ Comprehensive security audit logging

## 📁 Test Files

### Core Test Files

1. **`test_api_authorization_e2e.py`**
   - Basic API authorization tests
   - Ownership-based access control validation
   - Project modification authorization
   - Project list filtering tests

2. **`test_comprehensive_authorization_e2e.py`**
   - Comprehensive authorization tests with multiple scenarios
   - Role-based permission testing (admin, analyst, viewer, api_user)
   - Security headers and error response validation
   - Production-like environment testing

3. **`test_authorization_e2e.py`**
   - Playwright-based browser E2E tests
   - Frontend-to-backend authorization flow testing
   - Analysis endpoint authorization validation

### Test Runners

4. **`run_e2e_tests.py`**
   - Basic E2E test runner
   - Backend server management
   - Test environment setup

5. **`run_comprehensive_e2e_tests.py`**
   - Comprehensive test suite runner
   - Multiple test suite orchestration
   - Detailed result reporting

### Validation and Setup

6. **`validate_e2e_setup.py`**
   - E2E test environment validation
   - Dependency checking
   - Backend startup testing
   - Basic authentication flow validation

## 🚀 Running the Tests

### Quick Start

Run all comprehensive E2E tests with the shell script:

```bash
./run_comprehensive_e2e_tests.sh
```

### Manual Execution

1. **Validate Setup** (optional but recommended):
   ```bash
   cd tests/e2e
   python3 validate_e2e_setup.py
   ```

2. **Run Basic API Tests**:
   ```bash
   cd tests/e2e
   python3 test_api_authorization_e2e.py
   ```

3. **Run Comprehensive Tests**:
   ```bash
   cd tests/e2e
   python3 test_comprehensive_authorization_e2e.py
   ```

4. **Run All Test Suites**:
   ```bash
   cd tests/e2e
   python3 run_comprehensive_e2e_tests.py
   ```

### Prerequisites

- Python 3.8+
- Required packages: `requests`, `fastapi`, `uvicorn`, `sqlalchemy`, `PyJWT`
- Optional: `playwright` for browser-based tests

Install dependencies:
```bash
pip install requests fastapi uvicorn sqlalchemy PyJWT
pip install playwright  # Optional for browser tests
```

## 🧪 Test Scenarios

### Authentication Security Tests
- Invalid token rejection
- Malformed token handling
- Missing authorization header validation
- Valid token acceptance

### Ownership-Based Access Control Tests
- Owner access to their own projects
- Admin access to all projects
- Unauthorized user access denial
- Viewer role access restrictions

### Project Modification Authorization Tests
- Owner modification of their projects
- Admin modification of any project
- Unauthorized modification attempts
- Viewer modification restrictions

### Project List Filtering Tests
- Owner sees only their projects
- Admin sees all projects
- Unauthorized users see only their projects
- Proper filtering by ownership

### Role-Based Permission Tests
- Admin project creation capabilities
- Analyst project creation capabilities
- Viewer project creation restrictions
- API user access validation

### Security Headers and Response Tests
- Security headers in API responses
- Error response format validation
- API response consistency

## 🏗️ Test Environment

The E2E tests create a production-like test environment:

- **Backend Server**: Dedicated test server with production configuration
- **Database**: Isolated SQLite test databases with automatic cleanup
- **Authentication**: Real JWT tokens with secure secret keys
- **HTTP Requests**: Actual HTTP requests using the `requests` library
- **User Roles**: Multiple test users with different roles (admin, analyst, viewer, api_user)
- **Test Projects**: Multiple test projects for comprehensive scenario testing

## 📊 Test Results

The tests provide comprehensive reporting:

- **Individual Test Results**: Pass/fail status for each test scenario
- **Category Summaries**: Results grouped by test category
- **Overall Success Rate**: Percentage of tests passed
- **Security Feature Validation**: Confirmation of security features tested
- **Requirements Mapping**: Validation of specific requirements met

### Sample Output

```
🎯 FINAL COMPREHENSIVE E2E AUTHORIZATION TEST SUMMARY
================================================================================

📊 Test Suite Results:
   ✅ Passed Suites: 3/3
   ❌ Failed Suites: 0/3
   📈 Suite Success Rate: 100.0%

🔒 Security Features Comprehensively Tested:
   ✅ JWT token authentication and validation
   ✅ Ownership-based access control with strict enforcement
   ✅ Role-based permission system (admin, analyst, viewer, api_user)
   ✅ Admin privilege escalation and restrictions
   ✅ Unauthorized access prevention and security through obscurity
   ✅ Project modification authorization with ownership validation
   ✅ Project list filtering by ownership and role
   ✅ Multi-layer authorization with defense in depth
   ✅ Security headers and proper error handling
   ✅ Production-like environment testing

📋 Requirements Comprehensively Validated:
   ✅ 1.1-1.4: API endpoints enforce proper authorization checks
   ✅ 2.1-2.4: Project data isolation with ownership validation
   ✅ 3.1-3.4: Robust and explicit permission checking system
   ✅ 4.1-4.4: Secure JWT secret key handling in production
   ✅ 5.1-5.4: Multi-layer authorization with defense in depth

🎉 ALL COMPREHENSIVE E2E AUTHORIZATION TESTS PASSED!
```

## 🔧 Configuration

### Environment Variables

The tests use the following environment variables:

- `ENVIRONMENT=test`: Sets test environment mode
- `SECRET_KEY`: Secure JWT secret key for testing
- `DATABASE_URL`: SQLite database URL for test data
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`: Token expiration time
- `LOG_LEVEL=INFO`: Logging level for test output
- `BASE_URL=http://localhost:8000`: Backend server URL

### Test Data

The tests create the following test data:

- **Test Users**: 5 users with different roles
- **Test Projects**: Multiple projects for different test scenarios
- **JWT Tokens**: Valid tokens for each test user
- **Test Databases**: Isolated databases that are cleaned up after tests

## 🛡️ Security Considerations

The E2E tests validate critical security aspects:

1. **Authentication Security**: Proper JWT token validation and rejection of invalid tokens
2. **Authorization Enforcement**: Strict ownership-based access control
3. **Role-Based Permissions**: Proper role-based permission enforcement
4. **Admin Privileges**: Correct admin privilege escalation and restrictions
5. **Data Isolation**: Project data isolation with ownership validation
6. **Error Handling**: Secure error responses that don't leak information
7. **Production Readiness**: Production-like configuration validation

## 🧹 Cleanup

The tests automatically clean up:

- Test database files
- Backend server processes
- Temporary test data
- Environment variables

## 📝 Adding New Tests

To add new E2E tests:

1. **Add test methods** to existing test classes
2. **Create new test scenarios** in the comprehensive test file
3. **Update test runners** to include new test suites
4. **Document new requirements** being tested
5. **Update this README** with new test descriptions

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**: Kill existing backend processes
   ```bash
   pkill -f "uvicorn.*app.main:app"
   ```

2. **Database Locked**: Clean up test databases
   ```bash
   rm -f backend/test_*.db
   ```

3. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Permission Errors**: Ensure test files are executable
   ```bash
   chmod +x run_comprehensive_e2e_tests.sh
   ```

### Debug Mode

Run tests with verbose output:
```bash
./run_comprehensive_e2e_tests.sh --verbose
```

## 📚 Related Documentation

- [Authorization System Design](../../.kiro/specs/api-authorization-security/design.md)
- [Authorization Requirements](../../.kiro/specs/api-authorization-security/requirements.md)
- [Implementation Tasks](../../.kiro/specs/api-authorization-security/tasks.md)
- [Backend API Documentation](../../backend/README.md)

---

**Note**: These E2E tests are designed to run in a test environment and should not be run against production systems. They create and modify test data and may interfere with production operations.