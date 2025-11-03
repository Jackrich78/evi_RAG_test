# Testing Strategy: OpenWebUI Integration

**Feature ID:** FEAT-007
**Created:** 2025-10-30
**Test Coverage Goal:** 80% for new OpenAI endpoints

## Test Strategy Overview

This feature uses a **moderate testing approach** (from research.md Topic 10) balancing thoroughness with speed. We focus on automated endpoint tests for API compatibility and manual testing via OpenWebUI for UX validation. No Playwright/Selenium automation in Phase 1 - manual testing ensures quality without over-engineering.

**Testing Levels:**
- ✅ Unit Tests: OpenAI endpoint validation (4 automated tests)
- ✅ Integration Tests: Full stack flow (specialist agent → database → response)
- ✅ Manual Tests: 10 Dutch queries via OpenWebUI UI
- ❌ E2E Tests: Not in scope for Phase 1 (overkill for MVP)

---

## Unit Tests

*Tests for individual API endpoints in isolation with mocked specialist agent.*

### Test Files to Create

#### `tests/agent/test_openai_api.py`

**Purpose:** Validate `/v1/chat/completions` and `/v1/models` endpoints match OpenAI specification

**Test Stubs:**

1. **Test: Non-Streaming Chat Completions** (AC-007-001)
   - **Given:** FastAPI TestClient and mocked specialist response
   - **When:** POST to `/v1/chat/completions` with `stream: false` and Dutch query
   - **Then:** Response matches OpenAI format (id, object, created, choices, usage fields)
   - **Mocks:** `run_specialist_query()` returns pre-defined Dutch response with citations

2. **Test: Streaming Chat Completions** (AC-007-002)
   - **Given:** FastAPI TestClient and mocked specialist response
   - **When:** POST to `/v1/chat/completions` with `stream: true`
   - **Then:** Response is SSE stream with `data:` prefix, delta chunks, and `data: [DONE]`
   - **Mocks:** `run_specialist_query()` returns chunked content

3. **Test: Model Listing** (AC-007-010)
   - **Given:** FastAPI TestClient
   - **When:** GET to `/v1/models`
   - **Then:** Response includes `evi-specialist` model with OpenAI-compatible structure
   - **Mocks:** None (reads from static config)

4. **Test: Error Handling** (AC-007-015)
   - **Given:** FastAPI TestClient
   - **When:** POST with empty messages array OR database error simulated
   - **Then:** Error response matches OpenAI error format with Dutch messages
   - **Mocks:** Database connection failure to trigger 500 error

5. **Test: Dutch Language Detection** (Optional)
   - **Given:** FastAPI TestClient
   - **When:** Query contains Dutch words
   - **Then:** `language: "nl"` passed to specialist agent
   - **Mocks:** Verify specialist agent called with correct language parameter

6. **Test: Citation Formatting** (Optional)
   - **Given:** Specialist returns citations in response
   - **When:** Response formatted for OpenAI
   - **Then:** Citations embedded in content or metadata with "📚 Bronnen:" section
   - **Mocks:** Specialist response with 2+ citations

---

### Unit Test Coverage Goals

- **Functions:** All new endpoint functions tested (`openai_chat_completions`, `list_models`)
- **Branches:** Both streaming and non-streaming code paths
- **Edge Cases:** Empty input, invalid model, missing messages
- **Error Handling:** Database errors, specialist agent failures, timeouts

**Target Coverage:** 80% line coverage for new OpenAI endpoints in `agent/api.py`

---

## Integration Tests

*Tests for full stack interactions with real database and specialist agent.*

### Test Files to Create

#### `tests/integration/test_openwebui_integration.py`

**Purpose:** Validate end-to-end flow from OpenWebUI request through specialist agent to database

**Test Stubs:**

1. **Test: Dutch Query Through Full Stack**
   - **Components:** API → specialist_agent → hybrid_search → PostgreSQL
   - **Setup:** Real PostgreSQL with test guideline data, real specialist agent (no mocks)
   - **Scenario:** Send Dutch query "Wat is valbeveiliging?" → verify Dutch response with citations
   - **Assertions:** Response in Dutch, ≥2 citations, relevant chunks retrieved from DB

2. **Test: Streaming with Real Specialist Agent**
   - **Components:** API → specialist_agent (streaming mode) → database
   - **Setup:** Real database, real agent
   - **Scenario:** POST with `stream: true` → collect all SSE chunks → verify complete response
   - **Assertions:** Stream format correct, citations appear, content is Dutch

3. **Test: Conversation Context Maintenance** (If history implemented)
   - **Components:** API → OpenWebUI history → specialist agent
   - **Setup:** Mock OpenWebUI sending multi-turn conversation
   - **Scenario:** Send query 1, then query 2 referencing query 1 context
   - **Assertions:** Agent uses full message history, context maintained

---

### Integration Test Scope

**Internal Integrations:**
- API endpoint → specialist_agent.run_specialist_query(): Validates correct parameter passing
- specialist_agent → tools.hybrid_search_tool(): Validates search execution
- hybrid_search_tool → db_utils: Validates database queries with Dutch text

**External Integrations:**
- PostgreSQL: Real queries with Dutch full-text search and pgvector
- OpenAI/LLM: Real API calls (use test API key with quota limits)

**Mock Strategy:**
- **Fully Mocked:** None for integration tests (defeats purpose)
- **Partially Mocked:** LLM calls can use smaller/cheaper model for tests
- **Real:** Database, specialist agent, search tools (authentic integration)

---

## E2E Tests (Not Applicable)

*Phase 1 does not include automated E2E tests. Manual testing via OpenWebUI UI replaces this.*

**Rationale:** Research.md Topic 10 recommends "moderate testing" - manual testing is faster and more appropriate for MVP validation than Playwright automation (which would add 1-2 days).

---

## Manual Testing

*Tests requiring human verification through OpenWebUI web interface.*

### Manual Test Scenarios

**See `manual-test.md` for detailed step-by-step instructions.**

**Quick Reference:**
1. **Access OpenWebUI Interface** - Verify UI loads at localhost:3000
2. **Basic Dutch Guideline Query** - Test streaming, citations, Dutch response
3. **Multi-Turn Conversation** - Verify context maintained across turns
4. **Citation Rendering** - Verify "📚 Bronnen:" section with blockquotes
5. **10 Dutch Test Queries** - Validate response quality across diverse topics

**Manual Test Focus:**
- **Visual Verification:** Citation formatting (blockquotes, emoji), markdown rendering
- **User Experience:** Streaming smoothness, response clarity, error messages
- **Language Quality:** Dutch grammar, no English contamination, proper terminology
- **Cross-browser:** Chrome and Firefox on desktop

---

## Test Data Requirements

### Fixtures & Seed Data

**Unit Test Fixtures:**
```python
# Mock specialist response fixture
@pytest.fixture
def mock_specialist_response():
    return {
        "content": "Bij werken op hoogte moet u valbescherming gebruiken...",
        "citations": [
            {"title": "NVAB Richtlijn: Werken op Hoogte", "source": "NVAB", "quote": "..."},
            {"title": "STECR Veiligheidsnormen", "source": "STECR", "quote": "..."}
        ],
        "search_metadata": {"chunks_retrieved": 5}
    }
```

**Integration Test Data:**
- PostgreSQL test database with 3-5 Dutch guideline documents
- Topics: Werken op hoogte, PSA, Brandveiligheid (minimum)
- Embeddings pre-generated for test documents

**Manual Test Data:**
- 10 Dutch test queries (from research.md Topic 10)
- Expected response templates for comparison

---

## Mocking Strategy

### What to Mock

**Always Mock (Unit Tests):**
- `run_specialist_query()` function - Returns pre-defined response
- Database calls - Use in-memory mock or fixture data
- LLM API calls - Mock to avoid costs and ensure deterministic tests

**Sometimes Mock:**
- LLM calls in integration tests - Use cheaper model (gpt-3.5-turbo vs gpt-4)

**Never Mock (Integration Tests):**
- Database queries (use real PostgreSQL test DB)
- Specialist agent logic
- Hybrid search functionality

### Mocking Approach

**Framework:** pytest with `unittest.mock` or `pytest-mock`

**Mock Examples:**
```python
from unittest.mock import patch, AsyncMock

@patch('agent.specialist_agent.run_specialist_query')
async def test_openai_endpoint(mock_query, client):
    mock_query.return_value = AsyncMock(
        content="Dutch response text",
        citations=[...]
    )
    response = client.post("/v1/chat/completions", json={...})
    assert response.status_code == 200
```

---

## Test Execution

### Running Tests Locally

**Unit Tests:**
```bash
# Activate virtual environment
source venv_linux/bin/activate

# Run unit tests only
python3 -m pytest tests/agent/test_openai_api.py -v

# Run with coverage
python3 -m pytest tests/agent/test_openai_api.py --cov=agent.api --cov-report=term-missing
```

**Integration Tests:**
```bash
# Ensure Docker containers running
docker-compose up -d postgres

# Run integration tests
python3 -m pytest tests/integration/test_openwebui_integration.py -v -s
```

**Manual Tests:**
```bash
# Start all services
docker-compose up -d

# Access OpenWebUI at http://localhost:3000
# Follow manual-test.md for step-by-step validation
```

### CI/CD Integration (Phase 2 - Future)

**Pipeline Stages:**
1. Unit tests (run on every commit) - Must pass before merge
2. Integration tests (run on every commit) - Must pass before merge
3. Manual test checklist (run before release) - Human validation required
4. Coverage report generation - Enforce 80% minimum for new code

**Failure Handling:**
- Failing unit tests block merge automatically
- Failing integration tests block merge
- Manual tests documented in test report, blocking if critical failures

---

## Coverage Goals

### Coverage Targets

| Test Level | Target Coverage | Minimum Acceptable |
|------------|----------------|-------------------|
| Unit | 85% | 80% |
| Integration | 70% | 60% |
| Manual | N/A (workflow-based) | 8/10 queries pass |

### Critical Paths

**Must Have 100% Coverage:**
- Error handling for database failures
- OpenAI format validation (request/response structure)
- Citation extraction and formatting logic

**Can Have Lower Coverage:**
- Logging statements
- Configuration loading
- Non-critical metadata fields

---

## Performance Testing

*From AC-007-018: Response time requirements*

### Performance Benchmarks

**Requirement:** Tier 1 responses <2 seconds (P95)

**Test Approach:**
- **Tool:** Manual timing during manual tests (Phase 1), automated load testing (Phase 2)
- **Scenarios:**
  1. Single query: Response time <2 seconds
  2. 10 concurrent queries: All complete within 3 seconds (P95)

**Acceptance:**
- 2 seconds response time for tier 1 guideline queries
- 3 seconds P95 under concurrent load (10 users)

**Note:** Full load testing deferred to Phase 2. Manual tests will measure single-query performance only.

---

## Security Testing

*From AC-007-007 through AC-007-009: Authentication requirements*

### Security Test Scenarios

1. **Authentication Check:** Verify login required before accessing chat (manual test)
2. **Session Isolation:** Verify multi-user sessions don't leak data (integration test)
3. **Input Validation:** Verify no SQL injection via query input (unit test)
4. **Error Message Safety:** Verify errors don't expose sensitive info (unit test)

**Tools:**
- Manual testing for auth flow
- Integration tests for session isolation
- Unit tests for input sanitization

---

## Test Stub Generation (Phase 1)

*Test files created with TODO stubs during planning phase:*

```
tests/
├── agent/
│   └── test_openai_api.py (4 primary test stubs + 2 optional)
└── integration/
    └── test_openwebui_integration.py (3 integration test stubs)
```

**Total Test Stubs:** 9 test functions with TODO comments

**Stub Format:**
```python
def test_function_name(client, fixtures):
    """
    Test description.

    Validates: AC-007-XXX

    TODO: Implement test logic
    - Step 1
    - Step 2
    - Step 3
    """
    pass
```

---

## Out of Scope

*What we're explicitly NOT testing in Phase 1:*

- **Automated E2E tests** - Manual testing sufficient for MVP
- **Load testing** - Deferred to Phase 2 (performance monitoring)
- **Multi-browser automation** - Manual cross-browser checks only
- **Accessibility automation** - Manual WCAG checks (keyboard nav, contrast)
- **Product recommendations** - Feature not in FEAT-007 scope

---

**Next Steps:**
1. Planner generates test stub files (complete)
2. Phase 2: Implementer makes stubs functional
3. Phase 2: Execute tests and validate AC compliance
