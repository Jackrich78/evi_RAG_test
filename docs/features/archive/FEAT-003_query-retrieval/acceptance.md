# Acceptance Criteria: FEAT-003 - Specialist Agent with Vector Search

**Feature ID:** FEAT-003
**Created:** 2025-10-29
**Status:** Draft

## Overview

This feature is complete when:
- Specialist agent responds to Dutch safety queries with proper citations
- Response time consistently <3 seconds for 95th percentile
- All 10 test queries pass with ≥2 relevant citations each

## Functional Acceptance Criteria

### AC-FEAT-003-001: Dutch Query Accepted Without Encoding Errors

**Given** CLI is connected to API server
**When** user enters Dutch query with special characters (ë, ï, ü)
**Then** query is accepted without UTF-8 encoding errors and processed correctly

**Validation:**
- [ ] Test query: "Wat zijn de vereisten voor werken op hoogte?"
- [ ] No encoding errors in logs or response
- [ ] Dutch characters preserved in database and response

**Priority:** Must Have

---

### AC-FEAT-003-002: Response in Grammatically Correct Dutch

**Given** specialist agent receives Dutch query
**When** agent generates response
**Then** response is in grammatically correct Dutch (native speaker quality)

**Validation:**
- [ ] No English words mixed in response
- [ ] Proper Dutch grammar (verb conjugation, articles)
- [ ] Informal "je/jij" used (not formal "u")
- [ ] Validated by native speaker or GPT-4 self-check

**Priority:** Must Have

---

### AC-FEAT-003-003: Minimum 2 Citations Per Response

**Given** agent searches guidelines and finds relevant chunks
**When** agent synthesizes response
**Then** response includes ≥2 distinct guideline citations

**Validation:**
- [ ] Response contains at least 2 citations
- [ ] Citations include guideline title
- [ ] Citations include source attribution
- [ ] Citations are relevant to query

**Priority:** Must Have

---

### AC-FEAT-003-004: Hybrid Search Returns Semantically Similar Chunks

**Given** user queries "valbeveiliging" (fall protection)
**When** hybrid search executes
**Then** results include semantically similar terms ("veiligheid hoogte", "valbescherming")

**Validation:**
- [ ] Vector similarity component finds semantic matches
- [ ] Dutch full-text component finds keyword matches
- [ ] Results ranked by combined score (70% vector + 30% text)
- [ ] Top 5 results include ≥3 relevant chunks

**Priority:** Must Have

---

### AC-FEAT-003-005: Citations Include Title and Source

**Given** agent cites guidelines in response
**When** citations are formatted
**Then** each citation shows title (e.g., "NVAB Richtlijn: Werken op Hoogte") and source (NVAB, STECR, UWV, Arboportaal)

**Validation:**
- [ ] Citation format: **[Title]** \n Bron: [Source]
- [ ] Source is one of: NVAB, STECR, UWV, Arboportaal, ARBO
- [ ] Relevant quote or summary included

**Priority:** Must Have

---

### AC-FEAT-003-006: CLI Connects to API in <2 Seconds

**Given** API server is running on port 8058
**When** CLI starts and checks health endpoint
**Then** connection established and health check passes in <2 seconds

**Validation:**
- [ ] Health check response time measured
- [ ] ✓ API is healthy" message displayed
- [ ] Time from CLI start to ready prompt <2s

**Priority:** Must Have

---

### AC-FEAT-003-007: Query Response Time <3 Seconds (95th Percentile)

**Given** 100 test queries submitted
**When** measuring end-to-end response time
**Then** 95th percentile is <3 seconds

**Validation:**
- [ ] Measure time from Enter press to response complete
- [ ] Run 100 queries with varied complexity
- [ ] 95 out of 100 queries complete in <3s
- [ ] Breakdown: embedding (~300ms) + search (~200ms) + synthesis (~2s)

**Priority:** Must Have

---

## Edge Cases & Error Handling

### AC-FEAT-003-101: Empty Query Handling

**Scenario:** User submits empty query

**Given** user enters empty string or whitespace
**When** query is processed
**Then** agent responds with helpful message without crashing

**Validation:**
- [ ] No server crash or exception
- [ ] Response: "Ik heb geen vraag ontvangen. Stel een vraag over arbeidsveiligheid."
- [ ] Logged as INFO level (not ERROR)

**Priority:** Must Have

---

### AC-FEAT-003-102: Nonsense Query Handling

**Scenario:** User submits random characters

**Given** user enters "xyzabc qwerty foobar"
**When** search returns no relevant results
**Then** agent acknowledges gracefully without hallucination

**Validation:**
- [ ] Response acknowledges: "Geen relevante richtlijnen gevonden"
- [ ] No hallucinated guidelines cited
- [ ] Suggests rephrasing or contact support

**Priority:** Must Have

---

### AC-FEAT-003-103: Database Connection Failure

**Scenario:** PostgreSQL container is down

**Given** database connection cannot be established
**When** search tool attempts query
**Then** graceful error message shown to user

**Validation:**
- [ ] Tool returns empty results (not exception)
- [ ] Agent responds: "Kan momenteel niet zoeken in de kennisbank"
- [ ] Error logged with troubleshooting hint
- [ ] CLI doesn't crash

**Priority:** Must Have

---

### AC-FEAT-003-104: OpenAI API Key Invalid

**Scenario:** LLM_API_KEY is incorrect or expired

**Given** OpenAI API call fails with 401 Unauthorized
**When** agent attempts to generate response
**Then** clear error message logged and user notified

**Validation:**
- [ ] Error detected and logged
- [ ] User message: "Service tijdelijk niet beschikbaar"
- [ ] Includes hint to check API key in logs
- [ ] CLI remains responsive (can retry)

**Priority:** Must Have

---

### AC-FEAT-003-105: No Search Results Found

**Scenario:** Query doesn't match any chunks

**Given** search returns 0 results
**When** agent synthesizes response
**Then** agent acknowledges lack of information honestly

**Validation:**
- [ ] Response: "Geen relevante richtlijnen gevonden voor deze vraag"
- [ ] Suggests broader query or different keywords
- [ ] No citations shown (empty list acceptable)

**Priority:** Must Have

---

### AC-FEAT-003-106: Network Timeout

**Scenario:** OpenAI API takes >60 seconds to respond

**Given** API call hangs or times out
**When** timeout threshold exceeded
**Then** request is cancelled and user notified

**Validation:**
- [ ] Timeout set to 60 seconds
- [ ] Request cancelled if exceeded
- [ ] User message: "Verzoek duurde te lang, probeer opnieuw"
- [ ] No zombie processes or hanging connections

**Priority:** Should Have

---

## Non-Functional Requirements

### AC-FEAT-003-201: Performance Consistency

**Requirement:** Response time should not degrade over multiple queries

**Criteria:**
- **First Query:** May be slower (<5s) due to cold start
- **Subsequent Queries:** Consistent <3s response time
- **100 Query Test:** No significant degradation from query 1 to 100

**Validation:**
- [ ] Run 100 sequential queries
- [ ] Plot response times
- [ ] No upward trend in latency
- [ ] Memory usage stable (no leaks)

---

### AC-FEAT-003-202: Concurrent Query Handling

**Requirement:** System handles multiple simultaneous queries

**Criteria:**
- **5 Concurrent Users:** Each query completes <5s
- **Connection Pool:** Database pool manages concurrent connections
- **No Blocking:** Queries don't block each other

**Validation:**
- [ ] Simulate 5 concurrent CLI sessions
- [ ] All queries complete successfully
- [ ] No connection pool exhaustion errors
- [ ] Median response time <4s under load

---

### AC-FEAT-003-203: Dutch Language Quality

**Requirement:** Native Dutch speaker can validate response quality

**Criteria:**
- **Grammar:** No Dutch grammar errors
- **Terminology:** Proper workplace safety terminology
- **Naturalness:** Sounds like native Dutch, not translation
- **Tone:** Informal but professional (je/jij, not u)

**Validation:**
- [ ] Native speaker reviews 10 responses
- [ ] 9/10 rated "good" or "excellent" for grammar
- [ ] 9/10 rated "natural" (not machine-translated feel)
- [ ] No English words (except proper nouns like "NVAB")

---

### AC-FEAT-003-204: No English Language Mixing

**Requirement:** Responses must be pure Dutch

**Criteria:**
- **Response Content:** 100% Dutch
- **Citations:** Dutch titles (original guideline language)
- **Error Messages:** Dutch
- **Only Exception:** Proper nouns, acronyms (NVAB, STECR)

**Validation:**
- [ ] Automated check: no common English words in responses
- [ ] Manual review of 10 responses
- [ ] Exceptions documented (NVAB, PBM, etc.)

---

### AC-FEAT-003-205: API Startup Time <10 Seconds

**Requirement:** API server starts quickly for development iteration

**Criteria:**
- **Cold Start:** <10s from `uvicorn` command to "Application startup complete"
- **Database Init:** Connection pool initialized
- **Health Check:** Passes immediately after startup

**Validation:**
- [ ] Time `uvicorn` startup
- [ ] Health endpoint returns 200 OK within 10s
- [ ] No model loading delays blocking startup

---

### AC-FEAT-003-206: Local-Only Security (No Auth Needed)

**Requirement:** MVP runs locally without authentication

**Criteria:**
- **No Auth:** API endpoints accept all requests
- **Localhost Only:** Bind to 0.0.0.0:8058 (accessible on local network)
- **No Secrets in Code:** API keys in .env file
- **Warning:** Document that this is dev-only security

**Validation:**
- [ ] No authentication middleware in API
- [ ] API accessible from localhost
- [ ] .env file in .gitignore
- [ ] README warns about production security needs

---

### AC-FEAT-003-207: SQL Injection Prevention

**Requirement:** All database queries are parameterized

**Criteria:**
- **Parameterized Queries:** Use $1, $2 placeholders
- **No String Concatenation:** Never build SQL with f-strings
- **ORM/Driver Safety:** asyncpg handles escaping

**Validation:**
- [ ] Code review of db_utils.py
- [ ] All queries use parameterized format
- [ ] Test with malicious input (doesn't execute SQL)

---

## Integration Requirements

### AC-FEAT-003-301: CLI → API Integration

**Requirement:** CLI successfully communicates with API

**Given** API running on port 8058
**When** CLI makes POST request to /chat/stream
**Then** streaming response received and displayed

**Validation:**
- [ ] CLI uses aiohttp for async HTTP
- [ ] POST /chat/stream with JSON body
- [ ] SSE stream parsed correctly
- [ ] Response displayed with formatting

---

### AC-FEAT-003-302: API → Agent Integration

**Requirement:** API invokes specialist agent correctly

**Given** API receives chat request
**When** API calls specialist_agent.run_stream()
**Then** agent executes and returns structured response

**Validation:**
- [ ] API imports specialist_agent successfully
- [ ] SpecialistDeps initialized with session_id
- [ ] run_stream() called with query
- [ ] SpecialistResponse returned

---

### AC-FEAT-003-303: Agent → Database Integration

**Requirement:** Agent retrieves chunks via search tools

**Given** agent calls search_guidelines tool
**When** tool executes hybrid_search
**Then** relevant chunks returned from PostgreSQL

**Validation:**
- [ ] Tool calls db_utils.hybrid_search()
- [ ] Query embedding generated
- [ ] SQL function hybrid_search() executes
- [ ] ChunkResults returned to agent

---

### AC-FEAT-003-304: Streaming Response Delivery

**Requirement:** Responses stream token-by-token to CLI

**Given** agent generates response
**When** API streams via SSE
**Then** CLI displays tokens as they arrive

**Validation:**
- [ ] Pydantic AI run_stream() used
- [ ] API yields SSE data chunks
- [ ] CLI displays incrementally (not buffered)
- [ ] End marker received

---

### AC-FEAT-003-305: Existing Tools Reused

**Requirement:** 90% code reuse from existing codebase

**Given** existing tools.py, db_utils.py, api.py
**When** implementing specialist agent
**Then** reuse hybrid_search_tool and database utilities

**Validation:**
- [ ] specialist_agent.py created (NEW)
- [ ] specialist_prompt.py created (NEW)
- [ ] api.py modified (~50 lines)
- [ ] No changes to db_utils.py, tools.py, models.py
- [ ] Reuse rate: 90%+

---

## Acceptance Checklist

### Development Complete
- [ ] AC-FEAT-003-001 through 007 (Functional)
- [ ] AC-FEAT-003-101 through 106 (Edge Cases)
- [ ] AC-FEAT-003-201 through 207 (Non-Functional)
- [ ] AC-FEAT-003-301 through 305 (Integration)

### Testing Complete
- [ ] Unit tests written (13 stubs implemented)
- [ ] Integration tests passing
- [ ] Manual testing: 10 Dutch queries passed
- [ ] Performance testing: 95th percentile <3s

### Documentation Complete
- [ ] Code documented (docstrings)
- [ ] README updated with usage instructions
- [ ] CHANGELOG updated

### Deployment Ready
- [ ] Code reviewed
- [ ] All tests passing
- [ ] .env.example updated with APP_PORT=8058

---

**Appended to `/AC.md`:** Pending
**Next Steps:** Create testing strategy and manual test guide
