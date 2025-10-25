# Testing Strategy: [Feature Name]

**Feature ID:** FEAT-XXX
**Created:** YYYY-MM-DD
**Test Coverage Goal:** [X%]

## Test Strategy Overview

*High-level approach to testing this feature. ≤120 words.*

[What levels of testing are needed? What's the testing philosophy (TDD, BDD, etc.)? What are the priorities?]

**Testing Levels:**
- ✅ Unit Tests: [Scope]
- ✅ Integration Tests: [Scope]
- ✅ E2E Tests: [Scope if applicable]
- ✅ Manual Tests: [Scope]

## Unit Tests

*Tests for individual functions, components, or modules in isolation.*

### Test Files to Create

#### `tests/[path]/[filename].test.[ext]`

**Purpose:** [What aspect of the feature this file tests]

**Test Stubs:**
1. **Test:** [Test description referencing AC-FEAT-XXX-###]
   - **Given:** [Setup/precondition]
   - **When:** [Action]
   - **Then:** [Expected result]
   - **Mocks:** [What needs to be mocked]

2. **Test:** [Test description]
   - **Given:** [Setup]
   - **When:** [Action]
   - **Then:** [Result]
   - **Mocks:** [Mocks needed]

3. **Test:** [Test description]
   - **Given:** [Setup]
   - **When:** [Action]
   - **Then:** [Result]
   - **Mocks:** [Mocks needed]

*[List 3-7 unit test stubs per file]*

---

#### `tests/[path]/[filename2].test.[ext]`

**Purpose:** [What this file tests]

**Test Stubs:**
[Similar structure as above]

---

### Unit Test Coverage Goals

- **Functions:** All public functions tested
- **Branches:** All conditional branches covered
- **Edge Cases:** Boundary conditions tested
- **Error Handling:** All error paths tested

**Target Coverage:** [X%] line coverage

## Integration Tests

*Tests for interactions between components, modules, or external services.*

### Test Files to Create

#### `tests/integration/[filename].integration.test.[ext]`

**Purpose:** [What integration scenario this tests]

**Test Stubs:**
1. **Test:** [Integration test description]
   - **Components:** [Which components interact]
   - **Setup:** [Test data, mocks, environment]
   - **Scenario:** [End-to-end flow being tested]
   - **Assertions:** [What to verify]

2. **Test:** [Integration test description]
   - **Components:** [Components involved]
   - **Setup:** [Prerequisites]
   - **Scenario:** [Flow]
   - **Assertions:** [Verifications]

*[List 2-5 integration test stubs per file]*

---

### Integration Test Scope

**Internal Integrations:**
- [Component A] → [Component B]: [What's being tested]
- [Module X] → [Module Y]: [What's being tested]

**External Integrations:**
- [External Service/API]: [What's being tested]
- [Database]: [What's being tested]
- [Third-party SDK]: [What's being tested]

**Mock Strategy:**
- **Fully Mocked:** [Services too slow/expensive to hit]
- **Partially Mocked:** [Services with test environments]
- **Real:** [Local services/databases]

## E2E Tests (If Applicable)

*End-to-end tests simulating real user workflows.*

### Test Files to Create

#### `tests/e2e/[filename].e2e.test.[ext]`

**Purpose:** [User workflow being tested]

**Test Stubs:**
1. **Test:** [E2E scenario description]
   - **User Flow:** [Step-by-step user actions]
   - **Starting State:** [Initial system state]
   - **Actions:** [User interactions]
   - **Expected Outcome:** [What user should see/achieve]
   - **Cleanup:** [Teardown required]

2. **Test:** [E2E scenario]
   - **User Flow:** [Steps]
   - **Starting State:** [State]
   - **Actions:** [Interactions]
   - **Expected Outcome:** [Result]
   - **Cleanup:** [Teardown]

*[List 2-4 E2E test stubs]*

---

### E2E Test Environment

**Browser/Platform:**
- [Browsers to test: Chrome, Firefox, etc.]
- [Devices: Desktop, mobile, etc.]

**Test Data:**
- [How test data is created/seeded]
- [User accounts needed]
- [Database state required]

**Tools:**
- [Test framework: Playwright, Cypress, Selenium, etc.]
- [CI integration details]

## Manual Testing

*Tests that require human verification.*

### Manual Test Scenarios

*See `manual-test.md` for detailed step-by-step instructions.*

**Quick Reference:**
1. [Manual test scenario 1]: Verify [specific aspect]
2. [Manual test scenario 2]: Verify [specific aspect]
3. [Manual test scenario 3]: Verify [specific aspect]

**Manual Test Focus:**
- **Visual Verification:** [UI appearance, animations, responsiveness]
- **User Experience:** [Workflow intuition, error messages, feedback]
- **Accessibility:** [Keyboard nav, screen reader, contrast]
- **Cross-browser:** [Appearance and function across browsers]

## Test Data Requirements

### Fixtures & Seed Data

**Unit Test Fixtures:**
```[language]
// Example fixture structure
{
  "user": { "id": 1, "name": "Test User", ... },
  "data": { ... }
}
```

**Integration Test Data:**
- [Database seeding script location]
- [API mock data location]

**E2E Test Data:**
- [Test accounts/credentials]
- [Sample data sets]
- [Cleanup requirements]

## Mocking Strategy

### What to Mock

**Always Mock:**
- External paid APIs (to avoid costs)
- Slow operations (to keep tests fast)
- Non-deterministic operations (random, time, etc.)

**Sometimes Mock:**
- Internal APIs (mock for unit, real for integration)
- Databases (in-memory for unit, real for integration)

**Never Mock:**
- Core feature logic being tested
- Critical data validation

### Mocking Approach

**Framework:** [Jest, pytest, etc.]

**Mock Examples:**
```[language]
// Example mock implementation
mock[Service].method = jest.fn().mockReturnValue(...)
```

## Test Execution

### Running Tests Locally

**Unit Tests:**
```bash
[command to run unit tests]
# Example: npm test -- --coverage
```

**Integration Tests:**
```bash
[command to run integration tests]
# Example: npm run test:integration
```

**E2E Tests:**
```bash
[command to run E2E tests]
# Example: npm run test:e2e
```

### CI/CD Integration (Phase 2)

**Pipeline Stages:**
1. Unit tests (run on every commit)
2. Integration tests (run on every commit)
3. E2E tests (run on PR, pre-merge)
4. Coverage report generation
5. Test result artifacts

**Failure Handling:**
- Failing tests block merge
- Coverage drops block merge (if below threshold)
- Flaky test detection and reporting

## Coverage Goals

### Coverage Targets

| Test Level | Target Coverage | Minimum Acceptable |
|------------|----------------|-------------------|
| Unit | [X%] | [Y%] |
| Integration | [X%] | [Y%] |
| E2E | N/A (workflow-based) | [Z workflows] |

### Critical Paths

**Must Have 100% Coverage:**
- [Critical function/path 1]
- [Security-sensitive code]
- [Error handling for critical operations]

**Can Have Lower Coverage:**
- [UI styling code]
- [Logging/telemetry]
- [Non-critical edge cases]

## Performance Testing

*If performance is a requirement from AC non-functional criteria.*

### Performance Benchmarks

**Requirement:** [From AC-FEAT-XXX-201]

**Test Approach:**
- **Tool:** [Performance testing tool]
- **Scenarios:**
  1. [Scenario 1]: [Expected time/throughput]
  2. [Scenario 2]: [Expected time/throughput]

**Acceptance:**
- [X ms] response time for [operation]
- [Y req/sec] throughput under load

## Security Testing

*If security testing is required.*

### Security Test Scenarios

1. **Input Validation:** Verify all inputs sanitized
2. **Authentication:** Verify auth checks on all endpoints
3. **Authorization:** Verify permission checks
4. **Data Protection:** Verify sensitive data encrypted

**Tools:**
- [Security scanning tools if applicable]

## Test Stub Generation (Phase 1)

*These test files will be created with TODO stubs during planning:*

```
tests/
├── features/[feature-name]/
│   ├── [component].test.[ext] (X unit test stubs)
│   ├── [module].test.[ext] (Y unit test stubs)
│   └── [integration].integration.test.[ext] (Z integration stubs)
└── e2e/
    └── [workflow].e2e.test.[ext] (W E2E test stubs)
```

**Total Test Stubs:** [Sum] test functions with TODO comments

## Out of Scope

*What we're explicitly NOT testing in this phase:*

- [Excluded test type or scenario]
- [Rationale for exclusion]

---

**Next Steps:**
1. Planner will generate test stub files based on this strategy
2. Phase 2: Implementer will make stubs functional
3. Phase 2: Tester will execute and validate
