# Testing Strategy: FEAT-007 OpenWebUI Integration

**Feature ID:** FEAT-007
**Feature Name:** OpenWebUI Integration
**Last Updated:** 2025-10-30
**Status:** Planning Complete

---

## Overview

This document defines the comprehensive testing strategy for integrating OpenWebUI as the frontend chat interface for the EVI 360 RAG system. Testing focuses on OpenAI API compatibility, Dutch language support, streaming responses, citation rendering, and conversation management.

---

## Test Levels

### 1. Unit Tests

**Scope:** Individual API endpoint functions and response formatting logic.

**Test Files:**
- `tests/agent/test_openai_api.py` - OpenAI-compatible API endpoints

**Key Test Cases:**
1. **Non-streaming chat completions** - Validate JSON response format matches OpenAI spec
2. **Streaming chat completions** - Validate SSE format with `data:` prefix and `[DONE]` marker
3. **Model listing endpoint** - Validate `/v1/models` returns EVI specialist model
4. **Error handling** - Validate 400/500 error responses match OpenAI format

**Coverage Goal:** 85% line coverage for new OpenAI API endpoints

**Dependencies:**
- FastAPI TestClient for HTTP testing
- pytest fixtures for mock guideline data
- No external API calls (mock `run_specialist_query()`)

---

### 2. Integration Tests

**Scope:** End-to-end flow from OpenWebUI request to RAG response with real components.

**Test Files:**
- `tests/integration/test_openwebui_flow.py` - Full request/response cycle

**Key Test Cases:**
1. **Dutch query through OpenAI endpoint** - Verify language detection and Dutch response
2. **Citation extraction and formatting** - Verify citations parsed from specialist response
3. **Conversation history integration** - Verify multi-turn conversations maintain context
4. **Streaming with citations** - Verify citations appear after content in stream

**Coverage Goal:** 70% integration coverage (moderate approach per research.md)

**Dependencies:**
- Running PostgreSQL with test guidelines data
- pgvector with embedded test documents
- Redis for session management (if implemented)

---

### 3. Manual Testing

**Scope:** Human validation of UX, Dutch language quality, and visual citation rendering in OpenWebUI interface.

**Test Files:**
- `docs/features/FEAT-007_openwebui-integration/manual-test.md` - Step-by-step guide

**Key Scenarios:**
1. Access OpenWebUI at localhost:3000
2. Ask 10 Dutch workplace safety questions
3. Verify streaming responses appear smoothly
4. Verify citation rendering in "📚 Bronnen" section
5. Verify conversation history persistence
6. Test error scenarios (empty query, system overload)

**Acceptance Criteria:**
- All 10 Dutch queries return relevant guidelines
- Citations render with document titles and links
- Response time <2 seconds for tier 1 summaries
- No UI errors or broken layouts

---

### 4. End-to-End (E2E) Tests

**Scope:** Not required for Phase 1 (moderate testing approach). E2E tests with Playwright or Selenium deferred to Phase 2.

**Rationale:** Manual testing covers UX validation sufficiently for MVP. Automated E2E adds complexity without proportional value at this stage.

---

## Test Data Requirements

### Guideline Test Data

**Required Test Documents:**
- 3 Dutch guideline documents (tier 1, 2, 3 structure)
- Topics: Werken op hoogte, Persoonlijke beschermingsmiddelen, Brandveiligheid
- Embedded in pgvector test database

**Format:**
```sql
INSERT INTO evi_guidelines (title, content, tier, language, embedding)
VALUES
  ('Werken op hoogte', 'Samenvatting: Gebruik altijd valbescherming...', 1, 'nl', [0.1, 0.2, ...]),
  ('PSA Richtlijnen', 'Belangrijkste feiten: Helm, handschoenen...', 2, 'nl', [0.3, 0.4, ...]);
```

### Mock Responses

**Specialist Agent Mock:**
```python
def mock_specialist_response():
    return {
        "response": "Bij werken op hoogte moet u altijd valbescherming gebruiken...",
        "citations": [
            {"title": "Werken op hoogte richtlijn", "doc_id": "DOC-001", "tier": 1}
        ],
        "language": "nl"
    }
```

---

## Test Environment Setup

### Prerequisites

1. **Docker containers running:**
   - PostgreSQL (port 5432)
   - pgvector extension enabled
   - Redis (port 6379) - optional for Phase 1
   - OpenWebUI (port 3000)
   - EVI API (port 8058)

2. **Test database initialized:**
   - Schema: `sql/schema.sql`
   - EVI additions: `sql/evi_schema_additions.sql`
   - Test data: 3 Dutch guidelines embedded

3. **Environment variables:**
   - `DATABASE_URL` pointing to test database
   - `OPENAI_API_KEY` (for embeddings, can be mock in tests)
   - `API_PORT=8058`

### Test Execution Commands

```bash
# Activate virtual environment
source venv_linux/bin/activate

# Run unit tests only
python3 -m pytest tests/agent/test_openai_api.py -v

# Run integration tests
python3 -m pytest tests/integration/test_openwebui_flow.py -v

# Run all tests with coverage
python3 -m pytest --cov=agent --cov-report=html

# Manual testing - start services
docker-compose up -d
python3 -m uvicorn agent.api:app --port 8058 --reload
# Then follow manual-test.md steps
```

---

## Test Stub Generation

The following test stubs will be created in **`tests/agent/test_openai_api.py`**:

### Test Stub 1: Non-Streaming Chat Completions
```python
def test_openai_chat_completions_non_streaming():
    """
    Test /v1/chat/completions endpoint with stream=false.

    Validates:
    - AC-007-001: Basic guideline query returns tier 1 summary
    - Response format matches OpenAI Chat Completion object
    - Dutch language response
    - Citations included in response

    TODO: Implement test logic
    """
    pass
```

### Test Stub 2: Streaming Chat Completions
```python
def test_openai_chat_completions_streaming():
    """
    Test /v1/chat/completions endpoint with stream=true.

    Validates:
    - AC-007-002: Streaming response uses SSE format
    - Each chunk has 'data: ' prefix
    - Stream ends with 'data: [DONE]'
    - Citations streamed after content

    TODO: Implement test logic
    """
    pass
```

### Test Stub 3: Model Listing
```python
def test_list_models():
    """
    Test /v1/models endpoint returns EVI specialist model.

    Validates:
    - AC-007-010: Model list includes 'evi-specialist-v1'
    - Response format matches OpenAI Models list
    - Model metadata includes capabilities

    TODO: Implement test logic
    """
    pass
```

### Test Stub 4: Error Handling
```python
def test_error_handling():
    """
    Test error responses match OpenAI format.

    Validates:
    - AC-007-015: Empty queries return 400 error
    - AC-007-016: System errors return 500 error
    - Error format matches OpenAI error object
    - Error messages in Dutch

    TODO: Implement test logic
    """
    pass
```

---

## Coverage Goals

| Test Level | Coverage Target | Rationale |
|------------|----------------|-----------|
| Unit Tests | 85% | High coverage for API endpoints (critical for compatibility) |
| Integration Tests | 70% | Moderate coverage for full flow (per research decision) |
| Manual Tests | 100% | All 10 Dutch queries must be validated by human |
| E2E Tests | 0% (Phase 1) | Deferred to Phase 2 (MVP uses manual testing) |

**Overall Strategy:** Moderate testing approach balancing speed and reliability. Focus on critical path (Dutch queries → citations) with manual validation of UX.

---

## Success Criteria

Testing is complete when:
- ✅ All 4 unit test stubs implemented and passing
- ✅ Integration tests validate full OpenWebUI → EVI API → RAG flow
- ✅ Manual testing guide executed with 10 Dutch queries
- ✅ Coverage reports show ≥85% for OpenAI endpoints
- ✅ No blocking bugs in manual test scenarios
- ✅ Citation rendering validated in OpenWebUI interface

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| OpenAI API spec changes | High | Pin OpenWebUI version, monitor API changelog |
| Streaming format incompatibility | High | Test with real OpenWebUI client, not just unit tests |
| Dutch language quality issues | Medium | Include manual review by native speaker in AC |
| Citation rendering breaks | Medium | Manual test scenario specifically validates citations |
| Test data embedding failures | Low | Use fixed test embeddings, not live OpenAI calls |

---

## Next Steps (Phase 2)

1. Implement test stubs with actual test logic
2. Set up CI pipeline to run tests on every commit
3. Add E2E tests with Playwright if manual testing becomes bottleneck
4. Performance testing for concurrent users (load testing with Locust)
5. Security testing for API key validation and rate limiting

---

**Template Version:** 1.0.0
**Word Count:** 792 words
**Status:** Ready for Reviewer validation
