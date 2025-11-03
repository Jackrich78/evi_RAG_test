# Acceptance Criteria: OpenWebUI Stateless Multi-Turn Conversations

**Feature:** FEAT-008 - Advanced Memory and Context Management
**Version:** 2.0 (Corrected Approach)
**Date:** 2025-11-03
**Status:** Planned

## Overview

This document defines testable acceptance criteria for implementing stateless multi-turn conversations by extracting conversation history from OpenWebUI request messages. All criteria are binary (pass/fail) and mapped to user stories from the PRD.

## Functional Requirements

### AC-FEAT-008-NEW-001: First Message (No History)
**User Story:** As a user, I want to start a new conversation in OpenWebUI without errors.

**Given:** User opens OpenWebUI and sends first message "What is PPE?"
**When:** Request arrives with `messages = [{"role": "user", "content": "What is PPE?"}]`
**Then:**
- System extracts empty history (length 0)
- Agent receives `message_history=[]`
- Agent responds without referencing previous context
- Response completes successfully

**Test Method:** Integration test + manual OpenWebUI test

---

### AC-FEAT-008-NEW-002: Follow-up Message (With History)
**User Story:** As a user, I want the agent to remember my previous question when I ask a follow-up.

**Given:** User previously asked "What is PPE?" and received response
**When:** User sends follow-up "What are the types?" with request containing:
```json
messages = [
  {"role": "user", "content": "What is PPE?"},
  {"role": "assistant", "content": "PPE stands for..."},
  {"role": "user", "content": "What are the types?"}
]
```
**Then:**
- System extracts 2 previous messages (user + assistant)
- Agent receives `message_history=[ModelRequest(...), ModelResponse(...)]`
- Agent response references "PPE" context from first message
- Response is contextually relevant to original topic

**Test Method:** Integration test with mock messages + manual OpenWebUI test

---

### AC-FEAT-008-NEW-003: Long Conversation (10+ Turns)
**User Story:** As a user, I want to have extended conversations without context loss.

**Given:** Conversation with 10+ message turns (5 user, 5 assistant)
**When:** User sends 11th message
**Then:**
- System extracts all 10 previous messages
- Conversion completes in <5ms (performance requirement)
- Agent receives full history in correct chronological order
- Agent can reference any previous turn in the conversation
- No message truncation or loss

**Test Method:** Load test with sample 10-turn conversation

---

### AC-FEAT-008-NEW-004: Agent References Previous Context
**User Story:** As a user, I expect the agent to build on previous answers in the conversation.

**Given:** User asked "What safety equipment do I need for welding?"
**When:** User follows up with "How much does that cost?"
**Then:**
- Agent response references "welding safety equipment" without re-asking
- Agent provides pricing for items mentioned in previous response
- No generic "what equipment?" clarification needed

**Test Method:** Manual test scenario with specific conversation flow

---

### AC-FEAT-008-NEW-005: Streaming Works with History
**User Story:** As a user, I want streaming responses to work with conversation context.

**Given:** Follow-up message in ongoing conversation
**When:** Agent streams response chunks
**Then:**
- Streaming starts within 500ms
- Each chunk references conversation context
- Complete streamed response is contextually accurate
- No streaming errors or interruptions

**Test Method:** Integration test with streaming enabled + manual verification

---

### AC-FEAT-008-NEW-006: Message Format Conversion
**User Story:** As a developer, I need OpenAI format converted to PydanticAI format correctly.

**Given:** OpenWebUI message array in OpenAI format
**When:** `convert_openai_to_pydantic_history()` is called
**Then:**
- `user` role → `ModelRequest` with correct content
- `assistant` role → `ModelResponse` with correct content
- `system` messages excluded from history (handled separately)
- Last message (current query) excluded from history
- Message order preserved exactly
- No data loss or corruption

**Test Method:** Unit tests with various message arrays

---

## Edge Cases

### AC-FEAT-008-NEW-101: Empty Messages Array
**Given:** Malformed request with `messages = []`
**When:** Endpoint receives request
**Then:**
- System handles gracefully without crash
- Returns appropriate error message
- Logs warning about malformed request

**Test Method:** Unit test with edge case input

---

### AC-FEAT-008-NEW-102: System Message Handling
**Given:** Request contains system message: `{"role": "system", "content": "You are a helpful assistant"}`
**When:** History conversion occurs
**Then:**
- System message excluded from `message_history`
- System message handled separately (existing logic)
- No duplication of system instructions

**Test Method:** Unit test verifying system message filtering

---

### AC-FEAT-008-NEW-103: Message Order Preservation
**Given:** Conversation with interleaved user/assistant messages
**When:** History extracted and converted
**Then:**
- Chronological order exactly preserved
- First message in array = first in history
- No reordering or shuffling occurs
- Agent sees conversation in correct temporal sequence

**Test Method:** Unit test with time-stamped messages + verification

---

### AC-FEAT-008-NEW-104: Invalid Message Format
**Given:** Message missing required fields: `{"role": "user"}` (no content)
**When:** Conversion function processes message
**Then:**
- Function handles gracefully without crash
- Skips malformed message with warning log
- Continues processing valid messages
- Returns partial history with valid messages only

**Test Method:** Unit test with various malformed inputs

---

### AC-FEAT-008-NEW-105: Single Message (Current Query Only)
**Given:** Request with only current message (no history)
**When:** Conversion excludes last message
**Then:**
- Returns empty history list `[]`
- No error or exception thrown
- Agent receives empty `message_history`
- Behaves same as AC-FEAT-008-NEW-001

**Test Method:** Unit test with single-element array

---

### AC-FEAT-008-NEW-106: Mixed Role Sequences
**User Story:** As a system, I must handle unusual message patterns gracefully.

**Given:** Request with consecutive user messages (no assistant response between)
```json
messages = [
  {"role": "user", "content": "Hello"},
  {"role": "user", "content": "Anyone there?"},
  {"role": "user", "content": "Please respond"}
]
```
**When:** Conversion function processes the messages
**Then:**
- All user messages included in history (first two)
- No error or crash occurs
- Last message excluded as current query
- Agent receives valid history with user→user pattern
- Warning logged about unusual pattern (optional)

**Test Method:** Unit test with consecutive same-role messages

---

### AC-FEAT-008-NEW-107: Large Message Handling
**User Story:** As a user, I want to send detailed questions without system errors.

**Given:** Message with content >10,000 characters
**When:** Conversion processes large message
**Then:**
- Full content preserved (no truncation in conversion)
- Conversion completes in <10ms (slightly relaxed for large content)
- No memory errors or crashes
- Message correctly formatted as ModelRequest/ModelResponse

**Test Method:** Unit test with 10k+ character message content

---

### AC-FEAT-008-NEW-108: Unicode and Special Characters
**User Story:** As a Dutch user, I need proper handling of Dutch characters.

**Given:** Messages containing Dutch special characters (ë, ü, ö, ï, etc.)
```json
{"role": "user", "content": "Wat is persoonlijke beschermingsmiddelen?"}
{"role": "assistant", "content": "Persoonlijke beschermingsmiddelen zijn..."}
```
**When:** Conversion processes messages
**Then:**
- All Dutch characters preserved exactly
- No encoding corruption (UTF-8 maintained)
- Emoji and Unicode symbols preserved
- Content === original content (byte-for-byte)

**Test Method:** Unit test with Dutch text and Unicode characters

---

### AC-FEAT-008-NEW-109: Concurrent Request Isolation (Explicit)
**User Story:** As a deployed system, I must isolate concurrent user conversations.

**Given:** Two users send requests simultaneously:
- User A: Follow-up about "PPE equipment"
- User B: Follow-up about "fire safety"
**When:** Both requests processed concurrently
**Then:**
- User A receives response about PPE (not fire safety)
- User B receives response about fire safety (not PPE)
- No state bleeding between requests
- Each request completely self-contained
- History extraction is thread-safe

**Test Method:** Concurrent load test with different conversation histories

---

## Non-Functional Requirements

### AC-FEAT-008-NEW-201: Performance (Zero Database Latency)
**Requirement:** System must be stateless with no database queries.

**Given:** Any OpenWebUI request with conversation history
**When:** Request processed end-to-end
**Then:**
- Zero queries to `sessions` table
- Zero queries to `messages` table
- Message conversion completes in <5ms
- Total request latency unchanged from single-message baseline
- Database connection pool usage = 0 for history retrieval

**Test Method:** Performance profiling with query logging enabled

---

### AC-FEAT-008-NEW-202: Stateless Verification
**Requirement:** System must not depend on server-side session state.

**Given:** Two concurrent users with different conversations
**When:** Requests processed simultaneously
**Then:**
- No cross-contamination between conversations
- Each request fully self-contained
- Can scale horizontally without session affinity
- Server restart doesn't lose context (client handles this)

**Test Method:** Load test with concurrent sessions

---

### AC-FEAT-008-NEW-203: Backward Compatibility
**Requirement:** Changes must not break existing functionality.

**Given:** Existing OpenWebUI installation
**When:** Updated code deployed
**Then:**
- All existing features continue working
- Single-message requests still succeed
- Streaming functionality unchanged
- API contract maintained (no breaking changes)
- No migration script required

**Test Method:** Regression test suite + manual smoke testing

---

### AC-FEAT-008-NEW-204: Code Simplicity
**Requirement:** Implementation must be maintainable and simple.

**Given:** New message conversion code
**When:** Code review conducted
**Then:**
- Conversion function ≤50 lines
- No complex branching logic
- Type hints on all functions
- Docstrings following Google style
- No external dependencies added

**Test Method:** Code review checklist

---

### AC-FEAT-008-NEW-205: Error Logging
**Requirement:** System must log errors for debugging without crashing.

**Given:** Any error during message conversion
**When:** Error occurs
**Then:**
- Error logged with full context (message array, error type)
- Request continues with fallback behavior (empty history)
- User receives response (degraded but functional)
- Error details available for debugging

**Test Method:** Error injection testing + log verification

---

## Validation Scenarios

### Scenario 1: Basic Multi-Turn Conversation
**Steps:**
1. User asks "What is PPE?" (AC-FEAT-008-NEW-001)
2. Agent responds with definition
3. User asks "What types exist?" (AC-FEAT-008-NEW-002)
4. Agent lists types referencing PPE (AC-FEAT-008-NEW-004)
5. User asks "Which is cheapest?" (AC-FEAT-008-NEW-002, AC-FEAT-008-NEW-004)

**Expected:** All responses contextually aware, no database queries

---

### Scenario 2: Performance Under Load
**Steps:**
1. Simulate 10 concurrent users
2. Each conducts 5-turn conversation
3. Monitor database query count
4. Measure conversion latency

**Expected:** 0 DB queries, <5ms conversion (AC-FEAT-008-NEW-201)

---

### Scenario 3: Edge Case Handling
**Steps:**
1. Send empty messages array (AC-FEAT-008-NEW-101)
2. Send malformed message (AC-FEAT-008-NEW-104)
3. Send single message (AC-FEAT-008-NEW-105)
4. Send mixed valid/invalid (AC-FEAT-008-NEW-104)

**Expected:** Graceful handling, no crashes, appropriate errors logged

---

## Test Coverage Requirements

**Minimum Coverage:** 90% for new code
**Critical Paths:** 100% coverage required for:
- Message conversion function
- History extraction logic
- Error handling paths

**Test Types:**
- Unit tests: 15+ tests covering all message format variations
- Integration tests: 5+ tests covering endpoint → agent flow
- E2E tests: 3+ manual scenarios in actual OpenWebUI
- Performance tests: 2+ load/latency tests

---

## Definition of Done

Feature is complete when:
- ✅ All 25 acceptance criteria pass (20 functional + 5 non-functional)
- ✅ Unit test coverage ≥90%
- ✅ Integration tests pass in CI
- ✅ Manual testing completed in OpenWebUI (6 scenarios from manual-test-v2.md)
- ✅ Performance requirements verified (<5ms conversion, 0 DB queries)
- ✅ Edge cases validated (mixed roles, large messages, Unicode, concurrent)
- ✅ Code review approved
- ✅ Documentation updated (AC.md, IMPLEMENTATION_PROGRESS.md)
- ✅ No P0/P1 bugs open

---

## Traceability Matrix

| AC ID | User Story | Test Type | Priority |
|-------|-----------|-----------|----------|
| AC-FEAT-008-NEW-001 | First message | Integration | P0 |
| AC-FEAT-008-NEW-002 | Follow-up | Integration | P0 |
| AC-FEAT-008-NEW-003 | Long conversation | Performance | P1 |
| AC-FEAT-008-NEW-004 | Context reference | Manual | P0 |
| AC-FEAT-008-NEW-005 | Streaming | Integration | P1 |
| AC-FEAT-008-NEW-006 | Format conversion | Unit | P0 |
| AC-FEAT-008-NEW-101 | Empty array | Unit | P2 |
| AC-FEAT-008-NEW-102 | System messages | Unit | P2 |
| AC-FEAT-008-NEW-103 | Order preservation | Unit | P1 |
| AC-FEAT-008-NEW-104 | Invalid format | Unit | P2 |
| AC-FEAT-008-NEW-105 | Single message | Unit | P2 |
| AC-FEAT-008-NEW-106 | Mixed roles | Unit | P2 |
| AC-FEAT-008-NEW-107 | Large messages | Unit | P2 |
| AC-FEAT-008-NEW-108 | Unicode/Dutch | Unit | P1 |
| AC-FEAT-008-NEW-109 | Concurrent isolation | Load | P1 |
| AC-FEAT-008-NEW-201 | Performance | Performance | P0 |
| AC-FEAT-008-NEW-202 | Stateless | Load | P1 |
| AC-FEAT-008-NEW-203 | Compatibility | Regression | P0 |
| AC-FEAT-008-NEW-204 | Code quality | Review | P1 |
| AC-FEAT-008-NEW-205 | Error logging | Integration | P2 |

**Priority Legend:** P0 = Blocker | P1 = Critical | P2 = Important

---

**Document Status:** Ready for Implementation
**Total Criteria:** 6 functional + 9 edge cases + 5 non-functional = 20 criteria
**Estimated Test Time:** 5-6 hours (including manual testing)
