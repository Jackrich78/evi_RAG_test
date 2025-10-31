# Testing Strategy: True Token Streaming

**Feature:** FEAT-010: True Token Streaming
**Status:** Planning
**Created:** 2025-10-31

## Overview

This document defines the comprehensive testing strategy for implementing token streaming in the EVI 360 RAG system. Testing covers unit, integration, and end-to-end levels with specific focus on streaming behavior, performance, and error handling.

## Test Levels

### Unit Tests

**Scope:** Individual functions and components in isolation

**Backend Unit Tests:**
- SSE message formatting functions
- Stream chunk processing logic
- Error handling utilities
- Authentication/authorization decorators for streaming endpoints

**Frontend Unit Tests:**
- EventSource connection wrapper
- Token accumulation logic
- Citation marker parsing during streaming
- Error state management

**Location:** `tests/unit/streaming/`

**Files to Create:**
1. `tests/unit/streaming/test_sse_formatting.py` - SSE message format validation
2. `tests/unit/streaming/test_stream_handlers.py` - Stream processing logic
3. `tests/unit/streaming/test_frontend_accumulator.test.ts` - Token accumulation (if TypeScript)

### Integration Tests

**Scope:** Component interactions and API contracts

**Backend Integration Tests:**
- FastAPI SSE endpoint with Pydantic AI agent
- StreamingResponse yields chunks correctly
- Citation markers preserved through streaming pipeline
- Authentication middleware integration
- Rate limiting enforcement

**Frontend Integration Tests:**
- EventSource connection to backend SSE endpoint
- Real-time UI updates from streamed tokens
- Citation panel synchronization with streaming text
- Error handling and reconnection logic

**Location:** `tests/integration/streaming/`

**Files to Create:**
1. `tests/integration/streaming/test_sse_endpoint.py` - FastAPI SSE endpoint integration
2. `tests/integration/streaming/test_pydantic_streaming.py` - Pydantic AI streaming integration
3. `tests/integration/streaming/test_frontend_integration.test.ts` - EventSource integration (if TypeScript)

### End-to-End Tests

**Scope:** Full user workflows from browser to LLM and back

**Critical Flows:**
1. User submits query → First token appears within 500ms → Full response streams smoothly
2. Response with citations → Citations render correctly → Citation panel updates in real-time
3. Network interruption mid-stream → Error displayed → User retries successfully
4. Long response (2000+ tokens) → Streams without stuttering → Completes successfully
5. Bilingual responses (Dutch and English) → Stream correctly with proper encoding

**Location:** `tests/e2e/streaming/`

**Files to Create:**
1. `tests/e2e/streaming/test_streaming_workflow.py` - Complete streaming user flows

## Coverage Goals

### Code Coverage Targets

- **Unit Tests:** 90% coverage of streaming module code
- **Integration Tests:** 80% coverage of API endpoints and frontend integration
- **E2E Tests:** 100% coverage of critical user workflows (5 flows listed above)

### Acceptance Criteria Coverage

All 23 acceptance criteria from `acceptance.md` must have corresponding automated or manual tests:
- **Automated:** 18 criteria (AC-001 through AC-018)
- **Manual:** 5 criteria (AC-019 through AC-023 - browser/device compatibility)

## Test Environment

### Backend Environment

**Dependencies:**
- pytest (existing framework)
- pytest-asyncio (async test support)
- httpx (async HTTP client for testing FastAPI)
- pytest-mock (mocking Pydantic AI responses)

**Test Data:**
- Mock LLM responses with varying lengths (100, 500, 2000 tokens)
- Sample queries in Dutch and English
- Citation-heavy responses (5+ citations)
- Edge cases: empty responses, special characters, long delays

### Frontend Environment

**Dependencies:**
- Jest (assumed based on React ecosystem)
- React Testing Library
- Mock Service Worker (MSW) for SSE mocking
- Playwright (for E2E tests)

**Test Data:**
- Mock SSE event streams
- Simulated network interruptions
- Timeout scenarios

## Performance Testing

### Load Testing Scenarios

**Scenario 1: Single User Streaming**
- Measure time-to-first-token across 100 requests
- Target: 95th percentile < 500ms
- Tool: pytest with timing assertions

**Scenario 2: Concurrent Streams**
- 10 simultaneous streaming requests
- Measure per-stream latency and throughput
- Tool: pytest with asyncio concurrent tasks

**Scenario 3: Long Response Streaming**
- Stream 2000+ token responses
- Monitor memory usage and stream stability
- Tool: pytest with memory profiling

**Location:** `tests/performance/streaming/`

**Files to Create:**
1. `tests/performance/streaming/test_streaming_performance.py` - Performance benchmarks

## Manual Testing Requirements

### Browser Compatibility Testing

**Browsers to Test:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Test Procedure:** See `manual-test.md` for step-by-step instructions

### Mobile Device Testing

**Devices to Test:**
- iOS Safari (iPhone)
- Android Chrome (Samsung/Pixel)

**Test Procedure:** See `manual-test.md` for mobile-specific scenarios

### Accessibility Testing

**Checks:**
- Screen reader announces streaming text progressively
- Keyboard navigation during streaming
- Focus management during stream completion

**Tool:** Manual testing with NVDA/JAWS/VoiceOver

## Test Data Management

### Mock Responses

Create reusable mock responses in `tests/fixtures/streaming/`:
- `short_response.txt` - 100 token response
- `medium_response.txt` - 500 token response
- `long_response.txt` - 2000 token response
- `citations_response.txt` - Response with 5+ citations
- `dutch_response.txt` - Dutch language response
- `english_response.txt` - English language response

### Test Utilities

Create helper functions in `tests/utils/streaming_helpers.py`:
- `mock_sse_stream()` - Generate mock SSE event stream
- `measure_first_token_time()` - Timing utility for performance tests
- `simulate_network_interruption()` - Simulate connection drops
- `validate_citation_rendering()` - Assert citation correctness

## Continuous Integration

### CI Pipeline Integration

**Pre-commit Hooks:**
- Run unit tests for modified streaming modules
- Lint streaming code (black, ruff)

**PR Checks:**
- Full unit test suite (streaming modules)
- Integration tests (streaming endpoints)
- Coverage report (must meet 90% target for new code)

**Main Branch Merge:**
- Full E2E test suite
- Performance benchmarks (report if regressions detected)

### Test Reporting

**Metrics to Track:**
- Test pass/fail rate
- Code coverage percentage
- Performance benchmark trends (time-to-first-token)
- Flaky test detection

## Test Stub Structure

All test stubs will include:
- Proper imports and fixtures
- Descriptive test function names following `test_<behavior>_<condition>_<expected_result>` pattern
- TODO comments referencing acceptance criteria IDs
- Basic test structure (arrange-act-assert pattern)
- No implementation code (stubs only)

Example:
```python
def test_sse_endpoint_streams_first_token_within_500ms():
    """
    Test that first token appears within 500ms of query submission.

    Acceptance Criteria: AC-FEAT-010-001, AC-FEAT-010-012
    """
    # TODO: Implement test
    # 1. Mock Pydantic AI agent with delayed response
    # 2. Submit query to SSE endpoint
    # 3. Measure time to first SSE event
    # 4. Assert latency < 500ms
    pass
```

---

**Template Version:** 1.0.0
**Word Count:** 780 words
