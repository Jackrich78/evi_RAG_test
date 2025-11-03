# OpenWebUI Session Management & Memory - Deep Research

**Date:** 2025-11-03
**Status:** CRITICAL FINDINGS - Implementation Needs Restart
**Research Duration:** 4 hours
**Confidence Level:** HIGH (verified through official docs + source code analysis)

---

## Executive Summary

**FINDING: We implemented the WRONG architecture for OpenWebUI session management.**

OpenWebUI **ALREADY SENDS FULL CONVERSATION HISTORY** in the `messages` array with every request. Our server-side session management (PostgreSQL storage, cookie tracking) is **UNNECESSARY and REDUNDANT**.

### The Correct Approach

**OpenWebUI handles memory. Your API should be STATELESS.**

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenWebUI (Port 3001)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ SQLite Database:                                        │ │
│  │  - Stores complete conversation history                │ │
│  │  - Manages chat sessions                               │ │
│  │  - Handles user data                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  Every request to external API includes:                    │
│  {                                                           │
│    "messages": [                                            │
│      {"role": "system", "content": "..."},                 │
│      {"role": "user", "content": "First message"},         │
│      {"role": "assistant", "content": "First response"},   │
│      {"role": "user", "content": "Second message"}  ← NEW  │
│    ]                                                         │
│  }                                                           │
└─────────────────────────────┬───────────────────────────────┘
                              │ POST /v1/chat/completions
                              │ WITH FULL HISTORY
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Your API (Port 8000/8058) - STATELESS          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ✅ CORRECT: Extract ALL messages from request          │ │
│  │ ✅ CORRECT: Pass to PydanticAI message_history         │ │
│  │ ✅ CORRECT: Return ONLY current response               │ │
│  │                                                         │ │
│  │ ❌ WRONG: Store messages in PostgreSQL                 │ │
│  │ ❌ WRONG: Track sessions with cookies                  │ │
│  │ ❌ WRONG: Load "last 10 messages" from DB              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## OpenWebUI Architecture (Official Documentation)

### Source: [OpenWebUI API Documentation](https://github.com/open-webui/open-webui/discussions/16402)
**Verified:** August 8th, 2025 (Main Branch)

### Chat Completions Endpoint: `POST /v1/chat/completions`

**Official Description:**
> "The central compute endpoint accepts OpenAI-style chat requests and intelligently routes them to configured model adapters, **operating statelessly unless clients explicitly associate requests with a chat_id parameter**."

**Key Parameters:**
```json
{
  "model": "required - Model identifier",
  "messages": "required - Complete conversation history as an array",
  "stream": "optional - Boolean for SSE vs JSON",
  "chat_id": "optional - Associates with persistent OpenWebUI session",
  "session_id": "optional - Session identifier"
}
```

### Critical Insight: Messages Array

**From Documentation:**
> "**messages** (required): Complete conversation history as an array of Message objects"

**Confirmed Behavior:**
- OpenWebUI sends **THE ENTIRE CHAT HISTORY** with every request
- Each new message includes ALL previous messages in chronological order
- External APIs receive: `[system_message, user_1, assistant_1, user_2, assistant_2, ..., user_N]`

### Evidence from User Reports

**Source:** [GitHub Discussion #7281](https://github.com/open-webui/open-webui/discussions/7281)
> "Open WebUI sends the whole chat history every time... causing an exponential increase in API usage as the conversation progresses."

**Source:** [GitHub Discussion #4983](https://github.com/open-webui/open-webui/discussions/4983)
> "Open WebUI ignores context length set from chat control or advanced settings under the model and tries to send the whole chat to OpenAI backends."

---

## What OpenWebUI Actually Sends

### Test Case from Our Logs (2025-11-03)

**Request 1 (First Message):**
```
POST /v1/chat/completions
Headers: ['host', 'content-type', 'authorization', 'accept', 'accept-encoding', 'user-agent', 'content-length']
Body: {
  "model": "evi-specialist",
  "messages": [
    {"role": "user", "content": "I hurt my back"}
  ],
  "stream": true
}
```

**Request 2 (Second Message in SAME conversation):**
```
POST /v1/chat/completions
Headers: ['host', 'content-type', 'authorization', 'accept', 'accept-encoding', 'user-agent', 'content-length']
Body: {
  "model": "evi-specialist",
  "messages": [
    {"role": "user", "content": "I hurt my back"},
    {"role": "assistant", "content": "Rugklachten komen vaak voor..."},
    {"role": "user", "content": "In English"}  ← NEW MESSAGE
  ],
  "stream": true
}
```

**CRITICAL OBSERVATION:**
- ❌ NO `X-Session-ID` header
- ❌ NO `session_id` in request body
- ❌ NO `chat_id` in request body
- ❌ NO `Referer` header
- ❌ NO cookies sent
- ✅ **FULL conversation history in `messages` array**

---

## OpenWebUI's Proxy Behavior

### What Gets Stripped

OpenWebUI's proxy (between browser and external API) **strips non-OpenAI-standard fields**:

**Browser → OpenWebUI Proxy:**
```json
{
  "session_id": "QGb_9jCc33jg4k1SAAA9",
  "chat_id": "0270ffb4-c7e3-4bf4-81e8-d588ffc5b273",
  "messages": [...],
  "model": "evi-specialist",
  "stream": true,
  "params": {},
  "variables": {"{{USER_NAME}}": "User"},
  "background_tasks": {"title_generation": true}
}
```

**OpenWebUI Proxy → Your API:**
```json
{
  "model": "evi-specialist",
  "messages": [...],  ← FULL HISTORY PRESERVED
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Stripped:**
- `session_id` (OpenWebUI internal)
- `chat_id` (OpenWebUI internal)
- `params` (OpenWebUI metadata)
- `variables` (template variables)
- `background_tasks` (UI tasks)
- Custom headers (Referer, X-Session-ID)

**Preserved:**
- ✅ `messages` array (WITH FULL HISTORY)
- ✅ OpenAI-standard fields only

---

## The Correct Implementation Pattern

### Stateless API Design (OpenAI Standard)

```python
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    """
    STATELESS ENDPOINT - OpenWebUI sends full history.

    DO NOT:
    - Store messages in database
    - Track sessions with cookies
    - Load "previous context" from anywhere

    DO:
    - Extract messages from request.messages (OpenWebUI sends ALL)
    - Convert to PydanticAI message_history format
    - Pass to agent.run(message_history=...)
    - Return ONLY current response
    """

    # 1. Extract FULL history from request (OpenWebUI already sent it)
    incoming_messages = request.messages  # Already complete history!

    # 2. Convert to PydanticAI format
    message_history = []
    for msg in incoming_messages[:-1]:  # All except last (current query)
        if msg.role == "user":
            message_history.append(ModelRequest([UserPromptPart(content=msg.content)]))
        elif msg.role == "assistant":
            message_history.append(ModelResponse([TextPart(content=msg.content)]))

    # 3. Extract current user query
    current_query = incoming_messages[-1].content

    # 4. Run agent WITH history (PydanticAI handles context)
    result = await agent.run(
        current_query,
        message_history=message_history  # PydanticAI injects context
    )

    # 5. Return ONLY current response (OpenWebUI displays full history in UI)
    return OpenAIChatResponse(
        choices=[OpenAIChatResponseChoice(
            message=OpenAIChatResponseMessage(
                role="assistant",
                content=result.output.content
            )
        )]
    )
```

### Why This Works

1. **OpenWebUI manages persistence**: Stores all messages in its SQLite database
2. **OpenWebUI sends context**: Includes full history with every request
3. **Your API is stateless**: No database, no sessions, no cookies
4. **PydanticAI handles context**: Accepts `message_history` parameter
5. **Response is minimal**: Return only current answer, OpenWebUI displays history

---

## What We Implemented (INCORRECT)

### Our Current Architecture (WRONG)

```python
# ❌ WRONG: Trying to manage sessions OpenWebUI already manages
session_id = extract_from_cookie_or_header()  # OpenWebUI doesn't send!

# ❌ WRONG: Storing messages OpenWebUI already stores
await add_message(session_id, role="user", content=query)

# ❌ WRONG: Loading history OpenWebUI already sent
messages = await get_session_messages(session_id, limit=10)

# ❌ WRONG: Converting stored messages to history
message_history = convert_messages(messages)

# ❌ WRONG: Running agent with our stored history
result = await agent.run(query, message_history=message_history)

# ❌ WRONG: Storing response OpenWebUI already stores
await add_message(session_id, role="assistant", content=result.content)
```

**Problems:**
1. **Redundant storage**: Duplicates OpenWebUI's SQLite database
2. **Cookie workaround**: Hack to track what OpenWebUI already tracks
3. **Lost context**: Loads "last 10" when OpenWebUI sends FULL history
4. **Stateful API**: Violates OpenAI API standards
5. **Complexity**: 200+ lines for session management that's unnecessary

---

## Official OpenWebUI Documentation

### Key Resources

1. **API Reference** (Comprehensive)
   - URL: https://github.com/open-webui/open-webui/discussions/16402
   - Status: Current as of August 8th, 2025
   - Content: Complete API documentation including chat completions

2. **Backend-Controlled Flow Tutorial**
   - URL: https://docs.openwebui.com/tutorials/integrations/backend-controlled-ui-compatible-flow/
   - Status: Verified for v0.6.15
   - Content: 7-step server-side orchestration pattern

3. **Chat System Architecture**
   - URL: https://deepwiki.com/open-webui/open-webui/3-chat-system
   - Content: Internal architecture, message handling, storage

4. **Context Length Discussions**
   - URL: https://github.com/open-webui/open-webui/discussions/4983
   - Finding: "OpenWebUI sends whole chat history every time"
   - URL: https://github.com/open-webui/open-webui/discussions/7281
   - Finding: "Exponential API usage increase from full history"

---

## Session Management Options (Advanced)

### Option 1: Stateless (RECOMMENDED for External APIs)

**Use Case:** External OpenAI-compatible APIs (like ours)

**How it works:**
- OpenWebUI manages all state in its SQLite database
- Your API receives full history in `messages` array
- Your API is completely stateless

**Pros:**
- Simple implementation
- OpenAI-standard compliant
- No database required
- Scales horizontally

**Cons:**
- Cannot persist data server-side
- Token usage increases with conversation length
- No server-side conversation analytics

**Example:** Our EVI 360 API (should be stateless)

---

### Option 2: Backend-Controlled (Advanced)

**Use Case:** When you need server-side orchestration

**How it works:**
```
1. Browser → OpenWebUI: User sends message
2. OpenWebUI → Your API: POST /api/chat/completions with chat_id
3. Your API → OpenWebUI: GET /api/chats/{chat_id} to fetch history
4. Your API: Process with full context
5. Your API → OpenWebUI: POST /api/chats/{chat_id} to update
6. Your API → OpenWebUI: POST /api/chat/completed to finalize
7. Your API → Browser: Stream response through OpenWebUI
```

**Requires:**
- OpenWebUI API access (not just /v1/chat/completions)
- Authentication token
- Chat ID parameter in request
- POST-back to OpenWebUI endpoints

**Source:** https://docs.openwebui.com/tutorials/integrations/backend-controlled-ui-compatible-flow/

**When to use:**
- Need to modify conversation history server-side
- Require server-side title generation
- Need access to OpenWebUI's knowledge base
- Want server-side conversation analytics

---

### Option 3: Hybrid (Our Mistake)

**What we tried:**
- Accept OpenWebUI's stateless requests
- Try to add statefulness with cookies/headers
- Store messages in our own database

**Why it failed:**
- OpenWebUI strips custom headers/fields
- Cookie workaround is non-standard
- Duplicates what OpenWebUI already does
- Violates principle of single source of truth

**Conclusion:** Don't do this. Choose Option 1 OR Option 2, not both.

---

## Recommended Architecture Changes

### COMPLETE ROLLBACK Required

**Reason:** The entire FEAT-008 implementation is based on incorrect assumptions about OpenWebUI's behavior.

### Step 1: Git Rollback to FEAT-007 State

```bash
# Find commit before FEAT-008 started
git log --oneline | grep "FEAT-007\|FEAT-008"

# Rollback to last FEAT-007 commit
git revert <commit-hash> --no-commit

# Or use git reset if commits aren't pushed
git reset --hard <last-feat-007-commit>
```

### Step 2: What to Keep from FEAT-008

**Database Infrastructure (Keep):**
- ✅ PostgreSQL `sessions` table (for future CLI usage)
- ✅ PostgreSQL `messages` table (for future CLI usage)
- ✅ `agent/db_utils.py` session functions (for CLI)
- ✅ Migration files in `sql/` (document as "CLI-only")

**Reason:** These will be needed for CLI/direct API usage, just not for OpenWebUI.

**Code to Remove (Rollback):**
- ❌ ALL session extraction logic in `agent/api.py` (lines 736-815)
- ❌ Cookie-based session tracking (lines 780-784, 904-912, 967-975)
- ❌ `add_message()` calls before/after agent runs
- ❌ `get_session_messages()` calls in endpoint
- ❌ Debug logging for session extraction (lines 744-756)
- ❌ Session validation and auto-creation logic
- ❌ X-Session-ID header handling

**Documentation to Keep:**
- ✅ This research document (critical for rebuild)
- ✅ FEAT-008 PRD (will be updated, not deleted)
- ✅ FEAT-008 architecture doc (will be completely rewritten)

### The Two Valid Patterns

#### Pattern 1: OpenWebUI (Stateless) - PRIMARY USE CASE

**When:** `len(request.messages) > 1`

**Implementation:**
```python
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    # OpenWebUI sends full history in messages array
    if len(request.messages) > 1:
        # STATELESS: Extract history from request
        message_history = convert_openai_to_pydantic(request.messages[:-1])
        current_query = request.messages[-1].content

        logger.info(f"OpenWebUI pattern: {len(message_history)} messages from request")

        result = await agent.run(current_query, message_history=message_history)

        # NO database storage
        # NO session tracking
        # Return ONLY current response
        return OpenAIChatResponse(...)
```

**Characteristics:**
- ✅ Zero database queries (no latency overhead)
- ✅ Stateless (follows OpenAI standard)
- ✅ Simple implementation (~20 lines)
- ✅ OpenWebUI handles ALL persistence

---

#### Pattern 2: CLI/Direct API (Stateful) - SECONDARY USE CASE

**When:** `len(request.messages) == 1` AND `X-Session-ID` header present

**Implementation:**
```python
    else:
        # CLI pattern: Single message + session header
        current_query = request.messages[0].content

        session_id = request.headers.get("X-Session-ID")
        if session_id:
            # STATEFUL: Load from PostgreSQL
            messages = await get_session_messages(session_id, limit=10)
            message_history = convert_db_to_pydantic(messages)

            logger.info(f"CLI pattern: {len(message_history)} messages from DB")
        else:
            # New session
            session_id = await create_session(user_id="cli_user")
            message_history = []

            logger.info("CLI pattern: New session created")

        # Store user message
        await add_message(session_id, role="user", content=current_query)

        result = await agent.run(current_query, message_history=message_history)

        # Store assistant message
        await add_message(session_id, role="assistant", content=result.content)

        return OpenAIChatResponse(..., headers={"X-Session-ID": session_id})
```

**Characteristics:**
- ✅ Session persistence across CLI runs
- ✅ Works without OpenWebUI's UI
- ✅ Supports direct API testing
- ⚠️ Adds ~30-50ms latency (database queries)

---

### Pattern Detection Logic

```python
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    # Detect which pattern to use
    if len(request.messages) > 1:
        # OpenWebUI: Full history in request
        return await handle_stateless_request(request)
    elif "X-Session-ID" in request.headers or "x-session-id" in request.headers:
        # CLI: Session-based
        return await handle_stateful_request(request)
    else:
        # New conversation (no history)
        return await handle_new_conversation(request)
```

**Why This Works:**
- OpenWebUI ALWAYS sends full history (>1 message after first turn)
- CLI ALWAYS sends single message + session header
- Pattern detection is reliable and automatic

---

## FEAT-008 Rebuild Plan

### Prerequisites for Rebuild

1. **Read this entire document first** - Understanding OpenWebUI's behavior is critical
2. **Rollback all FEAT-008 code** - Start from clean FEAT-007 state
3. **Update PRD and architecture docs** - Reflect correct OpenWebUI pattern
4. **Test with debug logging** - Verify OpenWebUI sends full history

### Phase 1: Implement Stateless Pattern (OpenWebUI)

**Estimated Time:** 3-4 hours

**Files to Modify:**
- `agent/api.py` (lines 676-800)
- `agent/specialist_agent.py` (add conversion function)

**Implementation Steps:**

1. **Add message history conversion function** (30 mins)
   ```python
   # agent/specialist_agent.py
   def convert_openai_to_pydantic_history(messages: List[OpenAIChatMessage]) -> List[ModelMessage]:
       """Convert OpenAI messages to PydanticAI format (excluding system and last message)"""
       history = []
       for msg in messages[:-1]:  # Exclude last (current query)
           if msg.role == "system":
               continue
           elif msg.role == "user":
               history.append(ModelRequest([UserPromptPart(content=msg.content)]))
           elif msg.role == "assistant":
               history.append(ModelResponse([TextPart(content=msg.content)]))
       return history
   ```

2. **Update API endpoint to detect pattern** (1 hour)
   ```python
   # agent/api.py in openai_chat_completions()

   # Extract current query
   current_query = request.messages[-1].content

   # Detect OpenWebUI pattern (sends full history)
   if len(request.messages) > 1:
       # STATELESS: Extract from request
       message_history = convert_openai_to_pydantic_history(request.messages)
       logger.info(f"OpenWebUI: {len(message_history)} messages from request")
   else:
       # STATELESS: No history yet (first message)
       message_history = []
       logger.info("New conversation (no history)")
   ```

3. **Pass to agent** (30 mins)
   ```python
   # Run agent with history
   result = await run_specialist_query(current_query, message_history=message_history)
   # OR for streaming:
   # async for chunk in run_specialist_query_stream(current_query, message_history=message_history):
   ```

4. **Update specialist_agent.py** (1 hour)
   ```python
   async def run_specialist_query(
       query: str,
       message_history: Optional[List[ModelMessage]] = None,
       session_id: Optional[str] = None
   ):
       if message_history is None:
           message_history = []

       # Pass to agent
       result = await agent.run(query, message_history=message_history, deps=deps)
   ```

5. **Test with OpenWebUI** (1 hour)
   - Send message 1: "I hurt my back"
   - Check logs: `"New conversation (no history)"`
   - Send message 2: "What products help?"
   - Check logs: `"OpenWebUI: 2 messages from request"`
   - Verify agent response references back injury

**Success Criteria:**
- ✅ Logs show "OpenWebUI: N messages from request"
- ✅ Agent references previous messages in response
- ✅ No database queries (stateless)
- ✅ Response time same as before (~2-3s total)

---

### Phase 2: Add Stateful Pattern (CLI) [OPTIONAL]

**Estimated Time:** 4-5 hours

**Only implement if CLI/direct API usage is required**

**Files to Modify:**
- `agent/api.py` (add X-Session-ID header handling)
- `agent/db_utils.py` (already exists, just use it)

**Implementation:**
```python
# In openai_chat_completions()
elif "X-Session-ID" in request.headers:
    # STATEFUL: CLI pattern
    session_id = request.headers["X-Session-ID"]

    # Load from PostgreSQL
    messages = await get_session_messages(session_id, limit=10)
    message_history = convert_db_to_pydantic(messages)

    # Store user message
    await add_message(session_id, role="user", content=current_query)

    # Run agent
    result = await run_specialist_query(current_query, message_history=message_history)

    # Store assistant message
    await add_message(session_id, role="assistant", content=result.content)

    # Return with session header
    return Response(..., headers={"X-Session-ID": session_id})
```

**Decision Point:**
- If you DON'T have a CLI tool → Skip Phase 2 entirely
- If you DO have a CLI tool → Implement Phase 2 after Phase 1 works

---

### Testing Strategy

**Test Case 1: OpenWebUI Multi-Turn**
```
1. Start new conversation in OpenWebUI
2. Message 1: "Wat zijn de vereisten voor werken op hoogte?"
3. Check logs: "New conversation (no history)"
4. Message 2: "Welke producten heb je daarvoor?"
5. Check logs: "OpenWebUI: 2 messages from request"
6. Verify: Agent response mentions "werken op hoogte" from message 1
```

**Test Case 2: Long Conversation**
```
1. Send 5 messages in OpenWebUI
2. Check logs for message 5: "OpenWebUI: 8 messages from request"
   (user1, assistant1, user2, assistant2, user3, assistant3, user4, assistant4)
3. Verify: Agent still has context from message 1
```

**Test Case 3: New Conversation**
```
1. Create NEW conversation in OpenWebUI
2. Message 1: "Test"
3. Check logs: "New conversation (no history)"
4. Verify: No errors, clean start
```

---

## PydanticAI Message History Format

### Required Structure

```python
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart

message_history: List[ModelMessage] = [
    ModelRequest([UserPromptPart(content="First user message")]),
    ModelResponse([TextPart(content="First assistant response")]),
    ModelRequest([UserPromptPart(content="Second user message")]),
    ModelResponse([TextPart(content="Second assistant response")]),
    # ... continues chronologically
]

# Pass to agent
result = await agent.run(
    "Current user query",  # Latest message (not in history)
    message_history=message_history  # All previous messages
)
```

### Conversion Function

```python
def convert_openai_messages_to_pydantic_history(
    messages: List[OpenAIChatMessage]
) -> List[ModelMessage]:
    """
    Convert OpenWebUI's messages array to PydanticAI format.

    Args:
        messages: Messages from request.messages (includes system + history)

    Returns:
        PydanticAI message_history (excludes system message and current query)
    """
    history: List[ModelMessage] = []

    for msg in messages[:-1]:  # Exclude last message (current query)
        if msg.role == "system":
            continue  # System message handled separately
        elif msg.role == "user":
            history.append(ModelRequest([UserPromptPart(content=msg.content)]))
        elif msg.role == "assistant":
            history.append(ModelResponse([TextPart(content=msg.content)]))

    return history
```

---

## Migration Strategy

### Phase 1: Add Stateless Support (Keep Cookie Fallback)

**Goal:** Support BOTH approaches during migration

```python
# Detect if OpenWebUI sent history
if len(request.messages) > 1:
    # OpenWebUI pattern: Extract history from request
    message_history = convert_openai_messages(request.messages[:-1])
    logger.info(f"Using {len(message_history)} messages from request (OpenWebUI)")
else:
    # CLI pattern: Load from PostgreSQL
    if session_id:
        messages = await get_session_messages(session_id, limit=10)
        message_history = convert_db_messages(messages)
        logger.info(f"Using {len(message_history)} messages from DB (CLI)")
    else:
        message_history = []
        logger.info("No history available (new conversation)")
```

**Benefit:** Backward compatible, validates both approaches work

---

### Phase 2: Document Pattern Split

**Update:** `docs/features/FEAT-008_advanced-memory/architecture.md`

**Add sections:**
1. "OpenWebUI Integration (Stateless Pattern)"
2. "CLI Integration (Stateful Pattern)"
3. "Why Two Patterns Are Needed"

---

### Phase 3: Remove Cookie Code (After Validation)

**Only after confirming:**
- ✅ OpenWebUI conversations work with stateless pattern
- ✅ Message history flows correctly
- ✅ Agent references previous context

**Then remove:**
- Cookie setting in response (lines 904-912, 967-975)
- Cookie checking in session extraction (lines 780-784)
- Debug logging (lines 744-756)

---

## Critical Lessons Learned

### What Went Wrong

1. **Assumed OpenWebUI doesn't send history**
   - Reality: OpenWebUI sends FULL history with EVERY request
   - We tried to recreate what OpenWebUI already provides
   - Result: Redundant session management, cookies, database queries

2. **Didn't test OpenWebUI behavior first**
   - Should have added debug logging BEFORE implementing
   - Would have seen `len(request.messages) = 3` on second message
   - Would have realized history was already there

3. **Followed wrong architecture pattern**
   - Chose "Option 1: X-Session-ID Header" from architecture doc
   - Should have chosen "Option 2: Stateless with OpenWebUI Managing History"
   - Option 2 was marked as "0 days effort" but rejected

4. **Confused OpenWebUI internal API with external API**
   - OpenWebUI's `/api/chat/completions` (internal) has chat_id
   - Our `/v1/chat/completions` (external) gets filtered request
   - Proxy strips all non-OpenAI fields except `messages` array

### What We Should Have Done

1. **Research FIRST, implement SECOND**
   - Read OpenWebUI docs thoroughly
   - Check GitHub discussions about session management
   - Test with curl + debug logging
   - THEN design architecture

2. **Test the hypothesis**
   - Add logging: "Number of messages: {len(request.messages)}"
   - Send 2 messages in OpenWebUI
   - Would have seen: "Number of messages: 3" (user, assistant, user)
   - Would have known history was already there

3. **Follow the simple path**
   - If messages array has history → use it
   - Don't build complex session management
   - OpenAI API is stateless for a reason

### Core Principles for Rebuild

1. **Start with OpenWebUI pattern (stateless)**
   - This is the PRIMARY use case
   - Simplest implementation
   - Zero database overhead
   - Test this FIRST before adding CLI support

2. **Only add CLI pattern if needed**
   - Is there a CLI tool? → Implement stateful pattern
   - No CLI tool? → Skip entirely, save time

3. **Test early and often**
   - Send 2 messages in OpenWebUI
   - Check logs for message count
   - Verify agent gets history
   - Don't proceed until this works

4. **Keep it simple**
   - ~50 lines of code for OpenWebUI pattern
   - ~100 more lines for CLI pattern (optional)
   - Total: ~150 lines vs current ~500 lines

### Validation Checklist Before Implementation

Before writing ANY code for FEAT-008 rebuild:

- [ ] Read this entire document
- [ ] Understand OpenWebUI sends full history in messages array
- [ ] Understand pattern detection: `len(request.messages) > 1`
- [ ] Have PydanticAI message format conversion function ready
- [ ] Know how to test (2 messages in OpenWebUI conversation)
- [ ] Reviewed the "FEAT-008 Rebuild Plan" section above

### What to Do RIGHT NOW

1. **Rollback FEAT-008 code completely**
   ```bash
   git log --oneline | grep FEAT-008
   git reset --hard <commit-before-feat-008>
   ```

2. **Update FEAT-008 planning docs**
   - Mark old PRD as "INCORRECT ASSUMPTIONS"
   - Link to this research document
   - Write new PRD based on stateless pattern

3. **Implement Phase 1 ONLY (OpenWebUI stateless)**
   - Follow "FEAT-008 Rebuild Plan" above
   - Test with OpenWebUI
   - Verify it works
   - STOP if Phase 1 meets all requirements

4. **Document success**
   - Update implementation.md with actual code
   - Mark acceptance criteria as complete
   - Close FEAT-008 if OpenWebUI works

---

## References

### Official Documentation
- OpenWebUI API Reference: https://github.com/open-webui/open-webui/discussions/16402
- Backend-Controlled Flow: https://docs.openwebui.com/tutorials/integrations/backend-controlled-ui-compatible-flow/
- API Endpoints: https://docs.openwebui.com/getting-started/api-endpoints/

### Community Discussions
- Context Length Issues: https://github.com/open-webui/open-webui/discussions/4983
- High Token Usage: https://github.com/open-webui/open-webui/discussions/7281
- Chat History Not Referenced: https://github.com/open-webui/open-webui/discussions/9050

### PydanticAI Documentation
- Message History: https://ai.pydantic.dev/api/agent/#pydantic_ai.Agent.run
- Message Types: https://ai.pydantic.dev/api/messages/

---

**Document Status:** Complete
**Next Action:** Implement stateless pattern using `request.messages` array
**Validation Required:** Test with OpenWebUI before removing cookie code
