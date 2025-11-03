# Product Requirements Document: True Token Streaming

**Feature ID:** FEAT-010
**Status:** Exploring
**Created:** 2025-10-31
**Last Updated:** 2025-10-31

## Problem Statement

The current API implementation uses simulated streaming that provides poor user experience. When users ask questions via CLI, they wait 2-3 seconds seeing nothing while `run_specialist_query()` blocks for the complete response. Only then does the system artificially chunk the output into 20-character pieces with fake delays (`asyncio.sleep(0.01)`), creating an unnatural "typing effect" that masks the real issue: users see no feedback during the actual LLM generation.

This affects EVI 360 workplace safety specialists who need responsive answers. The blocking wait creates perceived slowness and uncertainty about whether the system is working. True token-by-token streaming would show the first token within 500ms, dramatically improving perceived performance and user confidence.

## Goals & Success Criteria

### Primary Goals
- Deliver first token to user within 500ms (not 2-3s blocking wait)
- Stream tokens incrementally as LLM generates them (no artificial chunking)
- Eliminate text duplication issues that plagued previous implementation
- Maintain clean SSE connection stability throughout response generation
- Ensure Pydantic validation works correctly with partial responses

### Success Metrics
- Time-to-first-token: <500ms (vs current 2000-3000ms)
- Zero text duplication occurrences in streaming output
- SSE connection success rate: >99% (no mid-stream crashes)
- Validator warnings reduced: <2 per query (vs 20+ in failed attempts)
- All 6 existing tests pass without modification to test logic

## User Stories

### Story 1: Responsive Query Feedback
**As a** EVI 360 workplace safety specialist
**I want** to see the answer start appearing within 500ms of asking a question
**So that** I know the system is working and feel confident the response is coming

**Acceptance Criteria:**
- [ ] First token arrives within 500ms for 95% of queries
- [ ] Tokens stream smoothly without artificial delays
- [ ] No visible "waiting" period before text starts appearing
- [ ] CLI displays tokens incrementally as they arrive via SSE

### Story 2: Clean Text Display
**As a** user of the CLI interface
**I want** the streamed response to display cleanly without duplication
**So that** I can read the answer naturally without confusion

**Acceptance Criteria:**
- [ ] No text duplication (e.g., "UWV UWV UWV...")
- [ ] Each token appears exactly once
- [ ] Text flows naturally as if typing in real-time
- [ ] Citations appear correctly after text completes

### Story 3: Robust Streaming Connections
**As a** developer maintaining the system
**I want** streaming to handle partial responses without validation errors
**So that** connections remain stable and errors don't crash mid-response

**Acceptance Criteria:**
- [ ] Pydantic validation accepts partial JSON objects (`{}`, `{"content": ""}`)
- [ ] Validator only logs warnings for final responses (not partials)
- [ ] SSE connections complete successfully without httpcore.ReadError
- [ ] Error events sent cleanly via SSE if generation fails

### Story 4: Backward Compatibility
**As a** developer with existing tests
**I want** the new streaming implementation to work with existing test mocks
**So that** I don't have to rewrite all 6 tests that mock `specialist_agent.run()`

**Acceptance Criteria:**
- [ ] Tests mocking `specialist_agent.run()` continue to pass
- [ ] New streaming function (`run_specialist_query_stream()`) added alongside existing `run_specialist_query()`
- [ ] API endpoint switches to streaming without breaking existing session/message storage
- [ ] CLI SSE client continues to work with new streaming format

## Scope & Non-Goals

### In Scope
**Phase 1 - True Token Streaming (This Feature):**
- Update `agent/models.py` to make `SpecialistResponse` fields optional with defaults
- Update `agent/models.py` to make `Citation.source` optional with default "Unknown"
- Update `agent/specialist_agent.py` to add lenient output validator (detect partials vs finals)
- Create `agent/specialist_agent.py:run_specialist_query_stream()` function using `.stream()` method
- Implement delta tracking logic (calculate new text since last message)
- Update `agent/api.py` to replace simulated streaming (lines 444-449) with true streaming
- Create `tests/agent/test_streaming.py` with comprehensive unit tests (9+ tests)
- Update any existing tests if they fail due to model changes
- Reference `learnings.md` as implementation blueprint

### Out of Scope (For This Version)
**Phase 2 - Advanced Streaming (Future FEAT-011):**
- Tool call visibility ("Searching guidelines...")
- Progress indicators ("Found 10 chunks")
- Progressive citation streaming (showing citations as they're discovered)
- Agent reasoning display ("Thinking...")
- Reason: Phase 1 focuses on core streaming stability; Phase 2 adds observability enhancements

**Other Exclusions:**
- WebSocket-based streaming (SSE works well for this use case)
- Streaming for non-CLI clients (Web UI not yet built)
- Real-time typing indicators in multi-user scenarios
- Reason: Not required for current MVP; SSE sufficient for CLI

## Constraints & Assumptions

### Technical Constraints
- Agent has `output_type=SpecialistResponse` - must use `.stream()` not `.stream_text()`
- Pydantic AI 0.3.2 deprecated `.stream_text()` for structured outputs
- Cannot use `.stream_text()` - only works for plain text responses (no output_type)
- `.stream()` returns accumulated partial responses (not token deltas) - must calculate differences
- All Pydantic model fields must allow partial/empty values during streaming
- Output validators run on EVERY partial response (Pydantic AI behavior)
- Existing tests mock `specialist_agent.run()` and expect blocking behavior
- CLI already implements SSE client (no changes needed to client side)

### Business Constraints
- Must maintain backward compatibility with existing tests
- Cannot break current blocking API (`run_specialist_query()`) - add streaming variant alongside
- Must preserve session and message storage functionality
- Should reference learnings.md for proven implementation patterns

### Assumptions
- OpenAI sends partial JSON in this order: `{}` → `{"content": ""}` → `{"content": "A"}` → `{"content": "Arbo"}` → etc.
- LLM fills citation fields non-atomically: `title` first, then `source`, then `quote`
- Partial responses have content but no citations (citations come at end of stream)
- SSE is sufficient for CLI streaming (no need for WebSocket)
- First token latency primarily depends on LLM response time (search tool runs first, ~500ms)
- Users tolerate 500ms wait better than 2500ms wait (perceived performance)

## Open Questions

1. **Should we remove the old simulated streaming code immediately or keep it as fallback?**
   - Why it matters: Code cleanup vs safety net if streaming has issues
   - Who can answer: Engineering (low risk - streaming proven in learnings.md)
   - Recommendation: Remove immediately (simpler codebase, streaming is proven)

2. **Do we need metrics/logging for stream duration and token count?**
   - Why it matters: Observability for performance monitoring
   - Who can answer: Product / Engineering
   - Recommendation: Add basic logging (start/end, duration, active streams) as in learnings.md

3. **Should validator strictness be configurable (lenient during streaming, strict for final)?**
   - Why it matters: Debugging vs log cleanliness
   - Who can answer: Engineering
   - Recommendation: Hardcode lenient behavior (proven in learnings.md), add debug flag if needed later

## Related Context

### Existing Features
- **FEAT-003 Query & Retrieval**: Current blocking implementation uses `run_specialist_query()` with simulated streaming
- **Session Management**: API endpoint creates/retrieves sessions before streaming
- **SSE Client (CLI)**: `cli.py:142-218` already handles SSE events (no changes needed)
- **Citation Display**: CLI already formats citations nicely via "tools" events

### References
- **Historical Implementation**: `docs/features/FEAT-010_streaming/learnings.md` - Complete implementation journey from FEAT-003 (reverted)
- **Key Learnings**:
  - `.stream()` provides cumulative content (not deltas) - track `last_content_length`
  - All model fields need defaults for partial JSON validation
  - Output validators run on partials - must detect `is_partial = content > 0 and citations == 0`
  - Citation fields fill incrementally: `title` → `source` → `quote`
- **Current Simulated Streaming**: `agent/api.py:444-449` - Artificial 20-char chunks with delays
- **Current Models**: `agent/models.py:456-471` - `SpecialistResponse` and `Citation` (required fields)
- **Existing Tests**: `tests/agent/test_specialist_agent.py` - 6 tests mock `specialist_agent.run()`
- **Pydantic AI Docs**: https://docs.pydantic.ai/latest/streaming/ - Structured output streaming guide

### Implementation Blueprint
**Reference Architecture** (from learnings.md):
```
User Query
    ↓
API /chat/stream endpoint (agent/api.py)
    ↓
run_specialist_query_stream() [NEW FUNCTION]
    ↓
agent.run_stream() [Pydantic AI]
    ↓
async for message in result.stream():
    ↓
Delta tracking (last_content_length)
    ↓
Yield only NEW text tokens
    ↓
SSE format: data: {"type": "text", "content": "..."}
    ↓
CLI displays incrementally
```

**Key Design Decisions** (from learnings.md):
1. Use `.stream()` not `.stream_text()` - required for structured outputs
2. Track deltas manually - `.stream()` gives cumulative content
3. All fields need defaults - Pydantic validates partial JSON
4. Lenient validation during streaming - strict only on final
5. Accept incomplete data - better UX than failing mid-stream

---

**Next Steps:**
1. Researcher agent will investigate: Pydantic AI 0.3.2 streaming API changes (if any since learnings.md)
2. After research completes, proceed to planning with `/plan FEAT-010`
3. Implementation will follow learnings.md blueprint closely to avoid repeating past mistakes
