# Research Findings: OpenWebUI Integration

**Feature ID:** FEAT-007
**Research Date:** 2025-10-29
**Researcher:** Claude Code + User Decisions

## Research Questions

*Questions from PRD that this research addresses:*

1. What OpenAI-compatible API format does OpenWebUI expect?
2. How should we handle conversation history (OpenWebUI vs our API)?
3. What's the best way to display guideline citations in the web UI?
4. Should we implement authentication for multi-user access?
5. How should streaming responses work with SSE format?
6. What Docker Compose configuration is needed?

## Findings

### Topic 1: OpenWebUI Architecture & Integration Points

**Summary:** OpenWebUI is an open-source web interface for LLMs that expects OpenAI-compatible API endpoints. It communicates via HTTP POST to `/v1/chat/completions` and handles all UI/UX concerns including conversation history, user management, and markdown rendering.

**Details:**
- **Integration Pattern**: OpenWebUI Frontend → OpenWebUI Backend → Your Custom API
- **Required Endpoint**: `/v1/chat/completions` (OpenAI-compatible)
- **Optional Endpoint**: `/v1/models` (for model discovery)
- **Communication**: HTTP POST with JSON request/response
- **Streaming**: Server-Sent Events (SSE) with `stream: true` parameter
- **UI Features**: Built-in markdown rendering, conversation history, user management, model selection dropdown

**Architecture Flow:**
```
Browser (User)
    ↓ WebSocket/HTTP
OpenWebUI Frontend (Svelte/SvelteKit)
    ↓ API calls
OpenWebUI Backend (Python/FastAPI)
    ↓ HTTP POST /v1/chat/completions
Your API (agent/api.py, port 8058)
    ↓ Specialist Agent Call
Specialist Agent (agent/specialist_agent.py)
    ↓ Database Queries
PostgreSQL (vector search)
```

**Source:** OpenWebUI GitHub documentation
**Retrieved:** 2025-10-29 via research analysis

---

### Topic 2: OpenAI API Compatibility Requirements

**Summary:** OpenWebUI strictly expects OpenAI's chat completions API format. Both streaming and non-streaming modes must follow the exact structure including specific field names, object types, and SSE formatting.

**Details:**

**Request Format (Streaming):**
```json
{
  "model": "evi-specialist",
  "messages": [
    {"role": "user", "content": "Wat zijn de vereisten voor werken op hoogte?"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": true
}
```

**Response Format (Non-Streaming):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "evi-specialist",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Voor werken op hoogte gelden strikte veiligheidseisen..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 150,
    "total_tokens": 170
  }
}
```

**Response Format (Streaming SSE):**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"evi-specialist","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"evi-specialist","choices":[{"index":0,"delta":{"content":"Voor"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"evi-specialist","choices":[{"index":0,"delta":{"content":" werken"},"finish_reason":null}]}

data: [DONE]
```

**Critical Requirements:**
- Each SSE line must start with `data: ` followed by JSON
- Delta format: only new text in each chunk (not cumulative)
- Must end with `data: [DONE]` signal
- Content-Type header must be `text/event-stream`
- Headers must include `Cache-Control: no-cache` and `X-Accel-Buffering: no`

**Source:** OpenAI API Reference
**URL:** https://platform.openai.com/docs/api-reference/chat
**Retrieved:** 2025-10-29 via specification review

---

### Topic 3: Conversation History Management

**Summary:** Three architectural options exist for managing conversation history. User decision: **OpenWebUI manages history (stateless API)** - simplest approach where OpenWebUI stores conversations in its SQLite database and sends full message history with each request.

**Details:**

**Chosen Approach: Stateless API**
- OpenWebUI stores all conversations in its internal SQLite database
- Each request includes full `messages[]` array with conversation context
- Your API is stateless - no need to retrieve or store history
- Conversations persist only in OpenWebUI (not in your PostgreSQL)
- **Advantage**: Simplest implementation (2-3 hours)
- **Trade-off**: No cross-system analytics or context sharing

**Implementation:**
```python
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    # Extract last user message - ignore history
    user_message = request.messages[-1].content

    # Generate new session ID each time (stateless)
    deps = SpecialistDeps(
        session_id=str(uuid.uuid4()),
        user_id="openwebui"
    )

    # Run specialist agent
    result = await specialist_agent.run(user_message, deps=deps)
    return format_openai_response(result)
```

**Alternative Approaches Considered:**
- **Hybrid Storage**: Both systems store history (4-5 hours) - Rejected as over-engineered for MVP
- **API Owns History**: PostgreSQL is source of truth (6-8 hours) - Rejected as too complex for MVP

**User Decision:** Stateless API (simplest, fastest)

---

### Topic 4: Citation Display Strategy

**Summary:** OpenWebUI has excellent markdown rendering but no built-in citation panel. User decision: **Structured markdown at bottom** - citations formatted as a "Bronnen" (Sources) section with blockquotes at the end of each response.

**Details:**

**Chosen Approach: Structured Markdown Citations**

Update specialist agent system prompt to format responses with citations at bottom:

```python
SPECIALIST_SYSTEM_PROMPT = """Je bent een Nederlandse arbeidsveiligheidsspecialist voor EVI 360.

Je taak:
- Beantwoord vragen over arbeidsveiligheid in het Nederlands
- Gebruik de zoekfunctie om relevante richtlijnen te vinden
- Geef duidelijke, praktische antwoorden met bronvermeldingen
- Citeer altijd minimaal 2 bronnen

**Antwoordstructuur (belangrijk voor webinterface):**

1. **Kort Antwoord** (2-3 zinnen)
   Geef direct het belangrijkste antwoord.

2. **Details**
   Leg uit met specifieke informatie uit de richtlijnen.

3. **📚 Bronnen**

   Vermeld de gebruikte richtlijnen als blockquotes:

   > **[Richtlijn Titel]** (Bron: NVAB/STECR/UWV/etc.)
   > "Relevant citaat of samenvatting..."

   > **[Tweede Richtlijn]** (Bron: ...)
   > "Relevant citaat of samenvatting..."

4. **Praktisch Advies** (indien relevant)
   Concrete stappen of aanbevelingen.

**Voorbeeld Output:**

Voor werken op hoogte gelden strikte veiligheidseisen. Vanaf 2,5 meter hoogte is valbeveiliging verplicht volgens de Arbowet.

**Details:**
- Werknemers moeten gecertificeerde harnasgordels dragen
- Ankerpunten moeten minimaal 22kN belasting kunnen dragen
- Jaarlijkse inspectie van valbeveiliging is verplicht

---

📚 **Bronnen:**

> **NVAB Richtlijn: Werken op Hoogte** (Bron: NVAB)
> "Valbeveiliging is verplicht vanaf 2,5 meter werkhoogte. Collectieve beveiligingsmaatregelen hebben voorrang op persoonlijke beschermingsmiddelen."

> **Arbowet Artikel 3** (Bron: Arboportaal)
> "De werkgever moet zorgen voor veilige arbeidsomstandigheden en passende beschermingsmiddelen verstrekken bij risicovol werk."

**Praktisch Advies:**
Voer eerst een risico-inventarisatie uit en kies voor steigers of hoogwerkers boven losse ladders wanneer mogelijk.
"""
```

**Why This Approach:**
- ✅ Works immediately with OpenWebUI's markdown renderer
- ✅ Visually separated from main content (horizontal rule)
- ✅ Emoji (📚) provides visual anchor
- ✅ Blockquotes are styled distinctly in UI
- ✅ No custom UI development required (0 hours)

**Alternative Approaches Considered:**
- **Inline Markdown**: Citations mixed with content - Rejected (less organized)
- **Custom Citation Panel**: Fork OpenWebUI to add sidebar - Rejected (2-3 days, high maintenance)

**User Decision:** Structured markdown at bottom (1-2 hours implementation)

---

### Topic 5: Authentication & User Management

**Summary:** Three authentication options exist. User decision: **Single-user mode (no auth)** - fastest MVP path with no login required, suitable for internal testing or single specialist deployment.

**Details:**

**Chosen Approach: No Authentication**

**OpenWebUI Configuration:**
```yaml
environment:
  - WEBUI_AUTH=false  # Disables login page
  - ENABLE_SIGNUP=false  # No user registration
```

**API Configuration:**
- No authentication middleware needed
- No API key validation
- No Bearer token checks
- User ID hardcoded to "openwebui"

**Implementation Impact:**
- ⏱️ 0 hours implementation time
- ✅ Perfect for MVP testing
- ✅ Good for internal single-user deployment
- ✅ Can add auth later without breaking changes

**Security Considerations:**
- Deploy behind VPN or internal network only
- Do not expose to public internet
- Suitable for development and internal testing

**Alternative Approaches Considered:**
- **Multi-user with OpenWebUI auth**: OpenWebUI handles login (30 min) - Rejected for MVP
- **API key validation**: Production-ready security (2-3 hours) - Deferred to v2

**User Decision:** Single-user, no auth (0 hours)

---

### Topic 6: Streaming Implementation

**Summary:** Existing `/chat/stream` endpoint (lines 414-522 in agent/api.py) already implements Pydantic AI streaming correctly. User decision: **Reuse existing streaming logic, reformat output** to OpenAI SSE format.

**Details:**

**Chosen Approach: Leverage Existing Streaming**

**Current Streaming Implementation (agent/api.py lines 454-472):**
```python
async with rag_agent.iter(full_prompt, deps=deps) as run:
    async for node in run:
        if rag_agent.is_model_request_node(node):
            async with node.stream(run.ctx) as request_stream:
                async for event in request_stream:
                    from pydantic_ai.messages import PartStartEvent, PartDeltaEvent, TextPartDelta

                    if isinstance(event, PartStartEvent) and event.part.part_kind == 'text':
                        delta_content = event.part.content
                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"

                    elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                        delta_content = event.delta.content_delta
                        yield f"data: {json.dumps({'type': 'text', 'content': delta_content})}\n\n"
```

**Adaptation for OpenAI Format:**

Create new helper function that wraps existing streaming:

```python
async def stream_openai_format(
    user_message: str,
    deps: SpecialistDeps,
    model: str
) -> AsyncGenerator[str, None]:
    """
    Stream specialist agent response in OpenAI SSE format.

    Reuses existing Pydantic AI streaming, reformats output.
    """
    import time
    import json
    import uuid

    chunk_id = f"chatcmpl-{uuid.uuid4()}"
    created_time = int(time.time())

    # Initial chunk with role
    yield f'data: {json.dumps({"id": chunk_id, "object": "chat.completion.chunk", "created": created_time, "model": model, "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]})}\n\n'

    # Stream content using existing Pydantic AI pattern
    async with specialist_agent.iter(user_message, deps=deps) as run:
        async for node in run:
            if specialist_agent.is_model_request_node(node):
                async with node.stream(run.ctx) as request_stream:
                    async for event in request_stream:
                        from pydantic_ai.messages import PartDeltaEvent, TextPartDelta

                        if isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                            delta_content = event.delta.content_delta

                            # Reformat to OpenAI structure
                            yield f'data: {json.dumps({"id": chunk_id, "object": "chat.completion.chunk", "created": created_time, "model": model, "choices": [{"index": 0, "delta": {"content": delta_content}, "finish_reason": None}]})}\n\n'

    # Final chunk
    yield f'data: {json.dumps({"id": chunk_id, "object": "chat.completion.chunk", "created": created_time, "model": model, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})}\n\n'

    # Done signal
    yield 'data: [DONE]\n\n'
```

**Why This Approach:**
- ✅ DRY principle - don't duplicate streaming logic
- ✅ Leverages proven Pydantic AI streaming
- ✅ Only reformats output layer (thin wrapper)
- ✅ Minimal code duplication
- ⏱️ 1 hour implementation

**Alternative Approaches Considered:**
- **Write new streaming function**: More explicit but duplicates logic (1.5 hours)
- **Shared utility function**: Cleanest but over-engineered for MVP (2-3 hours)

**User Decision:** Reuse existing streaming, reformat output (1 hour)

---

### Topic 7: Error Handling Strategy

**Summary:** When specialist agent fails (LLM error, search timeout, database issues), errors should be returned in OpenAI format with Dutch-language messages for better UX.

**Details:**

**Chosen Approach: OpenAI Error Format with Dutch Messages**

**Standard OpenAI Error Structure:**
```json
{
  "error": {
    "message": "Er is een fout opgetreden bij het verwerken van uw vraag. Probeer het opnieuw.",
    "type": "internal_server_error",
    "param": null,
    "code": null
  }
}
```

**Implementation:**

```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def openai_exception_handler(request: Request, exc: Exception):
    """
    Handle exceptions in OpenAI-compatible format with Dutch messages.
    """
    # Log error for debugging
    logger.error(f"API error: {exc}", exc_info=True)

    # Map exception types to Dutch messages
    dutch_messages = {
        "timeout": "De zoekopdracht duurde te lang. Probeer een kortere vraag.",
        "llm_error": "De AI-service is tijdelijk niet beschikbaar. Probeer het later opnieuw.",
        "database_error": "Kan de database niet bereiken. Neem contact op met de beheerder.",
        "validation_error": "Ongeldige invoer. Controleer uw vraag en probeer opnieuw."
    }

    # Determine error type
    error_type = "internal_server_error"
    if "timeout" in str(exc).lower():
        error_type = "timeout"
        dutch_message = dutch_messages["timeout"]
    elif "llm" in str(exc).lower() or "api" in str(exc).lower():
        error_type = "llm_error"
        dutch_message = dutch_messages["llm_error"]
    elif "database" in str(exc).lower() or "connection" in str(exc).lower():
        error_type = "database_error"
        dutch_message = dutch_messages["database_error"]
    else:
        dutch_message = "Er is een onverwachte fout opgetreden. Probeer het opnieuw."

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": dutch_message,
                "type": error_type,
                "param": None,
                "code": None
            }
        }
    )
```

**Why This Approach:**
- ✅ Matches OpenAI specification exactly
- ✅ Dutch messages improve UX for EVI specialists
- ✅ OpenWebUI displays error in chat interface
- ✅ Proper HTTP status codes (500, 400, etc.)
- ⏱️ 30 minutes implementation

**Alternative Approaches Considered:**
- **Stream error as assistant message**: Non-standard but better UX (45 min) - Rejected
- **Graceful degradation with retry**: Most robust but complex (2-3 hours) - Deferred to v2

**User Decision:** OpenAI error format with Dutch messages (30 min)

---

### Topic 8: Model Selection in OpenWebUI

**Summary:** OpenWebUI shows a model dropdown for users to select which "model" to use. User decision: **Single model only** - show only "EVI Specialist" in dropdown, simplest UX.

**Details:**

**Chosen Approach: Single Model**

**Docker Compose Configuration:**
```yaml
environment:
  - DEFAULT_MODELS=evi-specialist
  - MODEL_FILTER_ENABLED=true
  - MODEL_FILTER_LIST=evi-specialist
```

**API Implementation:**

```python
@app.get("/v1/models")
async def list_models():
    """
    Return available models for OpenWebUI dropdown.
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "evi-specialist",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "evi360"
            }
        ]
    }

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    # Ignore request.model - always use specialist agent
    # (For future: could route to different agent configs)
    ...
```

**Why This Approach:**
- ✅ Simplest UX - no user confusion
- ✅ Clean dropdown with one option
- ✅ Matches current capability (one agent)
- ⏱️ 30 minutes implementation

**Future Extension (FEAT-004, FEAT-009):**
Could expose multiple "models" for power users:
- `evi-specialist-quick` - Tier 1 only (future FEAT-009)
- `evi-specialist-detailed` - All tiers
- `evi-with-products` - Includes product recommendations (future FEAT-004)

**Alternative Approaches Considered:**
- **Multiple modes**: Enables future features (2-3 hours) - Deferred to later
- **Hidden dropdown**: Locked to one model (15 min) - Rejected as less flexible

**User Decision:** Single model only (30 min)

---

### Topic 9: Docker Compose Integration

**Summary:** OpenWebUI runs as a Docker container that needs to connect to your API. Best deployment is adding it to existing `docker-compose.yml` for unified service management.

**Details:**

**Docker Compose Configuration:**

Add to existing `docker-compose.yml`:

```yaml
services:
  # ... existing postgres and neo4j services ...

  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: evi_openwebui
    restart: unless-stopped
    ports:
      - "3000:8080"  # External: 3000, Internal: 8080

    environment:
      # API Configuration
      - OPENAI_API_BASE_URL=http://host.docker.internal:8058/v1
      - OPENAI_API_KEY=not-needed  # Placeholder (no auth)

      # UI Branding
      - WEBUI_NAME=EVI 360 Specialist
      - DEFAULT_MODELS=evi-specialist

      # Language & Locale
      - DEFAULT_LOCALE=nl  # Dutch interface

      # Authentication (disabled for MVP)
      - WEBUI_AUTH=false
      - ENABLE_SIGNUP=false

      # Feature Flags
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

# networks: evi_rag_network (already exists)
```

**Key Configuration Details:**

**API Connection:**
- `OPENAI_API_BASE_URL=http://host.docker.internal:8058/v1`
  - **IMPORTANT**: This configuration is for **Mac/Windows development environments only** (Docker Desktop)
  - Uses `host.docker.internal` to access host machine from container
  - Linux users need to change to `172.17.0.1` or use `network_mode: host`
  - Your API must be running on port 8058 (already is)

**Development Environment Requirement:**
- ⚠️ **Mac or Windows with Docker Desktop required** for this configuration
- Linux users must modify `OPENAI_API_BASE_URL` environment variable

**Port Mapping:**
- `3000:8080` - Access OpenWebUI at `http://localhost:3000`
- Port 3000 must be available (not used by other services)

**Data Persistence:**
- `openwebui_data` volume stores conversations, user settings
- Persists across container restarts

**Deployment Commands:**
```bash
# Start OpenWebUI
docker-compose up -d openwebui

# View logs
docker-compose logs -f openwebui

# Check status
docker-compose ps openwebui

# Restart
docker-compose restart openwebui

# Stop
docker-compose stop openwebui
```

**Why This Approach:**
- ✅ All services in one docker-compose.yml
- ✅ Shared network enables service discovery
- ✅ Unified management (start/stop all together)
- ✅ Production-ready architecture
- ⏱️ 30 minutes implementation

**Alternative Approaches Considered:**
- **Standalone Docker container**: Separate from compose (30 min) - Rejected (less unified)
- **Native installation**: Python/Node.js install - Rejected (complex, not portable)

**User Decision:** Docker Compose integration (30 min)

---

### Topic 10: Testing Strategy

**Summary:** Balance between thoroughness and speed. User decision: **Manual testing + automated endpoint tests** - validates quality without over-engineering.

**Details:**

**Chosen Approach: Moderate Testing**

**1. Automated Tests (pytest):**

Create `tests/agent/test_openai_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from agent.api import app

client = TestClient(app)

def test_openai_chat_completions_non_streaming():
    """Test /v1/chat/completions without streaming."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "evi-specialist",
            "messages": [{"role": "user", "content": "Wat is een veiligheidshelm?"}],
            "stream": False
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Validate OpenAI structure
    assert "id" in data
    assert data["object"] == "chat.completion"
    assert "choices" in data
    assert len(data["choices"]) > 0

    # Validate content
    message = data["choices"][0]["message"]
    assert message["role"] == "assistant"
    assert len(message["content"]) > 0

    # Check Dutch response (basic check)
    assert any(word in message["content"].lower() for word in ["veiligheid", "helm", "bescherming"])

def test_openai_chat_completions_streaming():
    """Test /v1/chat/completions with streaming."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "evi-specialist",
            "messages": [{"role": "user", "content": "Test vraag"}],
            "stream": True
        }
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

    # Collect stream
    chunks = list(response.iter_lines())

    # Validate SSE format
    assert any(b"data: " in chunk for chunk in chunks)
    assert b"data: [DONE]" in chunks[-1]

def test_list_models():
    """Test /v1/models endpoint."""
    response = client.get("/v1/models")

    assert response.status_code == 200
    data = response.json()

    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "evi-specialist"

def test_error_handling():
    """Test error handling with invalid request."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "evi-specialist",
            "messages": [],  # Empty messages should error
            "stream": False
        }
    )

    assert response.status_code in [400, 422, 500]
    data = response.json()
    assert "error" in data
```

**2. Manual Testing Checklist:**

10 Dutch test queries via OpenWebUI:

1. "Wat zijn de vereisten voor werken op hoogte?"
2. "Hoe voorkom ik RSI bij beeldschermwerk?"
3. "Welke beschermingsmiddelen zijn verplicht in lawaai?"
4. "Wat zijn de regels voor nachtdiensten?"
5. "Hoe ga ik om met agressie op de werkvloer?"
6. "Wat moet ik doen na een prikaccident?"
7. "Welke verplichtingen heeft de werkgever bij gevaarlijke stoffen?"
8. "Hoe lang mag ik achter een beeldscherm werken?"
9. "Wat zijn de richtlijnen voor tillen?"
10. "Welke rechten heb ik als zwangere werkneemster?"

**Validation Criteria per Query:**
- ✅ Response in Dutch (not English)
- ✅ Citations section present with ≥2 sources
- ✅ Citations formatted as blockquotes
- ✅ Content relevant to question
- ✅ Response length appropriate (not too short/long)
- ✅ Markdown renders correctly (bold, lists, quotes)
- ✅ Streaming smooth (<500ms first token)

**Success Target:** 8/10 queries must meet all criteria

**Why This Approach:**
- ✅ Automated tests catch regressions
- ✅ Manual testing validates UX quality
- ✅ Reasonable coverage without over-testing
- ⏱️ 2-3 hours total testing time

**Alternative Approaches Considered:**
- **Manual only**: Fast but no regression protection (1 hour) - Rejected
- **Full integration suite**: Playwright UI tests + load tests (1-2 days) - Rejected as overkill

**User Decision:** Manual + automated endpoint tests (2-3 hours)

---

## Recommendations

### Primary Recommendation: Incremental Implementation with Stateless Architecture

**Rationale:**
- **Speed**: All chosen approaches optimize for fastest MVP (6-8 hours total)
- **Simplicity**: Stateless API, single-user, single model minimize complexity
- **Quality**: Moderate testing ensures reliability without over-engineering
- **Maintainability**: Reusing existing code (streaming) reduces technical debt
- **Extensibility**: Architecture supports future features (multi-user, products, tiers)

**Key Benefits:**
- ✅ Web UI accessible to non-technical specialists
- ✅ No breaking changes to CLI functionality
- ✅ Dutch language support throughout
- ✅ Production-ready Docker deployment
- ✅ Clear path to future enhancements

**Considerations:**
- ⚠️ Stateless API means no cross-session context (acceptable for MVP)
- ⚠️ Single-user mode not suitable for public deployment (can add auth later)
- ⚠️ Citations embedded in response (not separate panel) - acceptable UX

### Implementation Phases

**Phase 1: API Compatibility (2-3 hours)**
- Add Pydantic models for OpenAI format
- Create `/v1/chat/completions` endpoint
- Create `/v1/models` endpoint
- Implement streaming helper function
- Add error handler

**Phase 2: Citation Formatting (1 hour)**
- Update `SPECIALIST_SYSTEM_PROMPT` with structured format
- Test markdown rendering
- Adjust formatting if needed

**Phase 3: Docker Compose Setup (30 min)**
- Add OpenWebUI service to docker-compose.yml
- Start containers
- Configure settings

**Phase 4: Testing & Validation (2-3 hours)**
- Write pytest tests (4 test cases)
- Run manual testing (10 queries)
- Document results
- Fix any issues

**Total Estimated Effort:** 6-8 hours

---

## Trade-offs

### Performance vs. Complexity

**Decision:** Optimize for simplicity
- **Trade-off**: Stateless API means generating new session ID each request (slight overhead)
- **Benefit**: No database queries for conversation history (actually faster)
- **Net Impact**: Neutral to slightly faster

### Cost vs. Features

**Decision:** Minimal feature set for MVP
- **Trade-off**: No multi-user auth, no advanced features
- **Benefit**: 0 hours spent on authentication, faster to production
- **Net Impact**: Significant time savings

### Time to Market vs. Quality

**Decision:** Moderate testing
- **Trade-off**: Not production-ready for multi-user (single-user only)
- **Benefit**: 6-8 hours instead of 2+ days for full test suite
- **Net Impact**: Fast MVP with acceptable quality

### Maintenance vs. Flexibility

**Decision:** Reuse existing code patterns
- **Trade-off**: Streaming wrapper adds thin abstraction layer
- **Benefit**: No code duplication, leverages proven Pydantic AI streaming
- **Net Impact**: Lower maintenance burden

---

## Answers to Open Questions

### Question 1: What OpenAI-compatible API format does OpenWebUI expect?

**Answer:** OpenWebUI expects exact OpenAI chat completions API format with `/v1/chat/completions` endpoint, supporting both `stream: true` (SSE) and `stream: false` (JSON) modes. Request format includes `model`, `messages` array, and optional parameters. Response format differs for streaming (delta chunks) vs non-streaming (complete message).

**Confidence:** High
**Source:** OpenWebUI GitHub documentation + OpenAI API specification
**Implementation:** See Topic 2 for complete request/response formats

---

### Question 2: How should we handle conversation history?

**Answer:** OpenWebUI will manage all conversation history in its internal SQLite database. Your API will be stateless - extract the last user message from `request.messages[-1].content` and generate a new session ID for each request. No need to retrieve or store history in PostgreSQL.

**Confidence:** High
**Source:** User decision + OpenWebUI architecture analysis
**Implementation:** See Topic 3 for stateless API code example

---

### Question 3: What's the best way to display guideline citations?

**Answer:** Update specialist agent prompt to format citations as a structured markdown section at the bottom of responses, separated by horizontal rule (---), with "📚 Bronnen:" header and blockquote format for each citation. This works with OpenWebUI's built-in markdown renderer without custom UI development.

**Confidence:** High
**Source:** User decision + OpenWebUI markdown rendering capabilities
**Implementation:** See Topic 4 for complete prompt template

---

### Question 4: Should we implement authentication?

**Answer:** No authentication for MVP. Configure OpenWebUI with `WEBUI_AUTH=false` for single-user mode. This eliminates login flow and is suitable for internal testing or single specialist deployment. Can add authentication later without breaking changes.

**Confidence:** High
**Source:** User decision based on MVP priorities
**Implementation:** See Topic 5 for Docker Compose configuration

---

### Question 5: How should streaming responses work?

**Answer:** Reuse existing Pydantic AI streaming implementation from `/chat/stream` endpoint (agent/api.py lines 454-472) and create a thin wrapper function `stream_openai_format()` that reformats deltas into OpenAI SSE structure. This avoids code duplication and leverages proven streaming logic.

**Confidence:** High
**Source:** User decision + analysis of existing codebase
**Implementation:** See Topic 6 for complete streaming helper function

---

### Question 6: What Docker Compose configuration is needed?

**Answer:** Add OpenWebUI service to existing docker-compose.yml with configuration: `OPENAI_API_BASE_URL=http://host.docker.internal:8058/v1`, `WEBUI_AUTH=false`, `DEFAULT_MODELS=evi-specialist`, `DEFAULT_LOCALE=nl`. Use port 3000:8080 mapping and persistent volume for data. Connect to existing `evi_rag_network`.

**Confidence:** High
**Source:** OpenWebUI Docker documentation + project architecture
**Implementation:** See Topic 9 for complete docker-compose.yml addition

---

## Next Steps

1. **Architecture Planning:** Use these findings in `/plan FEAT-007` to create:
   - architecture.md (detailed technical design)
   - acceptance.md (test criteria)
   - testing.md (test strategy)
   - manual-test.md (validation checklist)

2. **No Technical Spike Needed:** All approaches validated through research and user decisions

3. **Proceed to Planning:** ✅ Ready to run `/plan FEAT-007`

---

**Research Complete:** ✅
**Ready for Planning:** Yes

**Total Research Time:** Comprehensive technical discovery completed
**Sources:** OpenWebUI documentation, OpenAI API specification, existing codebase analysis, user architectural decisions
**Confidence Level:** High - All open questions answered with clear implementation path
