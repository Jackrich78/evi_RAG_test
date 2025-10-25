# SOP: Testing Strategy

**Purpose:** Define testing approach, standards, and best practices for code quality
**Applies To:** All code changes, all features
**Last Updated:** 2025-10-24

## Overview

We follow Test-Driven Development (TDD) principles with comprehensive testing at multiple levels. Tests are written before implementation, ensuring code meets requirements and remains maintainable.

## Testing Pyramid

```
      /\
     /E2E\      Few, slow, expensive (critical user paths)
    /------\
   /Integr \    Some, moderate speed (component interaction)
  /----------\
 /   Unit     \ Many, fast, cheap (individual functions)
/--

------------\
```

**Distribution Goal:**
- 70% Unit Tests
- 20% Integration Tests
- 10% E2E Tests

## Test-Driven Development (TDD)

### TDD Cycle (Phase 2)

1. **Red:** Write failing test first
2. **Green:** Write minimal code to pass test
3. **Refactor:** Improve code while keeping tests green

### Phase 1 TDD Preparation

Current phase creates:
- Test strategy documentation (`testing.md`)
- Test stubs with TODO comments
- Acceptance criteria for validation

Implementation (Phase 2) will make stubs functional.

## Testing Levels

### Unit Tests

**What:** Test individual functions, methods, or components in isolation

**When:** For all business logic, utilities, pure functions

**Standards:**
- One test file per source file
- Test file naming: `[source-file].test.[ext]` or `[source-file]_test.[ext]`
- Mock all external dependencies
- Fast execution (< 100ms per test)
- No network calls, no database, no file I/O

**Example:**
```javascript
// src/utils/validators.ts
export function isValidEmail(email: string): boolean { ... }

// tests/utils/validators.test.ts
describe('isValidEmail', () => {
  it('should return true for valid emails', () => {
    expect(isValidEmail('test@example.com')).toBe(true);
  });

  it('should return false for invalid emails', () => {
    expect(isValidEmail('invalid')).toBe(false);
  });
});
```

### Integration Tests

**What:** Test interactions between components, modules, or external services

**When:** For API endpoints, database operations, third-party integrations

**Standards:**
- Test files in `tests/integration/` directory
- Can use real databases (in-memory or test DB)
- Can hit test environments of external services
- Moderate speed (< 1s per test)
- Clean up after each test (transactions, teardown)

**Example:**
```javascript
// tests/integration/auth-api.integration.test.ts
describe('Authentication API', () => {
  it('should authenticate valid user', async () => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: 'test@example.com', password: 'test123' })
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.token).toBeDefined();
  });
});
```

### E2E Tests

**What:** Test complete user workflows from UI through backend

**When:** For critical user paths, complex multi-step workflows

**Standards:**
- Test files in `tests/e2e/` directory
- Simulate real user behavior
- Test in browser (Playwright, Cypress, Selenium)
- Slow execution (seconds to minutes)
- Run less frequently (PR, pre-deployment)
- Maintain test data/fixtures

**Example:**
```javascript
// tests/e2e/login-flow.e2e.test.ts
test('user can log in and access dashboard', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'user@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

## Test Coverage

### Coverage Targets

- **Overall:** 80% line coverage minimum
- **Critical Paths:** 100% coverage required
- **New Code:** 90% coverage for new features
- **Refactoring:** Maintain or improve existing coverage

### What Requires 100% Coverage

- Authentication/authorization logic
- Payment processing
- Data validation functions
- Security-sensitive code
- Error handling for critical operations

### What Can Have Lower Coverage

- UI styling/cosmetic code
- Logging statements
- Configuration files
- Non-critical edge cases

## Test Organization

### Directory Structure

```
tests/
├── unit/
│   ├── utils/
│   ├── services/
│   └── components/
├── integration/
│   ├── api/
│   └── database/
├── e2e/
│   └── workflows/
└── fixtures/
    ├── data/
    └── mocks/
```

### Naming Conventions

- **Test files:** `[feature].test.[ext]` or `[feature]_test.[ext]`
- **Test functions:** Descriptive, readable: `it('should authenticate user with valid credentials')`
- **Fixtures:** `[entity]-fixture.[ext]`

## Mocking Strategy

### Always Mock

- External APIs (cost, reliability, speed)
- Time/date functions (deterministic tests)
- Random number generators
- File system operations (in unit tests)
- Network calls

### Sometimes Mock

- Database (mock for unit, real for integration)
- Internal services (depends on test level)

### Never Mock

- The code being tested
- Core business logic
- Data validation

### Mock Tools

- **JavaScript:** Jest, Sinon
- **Python:** unittest.mock, pytest-mock
- **Go:** gomock
- **Rust:** mockall

## Test Data Management

### Fixtures

- Store reusable test data in `tests/fixtures/`
- Version control fixtures
- Keep fixtures minimal (only data needed for tests)

### Factories

- Use factories for generating test data
- Randomize non-essential fields
- Make essential fields explicit

### Cleanup

- Reset state after each test
- Use transactions for database tests (rollback after test)
- Clear mocks between tests

## Performance Testing

**When:** For features with performance requirements (from acceptance criteria)

**Tools:**
- Load testing: k6, Artillery, JMeter
- Profiling: built-in language profilers

**Approach:**
1. Define performance targets (response time, throughput)
2. Create performance test scenarios
3. Run tests in CI/CD
4. Alert on regressions

## Security Testing

**When:** For authentication, authorization, data handling features

**Checks:**
- Input validation (SQL injection, XSS)
- Authentication bypass attempts
- Authorization checks
- Sensitive data exposure

**Tools:**
- OWASP ZAP, Burp Suite (manual)
- Dependency scanning: Snyk, Dependabot
- Static analysis: SonarQube, Semgrep

## Running Tests

### Locally (Examples)

```bash
# Unit tests
npm test                  # JavaScript
pytest tests/unit/        # Python
cargo test                # Rust
go test ./...             # Go

# With coverage
npm test -- --coverage
pytest --cov=src tests/

# Integration tests
npm run test:integration
pytest tests/integration/

# E2E tests
npm run test:e2e
playwright test
```

### CI/CD (Phase 2)

Tests run automatically:
1. On every commit (unit + integration)
2. On PR (full suite + E2E)
3. Before deployment (full suite + smoke tests)
4. Nightly (full suite + performance)

## Test Failures

### When Tests Fail

1. **Don't skip or delete failing tests**
2. Fix the code or the test
3. If test is flaky, investigate and fix flakiness
4. If feature changed, update test to match

### Flaky Tests

**Causes:**
- Race conditions
- External dependencies
- Time-sensitive assertions
- Random data without fixed seeds
- Non-deterministic code

**Solutions:**
- Add waits/retries for async operations
- Mock external dependencies
- Use fixed seeds for random data
- Make tests idempotent

## Test Best Practices

✅ **Do:**
- Write tests before implementation (TDD)
- Keep tests simple and readable
- Test behavior, not implementation
- Use descriptive test names
- Arrange-Act-Assert pattern
- One assertion per test (when possible)

❌ **Don't:**
- Test implementation details
- Create test interdependencies
- Use real credentials in tests
- Commit commented-out tests
- Write slow unit tests
- Ignore flaky tests

## Related Documentation

- Feature-specific testing: `docs/features/FEAT-XXX/testing.md`
- Manual testing: `docs/features/FEAT-XXX/manual-test.md`
- Test templates: `docs/templates/testing-template.md`

---

**This SOP is enforced by:** Tester agent (Phase 2), code review, CI/CD checks
