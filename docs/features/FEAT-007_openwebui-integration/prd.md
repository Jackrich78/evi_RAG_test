# PRD: FEAT-007 - OpenWebUI Integration

**Feature ID:** FEAT-007
**Phase:** 7 (Web Interface)
**Status:** 🔍 Exploring (Research Complete)
**Priority:** Medium
**Owner:** Claude Code
**Dependencies:** FEAT-003 (MVP Specialist Agent - Complete ✅)
**Created:** 2025-10-26
**Last Updated:** 2025-10-29

**Related Documents:**
- [Research Findings](research.md) - Comprehensive technical research (2025-10-29)

---

## Problem Statement

EVI 360 workplace safety specialists need a user-friendly web interface to interact with the Dutch RAG system. CLI is sufficient for technical testing but not practical for daily use by non-technical specialists.

**Challenge:** OpenWebUI expects OpenAI-compatible API endpoints (`/v1/chat/completions`). Current API uses custom endpoints (`/chat/stream`). Need to add compatibility layer without breaking existing functionality.

---

> **📦 Important: OpenWebUI is a Separate Application**
>
> **OpenWebUI** is a **third-party open-source web application** (similar to ChatGPT's UI) that provides a chat interface for LLMs. It is:
> - A separate Docker container that will be **added to this project** during implementation
> - **NOT currently in `docker-compose.yml`** - we will add it in Phase 2
> - Designed to communicate with any OpenAI-compatible API
>
> **Why Two API Endpoints?**
> - `/chat/stream` (EXISTING) - Used by CLI tool ([cli.py](../../../cli.py)), keeps current custom format
> - `/v1/chat/completions` (NEW) - OpenAI-compatible format ONLY for OpenWebUI
> - **Both call the same** `run_specialist_query()` function internally - this is just a format adapter
>
> **Current State:** OpenWebUI is NOT installed. It will be deployed as a new Docker service during FEAT-007 implementation.

---

## Goals

1. **OpenAI-Compatible API**: Add `/v1/chat/completions` endpoint that maps to specialist agent
2. **OpenWebUI Deployment**: Configure and deploy OpenWebUI (Docker container or standalone)
3. **Dutch UI**: Configure OpenWebUI with Dutch language settings
4. **Citation Display**: Ensure guideline citations render properly in web UI
5. **Multi-User Support**: Basic user management (no advanced auth for v1)

---

## User Stories

### Story 1: Access Web Interface

**As a** workplace safety specialist
**I want** to access the RAG system via web browser
**So that** I don't need command-line knowledge

**Acceptance Criteria:**
- [ ] Navigate to `http://localhost:3000` (or configured URL)
- [ ] See OpenWebUI login page
- [ ] Login with email/password (or skip auth for internal deployment)
- [ ] Chat interface loads with EVI 360 branding

### Story 2: Ask Questions in Dutch via Web UI

**As a** specialist using the web interface
**I want** to type Dutch questions and see formatted responses
**So that** I can quickly find safety guidelines

**Acceptance Criteria:**
- [ ] Type "Wat zijn de vereisten voor werken op hoogte?" in web UI
- [ ] Response streams in real-time (like ChatGPT)
- [ ] Response is formatted with markdown (bold, lists, quotes)
- [ ] Citations are clickable or clearly separated

### Story 3: View Conversation History

**As a** specialist
**I want** to see my previous questions and answers
**So that** I can refer back to earlier guidance

**Acceptance Criteria:**
- [ ] Left sidebar shows conversation history
- [ ] Click on previous conversation to resume
- [ ] Conversations persist across browser sessions
- [ ] Can delete or archive old conversations

---

## Scope

### In Scope ✅

**API Compatibility Layer:**
- Add `/v1/chat/completions` endpoint to `agent/api.py`
- Map OpenAI request format to specialist agent
- Stream responses in OpenAI SSE format
- Support `stream: true` and `stream: false` modes

**OpenWebUI Configuration:**
- **Add new Docker service**: Deploy OpenWebUI via Docker Compose (currently NOT in `docker-compose.yml`)
- Configure to connect to API on `localhost:8058`
- Set Dutch as default language
- Customize branding (EVI 360 logo, colors)

**Citation Formatting:**
- Ensure specialist agent returns markdown-formatted citations
- Citations render as collapsible sections or footnotes in UI
- Guideline titles are bold, sources are italicized

**Basic Features:**
- Single-user mode (no authentication) OR simple password auth
- Conversation history (stored in OpenWebUI's internal SQLite)
- Model selection dropdown (only shows "EVI 360 Specialist")

### Out of Scope ❌

**Not included in v1:**
- Advanced authentication (SSO, SAML, LDAP)
- Multi-tenancy (separate workspaces per company)
- Admin dashboard (user management, analytics)
- Mobile app or responsive design optimization
- File upload (PDF guideline search)
- Voice input/output
- Integration with EVI 360 website

---

## Architecture Overview

```
User Browser
    ↓
OpenWebUI Container (port 3000)
    ↓ HTTP POST /v1/chat/completions
API Server (agent/api.py, port 8058)
    ├─ /v1/chat/completions (NEW - OpenAI-compatible)
    └─ /chat/stream (EXISTING - CLI uses this)
    ↓
Specialist Agent
    ↓
PostgreSQL (vector search)
```

**Key Changes:**
1. **New Endpoint**: `/v1/chat/completions` in `agent/api.py`
2. **Request Mapping**: Convert OpenAI format → SpecialistDeps
3. **Response Mapping**: Convert SpecialistResponse → OpenAI format
4. **Docker Compose**: Add OpenWebUI service

---

## Technical Notes

### OpenAI API Compatibility

**OpenWebUI Request Format:**
```json
{
  "model": "evi-specialist",
  "messages": [
    {"role": "user", "content": "Wat zijn de vereisten voor werken op hoogte?"}
  ],
  "stream": true
}
```

**Mapping to Specialist Agent:**
```python
# Extract last user message
user_message = request.messages[-1].content

# Initialize deps
deps = SpecialistDeps(
    session_id=generate_session_id(),
    user_id="openwebui_user"
)

# Run agent
result = await specialist_agent.run(user_message, deps=deps)
```

**OpenAI Response Format (Streaming):**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Voor"}}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":" werken"}}]}

data: [DONE]
```

### Docker Compose Addition

```yaml
services:
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: evi_openwebui
    ports:
      - "3000:8080"
    environment:
      - OPENAI_API_BASE_URL=http://host.docker.internal:8058/v1
      - OPENAI_API_KEY=not-needed  # Placeholder
      - WEBUI_NAME=EVI 360 Specialist
      - DEFAULT_MODELS=evi-specialist
      - DEFAULT_USER_ROLE=user
    volumes:
      - openwebui-data:/app/backend/data
    restart: unless-stopped

volumes:
  openwebui-data:
```

---

## Implementation Plan

### Phase 1: API Compatibility (2-3 hours)

**File: `agent/api.py` (MODIFY)**

Add new endpoint:
```python
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    """
    OpenAI-compatible chat completions endpoint for OpenWebUI.
    """
    # Extract user message
    user_message = request.messages[-1].content

    # Initialize specialist deps
    deps = SpecialistDeps(
        session_id=str(uuid.uuid4()),
        user_id="openwebui"
    )

    if request.stream:
        # Return SSE stream in OpenAI format
        return StreamingResponse(
            stream_openai_format(user_message, deps),
            media_type="text/event-stream"
        )
    else:
        # Return complete response
        result = await specialist_agent.run(user_message, deps=deps)
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": result.data.content
                },
                "finish_reason": "stop"
            }]
        }
```

**New Models:**
```python
class OpenAIChatMessage(BaseModel):
    role: str
    content: str

class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[OpenAIChatMessage]
    stream: bool = False
```

### Phase 2: OpenWebUI Deployment (1-2 hours)

1. Add OpenWebUI service to `docker-compose.yml`
2. Start containers: `docker-compose up -d openwebui`
3. Navigate to `http://localhost:3000`
4. Configure settings:
   - Set API base URL to `http://host.docker.internal:8058/v1`
   - Add model `evi-specialist`
   - Set Dutch language
5. Test chat interface

### Phase 3: Citation Formatting (1 hour)

Update specialist prompt to output markdown citations:
```python
SPECIALIST_SYSTEM_PROMPT = """
...
**Antwoordstructuur:**
1. Kort antwoord
2. **Bronnen:**
   > **NVAB Richtlijn: Werken op Hoogte** (NVAB)
   > "Quote hier..."

   > **Arbowet Artikel 3** (Arboportaal)
   > "Quote hier..."
3. Praktisch advies
"""
```

Test in OpenWebUI that citations render as blockquotes.

### Phase 4: Testing (1-2 hours)

- Run all 10 test queries via OpenWebUI
- Validate citations display correctly
- Check conversation history persists
- Test streaming vs non-streaming modes

---

## Success Criteria

**Functional:**
- ✅ OpenWebUI accessible at `http://localhost:3000`
- ✅ Can ask questions in Dutch and receive responses
- ✅ Responses match CLI quality (same specialist agent)
- ✅ Citations are visible and formatted
- ✅ Conversation history works

**Quality:**
- ✅ Response streaming is smooth (no lag)
- ✅ No errors in browser console
- ✅ Markdown rendering is correct
- ✅ 8/10 test queries return relevant answers

**Performance:**
- ✅ Response time <3 seconds (same as CLI)
- ✅ Page load time <2 seconds
- ✅ No memory leaks after 20 queries

---

## Dependencies

### Infrastructure
- ✅ Docker and Docker Compose
- ✅ FEAT-003 API server running on port 8058

### External
- OpenWebUI Docker image (public, free)
- No additional API keys needed

---

## References

**Documentation:**
- OpenWebUI GitHub: https://github.com/open-webui/open-webui
- OpenAI API Spec: https://platform.openai.com/docs/api-reference/chat
- FEAT-003 PRD: `docs/features/FEAT-003_query-retrieval/prd.md`

**Related Features:**
- FEAT-003: Specialist Agent (dependency)
- FEAT-008: Advanced Memory (future enhancement for conversation context)

---

**Last Updated:** 2025-10-29
**Status:** 🔍 Exploring (Research Complete - Ready for Planning)
**Estimated Effort:** 6-8 hours (reduced from initial estimate based on architectural decisions)
**Risk Level:** Low (OpenWebUI is well-documented, API compatibility is straightforward)

**Next Step:** Run `/plan FEAT-007` to create architecture.md, acceptance.md, testing.md
