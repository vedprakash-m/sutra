# E2E Testing Quick Reference

## Quick Commands

```bash
# 🚀 Run complete E2E test suite
npm run test:e2e

# 🎭 Run with interactive UI (great for debugging)
npm run test:e2e:ui

# 👀 Run with browser visible (see tests execute)
npm run test:e2e:headed

# 🔧 Manual service control
npm run e2e:setup      # Start all services
npm run e2e:cleanup    # Stop all services
npm run e2e:logs       # View service logs
npm run e2e:services   # Check service status

# 🔬 Validation and testing
npm run e2e:validate   # Comprehensive E2E validation
npm run ci:validate    # CI/CD environment simulation
npm run backend:test-deps  # Test backend dependencies
```

## Test Development

```bash
# Run specific test file
npx playwright test auth.spec.ts

# Run tests matching pattern
npx playwright test --grep "should create"

# Debug specific test
npx playwright test auth.spec.ts --debug

# Generate test code
npx playwright codegen http://localhost:3000
```

## Service URLs

- **Frontend**: http://localhost:3000
- **API**: http://localhost:7071
- **Cosmos DB Emulator**: https://localhost:8081/_explorer/index.html
- **Azurite Storage**: http://localhost:10000

## Test Data Management

The E2E suite automatically handles test data through:

1. **Global Setup**: Resets and seeds fresh test data before all tests
2. **Global Teardown**: Cleans up test data after all tests complete
3. **Data Isolation**: Each test run starts with a clean database state

### Manual Test Data Commands

```bash
# Reset test database (requires running services)
curl -X POST http://localhost:7071/api/admin/test-data/reset \
  -H "Content-Type: application/json" \
  -H "x-test-auth: admin"

# Seed fresh test data
curl -X POST http://localhost:7071/api/admin/test-data/seed \
  -H "Content-Type: application/json" \
  -H "x-test-auth: admin"
```

## Troubleshooting

### Backend Dependencies Fail to Install

If you see `grpcio` compilation errors:

```bash
cd api

# Quick fix: Use minimal requirements (most reliable)
pip install -r requirements-minimal.txt

# Alternative: Use CI requirements  
pip install -r requirements-ci.txt

# Alternative: Install without deps
pip install azure-functions-worker --no-deps
pip install -r requirements-ci.txt

# For conda users:
conda install grpcio grpcio-tools
pip install -r requirements.txt
```

### Services Won't Start
```bash
# Check Docker is running
docker --version
docker info

# Clean up old containers
docker compose down --volumes
docker system prune -f

# Rebuild and restart
npm run e2e:setup
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :3000  # Frontend
lsof -i :7071  # API
lsof -i :8081  # Cosmos DB

# Kill processes if needed
kill -9 <PID>
```

### Test Failures
```bash
# View detailed test output
npx playwright test --reporter=list

# View test reports
npx playwright show-report

# Check service logs
npm run e2e:logs
```

### Slow Performance
- Allocate more resources to Docker Desktop (4GB+ RAM recommended)
- Close unnecessary applications
- Use headless mode: `npx playwright test` (default)

## Test Structure

```
tests/e2e/
├── auth.spec.ts                 # Authentication flows
├── collection-management.spec.ts # Collection CRUD operations
├── prompt-management.spec.ts     # Prompt creation and testing
├── playbook-management.spec.ts   # Workflow automation
├── basic-navigation.spec.ts      # Navigation and UI
├── helpers.ts                   # Shared utilities
├── global-setup.ts              # Test data initialization
└── global-teardown.ts           # Test data cleanup
```

## Adding New Tests

1. Create test file: `tests/e2e/new-feature.spec.ts`
2. Use helpers for common actions: `import { E2EHelpers } from './helpers'`
3. Follow naming convention: `should [action] [expected result]`
4. Test both success and failure scenarios
5. Use descriptive assertions with good error messages

### Example Test Structure

```typescript
import { test, expect } from '@playwright/test'
import { E2EHelpers } from './helpers'

test.describe('New Feature', () => {
  let helpers: E2EHelpers

  test.beforeEach(async ({ page }) => {
    helpers = new E2EHelpers(page)
    await helpers.authenticate()
  })

  test('should perform feature action successfully', async ({ page }) => {
    // Arrange
    await helpers.navigateTo('Feature Page')
    
    // Act
    await page.click('button:has-text("Action")')
    
    // Assert
    await expect(page.locator('.success-message')).toBeVisible()
  })
})
```

## CI/CD Integration

The E2E suite is designed to work in CI environments:

```yaml
# GitHub Actions example
- name: Run E2E Tests
  run: |
    npm ci
    npx playwright install --with-deps
    npm run test:e2e
    
- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: playwright-report
    path: playwright-report/
```

## Best Practices

1. **Data Independence**: Don't rely on data from other tests
2. **Clear Descriptions**: Use descriptive test and step names
3. **Error Handling**: Test both success and failure paths
4. **Timeouts**: Use appropriate waits for dynamic content
5. **Page Objects**: Use helpers for reusable page interactions
6. **Assertions**: Use specific, meaningful assertions
7. **Cleanup**: Tests should not leave side effects

## Performance Tips

- Use `page.waitForLoadState('networkidle')` for dynamic content
- Prefer `page.locator()` over `page.$()` for better error messages
- Use `test.beforeEach()` for common setup instead of duplicating code
- Run tests in parallel when possible (currently disabled for data isolation)
- Use headless mode for faster execution in CI

---

📖 **Full Documentation**: [E2E_TESTING.md](./E2E_TESTING.md)  
🔧 **Project Setup**: [README.md](./README.md)  
🏗️ **Architecture**: [Tech_Spec_Sutra.md](./docs/Tech_Spec_Sutra.md)
