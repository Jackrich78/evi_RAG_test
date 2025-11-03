# Product Requirements Document: OpenWebUI Stateless Multi-Turn Conversations

**Feature ID:** FEAT-008 (Version 2 - Stateless Architecture)
**Status:** Ready for Planning
**Created:** 2025-11-03
**Last Updated:** 2025-11-03

## Problem Statement

The PydanticAI agent requires `message_history` parameter for multi-turn conversations, but our OpenWebUI integration currently ignores the conversation history that OpenWebUI sends with every request. OpenWebUI already handles all session management and sends the complete conversation history in the `messages` array with each request, but we extract only the last user message and treat every request as a new conversation. This breaks multi-turn interactions where users ask follow-up questions expecting context from previous exchanges.

**Impact:** Users cannot have natural conversations in OpenWebUI. Follow-up questions like "What about in English?" or "Tell me more" fail because the agent has no context.

**Root Cause:** Incorrect assumption that we needed server-side session management (PostgreSQL sessions/messages tables), when OpenWebUI already provides full history in every request.

## Goals & Success Criteria

### Primary Goals
1. **Stateless API Design:** API receives history from OpenWebUI, processes it, returns response - no database storage needed
2. **Multi-Turn Conversations:** Agent maintains context across conversation turns using OpenWebUI's message history
3. **Simple Implementation:** ~50 lines of code (message extraction + format conversion + passing to agent)
4. **Zero Breaking Changes:** Existing streaming and non-streaming endpoints continue working

### Success Metrics
- Multi-turn conversations work in OpenWebUI (test with "I hurt my back" → "In English")
- API remains stateless (no session reads/writes during chat)
- Response time unchanged (<5% variance)
- Streaming continues token-by-token without delays

## User Stories

### Story 1: Multi-Turn Follow-Up Questions
**As an** EVI workplace safety specialist using OpenWebUI
**I want** to ask follow-up questions in a conversation
**So that** I can explore topics without repeating context

**Acceptance Criteria:**
- [ ] First message: "Ik heb rugklachten" → Agent responds in Dutch with guidelines
- [ ] Second message: "In English" → Agent translates previous answer maintaining context
- [ ] Third message: "What about lifting?" → Agent understands we're discussing back safety
- [ ] All responses maintain conversation context from OpenWebUI's message history

### Story 2: Stateless API Scalability
**As a** system administrator
**I want** the API to be completely stateless
**So that** I can scale horizontally without session affinity

**Acceptance Criteria:**
- [ ] No database reads/writes for session or message storage during chat
- [ ] API can handle requests on any instance (no session stickiness needed)
- [ ] Multiple parallel conversations work independently
- [ ] Restart API server without losing conversation ability (OpenWebUI maintains state)

### Story 3: Developer Simplicity
**As a** developer maintaining the codebase
**I want** minimal code for conversation support
**So that** the system remains maintainable and debuggable

**Acceptance Criteria:**
- [ ] Message history extraction: ~10 lines
- [ ] Format conversion (OpenAI → PydanticAI): ~20 lines
- [ ] Integration with agent.run(): ~10 lines
- [ ] Total new code: ~50 lines (vs. 500+ in wrong approach)
- [ ] No new database tables or migration scripts

## Scope & Non-Goals

### In Scope
**What this feature WILL include:**
- Extract `request.messages` array from `OpenAIChatRequest` in `/v1/chat/completions` endpoint
- Convert OpenAI message format to PydanticAI `message_history` format
- Pass `message_history` to `agent.run()` and `agent.run_stream()` for context
- Support both streaming and non-streaming modes
- Handle system messages, user messages, and assistant messages from history
- Document the stateless pattern in architecture docs

### Out of Scope (For This Version)
**What this feature will NOT include:**
- CLI tool conversation support (CLI already has session management - different pattern)
- Database sessions/messages tables (REMOVING these - marked for cleanup)
- Cookie-based session tracking (not needed with stateless design)
- X-Session-ID header handling (OpenWebUI doesn't send it to external APIs)
- Message persistence (OpenWebUI's responsibility, not ours)
- Conversation export/import features
- **Reason:** OpenWebUI owns session management; we just need to use the history it provides

## Constraints & Assumptions

### Technical Constraints
1. **PydanticAI API:** Must use `message_history` parameter in `agent.run()` and `agent.run_stream()`
2. **OpenAI Format:** OpenWebUI sends messages as `{"role": "user|assistant|system", "content": "text"}`
3. **Streaming Preservation:** Token-by-token streaming must continue working (FEAT-010)
4. **No Breaking Changes:** Existing endpoints (`/chat`, `/chat/stream`) must remain functional

### Business Constraints
- Implementation time: <4 hours (simple conversion logic)
- No new dependencies required (use existing pydantic-ai)
- Must work with existing OpenWebUI deployment (no OpenWebUI changes)

### Assumptions
1. **OpenWebUI Behavior (Verified):** OpenWebUI sends full conversation history in `messages` array with EVERY request (verified in `openwebui-session-findings.md` lines 100-140)
2. **No Session Headers:** X-Session-ID and chat_id are stripped by OpenWebUI proxy (verified in findings lines 142-184)
3. **Message Order:** Messages are in chronological order: system (if present) → user → assistant → user → assistant → ... → user (latest)
4. **PydanticAI Compatibility:** PydanticAI accepts message_history as list of dicts with "role" and "content" keys (verified in PydanticAI docs)

## Open Questions

**NONE** - All questions answered in `docs/features/FEAT-008_advanced-memory/openwebui-session-findings.md`

Key findings from research document:
- **Lines 1-56:** Executive summary confirms OpenWebUI sends full history, server-side sessions are wrong
- **Lines 59-97:** Official OpenWebUI docs confirm `messages` array contains "complete conversation history"
- **Lines 100-140:** Real log examples show full history in second request of same conversation
- **Lines 142-184:** OpenWebUI proxy strips session_id/chat_id before forwarding to external APIs
- **Lines 186-263:** Correct stateless pattern with code examples

## Technical Implementation Notes

### Message Format Conversion

**Input (OpenWebUI → Our API):**
```python
request.messages = [
    {"role": "user", "content": "I hurt my back"},
    {"role": "assistant", "content": "Rugklachten komen vaak voor..."},
    {"role": "user", "content": "In English"}  # Latest message
]
```

**Output (Our API → PydanticAI):**
```python
message_history = [
    {"role": "user", "content": "I hurt my back"},
    {"role": "assistant", "content": "Rugklachten komen vaak voor..."}
    # Exclude last message - it becomes the current query
]

current_query = "In English"  # Last message in array
```

### Integration Points

**File:** `agent/api.py`

**Function:** `openai_chat_completions()` (lines 677-808)

**Changes Needed:**
1. Extract `request.messages[:-1]` as message_history (all but last)
2. Convert to PydanticAI format (already compatible - just pass as-is)
3. Pass `message_history=message_history` to `run_specialist_query()` and `run_specialist_query_stream()`

**File:** `agent/specialist_agent.py`

**Function:** `run_specialist_query()` and `run_specialist_query_stream()`

**Changes Needed:**
1. Add `message_history: Optional[List[Dict[str, str]]] = None` parameter
2. Pass to `agent.run(query, message_history=message_history, deps=deps)`
3. Pass to `agent.run_stream(query, message_history=message_history, deps=deps)`

### Code Removal (Technical Debt Cleanup)

**Database Tables to Remove:**
- `sessions` table (agent/db_utils.py - lines ~50-100)
- `messages` table (agent/db_utils.py - lines ~100-150)

**Functions to Remove:**
- `create_session()` (agent/db_utils.py)
- `get_session()` (agent/db_utils.py)
- `add_message()` (agent/db_utils.py)
- `get_session_messages()` (agent/db_utils.py)

**Migration:** Create migration to drop sessions and messages tables

**Note:** These are currently used by `/chat` and `/chat/stream` endpoints (legacy CLI endpoints). Decision needed: Remove those endpoints or keep separate session management for CLI?

## Related Context

### Existing Features
- **FEAT-007:** OpenWebUI integration (base OpenAI-compatible endpoints) - This feature extends it with conversation support
- **FEAT-010:** Token-by-token streaming - Must preserve streaming behavior
- **FEAT-003:** Specialist Agent MVP - PydanticAI agent that needs message_history

### Research Documents
- **Primary:** `docs/features/FEAT-008_advanced-memory/openwebui-session-findings.md` - 4 hours of verified research proving stateless approach
- **Archived (Incorrect):** `docs/features/archive/FEAT-008_incorrect_assumptions/` - Previous attempt with sessions (500+ lines, WRONG)

### External References
- [OpenWebUI API Documentation](https://github.com/open-webui/open-webui/discussions/16402) - Confirms stateless design
- [PydanticAI Message History](https://ai.pydantic.dev/message-history/) - How to pass conversation context
- [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat/create) - Message format standard

### Architecture Patterns
**Pattern:** Stateless API with client-managed history (standard for OpenAI-compatible APIs)

**Similar Examples:**
- OpenAI API itself (stateless, history in request)
- Anthropic Claude API (stateless, history in request)
- All serverless LLM APIs (client sends full context)

**Difference from CLI:** CLI tool uses database sessions because terminal has no state between commands. OpenWebUI has state (SQLite), so we stay stateless.

---

**Next Steps:**
1. ~~Researcher agent investigation~~ - **COMPLETE** (findings document has all research)
2. Proceed directly to planning with `/plan FEAT-008`
3. Planner creates architecture.md with stateless pattern
4. Planner creates testing.md with multi-turn conversation tests
5. Implementation phase: ~50 lines of code

**Version 2 Rationale:**
This is version 2 of FEAT-008 planning because version 1 implemented the wrong architecture (server-side sessions). Research document `openwebui-session-findings.md` proves the correct approach is stateless message extraction. Reusing FEAT-008 folder but creating fresh planning documents based on correct understanding.
