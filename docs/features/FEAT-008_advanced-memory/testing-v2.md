# Testing Strategy: OpenWebUI Stateless Multi-Turn Conversations

**Feature:** FEAT-008 - Advanced Memory and Context Management
**Version:** 2.0 (Corrected Approach)
**Date:** 2025-11-03
**Status:** Planned

## Testing Overview

This document defines the comprehensive testing strategy for implementing stateless multi-turn conversations. The strategy covers unit, integration, performance, and manual testing approaches to ensure the feature meets all acceptance criteria with 90%+ code coverage.

## Test Pyramid

```
      Manual Testing (3 scenarios)
           /\
          /  \
         /E2E \  (OpenWebUI flow)
        /------\
       /  API   \  (5 integration tests)
      /----------\
     /    Unit    \  (15+ unit tests)
    /--------------\
```

**Philosophy:**
- Heavy unit testing for message conversion logic (fast, isolated)
- Moderate integration testing for endpoint → agent flow
- Minimal E2E testing (manual OpenWebUI verification)
- Performance testing for zero-DB and latency requirements

## Test Levels

### 1. Unit Tests (Foundation)

**Scope:** Test `convert_openai_to_pydantic_history()` function in isolation

**Test Files to Create:**
- `tests/agent/test_message_conversion.py` (~15 test functions)

**Coverage Areas:**
- **Happy Path:** Standard user/assistant message pairs
- **Edge Cases:** Empty arrays, single message, system messages
- **Error Handling:** Malformed messages, missing fields
- **Data Validation:** Type checking, content preservation
- **Performance:** Conversion speed benchmarks

**Key Test Cases:**
1. `test_convert_empty_messages()` - AC-FEAT-008-NEW-001, AC-FEAT-008-NEW-105
2. `test_convert_with_history()` - AC-FEAT-008-NEW-002
3. `test_convert_long_conversation()` - AC-FEAT-008-NEW-003
4. `test_exclude_current_message()` - AC-FEAT-008-NEW-006
5. `test_exclude_system_messages()` - AC-FEAT-008-NEW-102
6. `test_preserve_message_order()` - AC-FEAT-008-NEW-103
7. `test_handle_invalid_format()` - AC-FEAT-008-NEW-104
8. `test_user_message_to_model_request()` - AC-FEAT-008-NEW-006
9. `test_assistant_message_to_model_response()` - AC-FEAT-008-NEW-006
10. `test_mixed_valid_invalid_messages()` - AC-FEAT-008-NEW-104
11. `test_conversion_performance()` - AC-FEAT-008-NEW-201
12. `test_empty_content_handling()` - AC-FEAT-008-NEW-104
13. `test_unknown_role_handling()` - AC-FEAT-008-NEW-104
14. `test_single_user_message()` - AC-FEAT-008-NEW-105
15. `test_alternating_roles()` - AC-FEAT-008-NEW-103

**Coverage Goal:** 100% for conversion function (critical path)

---

### 2. Integration Tests (API Layer)

**Scope:** Test endpoint → message extraction → agent invocation flow

**Test Files to Create:**
- `tests/agent/test_stateless_api.py` (~5 test functions)

**Coverage Areas:**
- **Request Handling:** Extract messages from OpenAI-format request
- **Agent Integration:** Pass history to `agent.run()`
- **Response Generation:** Agent uses context correctly
- **Streaming:** History works with streaming responses
- **Error Propagation:** Errors handled gracefully through stack

**Key Test Cases:**
1. `test_api_extracts_history_from_request()` - AC-FEAT-008-NEW-002
2. `test_agent_receives_converted_history()` - AC-FEAT-008-NEW-006
3. `test_agent_uses_context_in_response()` - AC-FEAT-008-NEW-004
4. `test_streaming_with_history()` - AC-FEAT-008-NEW-005
5. `test_malformed_request_handling()` - AC-FEAT-008-NEW-101

**Test Approach:**
- Use `TestClient` from FastAPI
- Mock PydanticAI agent responses (controlled output)
- Verify `agent.run()` called with correct `message_history` parameter
- Assert response contains expected context references

**Coverage Goal:** 90%+ for endpoint handler code

---

### 3. Performance Tests

**Scope:** Verify zero database queries and conversion latency

**Test Files to Create:**
- `tests/performance/test_stateless_performance.py` (8 test functions, reduced from 14)

**Coverage Areas:**
- **Database Queries:** Ensure 0 queries to sessions/messages tables (3 tests)
- **Conversion Latency:** Measure conversion time for various history lengths (2 tests)
- **Concurrent Load:** Test multiple simultaneous conversations (2 tests)
- **Scaling:** Verify linear O(n) complexity (1 test)

**Key Test Cases:**
1. `test_zero_database_queries_small_conversation()` - AC-FEAT-008-NEW-201
   - Mock database connection
   - Count queries during 10-message conversion
   - Assert count == 0

2. `test_zero_database_queries_large_conversation()` - AC-FEAT-008-NEW-201
   - Verify zero queries even for 200-message conversation
   - Confirms stateless at scale

3. `test_database_not_imported()` - AC-FEAT-008-NEW-201
   - Verify session_db module not imported during conversion
   - Confirms true stateless (no DB dependency)

4. `test_conversion_latency_small()` - AC-FEAT-008-NEW-201
   - Test 10-message conversion <5ms
   - Average over 100 iterations

5. `test_conversion_latency_large()` - AC-FEAT-008-NEW-201
   - Test 200-message conversion <10ms (relaxed)
   - Verify reasonable performance at scale

6. `test_conversion_scales_linearly()` - AC-FEAT-008-NEW-201
   - Test 10, 50, 100, 200 message arrays
   - Assert O(n) complexity, not O(n²)

7. `test_concurrent_conversations()` - AC-FEAT-008-NEW-202, AC-FEAT-008-NEW-109
   - Simulate 10 concurrent conversions
   - Verify no cross-contamination
   - Assert independent state

8. `test_stateless_no_shared_state()` - AC-FEAT-008-NEW-202
   - Sequential calls with different data
   - Verify each call independent

**Removed Tests (Redundant):**
- ❌ `test_conversion_latency_medium()` - Merged into small/large
- ❌ `test_memory_usage_large_conversation()` - Not critical for simple conversion
- ❌ `test_no_memory_leaks()` - Over-engineered for 30-line function
- ❌ `test_benchmark_small_conversation()` - Redundant with latency tests
- ❌ `test_benchmark_medium_conversation()` - Redundant with latency tests
- ❌ `test_benchmark_large_conversation()` - Redundant with latency tests

**Tools:**
- `pytest-mock` for database query counting
- `time.perf_counter()` for latency measurements (no pytest-benchmark needed)
- `concurrent.futures` for concurrency tests

**Coverage Goal:** All performance requirements validated with focused test set

---

### 4. Manual Testing (End-to-End)

**Scope:** Real-world usage in OpenWebUI interface

**Test Files:**
- `docs/features/FEAT-008_advanced-memory/manual-test-v2.md` (separate document)

**Coverage Areas:**
- **User Experience:** Natural conversation flow in OpenWebUI
- **Visual Verification:** Responses make sense in UI context
- **Streaming Behavior:** Smooth streaming with context
- **Error States:** User-facing error messages

**Key Test Scenarios:**
1. Basic multi-turn conversation (3-4 turns)
2. Long conversation (10+ turns)
3. Context reference verification
4. New conversation (clean start)

**Duration:** ~30 minutes per test cycle

---

## Test Data & Fixtures

### Sample Message Arrays

**Fixture 1: Empty History (First Message)**
```python
@pytest.fixture
def first_message():
    return [
        {"role": "user", "content": "What is PPE?"}
    ]
```

**Fixture 2: Simple Follow-up**
```python
@pytest.fixture
def simple_conversation():
    return [
        {"role": "user", "content": "What is PPE?"},
        {"role": "assistant", "content": "PPE stands for Personal Protective Equipment..."},
        {"role": "user", "content": "What are the types?"}
    ]
```

**Fixture 3: Long Conversation**
```python
@pytest.fixture
def long_conversation():
    messages = []
    for i in range(10):
        messages.append({"role": "user", "content": f"Question {i}"})
        messages.append({"role": "assistant", "content": f"Answer {i}"})
    messages.append({"role": "user", "content": "Final question"})
    return messages
```

**Fixture 4: Malformed Messages**
```python
@pytest.fixture
def malformed_messages():
    return [
        {"role": "user"},  # Missing content
        {"content": "No role specified"},  # Missing role
        {"role": "unknown", "content": "Unknown role"},
        {"role": "user", "content": "Valid message"}
    ]
```

---

## Testing Tools & Framework

**Primary Framework:** `pytest` (existing project standard)

**Required Libraries:**
```python
# Already in requirements.txt
pytest>=7.0.0
pytest-asyncio  # For async endpoint tests
pytest-cov      # Coverage reporting
pytest-mock     # Mocking utilities

# Add for this feature
pytest-benchmark>=4.0.0  # Performance testing
```

**Test Execution:**
```bash
# Activate virtual environment
source venv_linux/bin/activate

# Run all FEAT-008 tests
python3 -m pytest tests/agent/test_message_conversion.py -v
python3 -m pytest tests/agent/test_stateless_api.py -v
python3 -m pytest tests/performance/test_stateless_performance.py -v

# Run with coverage
python3 -m pytest tests/agent/ --cov=app.agent --cov-report=html

# Run performance benchmarks
python3 -m pytest tests/performance/ --benchmark-only
```

---

## Test Environment Setup

**Prerequisites:**
1. Python 3.12+ virtual environment activated
2. All dependencies installed: `pip3 install -r requirements.txt`
3. Environment variables configured (`.env` file)
4. OpenWebUI instance running (for manual tests)

**Mock Strategy:**
- **Agent responses:** Mock `agent.run()` to return controlled output
- **Database:** Mock connection to verify zero queries
- **External APIs:** Mock Anthropic/PydanticAI calls (not under test)

**Test Database:**
- Not needed (stateless implementation)
- Use existing test fixtures for other features

---

## Coverage Goals & Metrics

**Overall Target:** 90%+ coverage for new/modified code

**Per-Component Targets:**
- Message conversion function: 100% (critical path)
- Endpoint handler: 95%
- Error handling: 100%
- Edge cases: 90%

**Coverage Exclusions:**
- Logging statements (informational only)
- Type checking guards (caught by mypy)
- Defensive assertions (should never trigger)

**Measurement:**
```bash
python3 -m pytest --cov=app.agent.chat_agent --cov-report=term-missing
```

**Acceptance Threshold:**
- All AC criteria pass
- Coverage ≥90%
- Zero regressions in existing tests

---

## Regression Testing

**Scope:** Ensure existing functionality unaffected

**Test Areas:**
1. **Single-message requests:** Still work without history
2. **Streaming:** Unmodified for backward compatibility
3. **Error handling:** Existing error paths unchanged
4. **RAG integration:** Document retrieval still functional

**Test Execution:**
```bash
# Run full existing test suite
python3 -m pytest tests/ -v

# Focus on agent tests
python3 -m pytest tests/agent/ -v --ignore=tests/agent/test_message_conversion.py
```

**Acceptance:** Zero existing test failures

---

## CI/CD Integration

**GitHub Actions Workflow:**
```yaml
name: FEAT-008 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest tests/agent/test_message_conversion.py -v
      - name: Run integration tests
        run: pytest tests/agent/test_stateless_api.py -v
      - name: Generate coverage
        run: pytest tests/agent/ --cov=app.agent --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**Quality Gates:**
- All tests pass
- Coverage ≥90%
- No critical security issues
- Code formatted with `black`

---

## Test Execution Timeline

**Phase 1: Unit Tests (2 hours)**
- Write 15+ unit tests
- Achieve 100% coverage on conversion function
- Validate edge cases

**Phase 2: Integration Tests (1.5 hours)**
- Write 5 integration tests
- Mock agent responses
- Test full request flow

**Phase 3: Performance Tests (1 hour)**
- Implement database query counter
- Run latency benchmarks
- Test concurrent load

**Phase 4: Manual Testing (0.5 hour)**
- Execute manual test scenarios in OpenWebUI
- Document results
- Screenshot conversation flows

**Total Testing Time:** ~5 hours

---

## Risk Mitigation

**Risk 1: Message format inconsistencies**
- Mitigation: Comprehensive unit tests with various formats
- Fallback: Graceful degradation to empty history

**Risk 2: Performance degradation on large histories**
- Mitigation: Benchmark tests with 50+ message arrays
- Fallback: Add message truncation if needed (document decision)

**Risk 3: Breaking existing streaming**
- Mitigation: Integration test specifically for streaming
- Rollback plan: Feature flag to disable history extraction

**Risk 4: Cross-conversation contamination**
- Mitigation: Concurrent load test with state verification
- Detection: Automated test catches shared state bugs

---

## Definition of Done (Testing)

Feature testing is complete when:
- ✅ All 25 acceptance criteria have passing tests (updated with AC-106 to AC-109)
- ✅ Unit test coverage ≥100% for conversion function
- ✅ Integration test coverage ≥90% for endpoint
- ✅ Performance tests validate <5ms conversion, 0 DB queries (8 focused tests)
- ✅ Manual testing completed (all 6 scenarios pass)
- ✅ Zero existing test regressions
- ✅ CI pipeline passes with quality gates
- ✅ Test documentation updated

---

## Test Maintenance

**Ongoing Requirements:**
- Update tests when message format changes
- Add tests for newly discovered edge cases
- Maintain test data fixtures as system evolves
- Review test coverage quarterly

**Documentation:**
- Keep test README updated with new test files
- Document any test dependencies or setup requirements
- Maintain test data examples in `tests/fixtures/`

---

## References

- **Acceptance Criteria:** `acceptance-v2.md` (21 criteria mapped to tests)
- **Manual Test Guide:** `manual-test-v2.md` (step-by-step scenarios)
- **Pytest Docs:** https://docs.pytest.org/
- **Coverage Tools:** https://pytest-cov.readthedocs.io/

---

**Document Status:** Ready for Test Implementation (Updated with 4 additional AC)
**Estimated Total Test Time:** 5 hours (write) + 1 hour (execute) = 6 hours
**Test File Count:** 3 automated + 1 manual guide
**Total Test Functions:** ~30 tests (13 unit + 5 integration + 8 performance + 4 new AC tests)
