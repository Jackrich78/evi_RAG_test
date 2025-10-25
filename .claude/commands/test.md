---
description: Run tests and validate feature implementation against acceptance criteria
argument-hint: [FEAT-ID or test-type or 'all']
---

# Test: Test Execution & Validation Workflow

Run automated tests and validate implementation against acceptance criteria.

## Overview

This command guides the **main Claude Code agent** through running tests and validating that implementations meet requirements. It supports running specific test types, feature-specific tests, or the complete test suite.

## Usage

```bash
# Run tests for specific feature
/test FEAT-001

# Run specific test types
/test unit
/test integration
/test e2e

# Run complete test suite
/test all

# Run with coverage report (if available)
/test FEAT-001 --coverage
```

## Workflow

### Step 1: Determine Test Scope

```
1. Parse command argument:
   - FEAT-XXX: Run tests for specific feature
   - unit/integration/e2e: Run tests of specific type
   - all: Run complete test suite

2. If FEAT-XXX specified:
   - Read docs/features/FEAT-XXX/testing.md
   - Identify test files for this feature
   - Load acceptance criteria from docs/features/FEAT-XXX/acceptance.md
   - Prepare for validation

3. If test type specified:
   - Determine test command from project setup
   - Find all tests of that type
```

### Step 2: Detect Test Framework

```
4. Identify test framework based on project:
   - JavaScript/TypeScript: Jest, Vitest, Mocha, etc.
   - Python: pytest, unittest
   - Rust: cargo test
   - Go: go test
   - Check package.json, pyproject.toml, Cargo.toml, etc.

5. Determine test command:
   - npm test, npm run test:unit, etc.
   - pytest, pytest tests/unit/
   - cargo test
   - go test ./...

6. Check for test scripts in package.json or similar:
   - Use defined scripts if available
   - Fall back to framework defaults
```

### Step 3: Run Tests

```
7. Execute test command:
   - Run via Bash tool with appropriate timeout
   - Capture stdout and stderr
   - Record exit code
   - Show output to user in real-time if possible

8. If coverage requested:
   - Run with coverage flags:
     * Jest: --coverage
     * pytest: --cov
     * cargo: tarpaulin or llvm-cov
   - Capture coverage report
```

### Step 4: Analyze Results

```
9. Parse test output:
   - Count total tests
   - Count passing tests
   - Count failing tests
   - Count skipped tests
   - Identify which tests failed
   - Extract error messages

10. Parse coverage output (if available):
    - Overall coverage percentage
    - Per-file coverage
    - Uncovered lines
    - Coverage by test type

11. Compare against goals:
    - Read testing.md for coverage goals
    - Check if coverage meets target
    - Identify coverage gaps
```

### Step 5: Validate Against Acceptance Criteria

```
12. If feature-specific test (FEAT-XXX):
    - Read docs/features/FEAT-XXX/acceptance.md
    - Map tests to acceptance criteria:
      * Each AC-FEAT-XXX-### should have corresponding test
      * Check test names/descriptions for AC references
    - Determine which acceptance criteria are covered
    - Identify missing test coverage

13. Generate validation report:
    ✅ AC-FEAT-001-001: User authentication with valid credentials
       → test_authenticate_valid_credentials PASSED
    ✅ AC-FEAT-001-002: Reject invalid credentials
       → test_reject_invalid_credentials PASSED
    ❌ AC-FEAT-001-003: Password reset flow
       → No corresponding test found
```

### Step 6: Report Results

```
14. Present comprehensive report:
    - Test execution summary
    - Pass/fail status
    - Coverage metrics (if available)
    - Acceptance criteria validation
    - Recommendations for fixes
    - Next steps

15. If all tests pass:
    - Congratulate success
    - Suggest next step (/commit or manual testing)
    - Update Archon task (if available):
      If Archon MCP available and FEAT-XXX tests:
        Find validation task:
          tasks = mcp__archon__find_tasks(filter_by="feature", filter_value="FEAT-XXX")
          validate_task = [t for t in tasks if "Validate & Commit" in t["title"]]

        Mark as doing:
          mcp__archon__manage_task("update",
            task_id=validate_task["id"],
            status="doing"
          )

        Print:
          "✅ Tests passed - validation in progress"
          "   Next: Run /commit to complete feature"

16. If tests fail:
    - Show failing tests with errors
    - Suggest fixes based on error messages
    - Recommend running /build to fix issues
```

## Example Usage

### Example 1: Feature-Specific Tests

```
User: /test FEAT-001

Claude Code Agent:
1. [Reads docs/features/FEAT-001_authentication/testing.md]
2. [Identifies test files: tests/features/auth/*.test.ts]
3. [Runs: npm test -- tests/features/auth/]
4. [Output: 12 tests, 12 passed, 0 failed]
5. [Reads acceptance.md, validates coverage]
6. Presents:

✅ FEAT-001 Test Results: ALL PASSING

Test Summary:
- Total: 12 tests
- Passed: 12 (100%)
- Failed: 0
- Duration: 2.3s

Acceptance Criteria Coverage:
✅ AC-FEAT-001-001: Login with valid credentials (test_valid_login)
✅ AC-FEAT-001-002: Reject invalid credentials (test_invalid_login)
✅ AC-FEAT-001-003: Password reset flow (test_password_reset)
... (9 more criteria covered)

Next Steps:
- Run /test all to ensure no regressions
- Follow manual-test.md for human validation
- When ready: /commit to create git commit
```

### Example 2: Test Type

```
User: /test unit

Claude Code Agent:
1. [Detects test framework: pytest]
2. [Runs: pytest tests/unit/ -v]
3. [Output: 45 tests, 43 passed, 2 failed]
4. Presents:

⚠️ Unit Tests: 2 FAILURES

Test Summary:
- Total: 45 tests
- Passed: 43 (95.6%)
- Failed: 2
- Duration: 1.8s

Failures:
❌ tests/unit/auth/test_validation.py::test_email_validation
   AssertionError: Expected validation error for invalid email
   Line 23: assert result.error == "Invalid email format"
            But got: None

❌ tests/unit/utils/test_helpers.py::test_format_date
   AssertionError: Date formatting incorrect
   Line 45: assert formatted == "2025-10-24"
            But got: "10/24/2025"

Recommendations:
1. Fix email validation logic in src/auth/validation.py
2. Update date formatting in src/utils/helpers.py
3. Re-run /test unit to validate fixes
```

### Example 3: Full Suite with Coverage

```
User: /test all --coverage

Claude Code Agent:
1. [Runs: npm test -- --coverage]
2. [Executes all tests across unit, integration, e2e]
3. [Generates coverage report]
4. Presents:

✅ Full Test Suite: ALL PASSING

Test Summary:
- Unit: 45/45 passed
- Integration: 18/18 passed
- E2E: 8/8 passed
- Total: 71 tests, 0 failures
- Duration: 12.4s

Coverage Report:
- Overall: 87.3% (target: 80% ✅)
- src/auth/: 95.2%
- src/utils/: 78.4%
- src/api/: 82.1%

Uncovered Areas:
- src/utils/legacy.ts: Lines 45-67 (error handling)
- src/api/webhooks.ts: Lines 12-25 (edge case)

All acceptance criteria validated ✅

Next Steps:
- (Optional) Add tests for uncovered areas
- Proceed to /commit for git commit
- Follow manual-test.md for human testing
```

## Test Type Detection

The command automatically detects test types based on file locations and naming:

**Unit Tests:**
- `tests/unit/**/*`
- `tests/**/test_*.py` (Python)
- `tests/**/*.test.ts` (TypeScript)
- Files testing single functions/classes

**Integration Tests:**
- `tests/integration/**/*`
- `tests/**/integration/*.test.*`
- Files testing multiple components together

**E2E Tests:**
- `tests/e2e/**/*`
- `tests/**/*.e2e.test.*`
- Files testing complete user workflows

## Test Framework Commands

### JavaScript/TypeScript
```bash
# Jest
npm test
npm test -- tests/features/auth/
npm test -- --coverage

# Vitest
npm run test
npm run test:unit
npm run test:integration

# Mocha
npm test
mocha tests/**/*.test.js
```

### Python
```bash
# pytest
pytest
pytest tests/unit/
pytest tests/ -v --cov
pytest -k "auth" --cov=src/auth

# unittest
python -m unittest discover
```

### Rust
```bash
# Cargo
cargo test
cargo test --lib  # Unit tests only
cargo test --test integration_tests
cargo tarpaulin --out Html  # Coverage
```

### Go
```bash
# Go
go test ./...
go test -v ./pkg/auth/
go test -cover ./...
```

## Coverage Interpretation

**Coverage Thresholds:**
- **Excellent:** ≥90% - Comprehensive test coverage
- **Good:** 80-89% - Meets most projects' goals
- **Acceptable:** 70-79% - Minimum for production
- **Needs Improvement:** <70% - Add more tests

**Coverage Types:**
- **Line Coverage:** % of code lines executed during tests
- **Branch Coverage:** % of conditional branches tested
- **Function Coverage:** % of functions called in tests
- **Statement Coverage:** % of statements executed

## Validation Against Acceptance Criteria

For feature-specific tests (`/test FEAT-XXX`), the command validates:

1. **Test Existence:** Each AC has at least one test
2. **Test Passing:** Tests for each AC pass
3. **Coverage:** Acceptance criteria logic is covered by tests
4. **Naming:** Tests reference AC IDs in names or comments

**Example Mapping:**
```python
# Acceptance Criteria: AC-FEAT-001-001
# Given valid credentials, when user logs in, then they are authenticated

def test_ac_feat_001_001_authenticate_valid_credentials():
    """Test for AC-FEAT-001-001: User authentication"""
    # Test implementation...
```

## Error Handling & Troubleshooting

**Test Command Not Found:**
```
❌ Error: Test command not found
   Tried: npm test

Solution: Check package.json for test script
          Or specify test command manually
          For Python: Try 'pytest' or 'python -m pytest'
```

**All Tests Skipped:**
```
⚠️ Warning: All tests skipped
   0 tests executed

Solution: Check test file patterns
          Ensure test files match framework conventions
          Verify test discovery configuration
```

**Timeout:**
```
❌ Error: Test execution timeout (120s)
   Some tests may be hanging

Solution: Check for infinite loops or network calls
          Increase timeout for slow tests
          Mock external dependencies
```

**Coverage Tool Missing:**
```
⚠️ Warning: Coverage requested but tool not available
   Install: npm install --save-dev jest @coverage/jest
   Or: pip install pytest-cov

   Running tests without coverage...
```

## Integration with Other Commands

**Before /test:**
```
/build FEAT-XXX  →  Implements feature and tests
```

**After /test:**
```
If tests pass:
  → /commit  (Create git commit)
  → Follow manual-test.md

If tests fail:
  → Fix implementation
  → /test again to validate
```

## Quality Gates

**Required for Success:**
- ✅ All tests must pass (no failures)
- ✅ Coverage meets target from testing.md (if specified)
- ✅ Each acceptance criterion has test coverage
- ✅ No test errors or exceptions

**Optional Quality Checks:**
- ⚠️ Test execution time reasonable (<30s for unit, <2min for integration)
- ⚠️ No test warnings or deprecation notices
- ⚠️ Coverage trending upward (not declining)

## Best Practices

### Test Organization
- Group tests by feature in `tests/features/FEAT-XXX/`
- Separate unit, integration, and e2e tests
- Use descriptive test file names
- Reference acceptance criteria in test names

### Test Execution
- Run unit tests frequently (fast feedback)
- Run integration tests before commits
- Run e2e tests before PRs
- Run full suite in CI/CD

### Test Maintenance
- Keep tests green - fix failures immediately
- Update tests when requirements change
- Remove or update obsolete tests
- Monitor coverage trends

## Command Options

**Flags:**
- `--coverage` - Generate coverage report
- `--verbose` or `-v` - Detailed output
- `--watch` - Run tests in watch mode (if supported)
- `--bail` - Stop on first failure

**Examples:**
```bash
/test FEAT-001 --coverage
/test unit -v
/test all --coverage --verbose
```

## Test Result Formats

**Summary Format:**
```
✅ FEAT-XXX Tests: PASSING
- 12/12 tests passed
- Duration: 2.3s
- Coverage: 92%
```

**Detailed Format:**
```
Test Results for FEAT-001:

Unit Tests (tests/features/auth/):
  ✅ test_valid_login - 45ms
  ✅ test_invalid_login - 32ms
  ✅ test_password_reset - 156ms
  ... (9 more)

Acceptance Criteria:
  ✅ AC-FEAT-001-001: Login validation
  ✅ AC-FEAT-001-002: Invalid credentials
  ✅ AC-FEAT-001-003: Password reset
  ... (7 more)

Duration: 2.34s
Coverage: 92.1%
Status: READY FOR COMMIT
```

## Related Documentation

- [Testing Strategy SOP](../../docs/sop/testing-strategy.md)
- [/build Command](./build.md) - Implement with TDD
- [/commit Command](./commit.md) - Create commit after tests pass
- [Example Tests (FEAT-001)](../../docs/features/FEAT-001_example/testing.md)

---

**Note:** This command validates implementation quality. All tests must pass before proceeding to `/commit`. If tests fail, use error messages to guide fixes and re-run `/test`.
