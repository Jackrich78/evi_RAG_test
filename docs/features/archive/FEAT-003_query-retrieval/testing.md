# Testing Strategy: FEAT-003 - Specialist Agent with Vector Search

**Feature ID:** FEAT-003
**Created:** 2025-10-29
**Test Coverage Goal:** 80%

## Test Strategy Overview

This feature uses Test-Driven Development (TDD) principles with test stubs created during planning (Phase 1) and implemented during build (Phase 2).

**Testing Philosophy:** Create comprehensive test stubs with clear AC references, then implement tests before writing production code (Red-Green-Refactor cycle).

**Testing Levels:**
- ✅ Unit Tests: Specialist agent, search tools
- ✅ Integration Tests: End-to-end flow
- ✅ Manual Tests: Dutch quality and UX validation

## Unit Tests

### Test Files to Create

#### `tests/agent/test_specialist_agent.py`

**Purpose:** Test specialist agent behavior, tool calls, and response formatting

**Test Stubs:**

1. **Test:** Basic agent query returns Dutch response (AC-FEAT-003-001, 002)
   - **Given:** Specialist agent initialized with test dependencies
   - **When:** Agent runs query "Wat zijn de vereisten voor werken op hoogte?"
   - **Then:** Returns SpecialistResponse with Dutch content
   - **Mocks:** mock_llm_model, mock_database_pool

2. **Test:** Agent provides minimum 2 citations (AC-FEAT-003-003, 005)
   - **Given:** Search results contain 5 relevant chunks
   - **When:** Agent synthesizes response
   - **Then:** Response.citations has ≥2 items with title + source
   - **Mocks:** mock_llm_model, mock_vector_search_results

3. **Test:** Search metadata is populated correctly
   - **Given:** Search tool returns 10 chunks
   - **When:** Agent completes query
   - **Then:** Response.search_metadata contains chunks_retrieved: 10
   - **Mocks:** mock_llm_model, mock_database_pool

4. **Test:** Convenience function run_specialist_query works
   - **Given:** Query string and session ID provided
   - **When:** run_specialist_query() called
   - **Then:** Returns SpecialistResponse without requiring manual deps setup
   - **Mocks:** mock_llm_model

5. **Test:** Responses contain no English (AC-FEAT-003-004)
   - **Given:** Agent processes Dutch query
   - **When:** Response generated
   - **Then:** content.lower() has no common English words (safety, requirements, height)
   - **Mocks:** mock_llm_model with Dutch response fixture

6. **Test:** Empty query handled gracefully (AC-FEAT-003-101)
   - **Given:** Query is empty string or whitespace
   - **When:** Agent processes query
   - **Then:** Returns helpful Dutch message without crashing
   - **Mocks:** mock_llm_model

---

#### `tests/agent/test_tools.py`

**Purpose:** Test search tools return correct results and handle errors

**Test Stubs:**

1. **Test:** Hybrid search returns relevant chunks (AC-FEAT-003-004)
   - **Given:** Query "werken op hoogte" submitted
   - **When:** hybrid_search_tool executes
   - **Then:** Returns ChunkResults with score >0.6
   - **Mocks:** mock_embedding_client, mock_database_pool

2. **Test:** Vector search tool works as fallback
   - **Given:** Query submitted
   - **When:** vector_search_tool executes
   - **Then:** Returns results from pure vector similarity
   - **Mocks:** mock_embedding_client, mock_database_pool

3. **Test:** Dutch full-text search applies stemming
   - **Given:** Query "werken" submitted
   - **When:** Hybrid search executes
   - **Then:** Matches chunks containing "werk", "werkt", "gewerkt"
   - **Mocks:** mock_database_pool with Dutch test data

4. **Test:** Search handles empty results gracefully (AC-FEAT-003-105)
   - **Given:** Query matches no chunks
   - **When:** hybrid_search_tool executes
   - **Then:** Returns empty list (not exception)
   - **Mocks:** mock_database_pool returning no rows

---

### Unit Test Coverage Goals

- **Functions:** All public functions in specialist_agent.py tested
- **Branches:** All conditional branches covered
- **Edge Cases:** Empty query, no results, invalid input
- **Error Handling:** Database errors, API errors, timeouts

**Target Coverage:** 80% line coverage for agent module

## Integration Tests

### Test Files to Create

#### `tests/integration/test_specialist_flow.py`

**Purpose:** Test end-to-end flow from query to response

**Test Stubs:**

1. **Test:** Complete flow CLI → API → Agent → Database (AC-FEAT-003-001 through 007)
   - **Components:** FastAPI endpoint, Specialist Agent, Database utils
   - **Setup:** Start API in test mode, seed database with test chunks
   - **Scenario:**
     1. POST /chat/stream with Dutch query
     2. Agent searches database
     3. Agent generates response
     4. Response streamed back via SSE
   - **Assertions:**
     - Response is Dutch
     - Contains ≥2 citations
     - Response time <5s (lenient for tests)
     - Status code 200

2. **Test:** Streaming response delivers tokens incrementally (AC-FEAT-003-304)
   - **Components:** FastAPI SSE, Pydantic AI run_stream
   - **Setup:** Mock agent streaming response
   - **Scenario:**
     1. Request /chat/stream
     2. Receive SSE events
     3. Verify tokens arrive before full response complete
   - **Assertions:**
     - First token received within 1s
     - Multiple data: events received
     - End marker received last

3. **Test:** Database connection error handled gracefully (AC-FEAT-003-103)
   - **Components:** API error handling, Agent error handling
   - **Setup:** Mock database connection failure
   - **Scenario:**
     1. Stop PostgreSQL container
     2. Submit query
     3. Verify graceful error response
   - **Assertions:**
     - No 500 error
     - Dutch error message returned
     - API logs error with troubleshooting hint

---

### Integration Test Scope

**Internal Integrations:**
- FastAPI → Specialist Agent: Endpoint calls agent.run_stream()
- Agent → Search Tools: Agent tool calls hybrid_search_tool
- Search Tools → Database: Tools query PostgreSQL via db_utils

**External Integrations:**
- OpenAI API: Mocked for integration tests (use fixtures)
- PostgreSQL: Real database in test mode (seed with test data)

**Mock Strategy:**
- **Fully Mocked:** OpenAI API (expensive, slow)
- **Real:** PostgreSQL (fast, local)
- **Partially Mocked:** Neo4j (not used in MVP, always mocked)

## Manual Testing

### Manual Test Scenarios

*See `manual-test.md` for detailed step-by-step instructions.*

**Quick Reference:**
1. Basic Safety Question: Verify Dutch response, citations, <3s
2. Employee Health Query: Verify ergonomics guidelines cited
3. Workplace Noise Query: Verify decibel limits mentioned
4. Employer Duty Query: Verify Arbowet cited
5. Edge Case - Empty Query: Verify graceful handling
6. Edge Case - Nonsense Query: Verify no hallucination
7. Edge Case - Database Down: Verify error message
8. Performance - 10 Sequential Queries: Verify consistent <3s
9. Dutch Quality - Native Speaker Review: Verify grammar
10. Citation Format - Visual Check: Verify title + source visible

**Manual Test Focus:**
- **Visual Verification:** CLI output formatting, colors, structure
- **User Experience:** Response relevance, citation clarity
- **Dutch Quality:** Grammar, terminology, naturalness
- **Performance:** Actual perceived speed

## Test Data Requirements

### Fixtures & Seed Data

**Unit Test Fixtures:**
Located in `tests/conftest.py` (reuse existing fixtures):
- `mock_database_pool`: Mocked asyncpg connection pool
- `mock_embedding_client`: Mocked OpenAI embedding calls
- `mock_llm_model`: Mocked LLM for agent responses
- `mock_pydantic_agent`: Mocked Pydantic AI agent
- `mock_vector_search_results`: Sample ChunkResults
- `sample_chunks`: Test chunks with Dutch content

**Integration Test Data:**
- **Database Seeding:** Load 10 test chunks with Dutch content
- **Guideline Titles:** Sample NVAB, STECR, UWV guidelines
- **Session Data:** Test session_id and user_id

**Manual Test Data:**
- **Test Queries:** 10 Dutch queries from PRD (page 464-485)
- **Expected Results:** Documented in manual-test.md

## Mocking Strategy

### What to Mock

**Always Mock:**
- OpenAI API (embeddings, LLM) - use mock_embedding_client, mock_llm_model
- Neo4j (not used in MVP, always mocked)
- External network calls

**Sometimes Mock:**
- PostgreSQL (mock for unit tests, real for integration tests)
- Pydantic AI Agent (mock for API tests, real for agent tests)

**Never Mock:**
- Specialist agent core logic (actual test target)
- Search tool logic (test actual implementation)
- Data validation (Pydantic models)

### Mocking Approach

**Framework:** pytest with pytest-asyncio

**Mock Examples:**
```python
# Use fixtures from conftest.py
def test_example(mock_llm_model, mock_database_pool):
    # Fixtures automatically mocked
    result = await specialist_agent.run(...)
    assert result.data.content
```

## Test Execution

### Running Tests Locally

**Unit Tests:**
```bash
# Activate venv
source venv/bin/activate

# Run unit tests
pytest tests/agent/test_specialist_agent.py -v
pytest tests/agent/test_tools.py -v

# Run with coverage
pytest tests/agent/ --cov=agent --cov-report=html
```

**Integration Tests:**
```bash
# Start database
docker-compose up -d postgres

# Run integration tests
pytest tests/integration/test_specialist_flow.py -v
```

**All Tests:**
```bash
pytest tests/ -v
```

### CI/CD Integration (Phase 2 - Future)

**Pipeline Stages:**
1. Unit tests (run on every commit)
2. Integration tests (run on every commit)
3. Manual test checklist (run before merge)
4. Coverage report (must be ≥80%)

**Failure Handling:**
- Failing tests block merge
- Coverage below 80% blocks merge

## Coverage Goals

### Coverage Targets

| Test Level | Target Coverage | Minimum Acceptable |
|------------|----------------|-------------------|
| Unit | 85% | 80% |
| Integration | N/A (flow-based) | 3 flows complete |
| Manual | N/A (human validation) | 10 scenarios pass |

### Critical Paths

**Must Have 100% Coverage:**
- specialist_agent.run() method
- search_guidelines tool
- Dutch language validation logic
- Error handling for DB/API failures

**Can Have Lower Coverage:**
- Logging statements
- Debug utilities
- Non-critical edge cases (e.g., timeout >60s)

## Test Stub Generation (Phase 1)

*These test files will be created with TODO stubs during planning:*

```
tests/
├── agent/
│   ├── test_specialist_agent.py (6 test stubs)
│   └── test_tools.py (4 test stubs)
└── integration/
    └── test_specialist_flow.py (3 test stubs)
```

**Total Test Stubs:** 13 test functions with TODO comments

**Stub Format:**
```python
@pytest.mark.asyncio
async def test_function_name():
    """TODO: AC-FEAT-003-XXX
    Description of what this test validates."""
    pass
```

## Out of Scope

*What we're explicitly NOT testing in this phase:*

- Tier-aware search (tier column is NULL for MVP)
- Product recommendations (products table empty)
- Session memory (stateless for MVP)
- Knowledge graph queries (Neo4j empty)
- Multi-agent coordination (single agent only)
- OpenWebUI integration (CLI only for MVP)
- Load testing (>10 concurrent users)
- Security penetration testing (local dev only)

---

**Next Steps:**
1. Planner will generate test stub files based on this strategy
2. Phase 2: Implementer will make stubs functional (TDD approach)
3. Phase 2: Manual testing guide will be followed for validation
