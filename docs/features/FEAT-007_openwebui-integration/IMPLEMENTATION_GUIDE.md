# FEAT-007 Implementation Guide - Quick Start

**Feature:** OpenWebUI Integration
**Status:** ✅ Documentation Complete - Ready for Implementation
**Last Updated:** 2025-11-01
**Estimated Time:** 4-6 hours

---

## Quick Reference

### Key Decisions Made

| Decision | Answer | Document Reference |
|----------|--------|-------------------|
| Model ID | `evi-specialist` (v1 suffix removed) | All docs updated |
| Deployment Environment | Mac/Windows with Docker Desktop only | architecture.md, research.md, prd.md |
| Session Management | Stateless - last message only (`request.messages[-1].content`) | architecture.md:237-280 |
| Streaming Implementation | Reuse existing `run_specialist_query_stream()` + OpenAI adapter | architecture.md:283-387 |
| Function Placement | `stream_openai_format()` in agent/api.py near line 520 | architecture.md:424-500 |
| Conversation History | OpenWebUI manages all history (SQLite) - API is stateless | architecture.md:237-280 |

---

## Implementation Steps (Sequential)

### Step 1: Add Pydantic Models (1 hour)

**File:** `agent/models.py`

Add 6 new classes (~60 lines):
- `OpenAIChatMessage`
- `OpenAIChatRequest`
- `OpenAIChatResponseChoice`
- `OpenAIChatResponse`
- `OpenAIStreamChunk`
- `OpenAIError` + `OpenAIErrorResponse`

**Full code:** See architecture.md:426-469 and architecture.md:506-578

---

### Step 2: Add /v1/models Endpoint (30 min)

**File:** `agent/api.py` (add near line 580)

```python
@app.get("/v1/models")
async def list_models():
    """Return available models for OpenWebUI dropdown."""
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
```

**Test with curl:**
```bash
curl http://localhost:8058/v1/models
```

---

### Step 3: Add Streaming Adapter Function (1 hour)

**File:** `agent/api.py` (add near line 520, after `/chat/stream`)

```python
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
```

**Full code:** See architecture.md:303-351

---

### Step 4: Add /v1/chat/completions Endpoint (1.5 hours)

**File:** `agent/api.py` (add near line 600)

**Key points:**
- Extract ONLY last message: `request.messages[-1].content`
- Generate new session_id per request: `str(uuid.uuid4())`
- Validate model ID is "evi-specialist"
- Support both `stream: true` and `stream: false`
- Use OpenAI error format (see architecture.md:506-578)

**Streaming mode:**
```python
if request.stream:
    specialist_stream = run_specialist_query_stream(
        query=request.messages[-1].content,
        session_id=str(uuid.uuid4()),
        user_id="openwebui",
        language="nl"
    )

    async def generate():
        async for chunk in stream_openai_format(specialist_stream):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Non-streaming mode:**
```python
else:
    response = await run_specialist_query(
        query=request.messages[-1].content,
        session_id=str(uuid.uuid4()),
        user_id="openwebui",
        language="nl"
    )

    return OpenAIChatResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
        created=int(time.time()),
        choices=[
            OpenAIChatResponseChoice(
                message=OpenAIChatMessage(
                    role="assistant",
                    content=response.response  # Full response text
                )
            )
        ]
    )
```

**Full code with error handling:** See architecture.md:519-577

---

### Step 5: Add Docker Configuration (30 min)

**File:** `docker-compose.yml`

Add after neo4j service:

```yaml
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: evi_openwebui
    restart: unless-stopped
    ports:
      - "3000:8080"
    environment:
      - OPENAI_API_BASE_URL=http://host.docker.internal:8058/v1
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

**⚠️ Important:** This config is for **Mac/Windows with Docker Desktop only**. Linux users must change `OPENAI_API_BASE_URL` to `http://172.17.0.1:8058/v1`.

**Start services:**
```bash
docker-compose up -d openwebui
docker-compose ps  # Verify openwebui is running
```

---

### Step 6: Testing (1-2 hours)

#### Unit Tests

**File:** `tests/agent/test_openai_api.py` (already stubbed with TODOs)

Complete 8 test stubs:
1. `test_openai_chat_completions_non_streaming()`
2. `test_openai_chat_completions_streaming()`
3. `test_list_models()`
4. `test_error_handling()`
5. `test_dutch_language_detection()` (optional)
6. `test_citation_formatting()` (optional)
7. `test_conversation_history_context()` (optional)
8. `test_response_time_performance()` (optional)

**Run tests:**
```bash
source venv_linux/bin/activate
python3 -m pytest tests/agent/test_openai_api.py -v
```

#### Manual Testing

**Follow:** `manual-test.md` - 10 Dutch queries to validate via OpenWebUI UI

**Access OpenWebUI:**
1. Open browser to `http://localhost:3000`
2. Verify "evi-specialist" appears in model dropdown
3. Test all 10 queries from manual-test.md:213-227

---

## Required Imports

Add to `agent/api.py`:

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

---

## Verification Checklist

Before submitting PR:

- [ ] All tests in `test_openai_api.py` pass
- [ ] `/v1/models` returns `evi-specialist`
- [ ] `/v1/chat/completions` works with `stream: false`
- [ ] `/v1/chat/completions` works with `stream: true`
- [ ] Error responses match OpenAI format
- [ ] OpenWebUI container starts successfully
- [ ] Can access OpenWebUI at http://localhost:3000
- [ ] Model dropdown shows "evi-specialist"
- [ ] All 10 Dutch queries from manual-test.md pass
- [ ] Streaming works smoothly in OpenWebUI
- [ ] Citations render correctly
- [ ] No console errors in browser
- [ ] CLI `/chat/stream` endpoint still works (no breaking changes)

---

## Troubleshooting

### Issue: OpenWebUI can't connect to API

**Symptoms:** "Failed to connect to API" error in OpenWebUI

**Solutions:**
1. Verify API is running: `curl http://localhost:8058/health`
2. Check Docker networking: Mac/Windows should use `host.docker.internal`
3. Check OpenWebUI logs: `docker logs evi_openwebui`
4. Verify port 8058 is accessible from container

### Issue: Model not found

**Symptoms:** "Model 'evi-specialist-v1' not found"

**Solution:** Update to `evi-specialist` (v1 suffix removed). Check OpenWebUI environment variable `DEFAULT_MODELS=evi-specialist`.

### Issue: Empty responses

**Symptoms:** OpenWebUI shows blank responses

**Solutions:**
1. Check API logs: `docker logs -f <api-container>`
2. Test endpoint directly: `curl -X POST http://localhost:8058/v1/chat/completions -H "Content-Type: application/json" -d '{"model": "evi-specialist", "messages": [{"role": "user", "content": "Test"}], "stream": false}'`
3. Verify specialist agent is running correctly

### Issue: Streaming not working

**Symptoms:** Response appears all at once instead of streaming

**Solutions:**
1. Verify `stream: true` in request
2. Check `stream_openai_format()` function is yielding chunks correctly
3. Check browser Network tab shows `text/event-stream` content type
4. Verify `[DONE]` signal is sent at end

---

## Documentation References

| Document | Purpose | Lines |
|----------|---------|-------|
| `prd.md` | Product requirements, user stories, scope | 367 lines |
| `architecture.md` | Technical decisions, implementation details | 650+ lines |
| `research.md` | Comprehensive research findings | 922 lines |
| `acceptance.md` | Acceptance criteria (20 AC) | 219 lines |
| `testing.md` | Testing strategy, test stubs | 389 lines |
| `manual-test.md` | Manual testing guide (10 Dutch queries) | 330 lines |
| `IMPLEMENTATION_GUIDE.md` | This file - quick start guide | - |

---

## Next Steps After Implementation

1. **Update CHANGELOG.md** with FEAT-007 entry
2. **Update docs/system/architecture.md** to mention OpenWebUI as interface option
3. **Update README.md** with OpenWebUI access instructions
4. **Create PR** with conventional commit message
5. **Mark AC.md** entries as complete

---

**Status:** ✅ Ready for Implementation
**Blockers:** None - all decisions made, documentation complete
**Estimated Time:** 4-6 hours for complete implementation and testing
