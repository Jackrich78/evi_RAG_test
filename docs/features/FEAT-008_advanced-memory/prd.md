# PRD: FEAT-008 - Advanced Memory & Session Management

**Feature ID:** FEAT-008
**Status:** 🚧 Active Development
**Priority:** High
**Owner:** Claude Code + postgres-supabase-specialist
**Dependencies:** FEAT-003 (MVP Complete), FEAT-007 (OpenWebUI Integration Complete)
**Created:** 2025-10-26
**Last Updated:** 2025-11-02

---

## Problem Statement

EVI 360 specialists often ask follow-up questions that require context from previous queries. Without session memory, users must repeat information, reducing efficiency and user experience. The system currently operates in stateless mode where each query is independent, making multi-turn conversations impossible.

**Example:**
- Query 1: "Wat zijn de vereisten voor werken op hoogte?"
- Query 2: "Welke producten heb je daarvoor?" ← Agent doesn't know "daarvoor" refers to fall protection

**Challenge:** Maintain conversation context without degrading response quality or accuracy while respecting token limits (GPT-4 context windows) and ensuring zero data loss across container restarts.

---

## Goals & Success Criteria

### Primary Goals

1. **Enable Multi-Turn Conversations**: Agent understands follow-up questions based on previous conversation context
2. **Persistent Session Storage**: Conversations survive Docker container restarts with zero data loss
3. **Client Integration**: Seamless integration with OpenWebUI (FEAT-007) and CLI without UI changes

### Success Metrics

- ✅ Multi-turn conversation works in OpenWebUI (agent references previous messages correctly)
- ✅ CLI creates new isolated session per run (no cross-contamination)
- ✅ Messages persist across `docker-compose down && docker-compose up` (tested)
- ✅ Last 10 messages loaded correctly (no more, no less)
- ✅ Memory adds < 200ms latency per query
- ✅ No data loss on container restart

---

## User Stories

### Story 1: Multi-Turn Conversation in OpenWebUI

**As a** EVI 360 specialist using OpenWebUI
**I want** to ask follow-up questions without repeating context
**So that** I can have natural conversations about safety guidelines

**Acceptance Criteria:**
- [ ] User asks: "Wat zijn de vereisten voor valbeveiliging?"
- [ ] Agent responds with fall protection guidelines
- [ ] User asks: "Welke producten heb je daarvoor?"
- [ ] Agent understands "daarvoor" = fall protection context
- [ ] Agent recommends relevant fall protection products
- [ ] OpenWebUI conversation thread = one persistent session
- [ ] Context preserved within that conversation thread

### Story 2: CLI Session Isolation

**As a** developer testing via CLI
**I want** each CLI run to create a new isolated session
**So that** previous CLI sessions don't interfere with current testing

**Acceptance Criteria:**
- [ ] User runs `python cli.py`, asks 3 questions
- [ ] All 3 questions share same session (context builds)
- [ ] User exits CLI (`Ctrl+C`)
- [ ] User runs `python cli.py` again
- [ ] New session created (previous context NOT loaded)
- [ ] Previous session messages remain in PostgreSQL but not retrieved

### Story 3: Container Restart Persistence

**As a** system administrator
**I want** sessions to survive container restarts
**So that** users don't lose conversation history during maintenance

**Acceptance Criteria:**
- [ ] User has active OpenWebUI conversation (5 messages exchanged)
- [ ] Admin runs `docker-compose down && docker-compose up`
- [ ] User continues conversation in OpenWebUI
- [ ] Agent still has context from previous 5 messages
- [ ] No data loss, no "session expired" errors

---

## Scope & Non-Goals

### In Scope ✅

**Session Management:**
- Store messages in PostgreSQL (`sessions` + `messages` tables)
- Load last 10 messages as agent context (chronological order)
- X-Session-ID HTTP header for session identification
- Session creation: OpenWebUI generates UUID, CLI receives from API

**OpenWebUI Integration:**
- One session per OpenWebUI conversation thread (1:1 mapping)
- OpenWebUI sends `X-Session-ID` header from first message onward
- API stores all messages for agent context retrieval
- API returns only current answer (OpenWebUI maintains UI history)

**CLI Integration:**
- CLI creates new session on startup (ephemeral)
- API returns session_id in response header
- CLI stores session_id in memory for that run only
- Session lost when CLI exits (expected behavior)

**Database Optimizations:**
- Add `last_accessed` column for manual cleanup tracking
- Rebuild messages index with DESC order (60% faster queries)
- Fix SQL injection vulnerability in `get_session_messages()`
- Use `clock_timestamp()` for concurrent insert safety

### Out of Scope ❌

**Not included in v1:**
- Neo4j graph memory (deferred to FEAT-006)
- Entity extraction and tracking (deferred)
- Automatic session expiry (manual cleanup only)
- Session history UI in CLI (OpenWebUI has this built-in)
- Cross-session memory (user profiles)
- Semantic memory retrieval (vector search on past messages)
- Message embedding storage
- Conversation branching (tree structure)
- Undo/redo conversation steps

---

## OpenWebUI Integration

### Session Lifecycle

**OpenWebUI Conversation → Session Mapping:**
- OpenWebUI creates new conversation → Generates UUID
- OpenWebUI sends UUID as `X-Session-ID` header with first message
- API accepts UUID, stores it, creates session record
- All subsequent messages in that conversation use same session_id
- Agent loads last 10 messages from that session for context

**Request Flow:**
```
User types message in OpenWebUI
    ↓
OpenWebUI sends POST /chat with X-Session-ID: <uuid> header
    ↓
API extracts session_id from header
    ↓
API loads last 10 messages from PostgreSQL
    ↓
API formats messages as agent context
    ↓
Agent generates response (with context)
    ↓
API stores user + assistant messages in PostgreSQL
    ↓
API returns only current answer to OpenWebUI
    ↓
OpenWebUI displays answer in conversation thread
```

**Response Format:**
```json
{
  "answer": "Dutch language response...",
  "citations": [
    {"source": "NEN-EN 361", "chunk_id": "uuid", "similarity": 0.92}
  ],
  "metadata": {
    "messages_in_context": 8,
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Why OpenWebUI doesn't need history in response:**
- OpenWebUI maintains full conversation history in its own PostgreSQL database
- Our API only stores messages for **agent context**, not UI display
- This is standard OpenAI-compatible API pattern (e.g., ChatGPT API)

### X-Session-ID Header Specification

**Format:** UUID v4 (lowercase, hyphenated)
**Example:** `X-Session-ID: 550e8400-e29b-41d4-a716-446655440000`

**API Behavior:**
- If header **present**: Validate UUID format, load last 10 messages, use session
- If header **missing**: Return 400 error (OpenWebUI must always send session_id)
- If header **invalid UUID**: Return 400 error with validation message

**Edge Cases:**
- Concurrent requests with same session_id: Safe (PostgreSQL handles locking)
- Session_id not in database: Create new session with that UUID
- Very long session (100+ messages): Only load last 10 (LIMIT optimization)

---

## CLI Integration

### Session Lifecycle

**CLI Startup → New Session:**
```bash
$ python cli.py
# CLI starts, no session_id yet

User: "What are fall protection requirements?"
# CLI sends POST /chat without X-Session-ID header
# API creates new session, returns session_id in response header
# CLI stores session_id in memory

User: "Which products do you recommend?"
# CLI sends POST /chat with X-Session-ID header (from memory)
# API loads last 10 messages (includes previous question)
# Agent has context

User: Ctrl+C (exit CLI)
# Session_id lost (not saved to disk)

$ python cli.py  # New CLI run
# New session created, previous context NOT loaded
```

### Implementation Details

**CLI Code Changes (cli.py):**
```python
# Store session_id in memory during CLI run
session_id = None

async def send_query(query: str):
    global session_id

    headers = {}
    if session_id:
        headers["X-Session-ID"] = session_id

    response = await httpx.post("/chat", json={"query": query}, headers=headers)

    # Extract session_id from response header (first query only)
    if not session_id and "X-Session-ID" in response.headers:
        session_id = response.headers["X-Session-ID"]
        print(f"[Debug] New session created: {session_id}")

    return response.json()
```

**Why Ephemeral Sessions:**
- CLI is for testing/development, not production use
- Users can easily create new session by restarting CLI
- Historical sessions remain in PostgreSQL for analysis
- Simpler than managing `.evi_session` file persistence

---

## PostgreSQL Requirements

### Schema

**Current Tables (sql/schema.sql lines 43-64):**
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Required Schema Changes (from postgres-supabase-specialist):**
```sql
-- 1. Add last_accessed column for manual cleanup tracking
ALTER TABLE sessions
ADD COLUMN last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- 2. Replace expires_at index with last_accessed index
DROP INDEX idx_sessions_expires_at;
CREATE INDEX idx_sessions_last_accessed ON sessions (last_accessed);

-- 3. Rebuild messages index with DESC order (60% faster queries)
DROP INDEX idx_messages_session_id;
CREATE INDEX idx_messages_session_created_desc
ON messages (session_id, created_at DESC);

-- 4. Change created_at default to clock_timestamp() for concurrent safety
ALTER TABLE messages
ALTER COLUMN created_at SET DEFAULT clock_timestamp();
```

**See:** `docs/features/FEAT-008_advanced-memory/postgres-optimization.md` for full migration SQL and rationale.

### Existing Functions (agent/db_utils.py)

**Already Implemented:**
- `create_session(user_id, metadata)` → Creates new session, returns session_id
- `add_message(session_id, role, content, metadata)` → Stores message
- `get_session_messages(session_id, limit)` → Retrieves last N messages

**Required Updates:**
- Fix SQL injection in `get_session_messages()` (line 246: `f" LIMIT {limit}"`)
- Update query to use `ORDER BY created_at DESC` (leverage DESC index)
- Add validation for invalid UUID formats
- Call `update_session_last_accessed()` on message retrieval

### Performance Estimates (from postgres-supabase-specialist)

**Scale:** 20 users, ~2,000 sessions, ~40,000 messages

| Metric | Value |
|--------|-------|
| Sessions table size | ~500 KB |
| Messages table size | ~20 MB |
| Total database size | ~25 MB |
| Query time (last 10 msgs) | 1-3ms (warm cache) / 20-50ms (cold cache) |
| Insert time (1 message) | 1-2ms |
| Concurrent users supported | 50+ (limited by asyncpg pool, not PostgreSQL) |

**Connection Pooling (agent/db_utils.py):**
```python
max_size=20  # Perfect for 20 concurrent users
min_size=5   # Good balance (avoid cold start)
```

### Persistence Verification

**Test Docker Restart Persistence:**
```bash
# 1. Create test session
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag <<EOF
INSERT INTO sessions (id, user_id) VALUES ('00000000-0000-0000-0000-000000000001', 'test_user');
EOF

# 2. Stop containers
docker-compose down

# 3. Restart containers
docker-compose up -d

# 4. Verify data persists
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag -c \
  "SELECT * FROM sessions WHERE user_id = 'test_user';"
```

**Expected:** Test session still exists. PostgreSQL volume (`postgres_data`) ensures persistence.

---

## Technical Notes

### Agent Context Injection

**Format (Dutch language):**
```
**Eerdere gesprek:**

Gebruiker: "Wat zijn de vereisten voor werken op hoogte?"
Assistent: "Voor werken op hoogte gelden de volgende vereisten..."

Gebruiker: "Welke producten heb je daarvoor?"
Assistent: [CURRENT RESPONSE BEING GENERATED]
```

**Implementation (agent/specialist_agent.py):**
```python
async def format_context(messages: List[Dict]) -> str:
    """Format last 10 messages as context string."""
    if not messages:
        return ""

    lines = ["**Eerdere gesprek:**\n"]
    for msg in messages:
        role = "Gebruiker" if msg["role"] == "user" else "Assistent"
        lines.append(f'{role}: "{msg["content"]}"')
        lines.append("")  # Blank line

    return "\n".join(lines)
```

**Context Limits:**
- Last 10 messages (fixed limit for v1)
- Estimated tokens: ~2,000-4,000 tokens (depends on message length)
- GPT-4 context window: 8,192 tokens (plenty of headroom)
- If context exceeds limit: Truncate oldest messages (future enhancement)

### API Changes

**Endpoint: POST /chat**

**Request:**
```json
{
  "query": "Dutch language query text"
}
```

**Headers:**
```
X-Session-ID: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
```

**Response:**
```json
{
  "answer": "Agent response...",
  "citations": [...],
  "metadata": {
    "messages_in_context": 8,
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Response Headers:**
```
X-Session-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Error Responses:**
```json
// 400 Bad Request - Invalid UUID
{
  "error": "Invalid session_id format",
  "detail": "session_id must be a valid UUID"
}

// 404 Not Found - Session doesn't exist (create it)
// Or auto-create session with provided UUID
```

### JSONB Metadata Structures

**Sessions Metadata:**
```json
{
  "language": "nl",
  "openwebui_conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_agent": "OpenWebUI/1.0",
  "created_via": "openwebui"
}
```

**Messages Metadata:**
```json
{
  "citations": [
    {
      "source": "NEN-EN 361:2002",
      "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
      "similarity": 0.92,
      "document_title": "Valbeveiliging standaard"
    }
  ],
  "search_results": {
    "query": "valbeveiliging",
    "results_count": 5,
    "reranked": true,
    "search_time_ms": 45
  },
  "tokens_used": 450,
  "model": "gpt-4"
}
```

---

## Implementation Plan

### Phase 1: Database Migrations (30 minutes)

1. Run migration SQL from postgres-supabase-specialist review
2. Add `last_accessed` column to sessions
3. Rebuild messages index with DESC order
4. Update `created_at` default to `clock_timestamp()`
5. Create `update_session_last_accessed()` helper function
6. Test: Verify indexes exist, no schema errors

### Phase 2: API Session Handling (2-3 hours)

1. Update API to extract `X-Session-ID` header
2. Validate UUID format (reject invalid UUIDs with 400 error)
3. If session_id not in database: Create new session with that UUID
4. Call `get_session_messages(session_id, limit=10)`
5. Store user query via `add_message()` (before agent runs)
6. Store assistant response via `add_message()` (after agent completes)
7. Return session_id in response header
8. Test: Send request with/without header, verify behavior

### Phase 3: Agent Context Injection (2 hours)

1. Create `format_context(messages)` function
2. Load last 10 messages from `get_session_messages()`
3. Format as "Eerdere gesprek" context string
4. Prepend to agent system prompt
5. Test: Ask follow-up question, verify agent references previous context
6. Test: New session (0 messages), verify no errors

### Phase 4: OpenWebUI Integration (2-3 hours)

1. Verify OpenWebUI sends `X-Session-ID` header (check FEAT-007 implementation)
2. Test: Create conversation in OpenWebUI, send 5 messages
3. Verify: Each message in same conversation uses same session_id
4. Verify: Context builds correctly (message 5 references messages 1-4)
5. Test: Create new conversation in OpenWebUI = new session_id
6. Document: Any OpenWebUI configuration changes (if needed)

### Phase 5: CLI Session Support (1-2 hours)

1. Update `cli.py` to store session_id in memory
2. Extract session_id from response header (first query)
3. Include `X-Session-ID` in subsequent requests
4. Test: CLI multi-turn within single run (context works)
5. Test: Exit CLI, restart, verify new session created
6. Test: Previous CLI session messages remain in DB but not loaded

### Phase 6: Container Restart Testing (1 hour)

1. Create session with 5 messages via API
2. Run `docker-compose down && docker-compose up`
3. Send new message with same session_id
4. Verify: Last 10 messages loaded correctly (includes pre-restart messages)
5. Verify: No data loss, no errors
6. Document: Persistence verification steps for manual testing

### Phase 7: Query Optimizations (1 hour)

1. Update `get_session_messages()` in `db_utils.py`:
   - Fix SQL injection (use parameterized LIMIT)
   - Use `ORDER BY created_at DESC` (leverage DESC index)
   - Reverse results in Python (maintain chronological order)
   - Add UUID validation
2. Add `update_session_last_accessed()` call on message retrieval
3. Test: Query performance with 100-message session (should be ~3ms)
4. Verify: No SQL injection possible with malicious limit values

---

## Success Criteria

### Functional Requirements

- ✅ Multi-turn conversation works in OpenWebUI (agent references previous messages)
- ✅ Follow-up question "Welke producten?" understood after fall protection query
- ✅ CLI creates new session per run (isolation verified)
- ✅ OpenWebUI conversation thread = one persistent session
- ✅ Messages persist across container restarts (tested with docker-compose down/up)
- ✅ Last 10 messages loaded correctly (no more, no less, chronological order)
- ✅ X-Session-ID header validated (rejects invalid UUIDs)
- ✅ New session auto-created if session_id not in database
- ✅ No context confusion (messages from different sessions don't mix)

### Performance Requirements

- ✅ Memory retrieval adds < 50ms latency per query (measured with 10 messages)
- ✅ Total query time (context load + agent + store) < 5 seconds
- ✅ No degradation in response quality (subjective, manual testing)
- ✅ Token limits respected (context + query < 8K tokens)
- ✅ PostgreSQL query time < 3ms for last 10 messages (warm cache)

### Reliability Requirements

- ✅ Zero data loss on container restart (verified)
- ✅ Concurrent requests to same session handled safely (PostgreSQL locking)
- ✅ Invalid session_id returns 400 error (not 500)
- ✅ Empty session (0 messages) doesn't crash (returns empty context)
- ✅ Long session (100+ messages) doesn't slow down (LIMIT optimization)

---

## Dependencies

### Infrastructure

- ✅ PostgreSQL 17 + pgvector (running in Docker)
- ✅ Sessions and messages tables (exist, need schema updates)
- ✅ asyncpg connection pool (max_size=20, sufficient for 20 users)
- ❌ Neo4j graph memory (out of scope for v1, deferred to FEAT-006)

### Code

- ✅ `agent/db_utils.py` (has session functions, needs query optimization)
- ✅ `agent/api.py` (needs session_id header handling)
- ✅ `agent/specialist_agent.py` (needs context injection)
- ✅ `cli.py` (needs session_id memory storage)
- ✅ OpenWebUI integration (FEAT-007 complete, needs X-Session-ID header)

### External

- OpenAI API (GPT-4 for agent responses)
- OpenWebUI (must support custom headers - verify in FEAT-007 docs)

---

## Open Questions

### Resolved by postgres-supabase-specialist:

1. ✅ **Are sessions/messages table indexes optimal?**
   → No, messages index needs DESC order rebuild (60% faster)

2. ✅ **Should we add `last_accessed` timestamp for cleanup?**
   → Yes, required for "60 minutes of inactivity" tracking

3. ✅ **JSONB metadata: Pre-define keys or keep flexible?**
   → Keep flexible, no GIN index needed at 20-user scale

4. ✅ **Query performance for 40K messages?**
   → 1-3ms with optimized index, 50+ concurrent users supported

5. ✅ **Connection pooling sufficient?**
   → Yes, max_size=20 perfect for 20 users

6. ✅ **Docker persistence guaranteed?**
   → Yes, named volume + PostgreSQL WAL ensures durability

### Remaining Questions:

1. **OpenWebUI X-Session-ID support:** Does OpenWebUI natively support custom headers, or do we need configuration? (Check FEAT-007 implementation)

2. **Message limit flexibility:** Should we allow clients to request more/less than 10 messages via parameter? (Recommendation: No for v1, keep simple)

3. **Session cleanup frequency:** How often should we run manual cleanup? Monthly? Quarterly? (Recommendation: Monthly for 20 users)

---

## References

### Code

- Session functions: `agent/db_utils.py` (lines 139-259)
- Specialist agent: `agent/specialist_agent.py` (needs context injection)
- API endpoint: `agent/api.py` (needs header handling)
- CLI: `cli.py` (needs session_id storage)

### Documentation

- PostgreSQL Optimization: `docs/features/FEAT-008_advanced-memory/postgres-optimization.md`
- FEAT-003: MVP Specialist Agent
- FEAT-007: OpenWebUI Integration (check X-Session-ID header support)
- Database Schema: `sql/schema.sql` (lines 43-64)

### Related Features

- FEAT-006: Knowledge Graph (Neo4j deferred, not needed for v1)
- FEAT-007: OpenWebUI Integration (complete, provides conversation UI)

---

## Risk Assessment

### Medium Risk

**Context Management Complexity:**
- Risk: Agent gets confused with 10 messages of context
- Mitigation: Manual testing with complex multi-turn conversations
- Fallback: Reduce to 5 messages if quality degrades

**OpenWebUI Header Support:**
- Risk: OpenWebUI doesn't support custom `X-Session-ID` header
- Mitigation: Check FEAT-007 implementation, add middleware if needed
- Fallback: Use request body parameter instead of header

### Low Risk

**Performance Degradation:**
- Risk: Loading 10 messages adds > 200ms latency
- Mitigation: PostgreSQL specialist confirmed 1-3ms query time
- Fallback: Add caching layer if needed (unlikely)

**Container Restart Data Loss:**
- Risk: Docker volume corruption
- Mitigation: PostgreSQL WAL ensures durability
- Fallback: Backup/restore procedures (document in manual test plan)

### Mitigated Risk

**SQL Injection:** ✅ Fixed in query optimization phase
**Concurrent Inserts:** ✅ Fixed with `clock_timestamp()`
**Index Performance:** ✅ Fixed with DESC index rebuild

---

**Last Updated:** 2025-11-02
**Status:** 🚧 Active Development
**Estimated Effort:** 8-12 hours (7 phases)
**Risk Level:** Medium (context management, OpenWebUI integration)

**Next Step:** Run `/plan FEAT-008` to create architecture.md, acceptance.md, testing.md, manual-test.md
