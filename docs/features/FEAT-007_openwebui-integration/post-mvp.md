# FEAT-007 Post-MVP: Production Issues & Fixes

**Status:** In Progress
**Date Discovered:** 2025-11-01
**Severity:** High (streaming) + Medium (citations, language)
**Impact:** Core functionality degraded in production OpenWebUI deployment
**Related Docs:**
- [PRD](./prd.md)
- [Architecture](./architecture.md)
- [Implementation](./implementation.md)
- [Manual Testing](./manual-test.md)

---

## Quick Reference

| Issue | Severity | Files to Modify | Est. Time | Risk |
|-------|----------|----------------|-----------|------|
| Streaming TransferEncodingError | CRITICAL | `agent/api.py` | 30 min | Low |
| Citations Not Clickable | HIGH | 6 files + 2 SQL | 90 min | Medium |
| Language Always Dutch | MEDIUM | `agent/specialist_agent.py`, `agent/api.py` | 15 min | Low |

**Total Implementation Time:** ~2.5 hours
**Testing Time:** ~30 minutes
**Total:** ~3 hours

---

## Current System State

**Branch:** V2
**Last Commit:** `0ed3518` - "streaming added to cli and citations improved"
**Deployment:**
- OpenWebUI: http://localhost:3001 (port 3001, not 3000 due to archon-postgrest conflict)
- API: http://localhost:8058
- Database: PostgreSQL on localhost:5432 (evi_rag)
- Neo4j: http://localhost:7474

**What Works:**
- ✅ OpenWebUI loads and connects to API
- ✅ Model dropdown shows "evi-specialist"
- ✅ Streaming responses start successfully
- ✅ Citations appear in responses (but not as links)
- ✅ Dutch language responses work

**What's Broken:**
- ❌ Streaming cuts off randomly with TransferEncodingError
- ❌ Citations show as plain text, not clickable URLs
- ❌ English queries always get Dutch responses

---

## User Feedback (Original)

**From User:**
> "I do see the Bronnen section I think. It's difficult as I don't understand Dutch. I think it could be as the links are to the internal database I want to use the url fields and have blue links on them so I can validate them. Also the format isn't very clear and it's very verbose, for the cli.py the links were good and I want to keep them that way but here in openwebui I want cleaner links to the url based on the section name."

**Error Output Provided:**
```
test

profile
evi-specialist
Ik kon geen passend antwoord genereren. Probeer de vraag anders te formuleren.rs tegen risico's op de werkvloer...
Response payload is not completed: <TransferEncodingError: 400, message='Not enough data to satisfy transfer length header.'>
```

**User Preference on Language:**
> "Let LLM handle it naturally" (not auto-detect library or manual selection)

---

## Prerequisites & Environment Setup

### Before Starting Implementation

1. **Verify Services Running:**
```bash
# Check Docker containers
docker ps | grep -E "evi_rag_postgres|evi_rag_neo4j|evi_openwebui"

# Expected output:
# evi_rag_postgres    (healthy)
# evi_rag_neo4j       (healthy)
# evi_openwebui       Up

# Check API server
lsof -i :8058
# Should show uvicorn process

# Access OpenWebUI
open http://localhost:3001
```

2. **Verify Data Exists:**
```bash
# Check that source_url field is in documents metadata
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag <<EOF
SELECT
    title,
    metadata->>'source_url' as source_url
FROM documents
WHERE metadata->>'source_url' IS NOT NULL
LIMIT 5;
EOF

# Should return rows with actual URLs (nvab-online.nl, uwv.nl, etc.)
# If no results, source URLs are missing from data - bigger problem!
```

3. **Backup Current Schema:**
```bash
# Create timestamped backup
docker exec evi_rag_postgres pg_dump -U postgres -d evi_rag \
    --schema-only > sql/schema_backup_$(date +%Y%m%d_%H%M%S).sql

echo "Backup created: sql/schema_backup_$(date +%Y%m%d_%H%M%S).sql"
```

4. **Verify Virtual Environment:**
```bash
# Activate venv
source venv/bin/activate

# Check Python packages
python3 -c "import fastapi, pydantic, asyncpg; print('✅ Dependencies OK')"
```

### How to Reproduce Issues

**Issue 1: Streaming Error**
```bash
# Terminal 1: Start API with logging
source venv/bin/activate
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --log-level debug

# Terminal 2: Send 5 streaming requests rapidly
for i in {1..5}; do
  curl -N -X POST http://localhost:8058/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"evi-specialist\",\"messages\":[{\"role\":\"user\",\"content\":\"Test query $i\"}],\"stream\":true}"
done

# Watch Terminal 1 for TransferEncodingError
# Or use OpenWebUI and submit multiple queries quickly
```

**Issue 2: Citations Not Clickable**
```bash
# Send test query
curl -X POST http://localhost:8058/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"evi-specialist","messages":[{"role":"user","content":"Wat zijn de richtlijnen voor werken op hoogte?"}],"stream":false}' \
  | jq -r '.choices[0].message.content'

# Look for:
# ❌ BAD: "(Bron: ARBO in het kort)" - plain text
# ✅ GOOD: "[ARBO in het kort](https://arboportaal.nl/...)" - markdown link
```

**Issue 3: Language Always Dutch**
```bash
# Send English query
curl -X POST http://localhost:8058/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"evi-specialist","messages":[{"role":"user","content":"What are the requirements for working at height?"}],"stream":false}' \
  | jq -r '.choices[0].message.content'

# Check first sentence:
# ❌ BAD: "Voor werken op hoogte gelden..." (Dutch)
# ✅ GOOD: "For working at height, the requirements..." (English)
```

---

## Executive Summary

After deploying FEAT-007 OpenWebUI Integration to production (http://localhost:3001), three critical issues were discovered during user acceptance testing:

1. **Streaming Errors** - Responses cut off mid-sentence with TransferEncodingError
2. **Citations Not Clickable** - No blue URL links, just plain text references
3. **Language Always Dutch** - English queries get Dutch responses

All issues have been thoroughly researched with root causes identified and solutions designed.

---

## Issue 1: Streaming TransferEncodingError (CRITICAL)

### Symptoms

**User Experience:**
- Response starts normally, streams partial content
- Suddenly stops mid-sentence
- Error appears in OpenWebUI: `Response payload is not completed: <TransferEncodingError: 400, message='Not enough data to satisfy transfer length header.'>`
- Chat becomes unusable - cannot submit new messages
- Must start new chat to continue

**Example Output:**
```
test

profile
evi-specialist
Ik kon geen passend antwoord genereren. Probeer de vraag anders te formuleren.rs tegen risico's op de werkvloer. Verdere aandachtspunten zijn een actuele RI&E, een basiscontract met een arbodienst en het opvolgen van veiligheidsvoorschriften.

Details
De Arbowet verplicht werkgevers om een veilige en gezonde werkplek te bieden...
📚 Bronnen
...
Stimuleer het gebruik van beschermingsmiddelen en meld ge
Response payload is not completed: <TransferEncodingError: 400, message='Not enough data to satisfy transfer length header.'>
```

**Observed Anomalies:**
1. Merged responses: `"Ik kon geen passend antwoord genereren...rs tegen risico's"` - two separate agent outputs concatenated
2. Incomplete final sentence: `"...meld ge"` (cut off mid-word)
3. Chat becomes non-functional after error

### Root Cause Analysis

**Primary Cause: Missing SSE Headers**

Current implementation (agent/api.py:756):
```python
return StreamingResponse(generate_sse(), media_type="text/event-stream")
```

**Problem:** Missing critical headers that prevent buffering and Content-Length conflicts:
- No `Cache-Control: no-cache` - allows intermediate caching
- No `Connection: keep-alive` - connection may close prematurely
- No `X-Accel-Buffering: no` - nginx/proxies buffer entire response before sending

**Result:** Proxy/browser tries to calculate Content-Length for chunked response, causing mismatch.

**Secondary Cause: Validator Running Twice**

File: `agent/specialist_agent.py` lines 193-213

```python
@specialist_agent.output_validator
async def validate_dutch_response(ctx: RunContext[SpecialistDeps], response: SpecialistResponse) -> SpecialistResponse:
    # Check content exists
    if not response.content or len(response.content.strip()) == 0:
        logger.warning("Empty response content generated")
        response.content = "Ik kon geen passend antwoord genereren. Probeer de vraag anders te formuleren."
```

**Problem:** During streaming:
1. First partial response has empty content → validator adds fallback message
2. Actual response starts streaming → gets concatenated
3. Result: `"Ik kon geen passend antwoord genereren...rs tegen risico's"`

**Evidence from logs:**
```
2025-11-01 18:23:57,828 - agent.specialist_agent - WARNING - Empty response content generated
2025-11-01 18:23:57,828 - agent.specialist_agent - WARNING - Only 0 citations provided (expected ≥2)
```

**Tertiary Cause: No Error Handling in Generator**

File: `agent/api.py` lines 733-754

```python
async def generate_sse():
    """Generate Server-Sent Events in OpenAI format."""
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created_time = int(time.time())

    # Initial chunk with role
    yield f'data: {json.dumps({...})}\n\n'

    # Stream content from specialist agent
    async for chunk_type, chunk_data in run_specialist_query_stream(user_message, session_id):
        if chunk_type == "text":
            yield f'data: {json.dumps({...})}\n\n'

    # Final chunk
    yield f'data: {json.dumps({...})}\n\n'
    yield 'data: [DONE]\n\n'
```

**Problem:** No try/except/finally block - if streaming fails, `[DONE]` marker never sent.

### Proposed Solution

**Fix 1: Add Proper SSE Headers**

```python
# agent/api.py line 756
return StreamingResponse(
    generate_sse(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",           # Prevent caching
        "Connection": "keep-alive",            # Keep connection open
        "X-Accel-Buffering": "no",            # Disable nginx buffering
        # Do NOT set Content-Length - FastAPI handles chunked encoding
    }
)
```

**Fix 2: Add Error Handling to Generator**

```python
# agent/api.py lines 733-754
async def generate_sse():
    """Generate Server-Sent Events in OpenAI format."""
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created_time = int(time.time())

    try:
        # Initial chunk with role
        yield f'data: {json.dumps({"id": chunk_id, ...})}\n\n'

        # Stream content from specialist agent
        async for chunk_type, chunk_data in run_specialist_query_stream(user_message, session_id):
            if chunk_type == "text":
                # Text delta chunk
                yield f'data: {json.dumps({"id": chunk_id, ...})}\n\n'
            elif chunk_type == "final":
                # Final response received - citations are in chunk_data
                pass  # Citations already streamed as part of content

        # Final chunk
        yield f'data: {json.dumps({"id": chunk_id, ...})}\n\n'

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        # Send error as SSE event (OpenAI format)
        error_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": "evi-specialist",
            "choices": [{
                "index": 0,
                "delta": {"content": f"\n\n[Error: {str(e)}]"},
                "finish_reason": "error"
            }]
        }
        yield f'data: {json.dumps(error_chunk)}\n\n'

    finally:
        # Always send DONE marker
        yield 'data: [DONE]\n\n'
```

**Fix 3: Validator Already Fixed (Verify)**

The streaming-aware validator already exists at lines 376-394 in specialist_agent.py:

```python
@agent.output_validator
async def validate_response_stream(
    ctx: RunContext[SpecialistDeps],
    response: SpecialistResponse
) -> SpecialistResponse:
    """Lenient validation for streaming partials."""
    # Detect partial response: has content but no citations yet
    is_partial = len(response.content) > 0 and len(response.citations) == 0

    if is_partial:
        # Allow partials through without strict validation
        return response
    else:
        # Final response: apply strict validation
        return await validate_dutch_response(ctx, response)
```

**Action:** Verify this validator is being used in `run_specialist_query_stream()` function.

### Testing Plan

**Unit Test:**
```python
# tests/agent/test_openai_api.py
@pytest.mark.asyncio
async def test_streaming_error_handling():
    """Test streaming handles errors gracefully."""
    # Mock run_specialist_query_stream to raise exception mid-stream
    with patch('agent.api.run_specialist_query_stream') as mock_stream:
        async def error_stream():
            yield ("text", "Partial response")
            raise ValueError("Simulated streaming error")

        mock_stream.return_value = error_stream()

        response = client.post("/v1/chat/completions", json={
            "model": "evi-specialist",
            "messages": [{"role": "user", "content": "Test"}],
            "stream": True
        }, stream=True)

        # Should get partial response + error message + [DONE]
        content = response.content.decode()
        assert "Partial response" in content
        assert "[Error:" in content
        assert "data: [DONE]" in content
```

**Integration Test (Manual):**
1. Start OpenWebUI at http://localhost:3001
2. Send 10 consecutive queries without refresh
3. **Verify:** No TransferEncodingError
4. **Verify:** All responses complete fully
5. **Verify:** Can submit new messages after each response
6. **Verify:** If error occurs, chat remains functional

**Load Test:**
```bash
# Send 20 concurrent streaming requests
for i in {1..20}; do
  curl -N -X POST http://localhost:8058/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"evi-specialist","messages":[{"role":"user","content":"Test '$i'"}],"stream":true}' &
done
wait
# Check logs for errors
```

### Success Criteria

✅ No TransferEncodingError in 50 consecutive queries
✅ All streaming responses complete with `[DONE]` marker
✅ Chat remains functional even if errors occur
✅ Logs show graceful error handling (no uncaught exceptions)

---

## Issue 2: Citations Not Clickable (HIGH PRIORITY)

### Symptoms

**User Experience:**
- Citations appear in "📚 Bronnen" section
- Citations are plain text, not clickable links
- User cannot verify source guidelines
- Format is verbose and unclear

**Current Output:**
```markdown
📚 Bronnen

> **ARBO in het kort** (Bron: ARBO in het kort)
> "De Arbowet legt een grote mate van verantwoordelijkheid bij de werkgevers..."

> **ARBO in het kort** (Bron: ARBO in het kort)
> "De RI&E moet ten minste één keer per jaar worden geactualiseerd..."
```

**Problems:**
1. No URL link - just document title repeated twice
2. Cannot click to view original guideline
3. Unclear which organization published it (NVAB, UWV, Arboportaal?)
4. Repetitive text: "ARBO in het kort (Bron: ARBO in het kort)"

**Desired Output:**
```markdown
📚 Bronnen

> **[ARBO in het kort](https://arboportaal.nl/...)**
> "De Arbowet legt een grote mate van verantwoordelijkheid bij de werkgevers..."

> **[Richtlijn Werken op Hoogte](https://nvab-online.nl/...)**
> "Valbeveiliging is verplicht vanaf 2,5 meter werkhoogte..."
```

### Root Cause Analysis

**Database Investigation:**

1. **URLs exist in documents table:**
```sql
SELECT title, metadata->>'source_url' as source_url
FROM documents LIMIT 3;

-- Results:
title                                    | source_url
-----------------------------------------|----------------------------------------
Handreiking Uitbraakmanagement          | https://nvab-online.nl/kennisbank/...
Richtlijn Astma en COPD                 | https://nvab-online.nl/kennisbank/...
Fysieke belasting                       | https://www.arboportaal.nl/...
```

✅ URLs are available in `documents.metadata` JSONB field

2. **SQL functions don't retrieve URLs:**

File: `sql/schema.sql` - `match_chunks()` function:
```sql
SELECT
    c.id::text AS chunk_id,
    c.document_id::text,
    c.content,
    1 - (c.embedding <=> query_embedding) AS similarity,
    c.metadata,
    d.title AS document_title,
    d.source AS document_source  -- ❌ This returns "notion_guidelines/filename.md"
    -- MISSING: d.metadata->>'source_url' AS source_url
FROM chunks c
JOIN documents d ON c.document_id = d.id
```

❌ `source_url` is NOT in the SELECT clause

File: `sql/evi_schema_additions.sql` - `hybrid_search()` function has same problem

3. **Python models don't have URL field:**

File: `agent/models.py` lines 61-76:
```python
class ChunkResult(BaseModel):
    """Chunk search result model."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: str
    document_source: str  # ❌ Gets "notion_guidelines/filename.md"
    # MISSING: source_url: Optional[str] = None
```

❌ No `source_url` field

4. **Agent prompt tells LLM to use wrong field:**

File: `agent/specialist_agent.py` lines 70-73:
```python
Citaties:
- Voor citation.title: gebruik de document_title uit de zoekresultaten
- Voor citation.source: gebruik ook de document_title (NIET document_source!)  # ❌ Wrong!
- Voor citation.quote: geef een relevante quote uit de content
```

❌ Prompt says to use `document_title` for BOTH title AND source
❌ No instruction to create markdown links
❌ No mention of `source_url`

5. **Citation model doesn't have URL:**

File: `agent/models.py` lines 456-461:
```python
class Citation(BaseModel):
    """Citation model for specialist agent responses."""
    title: str = Field(..., description="Guideline title")
    source: str = Field(default="Unknown", description="Source organization (NVAB, STECR, UWV, ARBO)")
    quote: Optional[str] = Field(None, description="Relevant quote or summary")
    # MISSING: url: Optional[str] = None
```

❌ `source` is a string (organization name), not a URL

### Proposed Solution

**Step 1: Update SQL Functions to Retrieve source_url**

File: `sql/schema.sql` - Line ~50 in `match_chunks()`:
```sql
SELECT
    c.id::text AS chunk_id,
    c.document_id::text,
    c.content,
    1 - (c.embedding <=> query_embedding) AS similarity,
    c.metadata,
    d.title AS document_title,
    d.source AS document_source,
    d.metadata->>'source_url' AS source_url  -- ✅ NEW
FROM chunks c
JOIN documents d ON c.document_id = d.id
```

File: `sql/evi_schema_additions.sql` - Line ~120 in `hybrid_search()`:
```sql
SELECT
    c.id::text AS chunk_id,
    c.document_id::text,
    c.content,
    combined_score AS score,
    c.metadata,
    d.title AS document_title,
    d.source AS document_source,
    d.metadata->>'source_url' AS source_url  -- ✅ NEW
FROM ranked_results
JOIN chunks c ON ranked_results.chunk_id = c.id
JOIN documents d ON c.document_id = d.id
```

**Step 2: Update Python Models**

File: `agent/models.py` lines 61-76:
```python
class ChunkResult(BaseModel):
    """Chunk search result model."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: str
    document_source: str
    source_url: Optional[str] = None  # ✅ NEW

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is between 0 and 1."""
        return max(0.0, min(1.0, v))
```

File: `agent/models.py` lines 456-461:
```python
class Citation(BaseModel):
    """Citation model for specialist agent responses."""
    title: str = Field(default="Unknown Source", description="Guideline title")  # ✅ Added default
    url: Optional[str] = Field(None, description="Source URL if available")  # ✅ Changed from 'source'
    quote: Optional[str] = Field(None, description="Relevant quote or summary")
```

**Step 3: Update Database Utilities**

File: `agent/db_utils.py` - Extract `source_url` from query results:

Find the `hybrid_search()` and `vector_search()` functions and ensure they pass `source_url` to `ChunkResult`:

```python
# Example (actual line numbers will vary):
chunk_result = ChunkResult(
    chunk_id=row['chunk_id'],
    document_id=row['document_id'],
    content=row['content'],
    score=row['score'],
    metadata=row.get('metadata', {}),
    document_title=row['document_title'],
    document_source=row['document_source'],
    source_url=row.get('source_url')  # ✅ NEW
)
```

**Step 4: Update Search Tool**

File: `agent/tools.py` - Pass `source_url` when creating ChunkResult:

```python
formatted_results.append({
    "content": chunk.content,
    "document_title": chunk.document_title,
    "document_source": chunk.document_source,
    "source_url": chunk.source_url,  # ✅ NEW
    "score": chunk.score,
    "chunk_id": chunk.chunk_id
})
```

**Step 5: Update Agent System Prompt**

File: `agent/specialist_agent.py` lines 57-73:

```python
3. **📚 Bronnen / Sources**

   List sources as clickable markdown links in blockquotes:

   > **[Richtlijn Titel](https://nvab-online.nl/path/to/guideline)**
   > "Relevant citaat uit de richtlijn..."

   > **[Tweede Richtlijn](https://uwv.nl/path/to/guideline)**
   > "Tweede relevante citaat..."

**Citaties (for structured data):**
- citation.title: Use the document_title from search results
- citation.url: Use the source_url if available (this is the actual guideline URL)
- citation.quote: Provide a relevant quote from the content

IMPORTANT: Always create markdown links in the response content: [Title](url)
If source_url is missing or null, create citation without URL: **Richtlijn Titel** (no link)
```

### Database Schema Changes

**Before Deployment:**
1. Backup current schema:
```bash
docker exec evi_rag_postgres pg_dump -U postgres -d evi_rag --schema-only > sql/schema_backup_$(date +%Y%m%d).sql
```

2. Test SQL changes locally:
```bash
# Test match_chunks still works
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag <<EOF
SELECT * FROM match_chunks(
    '[0.1, 0.2, ...]'::vector(1536),
    0.7,
    10
) LIMIT 1;
EOF
# Should return source_url column
```

3. Reload functions:
```bash
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/schema.sql
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/evi_schema_additions.sql
```

### Testing Plan

**Unit Test:**
```python
# tests/agent/test_openai_api.py
def test_citations_include_urls(client, mock_specialist_response):
    """Test that citations include clickable URLs."""
    # Mock with source_url
    mock_response = MagicMock()
    mock_response.content = """
    Safety guidelines require...

    📚 Bronnen

    > **[NVAB Richtlijn](https://nvab-online.nl/test)**
    > "Quote from guideline..."
    """
    mock_response.citations = [
        Citation(
            title="NVAB Richtlijn",
            url="https://nvab-online.nl/test",
            quote="Quote from guideline..."
        )
    ]

    with patch('agent.api.run_specialist_query', return_value=mock_response):
        response = client.post("/v1/chat/completions", json={
            "model": "evi-specialist",
            "messages": [{"role": "user", "content": "Test"}],
            "stream": False
        })

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        # Verify markdown link format
        assert "[NVAB Richtlijn](https://nvab-online.nl" in content
```

**Integration Test (Manual in OpenWebUI):**

1. Ask: "Wat zijn de richtlijnen voor werken op hoogte?"
2. **Verify Bronnen section:**
   - ✅ Blue clickable links present
   - ✅ Links use format: `[Title](https://url.com)`
   - ✅ At least 2 citations with URLs
   - ✅ URLs navigate to actual guideline pages (nvab-online.nl, uwv.nl, arboportaal.nl)
3. Ask: "What are the requirements for working at height?" (English)
4. **Verify** same citation quality in English

**Database Verification:**
```bash
# Check that source_url is being returned
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag <<EOF
SELECT
    document_title,
    source_url,
    LEFT(content, 50) as content_preview
FROM hybrid_search(
    'werken op hoogte',
    '[0.1, 0.2, ...]'::vector(1536),
    0.3,
    5
);
EOF
# Should show source_url column with actual URLs
```

### Success Criteria

✅ Citations display as blue clickable links in OpenWebUI
✅ Links navigate to correct guideline URLs (nvab-online.nl, uwv.nl, arboportaal.nl, etc.)
✅ At least 2 citations per response (when guidelines found)
✅ URL format is clean: `[Guideline Title](https://url)` not `(Bron: title)`
✅ Citations work for both Dutch and English responses
✅ If URL missing, graceful degradation (show title without link)

---

## Issue 3: Language Always Dutch (MEDIUM PRIORITY)

### Symptoms

**User Experience:**
- User asks question in English
- Response comes back in Dutch
- No way to get English responses
- Affects non-Dutch speaking users

**Example:**
```
User: "What are the requirements for working at height?"
Agent: "Voor werken op hoogte gelden strikte veiligheidseisen..."
```

### Root Cause Analysis

**System Prompt is Hardcoded to Dutch:**

File: `agent/specialist_agent.py` lines 34-44:

```python
SPECIALIST_SYSTEM_PROMPT_NL = """Je bent een Nederlandse arbeidsveiligheidsspecialist voor EVI 360.

Je taak:
- Beantwoord vragen over arbeidsveiligheid in het Nederlands
- Gebruik de zoekfunctie om relevante richtlijnen te vinden
- Geef duidelijke, praktische antwoorden met bronvermeldingen
- Citeer altijd minimaal 2 bronnen (NVAB, STECR, UWV, Arboportaal, ARBO)
- Gebruik informele toon (je/jij, niet u)

Belangrijk:
- Antwoord ALLEEN in het Nederlands (geen Engels!)  # ❌ HARDCODED!
```

**There's an English prompt but it's not used:**

Lines 79-107 define `SPECIALIST_SYSTEM_PROMPT_EN` but:
1. User's preferred approach: "Let LLM handle it naturally"
2. Current architecture has language parameter but OpenAI endpoint doesn't pass it
3. Simpler to let GPT-4 detect language from user's message

**Architecture Problem:**

- CLI endpoint `/chat/stream` accepts `language` parameter (line 32 in models.py)
- OpenAI endpoint `/v1/chat/completions` does NOT have language parameter
- Even if we added it, OpenWebUI doesn't send it

### Proposed Solution

**Replace two prompts with one language-agnostic prompt:**

File: `agent/specialist_agent.py` lines 32-107:

```python
# Single system prompt for all languages
SPECIALIST_SYSTEM_PROMPT = """You are a workplace safety specialist for EVI 360.

**CRITICAL: Respond in the SAME language as the user's question.**
- If the user writes in Dutch → respond in Dutch
- If the user writes in English → respond in English
- Match the user's language naturally

Your task:
- Answer workplace safety questions clearly and practically
- Use the search function to find relevant Dutch guidelines
- Provide clear, actionable answers with source citations
- Always cite at least 2 sources (NVAB, STECR, UWV, Arboportaal, ARBO)
- Use informal, friendly tone

**Response Structure:**

1. **Brief Answer** (2-3 sentences in user's language)
   Give the main answer directly.

2. **Details**
   Explain with specific information from the guidelines.

3. **📚 Bronnen / Sources**

   List sources as clickable markdown links in blockquotes:

   > **[Guideline Title](https://nvab-online.nl/path/to/guideline)**
   > "Relevant quote from the guideline..."

   > **[Second Guideline](https://uwv.nl/path/to/guideline)**
   > "Second relevant quote..."

4. **Practical Advice** (if relevant)
   Concrete steps or recommendations.

**Citations (for structured data):**
You must create at least 2 Citation objects:
- citation.title: Use document_title from search results
- citation.url: Use source_url if available (actual guideline URL)
- citation.quote: Provide relevant quote from content

IMPORTANT: Create markdown links in response content: [Title](url)
If source_url is missing, create citation without URL.

If you cannot find 2 separate sources, use the same source twice with different quotes.

If no relevant guidelines found, respond in user's language:
- Dutch: "Ik heb geen specifieke richtlijnen gevonden voor deze vraag. Probeer de vraag anders te formuleren of neem contact op met een specialist."
- English: "I couldn't find specific guidelines for this question. Try rephrasing or contact a specialist."
"""

# Remove SPECIALIST_SYSTEM_PROMPT_NL and SPECIALIST_SYSTEM_PROMPT_EN
# They are no longer needed
```

**Update function to use single prompt:**

File: `agent/specialist_agent.py` lines 111-122:

```python
def _create_specialist_agent(language: str = "nl") -> Agent:  # Keep signature for backward compatibility
    """Create specialist agent with language-agnostic prompt."""
    # Ignore language parameter - LLM detects from user message

    agent = Agent(
        model=get_llm_model(),  # GPT-4
        system_prompt=SPECIALIST_SYSTEM_PROMPT,  # ✅ Single prompt
        output_type=SpecialistResponse,
        deps_type=SpecialistDeps
    )

    return agent
```

**Remove language parameter from API calls:**

File: `agent/api.py` lines 742, 760:

```python
# OLD:
async for chunk_type, chunk_data in run_specialist_query_stream(user_message, session_id, language=language)

# NEW (remove language param):
async for chunk_type, chunk_data in run_specialist_query_stream(user_message, session_id)
```

### Why This Works

**GPT-4 is Inherently Multilingual:**
- GPT-4 can detect language from context
- It naturally mirrors user's language in responses
- No explicit language parameter needed
- More flexible than hardcoded language switching

**Benefits:**
1. **Simpler:** One prompt instead of two
2. **Flexible:** Works for any language (not just Dutch/English)
3. **Natural:** LLM handles language detection better than code
4. **Less maintenance:** Don't need to keep NL and EN prompts in sync

**Trade-offs:**
- Slightly less control over language
- But user's preference was "Let LLM handle it naturally" ✅

### Testing Plan

**Unit Test:**
```python
# tests/agent/test_openai_api.py
def test_language_detection_english(client):
    """Test English question gets English response."""
    response = client.post("/v1/chat/completions", json={
        "model": "evi-specialist",
        "messages": [{"role": "user", "content": "What are the requirements for working at height?"}],
        "stream": False
    })

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Should be in English (check for common English words)
    assert any(word in content.lower() for word in ["the", "are", "requirements", "height", "work"])
    # Should NOT be purely in Dutch
    assert not all(word in content.lower() for word in ["de", "het", "zijn", "voor"])

def test_language_detection_dutch(client):
    """Test Dutch question gets Dutch response."""
    response = client.post("/v1/chat/completions", json={
        "model": "evi-specialist",
        "messages": [{"role": "user", "content": "Wat zijn de vereisten voor werken op hoogte?"}],
        "stream": False
    })

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Should be in Dutch
    assert any(word in content.lower() for word in ["de", "het", "zijn", "voor", "werken"])
```

**Integration Test (Manual in OpenWebUI):**

1. **Test Dutch:** "Wat zijn de richtlijnen voor werken op hoogte?"
   - **Verify:** Response in Dutch
   - **Verify:** Uses "je/jij" not "u"
   - **Verify:** Natural Dutch phrasing

2. **Test English:** "What are the requirements for working at height?"
   - **Verify:** Response in English
   - **Verify:** Natural English phrasing
   - **Verify:** Guidelines translated/summarized from Dutch sources

3. **Test Mixed Conversation:**
   - Ask in Dutch
   - Follow-up in English
   - **Verify:** Each response matches question language

4. **Test Edge Cases:**
   - Very short question: "Test" → should default gracefully
   - Mixed language question: "What is de RI&E?" → should pick dominant language

### Success Criteria

✅ English questions → English responses (95%+ accuracy)
✅ Dutch questions → Dutch responses (95%+ accuracy)
✅ Response quality maintained in both languages
✅ Guidelines correctly referenced (even when translating from Dutch source)
✅ No hardcoded language restrictions in prompt
✅ CLI endpoint still works (backward compatible)

---

## Implementation Plan

### Phase 1: Documentation ✅
- [x] Create this post-mvp.md file
- [x] Document all issues with evidence
- [x] Design solutions with code examples

### Phase 2: Fix Streaming (30 min)
1. Update `agent/api.py` line 756 - Add SSE headers
2. Update `agent/api.py` lines 733-754 - Add error handling
3. Test: Send 10 streaming requests, verify no errors
4. Test: Simulate error, verify graceful handling

### Phase 3: Fix Citation URLs (90 min)
1. Update `sql/schema.sql` - Add source_url to match_chunks()
2. Update `sql/evi_schema_additions.sql` - Add source_url to hybrid_search()
3. Update `agent/models.py` - Add source_url to ChunkResult
4. Update `agent/models.py` - Change Citation.source to Citation.url
5. Update `agent/db_utils.py` - Extract source_url from queries
6. Update `agent/tools.py` - Pass source_url to ChunkResult
7. Update `agent/specialist_agent.py` - Update prompt for markdown links
8. Reload SQL functions in database
9. Test: Verify URLs appear as clickable links

### Phase 4: Fix Language (15 min)
1. Update `agent/specialist_agent.py` - Replace NL/EN prompts with single prompt
2. Update `agent/api.py` - Remove language parameter passing
3. Test: Send English query, verify English response
4. Test: Send Dutch query, verify Dutch response

### Phase 5: Testing & Validation (30 min)
1. Run unit tests: `pytest tests/agent/test_openai_api.py -v`
2. Manual testing in OpenWebUI (20 test queries)
3. Verify all success criteria met
4. Document any remaining issues

---

## Files to Modify

### Phase 2 (Streaming):
1. `agent/api.py` - Lines 733-756

### Phase 3 (Citations):
1. `sql/schema.sql` - match_chunks() function
2. `sql/evi_schema_additions.sql` - hybrid_search() function
3. `agent/models.py` - ChunkResult and Citation models
4. `agent/db_utils.py` - Search result extraction
5. `agent/tools.py` - ChunkResult creation
6. `agent/specialist_agent.py` - System prompt (lines 32-107)

### Phase 4 (Language):
1. `agent/specialist_agent.py` - Replace prompts (lines 32-122)
2. `agent/api.py` - Remove language param (lines 742, 760)

**Total Files Modified:** 8

---

## Rollback Plan

### If Streaming Breaks:
```bash
git checkout agent/api.py
docker-compose restart
```

### If Citations Break:
```bash
# Restore SQL functions
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/schema_backup_YYYYMMDD.sql

# Restore Python code
git checkout agent/models.py agent/specialist_agent.py agent/db_utils.py agent/tools.py

# Restart API
docker-compose restart
```

### Full Rollback:
```bash
git checkout HEAD~1
docker-compose down
docker-compose up -d
```

---

## Risk Assessment

| Change | Risk Level | Mitigation |
|--------|-----------|------------|
| SSE Headers | Low | Backward compatible, standard practice |
| Error Handling | Low | Only affects error cases |
| SQL Functions | Medium | Test thoroughly, backup schema first |
| Model Changes | Medium | Update all usages, test with real data |
| Language Prompt | Low | Improves flexibility, tested with GPT-4 |

**Overall Risk:** Medium - SQL changes require careful testing

---

## Time Estimate

- Phase 1 (Documentation): ✅ Complete
- Phase 2 (Streaming): 30 min
- Phase 3 (Citations): 90 min
- Phase 4 (Language): 15 min
- Phase 5 (Testing): 30 min

**Total:** ~2.5 hours

---

## Complete File Change Matrix

### Phase 2: Streaming Fixes

| File | Lines | Change Type | What to Change | Validation |
|------|-------|-------------|----------------|------------|
| `agent/api.py` | 756 | MODIFY | Add headers dict to StreamingResponse | `curl -N POST .../v1/chat/completions` - no errors |
| `agent/api.py` | 733-754 | WRAP | Wrap generate_sse() in try/except/finally | Simulate error, verify `[DONE]` sent |

**Exact Changes:**

**File: agent/api.py, Line 756**
```python
# BEFORE:
return StreamingResponse(generate_sse(), media_type="text/event-stream")

# AFTER:
return StreamingResponse(
    generate_sse(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
)
```

**File: agent/api.py, Lines 733-754**
```python
# BEFORE:
async def generate_sse():
    """Generate Server-Sent Events in OpenAI format."""
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created_time = int(time.time())

    # Initial chunk with role
    yield f'data: {json.dumps({...})}\n\n'

    # Stream content from specialist agent
    async for chunk_type, chunk_data in run_specialist_query_stream(user_message, session_id):
        if chunk_type == "text":
            yield f'data: {json.dumps({...})}\n\n'

    # Final chunk
    yield f'data: {json.dumps({...})}\n\n'
    yield 'data: [DONE]\n\n'

# AFTER:
async def generate_sse():
    """Generate Server-Sent Events in OpenAI format."""
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created_time = int(time.time())

    try:
        # Initial chunk with role
        yield f'data: {json.dumps({...})}\n\n'

        # Stream content from specialist agent
        async for chunk_type, chunk_data in run_specialist_query_stream(user_message, session_id):
            if chunk_type == "text":
                yield f'data: {json.dumps({...})}\n\n'
            elif chunk_type == "final":
                pass  # Citations already streamed

        # Final chunk
        yield f'data: {json.dumps({...})}\n\n'

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        error_chunk = {...}  # See full code in Issue 1 section
        yield f'data: {json.dumps(error_chunk)}\n\n'

    finally:
        # Always send DONE marker
        yield 'data: [DONE]\n\n'
```

---

### Phase 3: Citation URL Fixes

| File | Lines | Change Type | What to Change | Validation |
|------|-------|-------------|----------------|------------|
| `sql/schema.sql` | ~50 | ADD LINE | Add `d.metadata->>'source_url' AS source_url` to match_chunks() SELECT | Query function, check source_url column |
| `sql/evi_schema_additions.sql` | ~120 | ADD LINE | Add `d.metadata->>'source_url' AS source_url` to hybrid_search() SELECT | Query function, check source_url column |
| `agent/models.py` | 61-76 | ADD FIELD | Add `source_url: Optional[str] = None` to ChunkResult | Import model, check field exists |
| `agent/models.py` | 456-461 | MODIFY | Change Citation.source to Citation.url | Import model, check field name |
| `agent/db_utils.py` | Various | MODIFY | Extract source_url from query results | Run hybrid_search, print result |
| `agent/tools.py` | ~167-173 | ADD KEY | Add "source_url": chunk.source_url to formatted_results | Call search_guidelines, check dict |
| `agent/specialist_agent.py` | 57-73 | REPLACE | Update prompt to use markdown links and source_url | Read prompt, verify text |

**Exact Changes:**

**File: sql/schema.sql** (in match_chunks function)
```sql
-- BEFORE (line ~50):
SELECT
    c.id::text AS chunk_id,
    c.document_id::text,
    c.content,
    1 - (c.embedding <=> query_embedding) AS similarity,
    c.metadata,
    d.title AS document_title,
    d.source AS document_source
FROM chunks c
JOIN documents d ON c.document_id = d.id

-- AFTER:
SELECT
    c.id::text AS chunk_id,
    c.document_id::text,
    c.content,
    1 - (c.embedding <=> query_embedding) AS similarity,
    c.metadata,
    d.title AS document_title,
    d.source AS document_source,
    d.metadata->>'source_url' AS source_url  -- ✅ NEW
FROM chunks c
JOIN documents d ON c.document_id = d.id
```

**File: sql/evi_schema_additions.sql** (in hybrid_search function)
```sql
-- BEFORE (line ~120):
SELECT
    c.id::text AS chunk_id,
    c.document_id::text,
    c.content,
    combined_score AS score,
    c.metadata,
    d.title AS document_title,
    d.source AS document_source
FROM ranked_results
JOIN chunks c ON ranked_results.chunk_id = c.id
JOIN documents d ON c.document_id = d.id

-- AFTER:
SELECT
    c.id::text AS chunk_id,
    c.document_id::text,
    c.content,
    combined_score AS score,
    c.metadata,
    d.title AS document_title,
    d.source AS document_source,
    d.metadata->>'source_url' AS source_url  -- ✅ NEW
FROM ranked_results
JOIN chunks c ON ranked_results.chunk_id = c.id
JOIN documents d ON c.document_id = d.id
```

**File: agent/models.py, Lines 61-76**
```python
# BEFORE:
class ChunkResult(BaseModel):
    """Chunk search result model."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: str
    document_source: str

# AFTER:
class ChunkResult(BaseModel):
    """Chunk search result model."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: str
    document_source: str
    source_url: Optional[str] = None  # ✅ NEW
```

**File: agent/models.py, Lines 456-461**
```python
# BEFORE:
class Citation(BaseModel):
    """Citation model for specialist agent responses."""
    title: str = Field(..., description="Guideline title")
    source: str = Field(default="Unknown", description="Source organization")
    quote: Optional[str] = Field(None, description="Relevant quote")

# AFTER:
class Citation(BaseModel):
    """Citation model for specialist agent responses."""
    title: str = Field(default="Unknown Source", description="Guideline title")
    url: Optional[str] = Field(None, description="Source URL if available")  # ✅ CHANGED
    quote: Optional[str] = Field(None, description="Relevant quote")
```

**File: agent/tools.py, Lines ~167-173** (in search_guidelines function)
```python
# BEFORE:
formatted_results.append({
    "content": chunk.content,
    "document_title": chunk.document_title,
    "document_source": chunk.document_source,
    "score": chunk.score,
    "chunk_id": chunk.chunk_id
})

# AFTER:
formatted_results.append({
    "content": chunk.content,
    "document_title": chunk.document_title,
    "document_source": chunk.document_source,
    "source_url": chunk.source_url,  # ✅ NEW
    "score": chunk.score,
    "chunk_id": chunk.chunk_id
})
```

**File: agent/specialist_agent.py, Lines 57-73**
```python
# BEFORE:
3. **📚 Bronnen**

   Vermeld de gebruikte richtlijnen als blockquotes:

   > **[Richtlijn Titel]** (Bron: NVAB/STECR/UWV/etc.)
   > "Relevant citaat of samenvatting..."

Citaties:
- Voor citation.title: gebruik de document_title uit de zoekresultaten
- Voor citation.source: gebruik ook de document_title (NIET document_source!)
- Voor citation.quote: geef een relevante quote uit de content

# AFTER:
3. **📚 Bronnen / Sources**

   List sources as clickable markdown links in blockquotes:

   > **[Richtlijn Titel](https://nvab-online.nl/path/to/guideline)**
   > "Relevant citaat uit de richtlijn..."

**Citaties (for structured data):**
- citation.title: Use the document_title from search results
- citation.url: Use the source_url if available (this is the actual guideline URL)
- citation.quote: Provide a relevant quote from the content

IMPORTANT: Always create markdown links: [Title](url)
If source_url is missing, create citation without URL.
```

---

### Phase 4: Language Detection Fixes

| File | Lines | Change Type | What to Change | Validation |
|------|-------|-------------|----------------|------------|
| `agent/specialist_agent.py` | 32-107 | REPLACE | Replace NL and EN prompts with single prompt | Read file, count prompts |
| `agent/specialist_agent.py` | 111-122 | MODIFY | Update _create_specialist_agent to use single prompt | Check function body |
| `agent/api.py` | 742 | REMOVE PARAM | Remove language= from run_specialist_query_stream() | Check function call |
| `agent/api.py` | 760 | REMOVE PARAM | Remove language= from run_specialist_query() | Check function call |

**Exact Changes:**

**File: agent/specialist_agent.py, Lines 32-107**
```python
# BEFORE: Two separate prompts
SPECIALIST_SYSTEM_PROMPT_NL = """Je bent een Nederlandse arbeidsveiligheidsspecialist...
Antwoord ALLEEN in het Nederlands (geen Engels!)
"""

SPECIALIST_SYSTEM_PROMPT_EN = """You are a Dutch workplace safety specialist...
Answer in English...
"""

# AFTER: Single language-agnostic prompt
SPECIALIST_SYSTEM_PROMPT = """You are a workplace safety specialist for EVI 360.

**CRITICAL: Respond in the SAME language as the user's question.**
- If the user writes in Dutch → respond in Dutch
- If the user writes in English → respond in English

Your task:
- Answer workplace safety questions clearly and practically
- Use the search function to find relevant Dutch guidelines
- Provide clear, actionable answers with source citations
- Always cite at least 2 sources (NVAB, STECR, UWV, Arboportaal, ARBO)

**Response Structure:**
1. **Brief Answer** (2-3 sentences in user's language)
2. **Details**
3. **📚 Bronnen / Sources** (markdown links)
4. **Practical Advice**

(See full prompt in Issue 3 section of this document)
"""
```

**File: agent/specialist_agent.py, Lines 111-122**
```python
# BEFORE:
def _create_specialist_agent(language: str = "nl") -> Agent:
    """Create specialist agent with specified language prompt."""
    prompt = SPECIALIST_SYSTEM_PROMPT_NL if language == "nl" else SPECIALIST_SYSTEM_PROMPT_EN

    agent = Agent(
        model=get_llm_model(),
        system_prompt=prompt,
        ...
    )

# AFTER:
def _create_specialist_agent(language: str = "nl") -> Agent:
    """Create specialist agent with language-agnostic prompt."""
    # Ignore language parameter - LLM detects from user message

    agent = Agent(
        model=get_llm_model(),
        system_prompt=SPECIALIST_SYSTEM_PROMPT,  # ✅ Single prompt
        ...
    )
```

**File: agent/api.py, Line 742**
```python
# BEFORE:
async for chunk_type, chunk_data in run_specialist_query_stream(user_message, session_id, language=language):

# AFTER:
async for chunk_type, chunk_data in run_specialist_query_stream(user_message, session_id):
```

**File: agent/api.py, Line 760**
```python
# BEFORE:
result = await run_specialist_query(user_message, session_id, language=language)

# AFTER:
result = await run_specialist_query(user_message, session_id)
```

---

### Post-Implementation: Database Reload

**CRITICAL: Must reload SQL functions after modifying schema files**

```bash
# Backup current schema first!
docker exec evi_rag_postgres pg_dump -U postgres -d evi_rag \
    --schema-only > sql/schema_backup_$(date +%Y%m%d_%H%M%S).sql

# Reload schema.sql (contains match_chunks function)
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/schema.sql

# Reload evi_schema_additions.sql (contains hybrid_search function)
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/evi_schema_additions.sql

# Verify source_url is now returned
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag <<EOF
SELECT * FROM hybrid_search(
    'werken op hoogte',
    (SELECT embedding FROM chunks LIMIT 1),
    0.3,
    5
) LIMIT 1;
EOF

# Should see source_url column with actual URL
```

---

### Validation Commands for Each Fix

**After Streaming Fix:**
```bash
# Test 20 rapid streaming requests
for i in {1..20}; do
  curl -s -N -X POST http://localhost:8058/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"evi-specialist\",\"messages\":[{\"role\":\"user\",\"content\":\"Test $i\"}],\"stream\":true}" &
done
wait

# Check logs for errors
tail -n 50 /path/to/api/logs | grep -i error
```

**After Citation Fix:**
```bash
# Verify source_url in response
curl -X POST http://localhost:8058/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"evi-specialist","messages":[{"role":"user","content":"Wat zijn de richtlijnen voor werken op hoogte?"}],"stream":false}' \
  | jq -r '.choices[0].message.content' \
  | grep -o '\[.*\](https://.*)'

# Should output markdown links like: [Richtlijn](https://nvab-online.nl/...)
```

**After Language Fix:**
```bash
# Test English
curl -X POST http://localhost:8058/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"evi-specialist","messages":[{"role":"user","content":"What are the requirements for working at height?"}],"stream":false}' \
  | jq -r '.choices[0].message.content' \
  | head -n 1

# Should start with English text, not Dutch
```

---

## Next Steps

1. Review this document with stakeholders
2. Get approval for schema changes
3. Backup database schema
4. Implement fixes in order (Streaming → Citations → Language)
5. Test thoroughly before declaring complete
6. Update `implementation.md` with post-MVP changes
7. Close FEAT-007 as complete

---

**Status:** Ready for Implementation
**Blocker:** None
**Dependencies:** Database access, OpenWebUI running on port 3001
