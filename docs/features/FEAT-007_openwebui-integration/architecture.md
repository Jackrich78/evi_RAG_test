# Architecture Decision: OpenWebUI Integration

**Feature ID:** FEAT-007
**Decision Date:** 2025-10-30
**Status:** Proposed
**Decider:** Planner Agent

## Context

EVI 360 RAG system currently provides API endpoints for retrieving workplace safety guidelines and product recommendations. To improve accessibility for safety specialists, we need a chat interface that allows natural language queries instead of direct API calls. OpenWebUI provides a proven platform for building custom AI assistants with RAG capabilities.

**Key Requirements:**
- Natural language query interface for Dutch-language safety guidelines
- Real-time access to 3-tier guideline system (Summary/Key Facts/Details)
- Product catalog integration with compliance tags
- Multi-turn conversation support with context retention
- Secure authentication and session management
- Deployment alongside existing FastAPI backend

**Constraints:**
- Must integrate with existing PostgreSQL database (Neon)
- Must support Docker deployment (production and development)
- Must handle Dutch language queries effectively
- API response time <2 seconds for guideline retrieval
- Support for multiple concurrent users (10+ simultaneous sessions)

---

## Important: What is OpenWebUI?

**OpenWebUI** is a **third-party open-source web application** (similar to ChatGPT's interface) that provides a production-ready chat UI for LLMs. It is:

- **A separate application** - Runs as its own Docker container
- **Not part of this project yet** - Will be added to `docker-compose.yml` during FEAT-007 implementation
- **OpenAI-compatible** - Expects API endpoints in OpenAI's chat completions format (`/v1/chat/completions`)
- **Feature-rich** - Handles conversation history, user management, markdown rendering, model selection

**Why Add OpenWebUI?**
- ✅ Production-ready chat interface without building from scratch
- ✅ Built-in features: conversation history, user management, markdown rendering
- ✅ Supports Dutch language naturally (via LLM, no special configuration)
- ✅ Actively maintained open-source project with large community
- ✅ Easy deployment via Docker

**Why Not Build Custom UI?**
- Would take 7-10 days vs 2-3 days for OpenWebUI integration
- Would require ongoing UI maintenance and frontend expertise
- OpenWebUI already solves all UI/UX needs for chat interfaces

**Current State:** OpenWebUI is **NOT installed** in this project. It will be added as a new Docker service during implementation.

**Existing Components:**
- ✅ CLI tool ([cli.py](../../../cli.py)) - Uses `/chat/stream` endpoint, works perfectly
- ✅ Specialist Agent ([specialist_agent.py](../../../agent/specialist_agent.py)) - `run_specialist_query()` function
- ✅ FastAPI backend ([api.py](../../../agent/api.py)) - Running on port 8058

## Options Considered

### Option 1: OpenWebUI Standalone with API Integration

**Description:**
Deploy OpenWebUI as a separate Docker container that connects to our FastAPI backend via HTTP REST API. OpenWebUI handles UI, conversation management, and LLM orchestration while delegating all guideline/product retrieval to existing endpoints.

**Development Environment:**
- ⚠️ **Mac/Windows with Docker Desktop required** for standard configuration
- Uses `host.docker.internal` for container-to-host communication
- Linux users must modify Docker networking (use `172.17.0.1` or `network_mode: host`)

**Architecture:**
```
User (Browser)
    ↓
OpenWebUI Container (port 3000) ← NEW SERVICE (not in project yet)
    ↓ HTTP POST /v1/chat/completions ← NEW ENDPOINT (OpenAI format)
FastAPI Backend (port 8058) [Mac/Windows: host.docker.internal:8058]
    ├─ /v1/chat/completions (NEW - for OpenWebUI only)
    ├─ /chat/stream (EXISTING - CLI keeps using this)
    └─ Both call → run_specialist_query() ← SHARED LOGIC
                            ↓
                    PostgreSQL + pgvector
```

**Key Point:** Both endpoints (`/chat/stream` and `/v1/chat/completions`) call the same `run_specialist_query()` function from [specialist_agent.py](../../../agent/specialist_agent.py). The new endpoint is just a format adapter to translate between OpenAI's API format and our internal specialist agent.

**Implementation Steps:**
1. Deploy OpenWebUI container with custom configuration
2. Create custom RAG pipeline that calls FastAPI endpoints
3. Configure OpenAI/Claude models via API keys
4. Implement authentication passthrough or shared session store
5. Add Docker Compose orchestration for both services

**Pros:**
- Clean separation of concerns (UI vs. backend logic)
- Minimal changes to existing FastAPI codebase
- Easy to swap UI layer if needed
- OpenWebUI handles conversation state management
- Built-in features: user management, chat history, model switching

**Cons:**
- Additional network latency (OpenWebUI → FastAPI → DB)
- Need to maintain two separate services
- Authentication complexity (coordinate between services)
- Potential for API versioning conflicts
- Higher resource consumption (two containers)

**Cost/Effort:**
- Development: 3-4 days
- Maintenance: Medium (two codebases to monitor)
- Infrastructure: Medium (additional container resources)

---

### Option 2: OpenWebUI Embedded with Direct Database Access

**Description:**
Integrate OpenWebUI as an embedded module within the FastAPI application, allowing it to directly access the PostgreSQL database for guideline retrieval. Replace REST API calls with direct database queries.

**Architecture:**
```
User → FastAPI + OpenWebUI (port 8000) → PostgreSQL
                ↓
            OpenAI/Anthropic API
```

**Implementation Steps:**
1. Install OpenWebUI as Python package dependency
2. Mount OpenWebUI routes within FastAPI application
3. Create custom RAG functions that query PostgreSQL directly
4. Share SQLAlchemy session/connection pool
5. Unify authentication using FastAPI middleware

**Pros:**
- Single deployment unit (simplified DevOps)
- Reduced latency (no HTTP overhead between services)
- Shared authentication and session management
- Easier to maintain consistent data models
- Lower resource consumption

**Cons:**
- Tight coupling between UI and backend
- Complex integration (OpenWebUI not designed for embedding)
- Harder to scale UI and API independently
- Risk of dependency conflicts (OpenWebUI may require different versions)
- Limited by OpenWebUI's architecture assumptions

**Cost/Effort:**
- Development: 5-6 days (integration complexity)
- Maintenance: High (tightly coupled systems)
- Infrastructure: Low (single container)

---

### Option 3: Custom Lightweight Chat UI with FastAPI Backend

**Description:**
Build a minimal custom chat interface (React/Vue + WebSocket) that connects to our existing FastAPI backend. Implement conversation management and LLM orchestration using Pydantic AI within FastAPI.

**Architecture:**
```
User → Custom UI (port 3000) → FastAPI + Pydantic AI (port 8000) → PostgreSQL
                                        ↓
                                OpenAI/Anthropic API
```

**Implementation Steps:**
1. Create simple chat UI with React/Vite
2. Add WebSocket endpoint to FastAPI for real-time chat
3. Implement conversation context management using Pydantic AI
4. Build RAG pipeline using existing database models
5. Add chat history storage to PostgreSQL

**Pros:**
- Full control over UI/UX and features
- Optimized for EVI 360's specific workflows
- Clean separation with defined API contracts
- Leverage existing FastAPI expertise
- No third-party UI dependencies to maintain

**Cons:**
- Significant development effort (build everything from scratch)
- Missing OpenWebUI features: prompt library, model switching, user management
- Ongoing UI maintenance burden
- Need frontend expertise for React/Vue development
- Longer time to production

**Cost/Effort:**
- Development: 7-10 days
- Maintenance: High (custom UI code)
- Infrastructure: Medium (two containers)

## Comparison Matrix

| Criteria | Option 1: Standalone OpenWebUI | Option 2: Embedded OpenWebUI | Option 3: Custom UI |
|----------|-------------------------------|------------------------------|---------------------|
| **Feasibility** | High - proven integration pattern | Medium - non-standard use of OpenWebUI | High - standard web app pattern |
| **Performance** | Medium - extra network hop (50-100ms) | High - direct DB access | High - optimized for use case |
| **Maintainability** | High - clear boundaries, standard deployment | Low - tight coupling, complex dependencies | Medium - full control but more code |
| **Cost** | Low - use existing tools | Low - single deployment | Medium - frontend development time |
| **Complexity** | Low - minimal custom code | High - deep integration work | Medium - standard stack |
| **Community Support** | High - active OpenWebUI community | Low - unusual integration approach | Medium - standard React/FastAPI |
| **Integration Ease** | High - RESTful APIs well-documented | Medium - requires OpenWebUI internals knowledge | High - full control over integration |

**Scoring:**
- Option 1: 6/7 criteria rated Medium-High → **Score: 85%**
- Option 2: 4/7 criteria rated Low-Medium → **Score: 55%**
- Option 3: 5/7 criteria rated Medium-High → **Score: 70%**

## Decision

**Recommended Approach:** **Option 1 - OpenWebUI Standalone with API Integration**

**Rationale:**

1. **Fastest Time to Value:** OpenWebUI provides production-ready chat UI, authentication, and conversation management out of the box. This allows focus on RAG pipeline optimization rather than UI development.

2. **Proven Architecture:** Microservices pattern with UI and API separation is well-established and aligns with modern deployment practices. Clear boundaries make debugging and scaling easier.

3. **Low Risk:** Minimal changes to existing FastAPI backend reduce risk of regression. If OpenWebUI doesn't meet needs, easy to swap with custom UI later.

4. **Feature-Rich:** OpenWebUI includes features that would take weeks to build: model switching, prompt templates, chat history, user management, document upload UI.

5. **Dutch Language Support:** OpenWebUI works with any LLM that supports Dutch (Claude, GPT-4) without language-specific modifications.

**Trade-offs Accepted:**
- Additional network latency (50-100ms) is acceptable for chat use case
- Resource overhead of second container is minimal with modern Docker deployment
- Authentication complexity manageable with shared JWT tokens or session store

**Risk Mitigation:**
- Start with shared Redis session store for authentication
- Implement API response caching to reduce latency
- Monitor performance and optimize API calls if needed
- Document API contracts clearly for future UI alternatives

---

## Session Management & Conversation History

**Decision:** **Stateless API - Last Message Only**

**How It Works:**
- OpenWebUI stores ALL conversation history in its internal SQLite database
- Each API request includes full `messages[]` array from OpenWebUI
- **Your API extracts ONLY the last user message**: `request.messages[-1].content`
- API generates new session_id per request (stateless operation)
- No conversation history stored in PostgreSQL

**Rationale:**
- ✅ Simplest implementation (2-3 hours vs 1-2 days for full history management)
- ✅ No database schema changes needed
- ✅ OpenWebUI already handles conversation UI perfectly
- ✅ Avoids dual conversation storage (SQLite + PostgreSQL)

**Code Example:**
```python
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    # Extract ONLY last user message (stateless)
    user_message = request.messages[-1].content

    # Generate new session ID (not persistent)
    session_id = str(uuid.uuid4())

    # Call specialist agent with single message
    response = await run_specialist_query(user_message, session_id)

    return format_openai_response(response)
```

**Trade-offs:**
- ⚠️ No cross-system conversation analytics
- ⚠️ Conversation history not available via API
- ✅ Acceptable for MVP - OpenWebUI provides all history features users need

**Future Enhancement (Post-MVP):**
If needed, could optionally store conversations in PostgreSQL for:
- Analytics and insights
- Cross-system conversation access
- Advanced context management

---

## Streaming Implementation

**Decision:** **Reuse Existing Streaming - Add OpenAI Format Adapter**

**Existing Streaming (agent/api.py:415-519):**
- Endpoint: `/chat/stream` (used by CLI)
- Function: `run_specialist_query_stream()` from specialist_agent.py
- Format: Custom SSE with `{"type": "text", "content": "..."}` chunks
- Status: ✅ **Working perfectly** - powers CLI streaming

**New Streaming for OpenWebUI:**
- Endpoint: `/v1/chat/completions` (to be added)
- Function: **Reuse same `run_specialist_query_stream()`**
- Format: Add adapter to convert → OpenAI SSE format
- Location: **In agent/api.py** (near existing `/chat/stream` endpoint)

**Implementation Approach:**
```python
# agent/api.py (add near line 519, after /chat/stream)

async def stream_openai_format(specialist_stream, model="evi-specialist"):
    """
    Adapter: Converts specialist agent stream to OpenAI SSE format.

    Reuses existing run_specialist_query_stream() output.
    """
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"

    # Initial chunk with role
    yield {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant", "content": ""},
            "finish_reason": None
        }]
    }

    # Stream content from existing specialist agent
    # Note: run_specialist_query_stream() yields tuples: ("text", delta) or ("final", response)
    async for item in specialist_stream:
        item_type, data = item

        if item_type == "text":
            # Convert custom format → OpenAI format
            yield {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": data},  # data is the text delta
                    "finish_reason": None
                }]
            }
        elif item_type == "final":
            # Optional: Stream citations here if needed
            pass

    # Final chunk
    yield {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    """OpenAI-compatible endpoint for OpenWebUI."""
    if request.stream:
        # Reuse existing streaming logic!
        specialist_stream = run_specialist_query_stream(
            query=request.messages[-1].content,
            session_id=str(uuid.uuid4()),
            user_id="openwebui"
        )

        # Wrap with OpenAI format adapter
        async def generate():
            async for chunk in stream_openai_format(specialist_stream):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        # Non-streaming mode...
```

**Why This Approach:**
- ✅ **Zero duplication** - reuses battle-tested streaming logic
- ✅ **Minimal code** - just a format adapter (30-40 lines)
- ✅ **Maintainable** - one streaming implementation, two format adapters
- ✅ **Fast** - no performance overhead
- ⏱️ 1-2 hours implementation

**Key Points:**
- Both endpoints share `run_specialist_query_stream()` function
- Adapter only converts data format (custom → OpenAI)
- No changes to specialist agent or streaming core
- Both CLI and OpenWebUI streaming work independently

---

## Endpoint Comparison

Understanding the two API endpoints and their purposes:

| Endpoint | Used By | Request Format | Response Format | Status | Purpose |
|----------|---------|---------------|-----------------|--------|---------|
| `/chat/stream` | CLI tool ([cli.py](../../../cli.py)) | Custom (ChatRequest) | SSE stream (custom) | ✅ **Exists** (api.py:415) | Terminal-based chat interface |
| `/v1/chat/completions` | OpenWebUI (web UI) | OpenAI format | OpenAI SSE/JSON | ⚠️ **To be added** (api.py:~520) | Web browser chat interface |

**Key Points:**
- **Same backend logic**: Both endpoints call `run_specialist_query_stream()` from [specialist_agent.py](../../../agent/specialist_agent.py)
- **Different clients**: CLI uses terminal, OpenWebUI uses web browser
- **Format adapter**: `/v1/chat/completions` wraps specialist stream with OpenAI format converter
- **No breaking changes**: Adding `/v1/chat/completions` does NOT affect existing `/chat/stream` endpoint
- **Parallel operation**: Both endpoints will work simultaneously (CLI and web UI can coexist)

**Example Flow Comparison:**

```
CLI Workflow (Existing):
User types in terminal → cli.py → POST /chat/stream → run_specialist_query_stream() → Dutch response

OpenWebUI Workflow (New):
User types in browser → OpenWebUI → POST /v1/chat/completions → stream_openai_format(run_specialist_query_stream()) → Dutch response
```

---

## Implementation Details

### Required Pydantic Models (agent/models.py)

Add these models to `agent/models.py` for OpenAI-compatible request/response handling:

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class OpenAIChatMessage(BaseModel):
    """Single message in OpenAI chat format."""
    role: Literal["system", "user", "assistant"]
    content: str

class OpenAIChatRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(description="Model ID (e.g., 'evi-specialist')")
    messages: List[OpenAIChatMessage] = Field(description="Conversation history")
    stream: bool = Field(default=False, description="Enable SSE streaming")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2000, ge=1)

class OpenAIChatResponseChoice(BaseModel):
    """Single response choice in OpenAI format."""
    index: int = 0
    message: OpenAIChatMessage
    finish_reason: str = "stop"

class OpenAIChatResponse(BaseModel):
    """OpenAI-compatible chat completion response (non-streaming)."""
    id: str = Field(description="Unique completion ID")
    object: str = "chat.completion"
    created: int = Field(description="Unix timestamp")
    model: str = "evi-specialist"
    choices: List[OpenAIChatResponseChoice]
    usage: Optional[dict] = None  # Optional token usage stats

class OpenAIStreamChunk(BaseModel):
    """Single SSE chunk in OpenAI streaming format."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str = "evi-specialist"
    choices: List[dict]  # [{index: 0, delta: {content: "..."}, finish_reason: None}]
```

### Required Imports (agent/api.py)

Add to existing imports in `agent/api.py`:

```python
import time
import uuid
import json
from agent.models import (
    OpenAIChatRequest,
    OpenAIChatResponse,
    OpenAIChatResponseChoice,
    OpenAIChatMessage
)
```

### File Structure

```
agent/
├── api.py (MODIFY)
│   ├── Line ~415: /chat/stream (existing)
│   ├── Line ~520: stream_openai_format() (NEW helper function)
│   ├── Line ~580: @app.get("/v1/models") (NEW endpoint)
│   ├── Line ~600: @app.post("/v1/chat/completions") (NEW endpoint)
│   └── Existing endpoints unchanged
├── models.py (MODIFY)
│   └── Add OpenAI* models (6 new classes, ~60 lines)
└── specialist_agent.py (NO CHANGES)
```

### Error Handling

Add OpenAI-compatible error responses:

```python
# agent/api.py

class OpenAIError(BaseModel):
    """OpenAI-compatible error format."""
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None

class OpenAIErrorResponse(BaseModel):
    error: OpenAIError

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    try:
        # Validate model ID
        if request.model != "evi-specialist":
            raise HTTPException(
                status_code=404,
                detail=OpenAIErrorResponse(
                    error=OpenAIError(
                        message=f"Model '{request.model}' not found. Available: 'evi-specialist'",
                        type="invalid_request_error",
                        param="model"
                    )
                ).dict()
            )

        # Validate messages not empty
        if not request.messages:
            raise HTTPException(
                status_code=400,
                detail=OpenAIErrorResponse(
                    error=OpenAIError(
                        message="Messages array cannot be empty",
                        type="invalid_request_error",
                        param="messages"
                    )
                ).dict()
            )

        # Extract last user message
        user_message = request.messages[-1].content

        if not user_message or user_message.strip() == "":
            raise HTTPException(
                status_code=400,
                detail=OpenAIErrorResponse(
                    error=OpenAIError(
                        message="Message content cannot be empty",
                        type="invalid_request_error",
                        param="messages"
                    )
                ).dict()
            )

        # ... rest of implementation ...

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OpenAI endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=OpenAIErrorResponse(
                error=OpenAIError(
                    message="Internal server error processing request",
                    type="internal_server_error"
                )
            ).dict()
        )
```

### Testing Files

Tests already stubbed in `/Users/builder/dev/evi_rag_test/tests/agent/test_openai_api.py`:
- 8 test stubs with TODO comments
- Test fixtures for mocking specialist responses
- Coverage: non-streaming, streaming, model list, errors, citations

### Docker Compose Updates

Add to existing `docker-compose.yml`:

```yaml
# Add after neo4j service

openwebui:
  image: ghcr.io/open-webui/open-webui:main
  container_name: evi_openwebui
  restart: unless-stopped
  ports:
    - "3000:8080"
  environment:
    - OPENAI_API_BASE_URL=http://host.docker.internal:8058/v1  # Mac/Windows only
    - OPENAI_API_KEY=not-needed
    - WEBUI_NAME=EVI 360 Specialist
    - DEFAULT_MODELS=evi-specialist
    - DEFAULT_LOCALE=nl
    - WEBUI_AUTH=false
    - ENABLE_RAG_WEB_SEARCH=false
    - ENABLE_IMAGE_GENERATION=false
    - ENABLE_COMMUNITY_SHARING=false
  volumes:
    - openwebui_data:/app/backend/data
  networks:
    - evi_rag_network
  depends_on:
    - postgres

volumes:
  # ... existing volumes ...
  openwebui_data:
    driver: local
```

### Implementation Checklist

Before starting implementation:
- [x] Model ID consolidated to `evi-specialist`
- [x] Docker networking clarified (Mac/Windows only)
- [x] Session management approach decided (stateless, last message only)
- [x] Streaming approach clarified (reuse existing + adapter)
- [x] Required models documented (6 Pydantic classes)
- [x] Required imports listed
- [x] Error handling pattern documented
- [x] File structure and line numbers specified

**Estimated Implementation Time:** 4-6 hours
- Phase 1: Pydantic models + /v1/models endpoint (1 hour)
- Phase 2: /v1/chat/completions non-streaming (1.5 hours)
- Phase 3: Streaming adapter (1.5 hours)
- Phase 4: Docker integration (1 hour)
- Phase 5: Testing (1-2 hours)

---

## Spike Plan

**Previous content below this line...**

```
CLI Workflow (Existing):
User types in terminal → cli.py → POST /chat/stream → run_specialist_query() → Dutch response

OpenWebUI Workflow (New):
User types in browser → OpenWebUI → POST /v1/chat/completions → run_specialist_query() → Dutch response
```

---

## Spike Plan

**Objective:** Validate OpenWebUI integration with FastAPI backend and measure performance.

**Duration:** 1.5 days

### Step 1: Environment Setup (2 hours)
- Clone OpenWebUI repository
- Create Docker Compose file with OpenWebUI + existing FastAPI + PostgreSQL
- Configure environment variables (API keys, database connection)
- Verify all services start and can communicate

**Success Criteria:**
- All containers running without errors
- OpenWebUI accessible at http://localhost:3000
- FastAPI accessible at http://localhost:8000
- Health checks pass for all services

---

### Step 2: Basic API Integration (3 hours)
- Create custom RAG function in OpenWebUI that calls FastAPI `/query` endpoint
- Test simple query: "Wat zijn de richtlijnen voor werken op hoogte?" (What are guidelines for working at height?)
- Verify response returns tier 1 summary correctly
- Measure end-to-end latency

**Success Criteria:**
- OpenWebUI successfully calls FastAPI endpoint
- Dutch query returns relevant guideline summary
- Latency <2 seconds for simple queries
- Response formatted correctly in chat UI

---

### Step 3: Multi-Turn Conversation (3 hours)
- Implement conversation context retention using OpenWebUI's history
- Test follow-up queries: "Geef me meer details" (Give me more details)
- Verify tier 2/3 guidelines retrieved based on context
- Test product recommendations in conversation flow

**Success Criteria:**
- Follow-up questions retrieve correct tier level
- Conversation context maintained across 3+ turns
- Product recommendations integrated naturally
- No context confusion between different guideline topics

---

### Step 4: Authentication & Session Management (2 hours)
- Implement shared authentication mechanism (JWT or Redis session)
- Test login flow and session persistence
- Verify user-specific chat history
- Test concurrent sessions (2+ users)

**Success Criteria:**
- Users can authenticate and access chat
- Sessions persist across page reloads
- Chat history correctly scoped to user
- No session conflicts with concurrent users

---

### Step 5: Performance Testing & Documentation (2 hours)
- Run load test: 10 concurrent users, 5 queries each
- Measure P95 latency and error rates
- Document integration architecture and configuration
- Create deployment guide for production

**Success Criteria:**
- P95 latency <3 seconds under load
- Zero errors with 10 concurrent users
- Architecture diagram created
- Deployment steps documented

**Spike Deliverables:**
1. Working Docker Compose configuration
2. Custom RAG pipeline code for OpenWebUI
3. Performance test results (latency, concurrency)
4. Integration architecture diagram
5. Deployment documentation

**Go/No-Go Decision Criteria:**
- ✅ P95 latency <3 seconds → Proceed with Option 1
- ❌ Latency >5 seconds → Evaluate Option 3 (custom UI)
- ✅ Dutch queries work accurately → Proceed
- ❌ Frequent authentication issues → Re-evaluate session strategy

---

**Next Steps After Spike:**
1. Review spike results with team
2. If successful: proceed to full implementation planning
3. Create detailed technical specifications for RAG pipeline
4. Plan production deployment strategy (CI/CD, monitoring)
5. Document API contracts for OpenWebUI ↔ FastAPI integration
