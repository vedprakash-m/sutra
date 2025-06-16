# End-to-End (E2E) Testing Guide

This document provides comprehensive instructions for setting up, running, and maintaining the local E2E testing environment for the Sutra application.

> **Quick Start**: For common commands and quick reference, see [E2E_QUICK_REFERENCE.md](./E2E_QUICK_REFERENCE.md)

## Overview

The Sutra E2E testing suite is designed to validate critical user flows and catch integration issues before they reach CI/CD. The setup uses:

- **Docker Compose** for service orchestration
- **Playwright** for browser automation and testing
- **Isolated test environment** with dedicated database
- **Comprehensive test coverage** of key user journeys

## Architecture

### Service Orchestration
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Functions     │    │   Cosmos DB     │
│   (React)       │◄───┤   (Python)      │◄───┤   Emulator      │
│   Port: 3000    │    │   Port: 7071    │    │   Port: 8081    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Azurite       │
                    │   (Storage)     │
                    │   Port: 10000   │
                    └─────────────────┘
```

### Test Data Management Strategy

1. **Global Setup**: Seed initial test data before test execution
2. **Test Isolation**: Each test operates in a clean environment
3. **Global Teardown**: Clean up test data after execution
4. **Database Reset**: API endpoint to reset test database state

## Quick Start

### Prerequisites

Ensure you have the following installed:
- **Node.js 18+**
- **Docker Desktop**
- **Docker Compose V2**

### Running E2E Tests

#### Option 1: Full Automated Workflow (Recommended)
```bash
# Start services, run tests, and cleanup in one command
npm run test:e2e
```

#### Option 2: Manual Control
```bash
# 1. Start all services
docker-compose up -d --build

# 2. Wait for services to be healthy (check Docker Desktop or logs)
docker-compose logs -f

# 3. Run E2E tests
npx playwright test

# 4. Cleanup
docker-compose down
```

#### Option 3: Development Mode
```bash
# Start services and keep them running
docker-compose up -d --build

# Run tests with UI for debugging
npm run test:e2e:ui

# Services remain running for multiple test iterations
# Cleanup when done: docker-compose down
```

## Test Suite Coverage

### 🔐 Authentication (`auth.spec.ts`)
- ✅ User login with valid credentials
- ✅ User logout and session cleanup  
- ✅ Session persistence across page reloads
- ✅ Access control for protected routes
- ✅ Error handling for invalid credentials

### 🎯 Prompt Management (`prompt-management.spec.ts`)
- ✅ Create new prompts with validation
- ✅ Edit and update existing prompts
- ✅ Delete prompts with confirmation
- ✅ Multi-LLM testing and comparison
- ✅ Prompt versioning and history
- ✅ AI-powered prompt suggestions
- ✅ Error handling for invalid inputs

### 📁 Collection Management (`collection-management.spec.ts`)
- ✅ Create and organize collections
- ✅ Add/remove prompts from collections
- ✅ Search and filter collections
- ✅ Collection permissions and sharing
- ✅ Import prompts from other collections
- ✅ Bulk operations on collections

### ⚡ Playbook Management (`playbook-management.spec.ts`)
- ✅ Create linear AI workflows
- ✅ Add and configure workflow steps
- ✅ Execute playbooks end-to-end
- ✅ Save and load draft playbooks
- ✅ Validate playbook configurations
- ✅ Error handling in workflow execution

### 🧭 Navigation (`basic-navigation.spec.ts`)
- ✅ Core application navigation
- ✅ Responsive design validation
- ✅ Loading states and error boundaries

## Configuration Files

### Docker Compose (`docker-compose.yml`)
Orchestrates the following services:
- **cosmos-emulator**: Cosmos DB with test data isolation
- **functions-api**: Azure Functions backend
- **azurite**: Azure Storage emulator
- **frontend**: React application served statically

### Playwright Config (`playwright.config.ts`)
Key configurations:
- **Single worker mode**: Ensures test data isolation
- **Multi-browser support**: Chrome, Firefox, Safari, Mobile
- **Global setup/teardown**: Automated data management
- **Rich reporting**: HTML, JSON, and console outputs
- **Failure artifacts**: Screenshots, videos, traces

### Test Utilities (`tests/e2e/helpers.ts`)
Reusable helper functions:
- Authentication and session management
- Navigation and page interaction
- CRUD operations for all entities
- Error checking and validation
- Data generation and cleanup

## Environment Configuration

### Test Environment Variables
The E2E environment uses these configurations:
```env
# Frontend
VITE_API_URL=http://functions-api:7071/api
NODE_ENV=production

# Backend
COSMOS_DB_ENDPOINT=https://cosmos-emulator:8081
COSMOS_DB_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
ENVIRONMENT=test
FUNCTIONS_WORKER_RUNTIME=python
```

### Health Checks
Services include health checks to ensure readiness:
- **Cosmos DB**: Validates emulator is accepting connections
- **Functions API**: Confirms `/api/health` endpoint responds
- **Frontend**: Validates React app is serving content

## Debugging E2E Tests

### Using Playwright UI
```bash
# Run tests with interactive UI
npm run test:e2e:ui
```

### Viewing Test Reports
```bash
# Open HTML report after test run
npx playwright show-report
```

### Debugging Failed Tests
1. **Screenshots**: Automatically captured on failures
2. **Videos**: Recorded for failed test reruns
3. **Traces**: Detailed execution traces available
4. **Logs**: Check Docker service logs for backend issues

### Manual Debugging
```bash
# Access running services
docker-compose ps                    # Check service status
docker-compose logs functions-api    # View API logs
docker-compose logs cosmos-emulator  # View database logs

# Test individual components
curl http://localhost:7071/api/health  # Test API health
curl http://localhost:3000             # Test frontend
```

## Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker is running
docker --version
docker-compose --version

# Clean up old containers
docker-compose down --volumes
docker system prune -f

# Rebuild and restart
docker-compose up -d --build --force-recreate
```

#### Port Conflicts
```bash
# Check for port usage
lsof -i :3000  # Frontend
lsof -i :7071  # API
lsof -i :8081  # Cosmos DB

# Kill processes if needed
kill -9 <PID>
```

#### Test Data Issues
```bash
# Reset test database manually
curl -X POST http://localhost:7071/api/admin/reset-test-data

# Or restart Cosmos emulator
docker-compose restart cosmos-emulator
```

#### Slow Test Execution
- Ensure Docker Desktop has sufficient resources (4GB+ RAM)
- Close unnecessary applications during test runs
- Use `--workers=1` flag if tests are flaky

### Performance Optimization

#### Docker Resource Allocation
- **Memory**: Allocate at least 4GB to Docker Desktop
- **CPU**: Use at least 2 cores for optimal performance
- **Storage**: Ensure sufficient disk space for images and volumes

#### Test Execution Tips
- Run tests in headless mode for faster execution
- Use specific test files instead of full suite during development
- Keep Docker images up to date for better performance

## Adding New Tests

### Test File Structure
```typescript
import { test, expect } from '@playwright/test';
import { E2EHelpers } from './helpers';

test.describe('Feature Name', () => {
  let helpers: E2EHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new E2EHelpers(page);
    await helpers.authenticate();
  });

  test('should perform action', async ({ page }) => {
    // Test implementation
  });
});
```

### Best Practices
1. **Use helpers**: Leverage existing helper functions
2. **Data isolation**: Don't rely on data from other tests
3. **Clear descriptions**: Use descriptive test names
4. **Error handling**: Test both success and failure scenarios
5. **Page object model**: Group related actions in helper methods

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
        
      - name: Install Playwright
        run: npx playwright install --with-deps
        
      - name: Run E2E tests
        run: npm run test:e2e
        
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
```

### Environment Considerations
- **Resource Requirements**: CI environments need Docker support
- **Service Startup Time**: Allow extra time for services to start
- **Parallel Execution**: Consider worker count based on CI resources
- **Artifact Storage**: Save reports and videos for debugging

## Maintenance

### Regular Tasks
1. **Update Dependencies**: Keep Playwright and Docker images current
2. **Review Test Coverage**: Ensure new features have E2E coverage
3. **Performance Monitoring**: Track test execution times
4. **Documentation Updates**: Keep this guide current with changes

### Monitoring Test Health
- **Flaky Test Detection**: Monitor test consistency
- **Execution Time Tracking**: Identify performance regressions
- **Coverage Analysis**: Ensure critical paths are tested

---

## Support

### Getting Help
- **Documentation**: Check this guide and inline code comments
- **Logs**: Review Docker and Playwright logs for errors
- **Community**: Playwright documentation and community resources

### Reporting Issues
When reporting E2E test issues, include:
1. **Test command used**
2. **Error messages and stack traces** 
3. **Docker service logs**
4. **Environment details** (OS, Docker version, Node version)
5. **Screenshots or videos** if available

---

*This E2E testing suite ensures robust validation of the Sutra application's critical user flows, providing confidence in local development and pre-deployment validation.*

## Backend Dependencies Issue Resolution

If you encounter grpcio compilation errors when installing backend dependencies, this is a known issue with Azure Functions Worker dependencies. Here are the solutions:

### Quick Fix for Local Development

```bash
cd api

# Option 1: Use minimal requirements (most reliable for CI)
pip install -r requirements-minimal.txt

# Option 2: Use CI requirements (comprehensive)
pip install -r requirements-ci.txt

# Option 3: Install Azure Functions Worker separately
pip install azure-functions-worker --no-deps
pip install -r requirements-ci.txt

# Option 4: Use conda instead of pip (if available)
conda install grpcio grpcio-tools
pip install -r requirements.txt
```

### For CI/CD Environments

The `requirements-minimal.txt` file contains only the essential dependencies needed for testing, avoiding all compilation issues. Use this in GitHub Actions:

```yaml
- name: Install Python dependencies
  run: |
    cd api
    pip install --upgrade pip setuptools wheel
    pip install -r requirements-minimal.txt
```

### Docker Development

The `Dockerfile.dev` has been configured to use `requirements-ci.txt` to avoid compilation issues in containerized environments.
