# API Specifications - EVI 360 RAG

**Last Updated:** 2025-10-25
**Status:** Phase 5-7 Planned (Not Yet Implemented)

## Overview

The EVI 360 RAG system will provide REST API endpoints for Dutch-language chat interactions with the multi-agent system. The API is **planned for Phase 5-7** and is not yet implemented.

**API Type:** REST with Server-Sent Events (SSE) for streaming
**Framework:** FastAPI 0.115.13 (planned)
**Server:** uvicorn 0.34.3 (planned)
**Base URL:** TBD (local development: `http://localhost:8000`)
**Authentication:** Not yet designed (Phase 7)

---

## Planned Endpoints (Phase 5-7)

### POST /chat

**Description:** Main agent endpoint for Dutch language queries. Returns complete response after processing.

**Phase:** 5-6 (Multi-agent System + Dutch Language)

**Authentication:** Not yet implemented

**Request Body:**
```json
{
  "message": "Wat zijn de vereisten voor werken op hoogte?",
  "session_id": "optional-uuid",
  "user_id": "optional-string"
}
```

**Response (200):**
```json
{
  "response": "Voor werken op hoogte gelden de volgende vereisten...",
  "guideline_citations": [
    {
      "title": "Werken op hoogte",
      "source": "NVAB",
      "tier": 2,
      "url": "https://notion.so/..."
    }
  ],
  "product_recommendations": [
    {
      "name": "Valbeschermingsharnas",
      "url": "https://evi360.nl/products/...",
      "reasoning": "Dit harnas voldoet aan EN 361 norm..."
    }
  ],
  "session_id": "uuid",
  "message_id": "uuid"
}
```

**Errors:**
- 400: Invalid input (empty message, invalid session_id)
- 500: Internal server error (database, LLM API issues)

---

### POST /chat/stream

**Description:** Streaming version of /chat using Server-Sent Events (SSE) for real-time responses.

**Phase:** 7 (CLI & API Enhancement)

**Authentication:** Not yet implemented

**Request Body:**
```json
{
  "message": "Wat zijn de vereisten voor persoonlijke beschermingsmiddelen?",
  "session_id": "optional-uuid"
}
```

**Response:** SSE stream with events:
```
event: thinking
data: {"status": "searching_guidelines", "tier": 1}

event: chunk
data: {"content": "Voor persoonlijke beschermingsmiddelen..."}

event: chunk
data: {"content": " gelden de volgende vereisten..."}

event: citations
data: {"guidelines": [...]}

event: products
data: {"recommendations": [...]}

event: done
data: {"session_id": "uuid", "message_id": "uuid"}
```

**Technology:**
- `sse-starlette 2.3.6` for server-side streaming
- `httpx-sse 0.4.0` for client-side consumption

---

### POST /research

**Description:** Direct access to Research Agent for debugging and testing. Returns structured data without Dutch language formatting.

**Phase:** 5 (Multi-agent System)

**Authentication:** Not yet implemented

**Request Body:**
```json
{
  "query": "valbescherming werken op hoogte",
  "tier": 2,
  "include_products": true,
  "match_count": 10
}
```

**Response (200):**
```json
{
  "guidelines": [
    {
      "chunk_id": "uuid",
      "content": "...",
      "tier": 2,
      "similarity": 0.92,
      "document_title": "Werken op hoogte",
      "document_source": "NVAB"
    }
  ],
  "products": [
    {
      "product_id": "uuid",
      "name": "Veiligheidshelm XYZ",
      "similarity": 0.88,
      "compliance_tags": ["EN_397", "CE_certified"]
    }
  ],
  "graph_relationships": []
}
```

---

## Data Models (Phase 5-7 - Planned)

**Request/Response Models:**
- Defined using Pydantic models from [`agent/models.py`](../../agent/models.py)
- Type-safe validation for all API inputs/outputs

**Models Already Implemented:**
- `ResearchAgentResponse` - Research agent output structure
- `SpecialistAgentResponse` - Specialist agent response structure
- `GuidelineSearchResult` - Guideline search results
- `ProductRecommendation` - Product recommendations with reasoning

---

## Authentication (Phase 7 - Planned)

**Method:** TBD (JWT, API Keys, or Session-based)

**Considerations:**
- Simple API keys for MVP testing
- JWT for production multi-user support
- Session management via `sessions` table in PostgreSQL

---

## Error Handling

**Standard Error Response:**
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Message cannot be empty",
    "details": {}
  }
}
```

**Error Codes (Planned):**
- `INVALID_INPUT` - 400: Invalid request parameters
- `UNAUTHORIZED` - 401: Missing or invalid authentication
- `NOT_FOUND` - 404: Resource not found (session, message)
- `RATE_LIMIT_EXCEEDED` - 429: Too many requests
- `INTERNAL_ERROR` - 500: Server error
- `LLM_API_ERROR` - 502: External LLM API failure
- `DATABASE_ERROR` - 503: Database unavailable

---

## Rate Limiting (Phase 7 - Planned)

**Limits:**
- 100 requests per minute per user (tentative)
- 1000 requests per day per user (tentative)

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## CORS Configuration (Phase 7 - Planned)

**Allowed Origins:**
- Development: `http://localhost:3000`, `http://localhost:8000`
- Production: TBD (specific EVI 360 domains)

**Allowed Methods:** GET, POST, OPTIONS

**Allowed Headers:** Content-Type, Authorization

---

## API Documentation (Phase 7 - Planned)

**OpenAPI/Swagger:**
- FastAPI auto-generates OpenAPI 3.0 spec
- Interactive docs at `/docs` (Swagger UI)
- ReDoc UI at `/redoc`

**Example:**
```bash
# Start API server
uvicorn agent.api:app --reload

# Access interactive docs
open http://localhost:8000/docs
```

---

## Testing (Phase 5-7 - Planned)

**Test Framework:** pytest 8.4.1 + pytest-asyncio 1.0.0

**Test Cases:**
1. `/chat` endpoint with various Dutch queries
2. `/chat/stream` SSE streaming functionality
3. `/research` endpoint with tier filtering
4. Error handling (invalid inputs, LLM failures)
5. Session management (create, retrieve, persist)

**Mocking:**
- Mock OpenAI API responses
- Mock database queries
- Mock Research Agent responses

---

## Performance Targets (Phase 5-7)

**Response Times:**
- `/research` endpoint: < 1000ms (Tier 2 queries)
- `/chat` endpoint: < 3000ms (full agent processing)
- `/chat/stream` first chunk: < 500ms

**Concurrency:**
- Support 10+ concurrent users
- Queue management for LLM API calls

---

## Implementation Status

**Phase 5: Multi-Agent System**
- ⏳ Research Agent implementation
- ⏳ Specialist Agent implementation
- ⏳ `/chat` and `/research` endpoints

**Phase 6: Dutch Language**
- ⏳ Dutch system prompts
- ⏳ Response validation

**Phase 7: CLI & API Enhancement**
- ⏳ `/chat/stream` SSE implementation
- ⏳ Authentication
- ⏳ Rate limiting
- ⏳ OpenAPI documentation

---

**Note:** Update this document when:
- API endpoints are implemented
- Request/response formats change
- Authentication is added
- Rate limits are configured

**See Also:**
- [architecture.md](architecture.md) - System architecture
- [stack.md](stack.md) - FastAPI and related technologies
- [`agent/models.py`](../../agent/models.py) - Pydantic models for API
- [FEAT-001 PRD](../features/FEAT-001_evi-rag-implementation/prd.md) - Implementation plan
