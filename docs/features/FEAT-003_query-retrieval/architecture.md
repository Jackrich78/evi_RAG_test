# Architecture: FEAT-003 - Specialist Agent with Vector Search

**Feature ID:** FEAT-003
**Status:** Proposed
**Decision Date:** 2025-10-26

---

## Context

EVI 360 needs a Dutch-language RAG system for workplace safety specialists to query 10,833 ingested guideline chunks. The system must prove retrieval accuracy and response quality without over-engineering (no tiers, products, or advanced memory for MVP).

**Technical Challenge:**
- Existing codebase has 90% of needed infrastructure (API, tools, database)
- Need to wire specialist agent to existing search tools
- Must support Dutch language end-to-end (query → search → response)
- CLI expects API server, not direct agent access

**Scope of Decision:**
How to architect the MVP query flow from CLI to database and back.

---

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  CLI (cli.py)                                             │   │
│  │  - Colored terminal output                                │   │
│  │  - aiohttp HTTP client                                    │   │
│  │  - Streaming response handler                             │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────┘
                    │ HTTP POST /chat/stream
                    │ {"message": "Dutch query", "session_id": "..."}
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (agent/api.py)                            │   │
│  │  - Port: 8058 (APP_PORT in .env)                          │   │
│  │  - Lifecycle: DB + Neo4j initialization                   │   │
│  │  - Endpoints: /health, /chat/stream, /search              │   │
│  │  - CORS: Configured for future OpenWebUI                  │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────┘
                    │ Call specialist_agent.run_stream()
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Specialist Agent (agent/specialist_agent.py)             │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  Pydantic AI Agent                                   │ │   │
│  │  │  - Model: GPT-4 (from .env LLM_API_KEY)              │ │   │
│  │  │  - System Prompt: SPECIALIST_SYSTEM_PROMPT (Dutch)   │ │   │
│  │  │  - Result Type: SpecialistResponse                   │ │   │
│  │  │    {content: str, citations: List, metadata: Dict}   │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  @tool: search_guidelines(query, limit=10)           │ │   │
│  │  │  - Wraps hybrid_search_tool                          │ │   │
│  │  │  - Returns: List[Dict] with chunks                   │ │   │
│  │  └────────────┬────────────────────────────────────────┘ │   │
│  └───────────────┼──────────────────────────────────────────┘   │
└─────────────────┼────────────────────────────────────────────────┘
                    │ Call hybrid_search_tool()
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                     TOOLS LAYER                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Search Tools (agent/tools.py)                            │   │
│  │                                                            │   │
│  │  hybrid_search_tool(HybridSearchInput)                    │   │
│  │  ├─ Generate embedding via OpenAI                         │   │
│  │  ├─ Call db_utils.hybrid_search()                         │   │
│  │  └─ Return ChunkResult[]                                  │   │
│  │                                                            │   │
│  │  vector_search_tool(VectorSearchInput)                    │   │
│  │  └─ Pure vector similarity (backup option)                │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────┘
                    │ SQL function calls
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Database Utils (agent/db_utils.py)                       │   │
│  │  - DatabasePool (asyncpg connection pool)                 │   │
│  │  - hybrid_search(embedding, query_text, limit, weight)    │   │
│  │  - vector_search(embedding, limit)                        │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────┘
                    │ SELECT * FROM hybrid_search($1, $2, $3, $4)
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                   POSTGRESQL DATABASE                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tables:                                                   │   │
│  │  - documents (87 rows)                                     │   │
│  │  - chunks (10,833 rows with embeddings)                   │   │
│  │    * tier column exists but NULL (unused for MVP)         │   │
│  │    * embedding vector(1536) indexed with ivfflat          │   │
│  │                                                            │   │
│  │  Functions:                                                │   │
│  │  - hybrid_search(embedding, text, limit, weight)           │   │
│  │    * Combines vector similarity (<=> operator)            │   │
│  │    * With Dutch full-text (to_tsvector('dutch', ...))     │   │
│  │    * Returns top N chunks ranked by combined score        │   │
│  │                                                            │   │
│  │  - match_chunks(embedding, limit)                          │   │
│  │    * Pure vector similarity search                        │   │
│  │    * Fallback option (not used by default)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Query to Response

### Step-by-Step Flow

```
┌────────────────────────────────────────────────────────────────┐
│ 1. User Input (CLI)                                             │
│    User types: "Wat zijn de vereisten voor werken op hoogte?"  │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 2. CLI → API (HTTP POST)                                        │
│    POST http://localhost:8058/chat/stream                       │
│    Body: {                                                      │
│      "message": "Wat zijn de vereisten...",                     │
│      "session_id": null,  # Stateless for MVP                  │
│      "user_id": "cli_user",                                     │
│      "search_type": "hybrid"                                    │
│    }                                                            │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 3. API Endpoint Handler                                         │
│    async def stream_chat(request: ChatRequest):                 │
│      # Initialize specialist agent dependencies                 │
│      deps = SpecialistDeps(                                     │
│        session_id=generate_session_id(),                        │
│        user_id=request.user_id                                  │
│      )                                                          │
│                                                                 │
│      # Run agent with streaming                                │
│      async with specialist_agent.run_stream(                    │
│        request.message, deps=deps                               │
│      ) as result:                                               │
│        async for chunk in result.stream():                      │
│          yield chunk  # SSE stream                              │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 4. Specialist Agent Reasoning                                   │
│    Agent reads system prompt (Dutch guidelines specialist)      │
│    Agent decides: "I need to search for 'werken op hoogte'"    │
│    Agent calls tool: search_guidelines()                        │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 5. Tool Execution: search_guidelines()                          │
│    @specialist_agent.tool                                       │
│    async def search_guidelines(ctx, query, limit=10):           │
│      results = await hybrid_search_tool(                        │
│        HybridSearchInput(                                       │
│          query="werken op hoogte",                              │
│          limit=10,                                              │
│          text_weight=0.3  # 70% vector, 30% text               │
│        )                                                        │
│      )                                                          │
│      return format_results(results)                             │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 6. Hybrid Search Tool: Generate Embedding                       │
│    embedding = await openai.embeddings.create(                  │
│      model="text-embedding-3-small",                            │
│      input="werken op hoogte"                                   │
│    )                                                            │
│    # Returns: [0.123, -0.456, 0.789, ...] (1536 dims)          │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 7. Database Utils: hybrid_search()                              │
│    async def hybrid_search(embedding, query_text, limit):       │
│      embedding_str = '[' + ','.join(map(str, embedding)) + ']' │
│      results = await conn.fetch(                                │
│        "SELECT * FROM hybrid_search($1::vector, $2, $3, $4)",   │
│        embedding_str,                                           │
│        "werken op hoogte",  # For Dutch full-text              │
│        10,  # limit                                             │
│        0.3  # text_weight                                       │
│      )                                                          │
│      return format_chunks(results)                              │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 8. PostgreSQL: hybrid_search() Function                         │
│    WITH vector_results AS (                                     │
│      SELECT *, 1 - (embedding <=> $1) AS vector_sim            │
│      FROM chunks WHERE embedding IS NOT NULL                    │
│    ),                                                           │
│    text_results AS (                                            │
│      SELECT *, ts_rank_cd(                                      │
│        to_tsvector('dutch', content),                           │
│        plainto_tsquery('dutch', $2)                             │
│      ) AS text_sim                                              │
│      FROM chunks                                                │
│      WHERE to_tsvector('dutch', content) @@                     │
│            plainto_tsquery('dutch', $2)                         │
│    )                                                            │
│    SELECT *, (vector_sim * 0.7 + text_sim * 0.3) AS score      │
│    FROM vector_results FULL OUTER JOIN text_results             │
│    ORDER BY score DESC LIMIT $3                                 │
│                                                                 │
│    Returns: Top 10 chunks with content, metadata, scores        │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 9. Tool Returns Results to Agent                                │
│    [                                                            │
│      {                                                          │
│        "content": "Bij werken op hoogte boven 2,5 meter...",   │
│        "score": 0.87,                                           │
│        "document_title": "NVAB Richtlijn: Werken op Hoogte",   │
│        "document_source": "NVAB",                               │
│        "chunk_id": "uuid-123"                                   │
│      },                                                         │
│      { ... 9 more chunks ... }                                  │
│    ]                                                            │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 10. Agent Synthesis (GPT-4)                                     │
│     Agent receives search results + original query              │
│     Agent follows Dutch system prompt:                          │
│       1. Summarize answer (2-3 sentences)                       │
│       2. Cite ≥2 guidelines with quotes                         │
│       3. Provide practical advice                               │
│                                                                 │
│     Agent generates SpecialistResponse:                         │
│       content: "Voor werken op hoogte gelden..."  (Dutch)      │
│       citations: [                                              │
│         {"title": "NVAB: Werken op Hoogte", "source": "NVAB"}, │
│         {"title": "Arbowet Artikel 3", "source": "Arboportaal"}│
│       ]                                                         │
│       metadata: {"chunks_retrieved": 10, "chunks_cited": 2}    │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 11. API Streams Response to CLI                                 │
│     Server-Sent Events (SSE) stream:                            │
│       data: {"type": "text", "content": "Voor werken..."}       │
│       data: {"type": "text", "content": "op hoogte..."}         │
│       data: {"type": "citations", "data": [...]}                │
│       data: {"type": "end"}                                     │
└────────────────┬───────────────────────────────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────────────────────────────┐
│ 12. CLI Displays Formatted Response                             │
│     🤖 Assistant:                                               │
│                                                                 │
│     Voor werken op hoogte gelden strikte veiligheidseisen.     │
│     Vanaf 2,5 meter hoogte is valbeveiliging verplicht...      │
│                                                                 │
│     Relevante richtlijnen:                                      │
│     • NVAB: Werken op Hoogte (NVAB)                            │
│     • Arbowet Artikel 3 (Arboportaal)                          │
│                                                                 │
│     ────────────────────────────────────────                   │
└────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. Specialist Agent (`agent/specialist_agent.py`)

**Responsibilities:**
- Receive Dutch query from API
- Decide when to search (always search first)
- Call `search_guidelines` tool with query
- Synthesize Dutch response from search results
- Format citations with guideline titles and sources
- Return structured SpecialistResponse

**Configuration:**
- Model: GPT-4 (configured via `get_llm_model()` from .env)
- System Prompt: `SPECIALIST_SYSTEM_PROMPT` (Dutch specialist behavior)
- Result Type: `SpecialistResponse` (content + citations + metadata)
- Dependencies: `SpecialistDeps` (session_id, user_id)

**Tool: search_guidelines()**
- **Purpose**: Wrapper around hybrid_search_tool
- **Input**: Dutch query string, limit (default 10)
- **Output**: List of chunks with content, scores, titles, sources
- **Behavior**: Always uses hybrid search (vector + text), no tier filtering

### 2. Search Tools (`agent/tools.py`)

**hybrid_search_tool()**
- **Input**: `HybridSearchInput(query, limit, text_weight)`
- **Process**:
  1. Generate embedding via OpenAI (`text-embedding-3-small`)
  2. Call `db_utils.hybrid_search(embedding, query_text, limit, 0.3)`
  3. Convert database rows to `ChunkResult` Pydantic models
- **Output**: List[ChunkResult]
- **Default Weights**: 70% vector similarity, 30% Dutch full-text

**vector_search_tool()** (backup, not used by default)
- Pure vector similarity search
- No keyword matching component

### 3. Database Utils (`agent/db_utils.py`)

**DatabasePool:**
- Manages asyncpg connection pool (5-20 connections)
- Lifecycle: initialized on API startup, closed on shutdown
- Timeout: 60s for SQL queries

**hybrid_search():**
- **Signature**: `async def hybrid_search(embedding: List[float], query_text: str, limit: int, text_weight: float)`
- **Process**:
  1. Convert embedding to PostgreSQL vector format: `'[0.1,0.2,...]'`
  2. Call SQL function: `SELECT * FROM hybrid_search($1::vector, $2, $3, $4)`
  3. Parse results into dictionaries
- **Returns**: List[Dict] with chunk_id, content, scores, metadata

### 4. PostgreSQL Functions (`sql/evi_schema_additions.sql`)

**hybrid_search() SQL Function:**
```sql
CREATE FUNCTION hybrid_search(
  query_embedding vector(1536),
  query_text TEXT,
  match_count INT DEFAULT 10,
  text_weight FLOAT DEFAULT 0.3
) RETURNS TABLE(...) AS $$
  WITH vector_results AS (
    SELECT *, 1 - (embedding <=> query_embedding) AS vector_sim
    FROM chunks WHERE embedding IS NOT NULL
  ),
  text_results AS (
    SELECT *, ts_rank_cd(
      to_tsvector('dutch', content),
      plainto_tsquery('dutch', query_text)
    ) AS text_sim
    FROM chunks
    WHERE to_tsvector('dutch', content) @@ plainto_tsquery('dutch', query_text)
  )
  SELECT *,
    (vector_sim * (1 - text_weight) + text_sim * text_weight) AS combined_score
  FROM vector_results FULL OUTER JOIN text_results
  ORDER BY combined_score DESC
  LIMIT match_count
$$;
```

**Key Features:**
- Dutch language support: `to_tsvector('dutch', ...)`
- Vector similarity: `<=>` operator (cosine distance)
- Combined ranking: Weighted sum of vector + text scores
- Deduplication: FULL OUTER JOIN ensures no duplicate chunks

### 5. API Server (`agent/api.py`)

**Endpoints:**
- `GET /health`: Health check (DB + Neo4j status)
- `POST /chat/stream`: Streaming chat with specialist agent
- `POST /search`: Direct search endpoint (optional, for debugging)

**Lifecycle:**
- **Startup**: Initialize DB pool, Neo4j client, run health checks
- **Shutdown**: Close DB pool, Neo4j client

**CORS Configuration:**
- Allowed origins: `http://localhost:3000, http://localhost:8058`
- Ready for future OpenWebUI integration

### 6. CLI (`cli.py`)

**Architecture:**
- Thin HTTP client (not embedding agent logic)
- Uses aiohttp for async HTTP requests
- Connects to API on `http://localhost:8058`

**Features:**
- Colored terminal output (ANSI codes)
- Streaming response display (token-by-token)
- Commands: `help`, `health`, `clear`, `exit`
- Session management (session_id persisted across queries in same session)

---

## Configuration

### Environment Variables (.env)

**Required:**
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/evi_rag

# Neo4j (currently unused for MVP)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4jpassword

# OpenAI API
LLM_API_KEY=sk-...                           # GPT-4 for specialist agent
OPENAI_API_KEY=sk-...                        # Embeddings (can be same key)
LLM_MODEL=gpt-4                              # Or gpt-4-turbo
EMBEDDING_MODEL=text-embedding-3-small

# API Server
APP_PORT=8058                                # API listens on this port
APP_HOST=0.0.0.0                             # Bind to all interfaces
APP_ENV=development                          # development | production
LOG_LEVEL=INFO                               # DEBUG | INFO | WARNING | ERROR
```

**Optional:**
```bash
# CORS (for future OpenWebUI)
CORS_ORIGINS=http://localhost:3000,http://localhost:8058

# Search defaults (can be overridden in code)
DEFAULT_SEARCH_LIMIT=10
DEFAULT_TEXT_WEIGHT=0.3
```

### Port Configuration

**CLI Default:** `http://localhost:8058` (hardcoded in cli.py line 34)
**API Default:** Port 8000 (agent/api.py line 61) **BUT** overridden by APP_PORT in .env.example (8058)

**Startup Command:**
```bash
# Option 1: Use .env APP_PORT=8058 (recommended)
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058

# Option 2: Specify port explicitly
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058
```

**CLI Connects To:**
```bash
# CLI expects API at http://localhost:8058
# This is the default in cli.py, can be overridden with --url flag
python3 cli.py --url http://localhost:8058
```

---

## Sequence Diagram

```
User          CLI              API              Agent           Tool          DB
 │             │                │                │               │              │
 │─query────> │                │                │               │              │
 │             │─POST /chat───> │                │               │              │
 │             │                │─run_stream()─> │               │              │
 │             │                │                │─search()────> │              │
 │             │                │                │               │─embed()────> OpenAI
 │             │                │                │               │ <────embedding─────│
 │             │                │                │               │─search()──> │
 │             │                │                │               │             │─SQL hybrid()
 │             │                │                │               │ <─────chunks────────│
 │             │                │                │ <─────results──────│              │
 │             │                │                │─synthesize─> GPT-4 │              │
 │             │                │                │ <─Dutch response──────│              │
 │             │                │ <─SpecialistResponse────│               │              │
 │             │ <─SSE stream─────────│                │               │              │
 │ <─display───│                │                │               │              │
```

---

## Performance Considerations

### Expected Latencies

**Breakdown (3-second target):**
1. Embedding generation: ~200-500ms (OpenAI API call)
2. Database search: ~100-300ms (vector + full-text hybrid)
3. Agent synthesis: ~1-2s (GPT-4 streaming response)
4. Network overhead: ~100-200ms (CLI ↔ API ↔ OpenAI)

**Total:** ~1.5-3 seconds (within target)

### Bottlenecks & Mitigation

**Potential Bottleneck:** OpenAI API latency (embedding + GPT-4)
- **Mitigation**: Use streaming for immediate feedback
- **Future**: Cache embeddings for common queries (not MVP)

**Potential Bottleneck:** Database hybrid search on 10,833 chunks
- **Mitigation**: pgvector ivfflat index already configured
- **Future**: Increase lists parameter if search slows down (currently lists=100)

**Potential Bottleneck:** Full-text search on Dutch content
- **Mitigation**: GIN index on to_tsvector('dutch', content) recommended
- **Action**: Verify index exists (not in current schema)

---

## Security Considerations

### API Authentication

**MVP:** No authentication (local development only)
**Future (FEAT-007):** Add API key or JWT for OpenWebUI

### Input Validation

**CLI → API:** FastAPI Pydantic models validate input
**Agent → Tools:** Pydantic Input models validate parameters
**SQL Injection:** Prevented by parameterized queries ($1, $2, etc.)

### Data Privacy

**Session IDs:** Generated UUIDs, no PII stored
**Guideline Content:** Public workplace safety guidelines (non-sensitive)
**Logs:** Avoid logging full guideline content (only metadata)

---

## Error Handling

### Common Errors & Responses

**Database Connection Failure:**
- **Trigger**: PostgreSQL container down
- **Detection**: API `/health` endpoint returns 500
- **Response**: CLI shows "✗ API is unhealthy"
- **Recovery**: Restart Docker containers

**Embedding API Failure:**
- **Trigger**: OpenAI API key invalid or quota exceeded
- **Detection**: `generate_embedding()` raises exception
- **Response**: Tool returns empty results, agent responds "Kan momenteel niet zoeken"
- **Recovery**: Fix .env LLM_API_KEY, check OpenAI quota

**No Search Results:**
- **Trigger**: Query doesn't match any chunks (unlikely with 10,833 chunks)
- **Detection**: hybrid_search returns empty list
- **Response**: Agent responds "Geen relevante richtlijnen gevonden in de kennisbank"
- **Recovery**: User rephrases query

**Agent Timeout:**
- **Trigger**: GPT-4 takes >60s to respond (very rare)
- **Detection**: Pydantic AI timeout
- **Response**: API returns 504 Gateway Timeout
- **Recovery**: Retry query, check OpenAI status

---

## Testing Strategy

### Unit Tests

**Agent Tests:**
- `test_specialist_search_tool()`: Verify search tool calls hybrid_search
- `test_dutch_output()`: Validate responses are in Dutch
- `test_citation_format()`: Check citations include title + source

**Tool Tests:**
- `test_hybrid_search_tool()`: Mock embedding, verify SQL call
- `test_vector_search_tool()`: Test fallback search method

**Database Tests:**
- `test_hybrid_search_function()`: Direct SQL function call
- `test_dutch_stemming()`: Verify "werken" matches "werk"

### Integration Tests

**End-to-End Flow:**
1. Start API in test mode
2. Send test query via HTTP POST
3. Validate response structure and Dutch content
4. Verify citations include ≥2 guidelines
5. Check response time <3 seconds

**Test Queries:** (See PRD testing section)
- "Wat zijn de vereisten voor werken op hoogte?"
- "Hoe voorkom ik rugklachten bij werknemers?"
- ...10 total queries

### Manual Testing

**Checklist:**
- [ ] API starts without errors
- [ ] CLI connects to API successfully
- [ ] Dutch queries accepted without encoding issues
- [ ] Responses are grammatically correct Dutch
- [ ] Citations include NVAB, STECR, UWV, or Arboportaal sources
- [ ] Response time <3 seconds for 8/10 queries
- [ ] No crashes during 10-query session

---

## Deployment

### Local Development

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Activate venv
source venv_linux/bin/activate

# 3. Start API server
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload

# 4. In separate terminal, run CLI
python3 cli.py
```

### Production (Future)

**Not in scope for MVP**
- Dockerize API server
- Use gunicorn + uvicorn workers
- Add authentication middleware
- Configure CORS for production domains
- Use managed PostgreSQL (not Docker)

---

## Future Enhancements

**Post-MVP features (documented in separate PRDs):**

**FEAT-007: OpenWebUI Integration**
- OpenAI-compatible `/v1/chat/completions` endpoint
- Web UI for non-technical users
- Multi-user session management

**FEAT-008: Advanced Memory**
- Session-based conversation context
- Entity tracking across queries
- Graph-based memory (Neo4j)

**FEAT-009: Tier-Aware Search**
- Enable tier column usage (currently NULL)
- Tier traversal strategy (Tier 1 → 2 → 3)
- Adaptive tier selection based on query complexity

**FEAT-004: Product Catalog**
- Scrape EVI 360 website products
- AI categorization and compliance tagging
- Product recommendation integration with specialist agent

**FEAT-005: Multi-Agent System**
- Separate Research Agent (handles search)
- Specialist Agent calls Research Agent as tool
- Agent-calling-agent pattern for complex workflows

**FEAT-006: Knowledge Graph**
- Populate Neo4j with Graphiti
- Guideline relationship mapping
- Enable graph_search tool in specialist agent

---

## References

**Code:**
- Specialist Agent: `agent/specialist_agent.py` (to be created)
- Search Tools: `agent/tools.py` (existing)
- Database Utils: `agent/db_utils.py` (existing)
- API Server: `agent/api.py` (existing, needs modification)
- CLI: `cli.py` (existing, no changes)

**Documentation:**
- PRD: `docs/features/FEAT-003_query-retrieval/prd.md`
- Implementation Guide: `docs/features/FEAT-003_query-retrieval/implementation-guide.md` (to be created)
- System Architecture: `docs/system/architecture.md`
- Database Schema: `sql/schema.sql`, `sql/evi_schema_additions.sql`

**External:**
- Pydantic AI Docs: https://ai.pydantic.dev
- pgvector Docs: https://github.com/pgvector/pgvector
- PostgreSQL Dutch Text Search: https://www.postgresql.org/docs/current/textsearch-dictionaries.html

---

**Decision Status:** Proposed
**Next Steps:**
1. Review this architecture with team
2. Proceed to implementation-guide.md for code changes
3. Create specialist_agent.py and specialist_prompt.py
4. Modify agent/api.py to register specialist agent
5. Test end-to-end flow with 10 Dutch queries
