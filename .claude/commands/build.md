---
description: Implement feature using Test-Driven Development (Red-Green-Refactor)
argument-hint: [FEAT-ID]
---

# Build: Test-Driven Implementation Workflow

Implement a feature following TDD principles: Write tests first (RED), implement minimal code (GREEN), then refactor for quality.

## Overview

This command guides the **main Claude Code agent** through implementing a planned feature using the Red-Green-Refactor TDD cycle. The agent implements both tests and code directly - no specialized sub-agents are invoked.

## Prerequisites

Before running `/build FEAT-XXX`, ensure:
- ✅ Planning docs exist: `docs/features/FEAT-XXX/` contains all 6 planning documents
- ✅ Architecture decision made in `architecture.md`
- ✅ Acceptance criteria defined in `acceptance.md`
- ✅ Test strategy documented in `testing.md`
- ✅ Test stubs created in `tests/` directory
- ✅ Reviewer validation passed

## Archon Task Management (If Available)

Before starting build, update task status in Archon to track progress.

**Mark Build Task as "Doing":**
```
If Archon MCP available:
  Try to find tasks for this feature:
    tasks = mcp__archon__find_tasks(filter_by="feature", filter_value="FEAT-XXX")

  If tasks found:
    Find build task:
      build_task = [t for t in tasks if "Build with TDD" in t["title"]]

    If build task exists:
      Mark as doing:
        mcp__archon__manage_task("update",
          task_id=build_task["id"],
          status="doing"
        )

      Print:
        "🔨 Started: FEAT-XXX - Build with TDD"
        "   Status: doing"
```

**Error Handling:**
- If Archon unavailable: Skip silently
- If no tasks found: Skip (continue build normally)
- Never block build workflow on task update failures

## TDD Workflow: Red-Green-Refactor

### Phase 1: RED - Failing Tests

**Goal:** Turn test stubs into functional tests that fail appropriately

```
1. Read planning documentation:
   - docs/features/FEAT-XXX/architecture.md (implementation approach)
   - docs/features/FEAT-XXX/acceptance.md (what to test)
   - docs/features/FEAT-XXX/testing.md (test strategy)

2. Find test stub files:
   - Use Glob to find test files: tests/**/*FEAT-XXX*.test.* or tests/**/test_*.py
   - Read test stubs created by Planner agent

3. Implement test stubs:
   - For each TODO in test files:
     * Read corresponding acceptance criteria (AC-FEAT-XXX-###)
     * Write functional test implementing Given/When/Then
     * Use appropriate assertions and matchers
     * Mock external dependencies as specified in testing.md
   - Follow test framework conventions (Jest, pytest, etc.)

4. Run tests to confirm RED:
   - Execute test suite: npm test, pytest, cargo test, etc.
   - Verify all new tests FAIL with appropriate error messages
   - If tests pass prematurely, they're not testing the right thing
   - Fix test implementation until proper failures occur

5. Checkpoint:
   ✅ All acceptance criteria have corresponding functional tests
   ✅ All tests fail with clear, expected error messages
   ✅ Test code is readable and follows conventions
```

### Phase 2: GREEN - Minimal Implementation

**Goal:** Write just enough code to make tests pass

```
6. Read architecture decision:
   - Review recommended approach from architecture.md
   - Note any specific patterns, libraries, or constraints
   - Check integration points with existing code

7. Implement minimal working code:
   - For each failing test:
     * Write simplest code that makes it pass
     * Don't optimize yet - focus on correctness
     * Follow architecture recommendations
   - Start with core functionality
   - Add edge case handling as tests demand

8. Run tests iteratively:
   - After each implementation chunk:
     * Run test suite
     * Fix failures
     * Ensure no regressions in existing tests
   - Continue until ALL tests pass

9. Checkpoint:
   ✅ All new tests passing
   ✅ No existing tests broken
   ✅ Core functionality working
   ✅ Acceptance criteria met
```

### Phase 3: REFACTOR - Improve Quality

**Goal:** Improve code quality while keeping tests green

```
10. Refactor for quality:
    - Extract repeated code into functions
    - Improve naming and clarity
    - Apply design patterns from architecture.md
    - Add type hints/annotations
    - Add inline documentation for complex logic
    - Improve error handling

11. Run tests after EACH refactor:
    - Never refactor without running tests
    - If tests fail, undo and try smaller changes
    - Keep tests green throughout refactoring

12. Code quality checks:
    - Run linter (if configured): eslint, ruff, clippy
    - Run formatter (if configured): prettier, black, rustfmt
    - Check for code smells
    - Ensure consistent style

13. Final validation:
    - Run complete test suite
    - Check test coverage (if tooling available)
    - Verify acceptance criteria in acceptance.md
    - Ensure non-functional requirements met

14. Checkpoint:
    ✅ All tests still passing
    ✅ Code is clean and well-structured
    ✅ No obvious code smells
    ✅ Documentation inline where needed
```

### Phase 4: Documentation & Handoff

**Goal:** Document implementation and prepare for review

```
15. Create implementation notes:
    - Add docs/features/FEAT-XXX/implementation.md with:
      * Implementation summary
      * Key files created/modified
      * Design decisions made
      * Known limitations or tech debt
      * Testing notes
      * Deployment considerations (if applicable)

16. Update documentation index:
    - Run /update-docs to regenerate docs/README.md
    - Verify all links work
    - Update feature status to "Implemented"

17. Prepare for manual testing:
    - Review docs/features/FEAT-XXX/manual-test.md
    - Note any setup required
    - Identify what needs human validation

18. Summary report:
    Present to user:
    - Files created/modified
    - Test results (number passed)
    - Acceptance criteria status
    - Next steps (manual testing, commit, deploy)

19. Update Archon task (if available):
    If Archon MCP available:
      Find build task:
        tasks = mcp__archon__find_tasks(filter_by="feature", filter_value="FEAT-XXX")
        build_task = [t for t in tasks if "Build with TDD" in t["title"]]

      Mark as review:
        mcp__archon__manage_task("update",
          task_id=build_task["id"],
          status="review"
        )

      Print:
        "✅ Build complete - marked for review"
        "   Next: Run /test FEAT-XXX to validate"
```

## Example Usage

```
User: /build FEAT-001

Claude Code Agent:
1. [Reads architecture.md, acceptance.md, testing.md]
2. [Finds test stubs in tests/features/authentication/]
3. [Implements 12 functional tests for authentication]
4. [Runs tests - all fail as expected] ✅ RED
5. [Implements Auth service following architecture.md]
6. [Runs tests iteratively - all pass] ✅ GREEN
7. [Refactors: extracts validation, improves naming]
8. [Runs tests after each refactor - still green] ✅ REFACTOR
9. [Runs linter and formatter]
10. [Creates implementation.md]
11. [Updates docs index]
12. Presents: "FEAT-001 implemented. 12/12 tests passing. Ready for manual testing."
```

## Command Arguments

- **FEAT-ID** (required): Feature ID like `FEAT-001`
- **Optional flags** (future):
  - `--skip-tests`: Skip test implementation (not recommended)
  - `--watch`: Run tests in watch mode during development
  - `--coverage`: Generate coverage report

## Validation & Quality Gates

**Before Implementation:**
- Planning docs must exist and be complete
- Reviewer validation must have passed
- Test stubs must be present

**During Implementation:**
- Tests must fail before implementation (RED)
- Tests must pass after implementation (GREEN)
- Tests must stay green during refactoring

**After Implementation:**
- All acceptance criteria met
- No test failures
- Code passes linter (if configured)
- Implementation documented

## Error Handling

**Missing Planning Docs:**
```
❌ Error: Planning incomplete for FEAT-001
   Missing: architecture.md

   Run /plan FEAT-001 first to create planning documentation.
```

**Tests Pass Prematurely:**
```
⚠️ Warning: Tests passing before implementation
   Expected: Tests should fail until feature code is written

   Review tests to ensure they're actually testing the feature.
   Common issues:
   - Test mocks return hardcoded success
   - Test doesn't assert on actual behavior
   - Test stub wasn't updated properly
```

**Test Failures During Refactor:**
```
❌ Error: Tests failed during refactoring
   Previously passing: 12/12
   Currently passing: 10/12

   Undo last refactor and try smaller changes.
   Keep tests green throughout refactoring phase.
```

## Integration with Other Commands

**Before /build:**
```
/explore [topic]  →  Creates PRD and research
/plan FEAT-XXX    →  Creates planning docs and test stubs
```

**After /build:**
```
/test FEAT-XXX    →  Run test suite and validate
/commit           →  Create conventional commit
```

## Best Practices

### Testing
- Write tests that fail for the right reason
- Use descriptive test names: `should_authenticate_user_with_valid_credentials`
- Test edge cases from acceptance criteria
- Mock external dependencies (APIs, databases)
- Avoid testing implementation details

### Implementation
- Start simple, add complexity as tests demand
- Follow architecture.md recommendations
- Integrate with existing code patterns
- Use existing utilities and helpers
- Add error handling for edge cases

### Refactoring
- Make one change at a time
- Run tests after each change
- Improve names first (easiest refactor)
- Extract functions for repeated code
- Apply patterns from architecture.md

## Technology-Specific Patterns

### TypeScript/JavaScript
```typescript
// Test file: tests/features/auth/login.test.ts
describe('FEAT-001: User Authentication', () => {
  it('should authenticate user with valid credentials', async () => {
    // Given: User with valid credentials
    const user = { email: 'test@example.com', password: 'valid123' };

    // When: User attempts login
    const result = await authService.login(user.email, user.password);

    // Then: User is authenticated
    expect(result.success).toBe(true);
    expect(result.token).toBeDefined();
  });
});
```

### Python
```python
# Test file: tests/features/auth/test_login.py
def test_authenticate_user_with_valid_credentials():
    """AC-FEAT-001-001: User can authenticate with valid credentials"""
    # Given: User with valid credentials
    user = {"email": "test@example.com", "password": "valid123"}

    # When: User attempts login
    result = auth_service.login(user["email"], user["password"])

    # Then: User is authenticated
    assert result["success"] is True
    assert "token" in result
```

### Rust
```rust
// Test file: tests/features/auth/login_test.rs
#[test]
fn test_authenticate_user_with_valid_credentials() {
    // Given: User with valid credentials
    let email = "test@example.com";
    let password = "valid123";

    // When: User attempts login
    let result = auth_service::login(email, password);

    // Then: User is authenticated
    assert!(result.is_ok());
    assert!(result.unwrap().token.is_some());
}
```

## Troubleshooting

**Problem:** Not sure what to implement
```
Solution: Read architecture.md for recommended approach
          Check acceptance.md for specific requirements
          Look at test descriptions for expected behavior
```

**Problem:** Tests too complex to implement
```
Solution: Break into smaller tests
          Implement simplest case first
          Add edge cases incrementally
```

**Problem:** Implementation seems too big
```
Solution: This is normal for new features
          Take it one test at a time
          Commit progress frequently (use /commit)
```

**Problem:** Existing tests breaking
```
Solution: Check what changed in shared code
          May need to update architecture approach
          Consider backward compatibility
```

## Implementation Checklist

Use this checklist to ensure complete implementation:

- [ ] Read all planning documentation
- [ ] Found and reviewed test stubs
- [ ] Implemented all test stubs as functional tests
- [ ] Ran tests - all failed appropriately (RED)
- [ ] Implemented core functionality
- [ ] Ran tests iteratively - all passed (GREEN)
- [ ] Refactored for code quality
- [ ] Ran tests after each refactor - stayed green
- [ ] Ran linter and formatter
- [ ] Created implementation.md documentation
- [ ] Updated documentation index via /update-docs
- [ ] All acceptance criteria met
- [ ] Ready for manual testing

## Related Documentation

- [TDD Strategy SOP](../../docs/sop/testing-strategy.md)
- [Code Style SOP](../../docs/sop/code-style.md)
- [Example Implementation (FEAT-001)](../../docs/features/FEAT-001_example/)
- [/test Command](./../commands/test.md) - Next step: validate implementation

---

**Note:** This command guides the main Claude Code agent. No specialized sub-agents are invoked for implementation - the agent writes both tests and code directly, following the TDD workflow above.
