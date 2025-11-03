# Architecture Decision: True Token Streaming

**Feature:** FEAT-010: True Token Streaming
**Status:** Planning
**Decision Date:** 2025-10-31
**Deciders:** Development Team

## Context

The EVI 360 RAG system currently buffers entire LLM responses before displaying them to users, creating a poor user experience with long wait times (5-10 seconds). Users expect modern streaming behavior where tokens appear progressively as they're generated. The system uses Pydantic AI with Anthropic Claude models in a FastAPI backend serving a web UI.

**Key Constraints:**
- Must work with Pydantic AI framework (agent.run_stream())
- FastAPI backend with WebSocket or SSE transport
- React frontend (assumed based on research)
- Bilingual responses (Dutch/English)
- Citation markers must stream correctly without breaking

## Options Analysis

### Option 1: Server-Sent Events (SSE) with Pydantic AI StreamedRunResult

**Description:**
Implement SSE endpoint in FastAPI that yields chunks from Pydantic AI's `agent.run_stream()`. Use `EventSource` API in frontend to consume stream. Convert StreamedRunResult chunks to SSE format with proper event typing.

**Pros:**
- Built-in browser support (EventSource API)
- Simple HTTP-based protocol (no WebSocket complexity)
- Automatic reconnection handling
- Pydantic AI has native streaming support
- Easy to implement with FastAPI StreamingResponse

**Cons:**
- Unidirectional only (server → client)
- Cannot send follow-up messages mid-stream
- Some proxy/firewall issues in corporate environments
- Limited browser compatibility for older browsers

**Implementation Complexity:** Medium
**Estimated Effort:** 3-5 days

---

### Option 2: WebSockets with Pydantic AI StreamedRunResult

**Description:**
Establish WebSocket connection for bidirectional communication. Stream Pydantic AI chunks over WebSocket messages. Handle connection lifecycle, reconnection, and error states manually.

**Pros:**
- Bidirectional communication (enables follow-ups)
- Full-duplex streaming
- Better for future interactive features
- No HTTP overhead per message
- Works well with corporate proxies (uses HTTP upgrade)

**Cons:**
- More complex connection management
- Requires manual reconnection logic
- Higher initial implementation cost
- Potential scaling issues (connection pools)
- Requires WebSocket support on infrastructure

**Implementation Complexity:** High
**Estimated Effort:** 5-8 days

---

### Option 3: Polling with Chunked Responses

**Description:**
Store streaming output in Redis/memory cache. Client polls endpoint repeatedly to fetch accumulated chunks. Simple implementation but poor UX and resource usage.

**Pros:**
- Works everywhere (maximum compatibility)
- Simple to understand and debug
- No special browser APIs needed
- Easy to cache intermediate states

**Cons:**
- High latency (polling intervals)
- Inefficient resource usage
- Poor user experience (choppy streaming)
- Increased server load from polling
- Not true streaming (defeats purpose)

**Implementation Complexity:** Low
**Estimated Effort:** 2-3 days

## Comparison Matrix

| Criterion          | SSE (Option 1) | WebSockets (Option 2) | Polling (Option 3) |
|--------------------|----------------|----------------------|---------------------|
| **Feasibility**    | High           | High                 | High                |
| **Performance**    | Excellent      | Excellent            | Poor                |
| **Maintainability**| High           | Medium               | High                |
| **Cost**           | Low            | Medium               | High (server load)  |
| **Complexity**     | Low            | High                 | Low                 |
| **Community**      | Strong         | Strong               | Limited             |
| **Integration**    | Excellent      | Good                 | Fair                |

**Scoring:**
- Option 1 (SSE): 28/35 points
- Option 2 (WebSockets): 25/35 points
- Option 3 (Polling): 18/35 points

## Recommendation

**Selected Option:** Option 1 - Server-Sent Events (SSE) with Pydantic AI StreamedRunResult

**Rationale:**
1. **Best fit for use case:** Unidirectional streaming matches current requirement (no follow-ups mid-stream)
2. **Lowest complexity:** Simple HTTP-based protocol with browser-native support
3. **Pydantic AI alignment:** Framework has excellent SSE examples and documentation
4. **Time to value:** Fastest implementation path (3-5 days vs 5-8 for WebSockets)
5. **Future-proof:** Can migrate to WebSockets later if bidirectional becomes necessary

**Trade-offs Accepted:**
- No mid-stream follow-ups (acceptable for current workflow)
- Unidirectional limitation (can add WebSockets in future if needed)

**Migration Path:** If bidirectional communication becomes required, SSE implementation provides foundation for WebSocket upgrade with minimal frontend changes.

## Spike Plan

### Goal
Validate that SSE works end-to-end with Pydantic AI streaming, FastAPI, and React frontend for bilingual responses with citations.

### Steps

**Step 1: Backend SSE Endpoint (2 hours)**
- Create FastAPI route `/api/v1/stream/query` with StreamingResponse
- Integrate `specialist_agent.run_stream()` from existing agent
- Yield SSE-formatted chunks with proper `data:` prefix
- Test with curl to verify streaming output

**Step 2: Frontend EventSource Integration (2 hours)**
- Implement EventSource connection in React component
- Parse SSE messages and accumulate text
- Display streaming text in UI with cursor/animation
- Handle connection errors and stream completion

**Step 3: Citation Handling (2 hours)**
- Test citation markers `[1]` streaming correctly
- Verify citation panel updates in real-time
- Ensure no broken markers across chunk boundaries
- Test bilingual responses (Dutch and English)

**Step 4: Error & Edge Cases (2 hours)**
- Test network interruption mid-stream
- Verify timeout handling (30+ second responses)
- Test rapid consecutive queries
- Validate memory cleanup after stream completion

**Step 5: Performance & UX Validation (2 hours)**
- Measure time-to-first-token (target <500ms)
- Verify smooth streaming (no stuttering)
- Test with long responses (2000+ tokens)
- Gather user feedback on perceived responsiveness

**Success Criteria:**
- ✅ First token appears within 500ms
- ✅ Streaming remains smooth for 2000+ token responses
- ✅ Citations render correctly without breaking
- ✅ No memory leaks after 50 consecutive queries
- ✅ Bilingual responses stream correctly

**Timeline:** 2 days (10 hours total)

## Implementation Notes

**Key Libraries:**
- FastAPI StreamingResponse for backend
- Pydantic AI StreamedRunResult for LLM streaming
- EventSource API (browser native) for frontend
- No additional dependencies required

**Security Considerations:**
- Same authentication as existing endpoints (JWT/session)
- Rate limiting per user (prevent stream abuse)
- Timeout enforcement (kill streams after 60s)

**Monitoring:**
- Track time-to-first-token metrics
- Monitor active stream count
- Log stream completion/error rates
- Alert on streams exceeding 60s

## References

- Pydantic AI Streaming Documentation: https://ai.pydantic.dev/streaming/
- FastAPI StreamingResponse: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- MDN EventSource API: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- Research findings: `/docs/features/FEAT-010_streaming/research.md`

---

**Word Count:** 780 words
**Template Version:** 1.0.0
