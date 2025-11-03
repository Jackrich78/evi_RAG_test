# Manual Testing Guide: OpenWebUI Stateless Multi-Turn Conversations

**Feature:** FEAT-008 - Advanced Memory and Context Management
**Version:** 2.0 (Corrected Approach)
**Date:** 2025-11-03
**Status:** Ready for Testing

## Overview

This guide provides step-by-step instructions for manually testing the stateless multi-turn conversation feature in OpenWebUI. Each test scenario validates specific acceptance criteria and ensures the feature works correctly in real-world usage.

**Estimated Time:** 30 minutes per complete test cycle

## Prerequisites

### System Setup
1. ✅ EVI 360 RAG system running with updated code
2. ✅ OpenWebUI instance running and accessible
3. ✅ OpenWebUI connected to EVI 360 backend (`/v1/chat/completions` endpoint)
4. ✅ Backend logs accessible for verification
5. ✅ Test user account created in OpenWebUI

### Environment Check
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check logs are accessible
tail -f logs/app.log

# Verify OpenWebUI connection
# In OpenWebUI: Settings → Connections → Add OpenAI endpoint
# URL: http://localhost:8000/v1
# API Key: (your configured key)
```

### Test Data Preparation
- Prepare 3-4 test questions about workplace safety (PPE, guidelines, products)
- Have backend logs visible during testing
- Use browser DevTools Network tab to inspect requests (optional)

---

## Test Scenario 1: First Message (No History)

**Validates:** AC-FEAT-008-NEW-001

**Objective:** Verify first message in new conversation works without errors

### Steps

1. **Open OpenWebUI**
   - Navigate to OpenWebUI interface
   - Ensure you're starting a fresh conversation
   - No previous messages in chat window

2. **Send First Message**
   - Type: `"What is PPE?"`
   - Click Send button
   - Observe response loading

3. **Verify Response**
   - Response appears within 3 seconds
   - Response provides definition of PPE
   - No error messages displayed
   - Streaming works smoothly (if enabled)

4. **Check Backend Logs**
   - Open backend log file
   - Search for recent log entry
   - Verify log shows: `"message_history length: 0"`
   - Verify no database query logs (should be zero)

### Expected Results

✅ **Pass Criteria:**
- Message sent successfully
- Response received without errors
- Backend log confirms empty history (length 0)
- Zero database queries logged

❌ **Fail Criteria:**
- Error message displayed to user
- No response received
- Backend crashes or throws exception
- Database queries present in logs

### Troubleshooting

**Issue:** Response not received
- Check backend is running: `curl http://localhost:8000/health`
- Verify OpenWebUI connection settings
- Check API key configuration

**Issue:** Database queries still logged
- Ensure updated code deployed
- Verify session management code removed
- Check for cached/stale code

---

## Test Scenario 2: Follow-up Message (With History)

**Validates:** AC-FEAT-008-NEW-002, AC-FEAT-008-NEW-004

**Objective:** Verify agent uses previous conversation context in follow-up response

### Steps

1. **Continue from Scenario 1**
   - Previous message: "What is PPE?"
   - Agent response about PPE definition visible

2. **Send Follow-up Message**
   - Type: `"What are the main types?"`
   - Click Send button
   - Do NOT start new conversation

3. **Verify Context Awareness**
   - Response should reference "PPE types" specifically
   - Response should NOT ask "types of what?"
   - Agent assumes context from previous question
   - Response lists PPE categories (helmets, gloves, etc.)

4. **Check Backend Logs**
   - Search for latest request log entry
   - Verify log shows: `"message_history length: 2"`
   - Confirm: 1 previous user message + 1 previous assistant message
   - Verify zero database queries

5. **Send Second Follow-up**
   - Type: `"Which type is most important for welding?"`
   - Verify response references PPE context
   - Check logs show: `"message_history length: 4"`

### Expected Results

✅ **Pass Criteria:**
- Follow-up questions answered with context
- Agent doesn't ask for clarification on "what types?"
- Responses build on previous answers
- Backend logs show growing history (2, 4, 6...)
- Zero database queries

❌ **Fail Criteria:**
- Agent asks "types of what?"
- Response ignores previous context
- History length stays at 0
- Database queries present

### Troubleshooting

**Issue:** Agent doesn't use context
- Verify `message_history` parameter passed to agent
- Check conversion function extracting messages correctly
- Ensure PydanticAI agent configured to use history

**Issue:** History length incorrect
- Verify messages array includes all previous messages
- Check conversion function not skipping messages
- Ensure system messages excluded correctly

---

## Test Scenario 3: Long Conversation (10+ Turns)

**Validates:** AC-FEAT-008-NEW-003, AC-FEAT-008-NEW-103

**Objective:** Verify system handles extended conversations without context loss

### Steps

1. **Start New Conversation**
   - Create fresh chat in OpenWebUI
   - Prepare 10+ questions on related topic

2. **Execute Long Conversation**
   - **Turn 1:** "What safety equipment is required for construction sites?"
   - **Turn 2:** "What about head protection specifically?"
   - **Turn 3:** "What standards must hard hats meet?"
   - **Turn 4:** "How often should they be replaced?"
   - **Turn 5:** "What are signs of wear and tear?"
   - **Turn 6:** "Can they be repaired?"
   - **Turn 7:** "What about impact vs penetration protection?"
   - **Turn 8:** "Which brands do you recommend?"
   - **Turn 9:** "What's the price range?"
   - **Turn 10:** "Do you have any in stock?"

3. **Verify Context Maintenance**
   - At turn 10, agent should still reference "hard hats"
   - Response should not lose thread of conversation
   - Agent builds on answers from turns 1-9

4. **Check Backend Logs**
   - Verify history length increases: 0 → 2 → 4 → 6 → 8 → 10 → 12 → 14 → 16 → 18
   - Confirm no errors or warnings
   - Verify conversion time stays <5ms (check performance logs)

5. **Test Reference to Early Context**
   - **Turn 11:** "Going back to your earlier answer about standards, which is most stringent?"
   - Verify agent recalls turn 3 context (standards discussion)

### Expected Results

✅ **Pass Criteria:**
- All 10+ turns complete successfully
- Context maintained throughout conversation
- Agent references earlier turns when relevant
- History length grows correctly (2n where n=turns)
- No performance degradation
- Zero database queries

❌ **Fail Criteria:**
- Context lost after 5-6 turns
- Agent forgets earlier topics
- Performance degrades (slow responses)
- Errors or crashes occur
- Database queries present

### Troubleshooting

**Issue:** Context lost after N turns
- Check if message array truncated by OpenWebUI
- Verify conversion handles large arrays
- Test array size limit (if any)

**Issue:** Slow performance
- Check conversion latency in logs
- Verify no N² algorithm complexity
- Test with benchmark: `pytest tests/performance/test_stateless_performance.py`

---

## Test Scenario 4: New Conversation (Clean Start)

**Validates:** AC-FEAT-008-NEW-202

**Objective:** Verify new conversations start with clean slate (no cross-contamination)

### Steps

1. **Complete Scenario 3**
   - Have long conversation about hard hats
   - Conversation history: 10+ turns

2. **Start New Conversation**
   - Click "New Chat" button in OpenWebUI
   - Fresh conversation window opens
   - Previous conversation still saved separately

3. **Send Unrelated Message**
   - Type: `"What are chemical handling guidelines?"`
   - Topic completely unrelated to hard hats

4. **Verify Clean Start**
   - Response should NOT reference hard hats
   - Response should NOT reference construction site safety
   - Agent treats this as brand new conversation
   - Backend logs show: `"message_history length: 0"`

5. **Switch Back to Previous Conversation**
   - Open previous hard hat conversation
   - Send follow-up: "What about chin straps?"
   - Verify context switches back to hard hats

### Expected Results

✅ **Pass Criteria:**
- New conversation starts with empty history
- No cross-contamination between conversations
- Each conversation maintains independent context
- Switching between conversations works correctly
- Zero database queries (OpenWebUI handles state)

❌ **Fail Criteria:**
- New conversation references old topics
- Context bleeds between conversations
- Agent confused by conversation switches
- Database queries present

### Troubleshooting

**Issue:** Cross-contamination detected
- Verify system is truly stateless
- Check no shared global state
- Ensure request processing isolated

**Issue:** Context not preserved on switch
- Verify OpenWebUI sends full history on switch
- Check message array includes switched conversation

---

## Test Scenario 5: Streaming with History

**Validates:** AC-FEAT-008-NEW-005

**Objective:** Verify streaming responses work correctly with conversation history

### Steps

1. **Enable Streaming** (if not default)
   - Check OpenWebUI settings
   - Ensure streaming enabled

2. **Start Conversation**
   - First message: "Explain PPE in detail"
   - Observe streaming response (chunks arrive gradually)

3. **Send Follow-up**
   - Second message: "Summarize that in 3 bullet points"
   - Observe streaming response

4. **Verify Streaming Quality**
   - Chunks appear smoothly
   - No stuttering or pauses
   - Complete response coherent
   - Response references detailed explanation from first message
   - Bullet points summarize PPE concepts

5. **Check Backend Logs**
   - Verify streaming enabled in logs
   - Check history extracted before streaming starts
   - Confirm no streaming errors

### Expected Results

✅ **Pass Criteria:**
- Streaming works with history
- Chunks delivered smoothly
- Follow-up response uses context
- No streaming errors or interruptions
- History doesn't break streaming

❌ **Fail Criteria:**
- Streaming fails or errors
- Chunks arrive in wrong order
- Response incomplete
- Context not used in streamed response

### Troubleshooting

**Issue:** Streaming broken
- Check streaming configuration unchanged
- Verify history extraction doesn't block streaming
- Test streaming without history (baseline)

---

## Test Scenario 6: Error Handling

**Validates:** AC-FEAT-008-NEW-101, AC-FEAT-008-NEW-104, AC-FEAT-008-NEW-205

**Objective:** Verify system handles errors gracefully

### Steps

1. **Test Empty Request** (Developer test)
   - Use curl to send empty messages array
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"messages": [], "model": "evi-agent"}'
   ```
   - Verify error message returned (not crash)

2. **Test Malformed Message** (Developer test)
   - Send message missing content field
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user"}], "model": "evi-agent"}'
   ```
   - Verify graceful error handling

3. **Check Error Logs**
   - Verify errors logged with details
   - Confirm system didn't crash
   - Check appropriate error codes returned

### Expected Results

✅ **Pass Criteria:**
- Errors handled gracefully
- Appropriate error messages
- System stays running (no crash)
- Errors logged for debugging

❌ **Fail Criteria:**
- System crashes
- No error message returned
- Errors not logged
- Silent failures

---

## Acceptance Checklist

After completing all scenarios, verify:

- [ ] First message works (Scenario 1)
- [ ] Follow-up messages use context (Scenario 2)
- [ ] Long conversations maintain context (Scenario 3)
- [ ] New conversations start clean (Scenario 4)
- [ ] Streaming works with history (Scenario 5)
- [ ] Errors handled gracefully (Scenario 6)
- [ ] Zero database queries in all scenarios
- [ ] Backend logs show correct history lengths
- [ ] No cross-contamination between conversations
- [ ] Performance acceptable (<3 second responses)

**Overall Pass Criteria:** All checkboxes ticked

---

## Test Results Documentation

### Test Session Information

**Date:** _______________
**Tester:** _______________
**Environment:** _______________
**Backend Version:** _______________
**OpenWebUI Version:** _______________

### Scenario Results

| Scenario | Status | Notes |
|----------|--------|-------|
| 1. First Message | ⬜ Pass ⬜ Fail | |
| 2. Follow-up | ⬜ Pass ⬜ Fail | |
| 3. Long Conversation | ⬜ Pass ⬜ Fail | |
| 4. New Conversation | ⬜ Pass ⬜ Fail | |
| 5. Streaming | ⬜ Pass ⬜ Fail | |
| 6. Error Handling | ⬜ Pass ⬜ Fail | |

### Issues Found

1. **Issue:** _______________
   - **Severity:** ⬜ Critical ⬜ Major ⬜ Minor
   - **Steps to Reproduce:** _______________
   - **Expected:** _______________
   - **Actual:** _______________

2. **Issue:** _______________
   - **Severity:** ⬜ Critical ⬜ Major ⬜ Minor
   - **Steps to Reproduce:** _______________
   - **Expected:** _______________
   - **Actual:** _______________

### Screenshots

**Location:** _______________

Include screenshots of:
- OpenWebUI conversation showing context awareness
- Backend logs showing message_history length
- Any error states encountered

---

## Sign-off

**Tester Signature:** _______________
**Date:** _______________

**Approval:** ⬜ Approved ⬜ Rejected

**Reason (if rejected):** _______________

---

## References

- **Acceptance Criteria:** `acceptance-v2.md`
- **Testing Strategy:** `testing-v2.md`
- **Architecture:** `architecture-v2.md`
- **Backend Logs:** `/logs/app.log`

---

**Document Status:** Ready for Manual Testing
**Estimated Duration:** 30-45 minutes per complete test cycle
**Recommended Frequency:** After each code change, before deployment
