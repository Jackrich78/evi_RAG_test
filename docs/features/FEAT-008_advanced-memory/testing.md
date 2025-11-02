# Testing Strategy: Advanced Memory & Session Management

**Feature ID:** FEAT-008
**Created:** 2025-11-02
**Status:** Planning Phase

## Overview

This document defines the comprehensive testing strategy for FEAT-008 Advanced Memory & Session Management. The feature adds stateful conversation capabilities via X-Session-ID header with PostgreSQL session storage, requiring thorough testing of session lifecycle, context injection, performance, and data persistence.

**Testing Objectives:**
- Verify multi-turn conversation context retention across requests
- Validate session isolation between CLI runs and concurrent users
- Ensure zero data loss on container restarts
- Prevent SQL injection vulnerability in get_session_messages()
- Confirm performance requirements (<50ms context retrieval, <5s total query time)
- Test automatic session cleanup with last_accessed tracking

## Test Levels

### Unit Tests (Target Coverage: 90%)

Unit tests focus on individual functions and components in isolation using mocked dependencies.

**Test Files to Create:**

**1. tests/agent/test_db_utils_session.py**
Tests for session management functions in agent/db_utils.py (lines 84-259)

Test Cases:
- `test_create_session_with_last_accessed()` - Verify last_accessed timestamp set on creation (AC-FEAT-008-207)
- `test_create_session_returns_uuid()` - Verify session creation returns valid UUID
- `test_get_session_by_id_success()` - Verify session retrieval with valid UUID
- `test_get_session_by_id_not_found()` - Verify None returned for non-existent session (AC-FEAT-008-106)
- `test_add_message_updates_last_accessed()` - Verify last_accessed updates on new message (AC-FEAT-008-207)
- `test_add_message_stores_correctly()` - Verify message content, role, session_id stored
- `test_get_session_messages_sql_injection_safe()` - Verify parameterized LIMIT query (AC-FEAT-008-107, AC-FEAT-008-301)
- `test_get_session_messages_order_correct()` - Verify messages in chronological order (AC-FEAT-008-108)
- `test_get_session_messages_limit_10()` - Verify only last 10 messages returned (AC-FEAT-008-104)
- `test_get_session_messages_empty_session()` - Verify empty list for new session (AC-FEAT-008-105)

**2. tests/agent/test_api_session_header.py**
Tests for X-Session-ID header parsing and validation in agent/api.py

Test Cases:
- `test_x_session_id_header_valid_uuid()` - Accept valid UUID header (AC-FEAT-008-003)
- `test_x_session_id_header_invalid_uuid()` - Return 400 for invalid UUID (AC-FEAT-008-101, AC-FEAT-008-302)
- `test_x_session_id_header_missing()` - Auto-create session if header absent (AC-FEAT-008-102)
- `test_x_session_id_header_non_existent()` - Return 404 for valid UUID not in DB (AC-FEAT-008-106)
- `test_x_session_id_response_header()` - Verify response includes session ID header (AC-FEAT-008-003)
- `test_x_session_id_auto_creation_response()` - Verify new session ID returned in header (AC-FEAT-008-102)

**3. tests/agent/test_specialist_context.py**
Tests for context injection into PydanticAI agent

Test Cases:
- `test_context_loaded_in_message_history()` - Verify message_history parameter receives context (AC-FEAT-008-001)
- `test_context_format_pydantic_ai()` - Verify messages converted to PydanticAI format
- `test_context_empty_for_new_session()` - Verify empty context doesn't break agent (AC-FEAT-008-105)
- `test_context_includes_last_10_messages()` - Verify only last 10 messages passed (AC-FEAT-008-104)

**Coverage Goals:**
- Session management functions: 95% (critical path)
- Header validation: 90% (security-critical)
- Context injection: 85% (integration with PydanticAI)

**Mocking Strategy:**
- Mock database connections using `unittest.mock.AsyncMock`
- Mock PydanticAI agent.run() to verify message_history parameter
- Use pytest fixtures for test data (sample sessions, messages, UUIDs)

### Integration Tests (Target Coverage: 80%)

Integration tests verify interaction between components with real PostgreSQL database (test container).

**Test Files to Create:**

**1. tests/integration/test_session_flow.py**
End-to-end session lifecycle tests with real database

Test Cases:
- `test_create_session_add_messages_retrieve()` - Full flow: create → add 5 messages → retrieve last 10 (AC-FEAT-008-002)
- `test_multi_turn_conversation()` - Simulate OpenWebUI multi-turn with context (AC-FEAT-008-001)
- `test_concurrent_sessions_isolated()` - Verify 2 sessions don't share context (AC-FEAT-008-103)
- `test_session_cleanup_old_sessions()` - Verify sessions deleted after 30 days (AC-FEAT-008-205)
- `test_cascade_delete_messages()` - Verify messages deleted when session deleted (AC-FEAT-008-205)

**2. tests/integration/test_container_persistence.sh**
Bash script to test docker-compose restart persistence

Test Steps:
```bash
#!/bin/bash
# AC-FEAT-008-006, AC-FEAT-008-007, AC-FEAT-008-203

# 1. Start containers
docker-compose up -d

# 2. Create session with 5 messages via API
SESSION_ID=$(curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"evi-specialist","messages":[{"role":"user","content":"Test 1"}]}' \
  | jq -r '.headers["x-session-id"]')

# Add 4 more messages
for i in {2..5}; do
  curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "X-Session-ID: $SESSION_ID" \
    -d "{\"model\":\"evi-specialist\",\"messages\":[{\"role\":\"user\",\"content\":\"Test $i\"}]}"
done

# 3. Verify 5 messages in database
docker-compose exec db psql -U postgres -d evi_rag -c \
  "SELECT COUNT(*) FROM messages WHERE session_id='$SESSION_ID';" | grep 5

# 4. Restart containers
docker-compose down
docker-compose up -d

# 5. Verify session and messages still exist
docker-compose exec db psql -U postgres -d evi_rag -c \
  "SELECT COUNT(*) FROM sessions WHERE id='$SESSION_ID';" | grep 1

docker-compose exec db psql -U postgres -d evi_rag -c \
  "SELECT COUNT(*) FROM messages WHERE session_id='$SESSION_ID';" | grep 5

# 6. Send new message to session
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION_ID" \
  -d '{"model":"evi-specialist","messages":[{"role":"user","content":"Test 6"}]}'

# 7. Verify 6 messages now
docker-compose exec db psql -U postgres -d evi_rag -c \
  "SELECT COUNT(*) FROM messages WHERE session_id='$SESSION_ID';" | grep 6

echo "✅ Container restart persistence test passed"
```

**Database Setup:**
- Use separate test database: `evi_rag_test`
- Reset database before each test suite
- Seed test data with pytest fixtures
- Clean up after tests (DROP test database)

**Coverage Goals:**
- Session lifecycle: 90% (critical for feature)
- Concurrent access: 75% (edge cases)
- Cleanup automation: 85% (data integrity)

### End-to-End Tests (Manual - see manual-test.md)

E2E tests verify user-facing functionality through real UI and CLI interactions.

**Test Scenarios:**
1. Multi-turn conversation in OpenWebUI (AC-FEAT-008-001)
2. CLI session isolation verification (AC-FEAT-008-004, AC-FEAT-008-005)
3. Container restart with active session (AC-FEAT-008-006, AC-FEAT-008-007)
4. Invalid session ID error handling (AC-FEAT-008-101)

**Manual Testing Required:**
- Visual confirmation of agent responses in OpenWebUI
- CLI output verification for session creation
- Database inspection with psql for message counts
- Performance monitoring (response times <5s)

**Automation Opportunity (Phase 3):**
- Playwright/Selenium tests for OpenWebUI flows
- Automated CLI testing with expect scripts
- Performance regression tests with locust/k6

### Performance Tests

**Test Files to Create:**

**1. tests/performance/test_context_retrieval_speed.py**

Test Cases:
- `test_get_messages_latency_50ms()` - Verify context retrieval <50ms (AC-FEAT-008-201)
- `test_concurrent_users_20()` - Verify 20 concurrent sessions work (AC-FEAT-008-206)
- `test_large_session_100_messages()` - Verify performance with 100+ messages (AC-FEAT-008-104)

Performance Benchmarks:
- Context retrieval: <50ms (AC-FEAT-008-201)
- Total request time: <5s (AC-FEAT-008-202)
- Concurrent users: 20 without errors (AC-FEAT-008-206)

**Tools:**
- pytest-benchmark for timing measurements
- PostgreSQL EXPLAIN ANALYZE for query optimization
- Load testing with locust (optional for Phase 3)

### Security Tests

**Test Files to Create:**

**1. tests/security/test_sql_injection.py**

Test Cases:
- `test_limit_sql_injection_prevention()` - Verify parameterized LIMIT (AC-FEAT-008-107, AC-FEAT-008-301)
- `test_session_id_input_validation()` - Verify UUID validation (AC-FEAT-008-302)
- `test_message_content_escaping()` - Verify message content doesn't break queries

**Security Validation:**
- OWASP SQL Injection tests with malicious inputs
- UUID format validation (reject arbitrary strings)
- Parameterized queries for all user inputs

## Test Data Management

**Fixtures:**
```python
# tests/conftest.py

@pytest.fixture
async def test_session():
    """Create test session with known UUID"""
    session_id = uuid.uuid4()
    await create_session(user_id="test_user", session_id=session_id)
    yield session_id
    # Cleanup after test
    await cleanup_session(session_id)

@pytest.fixture
async def session_with_messages():
    """Create session with 10 sample messages"""
    session_id = await test_session()
    for i in range(10):
        await add_message(
            session_id=session_id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Test message {i}"
        )
    yield session_id
```

**Test Database:**
- Separate `evi_rag_test` database for tests
- Reset schema before each test suite
- Use transactions with rollback for test isolation
- Seed with consistent test data (UUIDs, timestamps)

## Test Execution Strategy

**Local Development:**
```bash
# Activate virtual environment
source venv_linux/bin/activate

# Run all tests
python3 -m pytest tests/ -v

# Run specific test level
python3 -m pytest tests/agent/ -v  # Unit tests only
python3 -m pytest tests/integration/ -v  # Integration tests

# Run with coverage
python3 -m pytest tests/ --cov=agent --cov-report=html

# Run performance tests
python3 -m pytest tests/performance/ -v --benchmark-only
```

**CI/CD Pipeline (Future):**
- Run unit tests on every commit
- Run integration tests on PR to main branch
- Run performance tests on release candidates
- Fail build if coverage <90% for critical paths

**Test Execution Order:**
1. Unit tests (fastest, no external dependencies)
2. Integration tests (require test database)
3. Performance tests (require stable environment)
4. Manual E2E tests (before release)

## Coverage Requirements

**By Component:**
- Session management (db_utils.py): 95% coverage
- API endpoint (api.py session handling): 90% coverage
- Context injection (specialist_agent.py): 85% coverage
- Overall feature: 90% minimum

**Critical Paths (100% coverage required):**
- SQL injection prevention (parameterized queries)
- Session ID validation (UUID format)
- last_accessed timestamp updates
- CASCADE delete on session cleanup

**Exclusions:**
- Logging statements
- Type checking code (if TYPE_CHECKING blocks)
- Debug/development-only code

## Test Maintenance

**Updating Tests:**
- Update tests BEFORE modifying implementation (TDD)
- Add new test for each bug fix (regression prevention)
- Refactor tests when implementation changes
- Keep test data fixtures up to date

**Documentation:**
- Every test case references AC ID in docstring
- Complex test logic includes inline comments
- Test failures include helpful error messages
- README in tests/ directory explains structure

## Acceptance Test Checklist

Before marking FEAT-008 as complete, verify:
- ✅ All 28 acceptance criteria have passing tests
- ✅ Unit test coverage ≥90%
- ✅ Integration test coverage ≥80%
- ✅ Manual E2E tests completed successfully
- ✅ Performance benchmarks meet requirements (<50ms, <5s)
- ✅ Security tests pass (SQL injection, UUID validation)
- ✅ Container restart test passes (zero data loss)
- ✅ All test stubs replaced with implementations
- ✅ CI/CD pipeline runs all tests successfully (future)

## Related Documentation

- Acceptance Criteria: docs/features/FEAT-008_advanced-memory/acceptance.md
- Manual Test Guide: docs/features/FEAT-008_advanced-memory/manual-test.md
- Architecture: docs/features/FEAT-008_advanced-memory/architecture.md
- PRD: docs/features/FEAT-008_advanced-memory/prd.md

---

**Status:** Test stubs ready for Phase 2 implementation
**Next Steps:** Generate test stub files in tests/ directory
