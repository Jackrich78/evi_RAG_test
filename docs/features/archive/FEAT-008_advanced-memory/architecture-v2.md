# Architecture Decision: OpenWebUI Stateless Multi-Turn Conversations

**Feature:** FEAT-008 - Advanced Memory and Context Management
**Version:** 2.0 (Corrected Approach)
**Date:** 2025-11-03
**Status:** Planned

## Problem Statement

Previous implementation (archived) incorrectly assumed OpenWebUI sent single messages requiring database session management. After 4 hours of research and testing, we discovered **OpenWebUI already sends complete conversation history** in every request's `messages` array. The current implementation ignores this and attempts to recreate history from database, introducing unnecessary complexity and latency.

**Key Finding:** OpenWebUI sends `messages: [{role, content}, ...]` containing ALL previous turns. We just need to extract and convert them.

## Context & Constraints

**Current State:**
- `app/agent/chat_agent.py` receives OpenWebUI requests via OpenAI-compatible endpoint
- Request contains `messages` array with full conversation history
- Current code ignores this and passes empty `message_history=[]` to `agent.run()`
- Database has `sessions` and `messages` tables that duplicate OpenWebUI's memory

**Constraints:**
- Must maintain OpenAI API compatibility (`/v1/chat/completions`)
- Must not break existing functionality
- PydanticAI expects `list[ModelMessage]` (not OpenAI format)
- OpenWebUI handles all session persistence (we're stateless)

**Success Criteria:**
- Agent references previous conversation context
- Zero database queries per request
- <5ms overhead for message conversion
- Compatible with OpenWebUI's message format

## Implementation Options

### Option 1: Pure Stateless (Extract from request.messages) ✅ RECOMMENDED

**Description:**
Extract `messages` array from request, convert to PydanticAI format, pass to agent. Remove database session management entirely.

**Technical Approach:**
```python
# In chat_agent.py endpoint
def convert_openai_to_pydantic_history(messages: list[dict]) -> list[ModelMessage]:
    """Convert OpenAI messages to PydanticAI ModelMessage format.

    Exclude last message (current query), convert previous messages only.
    """
    history = []
    for msg in messages[:-1]:  # Exclude current message
        if msg["role"] == "user":
            history.append(ModelRequest(parts=[msg["content"]]))
        elif msg["role"] == "assistant":
            history.append(ModelResponse(parts=[msg["content"]]))
    return history

# In endpoint handler
message_history = convert_openai_to_pydantic_history(request.messages)
result = await agent.run(query, message_history=message_history)
```

**Pros:**
- Extremely simple (~50 lines of code)
- Zero database latency
- Leverages OpenWebUI's existing memory
- Removes 500+ lines of session management code
- No migration needed (can drop tables)
- Truly stateless (scales horizontally)

**Cons:**
- No CLI support (requires client to send history)
- Cannot reconstruct conversations without client storage
- No server-side conversation persistence

**Effort:** 2-3 hours
**Risk:** Low (backed by verified findings)

**Required Imports:**
```python
# Add to agent/specialist_agent.py
from pydantic_ai.messages import ModelRequest, ModelResponse
from pydantic_ai.messages import UserPromptPart, TextPart
```

**System Message Handling:**
- System messages (role="system") are excluded from `message_history`
- System prompt is handled separately via PydanticAI's agent configuration
- Only user/assistant messages are converted to history
- This prevents duplication of system instructions in the conversation

**Example Full Conversion:**
```python
# OpenWebUI request format
request.messages = [
    {"role": "system", "content": "You are a safety specialist"},  # Excluded
    {"role": "user", "content": "What is PPE?"},
    {"role": "assistant", "content": "PPE stands for..."},
    {"role": "user", "content": "What are the types?"}  # Current query
]

# Converted to PydanticAI format
message_history = [
    ModelRequest(parts=[UserPromptPart(content="What is PPE?")]),
    ModelResponse(parts=[TextPart(content="PPE stands for...")])
]
# Note: Last message excluded (current query), system message filtered out
```

---

### Option 2: Hybrid (OpenWebUI stateless + CLI database fallback)

**Description:**
Detect message source. If `len(messages) > 1`, use stateless extraction. If `X-Session-ID` header present, load from database for CLI compatibility.

**Technical Approach:**
```python
def get_message_history(request, headers):
    if len(request.messages) > 1:
        # OpenWebUI sent history - extract it
        return convert_openai_to_pydantic_history(request.messages)
    elif session_id := headers.get("X-Session-ID"):
        # CLI or custom client - load from database
        return await load_session_history(session_id)
    else:
        # First message or standalone query
        return []
```

**Pros:**
- Supports both OpenWebUI and future CLI tools
- Maintains database for non-OpenWebUI clients
- Flexible for future integrations

**Cons:**
- More complex (~100 lines vs 50)
- Maintains database code we don't currently need
- Unclear if CLI support is needed (no CLI planned)
- Additional testing burden (two code paths)

**Effort:** 5-6 hours
**Risk:** Medium (added complexity for uncertain value)

---

### Option 3: Keep Database Sessions (NOT RECOMMENDED)

**Description:**
Continue storing every message in database, ignore OpenWebUI's provided history. This is the archived approach that was proven incorrect.

**Technical Approach:**
- Parse `messages` array
- Store each message in database
- Load session history from database
- Pass to agent

**Pros:**
- Server-side conversation persistence
- Independent of client capabilities
- Audit trail of all conversations

**Cons:**
- 500+ lines of code to maintain
- Redundant with OpenWebUI's memory
- Database write latency on every request
- Requires migrations and table maintenance
- Based on false assumption (OpenWebUI doesn't need this)
- Already attempted and archived for being wrong

**Effort:** N/A (already attempted)
**Risk:** High (proven incorrect approach)

## Comparison Matrix

| Criterion | Option 1: Stateless | Option 2: Hybrid | Option 3: Database |
|-----------|--------------------|-----------------|--------------------|
| **Feasibility** | ✅ High (proven) | ⚠️ Medium | ❌ Low (wrong model) |
| **Performance** | ✅ Excellent (<5ms) | ⚠️ Good (dual path) | ❌ Poor (DB writes) |
| **Maintainability** | ✅ Simple (50 lines) | ⚠️ Medium (100 lines) | ❌ Complex (500+ lines) |
| **Cost** | ✅ Zero DB queries | ⚠️ Conditional DB | ❌ High DB usage |
| **Complexity** | ✅ Minimal | ⚠️ Moderate | ❌ High |
| **Community** | ✅ Standard pattern | ⚠️ Custom hybrid | ❌ Anti-pattern |
| **Integration** | ✅ OpenWebUI only | ⚠️ OpenWebUI + future | ❌ Redundant |

**Legend:** ✅ Excellent | ⚠️ Acceptable | ❌ Poor

## Decision & Rationale

**Chosen Approach:** Option 1 - Pure Stateless

**Rationale:**
1. **Backed by Evidence:** 4 hours of testing confirmed OpenWebUI sends full history
2. **YAGNI Principle:** No CLI client exists, don't build for hypothetical needs
3. **Simplicity:** 50 lines vs 100+ lines for uncertain future value
4. **Performance:** Zero database overhead, sub-5ms conversion
5. **Correctness:** Aligned with OpenWebUI's actual behavior (not assumptions)

**Trade-offs Accepted:**
- No server-side conversation persistence (OpenWebUI handles this)
- Future CLI would need to send history or we'd add Option 2 later
- Cannot audit conversations server-side (can add logging if needed)

**Why Not Option 2:**
- Adds complexity for feature that doesn't exist (CLI)
- If CLI needed later, we can add it (takes 2-3 hours)
- YAGNI > premature optimization

**Why Not Option 3:**
- Proven incorrect via research findings
- Archived for documented reasons
- Serves as lessons learned documentation

## Validation Plan (Spike)

**Goal:** Confirm stateless extraction works end-to-end in OpenWebUI

**Step 1: Inspect Request Format (30 min)**
- Add logging to `chat_agent.py` endpoint
- Log `request.messages` structure from real OpenWebUI request
- Verify format matches OpenAI spec: `[{role, content}, ...]`
- **Success:** Logs show array with multiple messages on follow-up

**Step 2: Implement Conversion Function (1 hour)**
- Create `convert_openai_to_pydantic_history()` function
- Handle `user` and `assistant` roles
- Skip `system` messages (handled separately)
- Unit test with sample data
- **Success:** Function converts 3-message array to 2 ModelMessages

**Step 3: Integrate with Agent (1 hour)**
- Extract history in endpoint handler
- Pass to `agent.run(message_history=history)`
- Test with OpenWebUI: send follow-up message
- **Success:** Agent response references previous context

**Step 4: Test Edge Cases (30 min)**
- First message (empty history)
- Long conversation (10+ turns)
- Message order preservation
- **Success:** All edge cases handled correctly

**Step 5: Remove Session Code (30 min)**
- Comment out database session writes
- Verify no functionality breaks
- Mark sessions/messages tables for deprecation
- **Success:** System works without database queries

**Total Spike Time:** 3.5 hours
**Success Criteria:** Agent correctly uses conversation context in OpenWebUI follow-up messages with zero database queries

## Migration Impact

**Database Changes:**
- ✅ Can safely drop `sessions` table (redundant)
- ✅ Can safely drop `messages` table (redundant)
- ⚠️ Keep tables initially, deprecate after validation
- No migration needed (pure removal)

**API Changes:**
- ✅ No breaking changes (same endpoint)
- ✅ Request/response format unchanged
- ✅ Fully backward compatible

**Code Removal:**
- Remove `app/db/session_db.py` (~200 lines)
- Remove session management from `chat_agent.py` (~100 lines)
- Simplify endpoint handler (~50 lines → 10 lines)
- **Net:** -340 lines, +50 lines = -290 lines total

## Security Considerations

**Authentication:**
- No change (endpoint auth unchanged)

**Data Privacy:**
- IMPROVED: No conversation storage in our database
- OpenWebUI handles data retention per their policies
- Less data = less privacy risk

**Input Validation:**
- Must validate `messages` array structure
- Sanitize content before conversion
- Handle malformed requests gracefully

## Future Enhancements

**If CLI Support Needed (Post-MVP):**
1. Add `X-Session-ID` header detection
2. Implement database fallback (Option 2)
3. Estimated effort: 2-3 hours

**If Conversation Analytics Needed:**
- Add non-blocking logging to analytics pipeline
- Don't reintroduce blocking database writes
- Use message queues for async processing

**If Multi-Agent Orchestration:**
- Extract conversation graph from history
- Pass to agent orchestrator
- Keep stateless pattern

## References

- **Research Document:** `openwebui-session-findings.md` (verified evidence)
- **OpenWebUI Docs:** [Connections - OpenAI API](https://docs.openwebui.com/tutorial/connections)
- **PydanticAI Docs:** [Message History](https://ai.pydantic.dev/)
- **Archived Attempt:** `docs/archive/FEAT-008_session-management-v1/` (lessons learned)

---

**Decision Confidence:** High (backed by 4 hours of verification testing)
**Implementation Complexity:** Low (50 lines of code)
**Expected ROI:** High (fixes broken feature with minimal effort)
