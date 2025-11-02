# Manual Testing Guide: Advanced Memory & Session Management

**Feature ID:** FEAT-008
**Created:** 2025-11-02
**Tester:** QA/Product Team
**Status:** Ready for Testing

## Prerequisites

Before starting manual testing, ensure the following setup is complete:

### Environment Setup
- ✅ Docker and docker-compose installed and running
- ✅ EVI 360 containers running: `docker-compose up -d`
- ✅ OpenWebUI accessible at http://localhost:3000
- ✅ API accessible at http://localhost:8000
- ✅ PostgreSQL accessible: `docker-compose exec db psql -U postgres -d evi_rag`

### Test User Accounts
- OpenWebUI account created (register at http://localhost:3000)
- API authentication configured (if required)

### Test Data
- No pre-seeding required (feature creates sessions dynamically)
- Database should be in clean state before testing

### Tools Required
- Web browser (Chrome/Firefox recommended)
- Terminal with curl installed
- psql CLI access for database verification
- Text editor for notes/screenshots

## Test Scenarios

### Scenario 1: Multi-Turn Conversation in OpenWebUI

**Objective:** Verify that the agent remembers context from previous questions in the same session

**Acceptance Criteria:** AC-FEAT-008-001, AC-FEAT-008-002, AC-FEAT-008-003

**Test Steps:**

1. **Open OpenWebUI**
   - Navigate to http://localhost:3000
   - Log in with test account
   - Click "New Chat" to start fresh conversation

2. **Ask First Question**
   - Type: "Wat zijn de vereisten voor valbeveiliging?" (What are the requirements for fall protection?)
   - Click Send
   - Wait for response (should take <5 seconds)

3. **Verify First Response**
   - Agent should provide information about fall protection requirements
   - Note: No specific context reference expected (first message)
   - Response should be in Dutch

4. **Ask Follow-Up Question**
   - Type: "Welke producten heb je daarvoor?" (Which products do you have for that?)
   - Click Send
   - Wait for response

5. **Verify Context Retention**
   - **Expected:** Agent references "valbeveiliging" (fall protection) from previous question
   - **Expected:** Agent recommends specific products for fall protection
   - **Expected:** Response shows agent understood "daarvoor" (for that) refers to fall protection
   - **Not Expected:** Agent asks "for what?" (would indicate no context)

6. **Check Database**
   - Open terminal and connect to database:
     ```bash
     docker-compose exec db psql -U postgres -d evi_rag
     ```
   - Query sessions:
     ```sql
     SELECT id, user_id, created_at, last_accessed
     FROM sessions
     ORDER BY created_at DESC
     LIMIT 1;
     ```
   - Copy the session ID from result
   - Query messages:
     ```sql
     SELECT role, content, created_at
     FROM messages
     WHERE session_id = '<paste-session-id-here>'
     ORDER BY created_at;
     ```
   - **Expected:** 4 messages total (2 user, 2 assistant)
   - **Expected:** Messages in chronological order
   - **Expected:** Content matches what was sent/received in UI

7. **Ask Third Follow-Up Question**
   - Type: "Hoeveel kosten deze producten?" (How much do these products cost?)
   - Click Send

8. **Verify Extended Context**
   - **Expected:** Agent provides pricing for fall protection products mentioned earlier
   - **Expected:** No need to repeat "valbeveiliging" in question
   - **Expected:** Response maintains conversational context

**Pass Criteria:**
- ✅ Agent references "valbeveiliging" in second response
- ✅ Agent provides relevant products without needing context repeated
- ✅ Database shows all messages in same session
- ✅ last_accessed timestamp updates with each message
- ✅ Total response time <5 seconds per message

**Screenshot Locations:**
- [ ] Screenshot 1: First question and response
- [ ] Screenshot 2: Follow-up question showing context retention
- [ ] Screenshot 3: Database query showing session messages

---

### Scenario 2: CLI Session Isolation

**Objective:** Verify that each CLI run creates a new session without inheriting context from previous runs

**Acceptance Criteria:** AC-FEAT-008-004, AC-FEAT-008-005

**Test Steps:**

1. **First CLI Run**
   - Open terminal and navigate to project root
   - Activate virtual environment:
     ```bash
     source venv_linux/bin/activate
     ```
   - Run CLI:
     ```bash
     python3 cli.py
     ```

2. **Ask Questions in First Run**
   - Type: "Wat zijn arbovereisten voor heftrucks?" (What are safety requirements for forklifts?)
   - Wait for response
   - Type: "Heb je trainingen hiervoor?" (Do you have training for this?)
   - Wait for response
   - Type: "Hoeveel kost de training?" (How much does the training cost?)
   - Wait for response

3. **Verify First Run Context**
   - **Expected:** Second and third questions reference forklift context
   - **Expected:** Agent provides training info related to forklifts
   - Note the session flow works correctly

4. **Exit First CLI Run**
   - Type: "exit" or press Ctrl+C
   - CLI should terminate

5. **Check Database After First Run**
   - Connect to database:
     ```bash
     docker-compose exec db psql -U postgres -d evi_rag
     ```
   - Query sessions:
     ```sql
     SELECT id, user_id, created_at
     FROM sessions
     ORDER BY created_at DESC
     LIMIT 1;
     ```
   - **Expected:** One session from CLI run
   - Note the session ID for comparison

6. **Second CLI Run**
   - Run CLI again:
     ```bash
     python3 cli.py
     ```
   - Type: "Welke producten heb je?" (Which products do you have?)
   - Wait for response

7. **Verify Session Isolation**
   - **Expected:** Agent does NOT reference forklifts or training from previous run
   - **Expected:** Agent asks for clarification or provides general product list
   - **Expected:** No context from previous CLI session

8. **Check Database After Second Run**
   - Query sessions again:
     ```sql
     SELECT id, user_id, created_at
     FROM sessions
     ORDER BY created_at DESC
     LIMIT 2;
     ```
   - **Expected:** Two distinct sessions with different UUIDs
   - **Expected:** Second session created after first session
   - **Expected:** Each session has its own messages (no mixing)

9. **Verify Message Isolation**
   - Query messages for both sessions:
     ```sql
     SELECT session_id, role, content
     FROM messages
     ORDER BY session_id, created_at;
     ```
   - **Expected:** Messages grouped by session_id
   - **Expected:** Forklift messages only in first session
   - **Expected:** Second session messages don't reference forklift context

**Pass Criteria:**
- ✅ Each CLI run creates new session (different UUID)
- ✅ Second CLI run shows no context from first run
- ✅ Database confirms two separate sessions
- ✅ Messages are isolated by session_id

**Screenshot Locations:**
- [ ] Screenshot 1: First CLI run with 3 questions
- [ ] Screenshot 2: Second CLI run showing no context from first
- [ ] Screenshot 3: Database query showing two separate sessions

---

### Scenario 3: Container Restart Persistence

**Objective:** Verify that session data survives container restarts with zero data loss

**Acceptance Criteria:** AC-FEAT-008-006, AC-FEAT-008-007, AC-FEAT-008-203

**Test Steps:**

1. **Create Session with Messages**
   - Open OpenWebUI at http://localhost:3000
   - Start new conversation
   - Ask 5 questions:
     1. "Wat is PSA?" (What is PPE?)
     2. "Welke soorten PSA heb je?" (What types of PPE do you have?)
     3. "Wat kost een veiligheidshelm?" (How much does a safety helmet cost?)
     4. "Heb je ook veiligheidsbrillen?" (Do you also have safety glasses?)
     5. "Wat zijn de certificeringen?" (What are the certifications?)

2. **Verify Session Creation**
   - Check database:
     ```bash
     docker-compose exec db psql -U postgres -d evi_rag
     ```
   - Query:
     ```sql
     SELECT id, user_id, created_at
     FROM sessions
     ORDER BY created_at DESC
     LIMIT 1;
     ```
   - Copy session ID
   - Verify message count:
     ```sql
     SELECT COUNT(*) FROM messages WHERE session_id = '<session-id>';
     ```
   - **Expected:** 10 messages (5 user + 5 assistant)

3. **Stop Containers**
   - In terminal, stop all containers:
     ```bash
     docker-compose down
     ```
   - **Expected:** All containers stop gracefully
   - **Expected:** No error messages about data corruption

4. **Start Containers**
   - Restart containers:
     ```bash
     docker-compose up -d
     ```
   - Wait for all services to be ready (~30 seconds)
   - Check logs for errors:
     ```bash
     docker-compose logs api
     docker-compose logs db
     ```
   - **Expected:** No errors in startup logs

5. **Verify Session Persists**
   - Reconnect to database:
     ```bash
     docker-compose exec db psql -U postgres -d evi_rag
     ```
   - Check session still exists:
     ```sql
     SELECT id, user_id, created_at
     FROM sessions
     WHERE id = '<session-id>';
     ```
   - **Expected:** Session found with same UUID
   - **Expected:** created_at timestamp unchanged

6. **Verify Messages Persist**
   - Query messages:
     ```sql
     SELECT role, content, created_at
     FROM messages
     WHERE session_id = '<session-id>'
     ORDER BY created_at;
     ```
   - **Expected:** All 10 messages still present
   - **Expected:** Message content exactly as before restart
   - **Expected:** created_at timestamps unchanged

7. **Continue Conversation**
   - Return to OpenWebUI (refresh page if needed)
   - In same conversation, ask new question:
     - "Heb je ook handschoenen?" (Do you also have gloves?)
   - Wait for response

8. **Verify Context After Restart**
   - **Expected:** Agent references PSA/PPE from pre-restart conversation
   - **Expected:** Agent continues conversation naturally
   - **Expected:** Response relevant to previous context

9. **Final Database Verification**
   - Check message count:
     ```sql
     SELECT COUNT(*) FROM messages WHERE session_id = '<session-id>';
     ```
   - **Expected:** 12 messages now (10 from before + 2 new)
   - Verify all messages present:
     ```sql
     SELECT role, content FROM messages WHERE session_id = '<session-id>' ORDER BY created_at;
     ```
   - **Expected:** Chronological order maintained
   - **Expected:** No gaps or duplicates

**Pass Criteria:**
- ✅ Session persists after docker-compose down/up
- ✅ All 10 pre-restart messages remain intact
- ✅ New messages can be added after restart
- ✅ Agent maintains context from pre-restart conversation
- ✅ No data corruption or loss
- ✅ SELECT COUNT(*) queries return expected values

**Screenshot Locations:**
- [ ] Screenshot 1: Initial 5 questions before restart
- [ ] Screenshot 2: Database showing 10 messages pre-restart
- [ ] Screenshot 3: docker-compose down/up terminal output
- [ ] Screenshot 4: Continued conversation after restart
- [ ] Screenshot 5: Database showing 12 messages post-restart

---

### Scenario 4: Invalid Session ID Error Handling

**Objective:** Verify proper error handling for invalid X-Session-ID header values

**Acceptance Criteria:** AC-FEAT-008-101, AC-FEAT-008-302

**Test Steps:**

1. **Test Invalid UUID Format**
   - Use curl to send request with invalid session ID:
     ```bash
     curl -X POST http://localhost:8000/v1/chat/completions \
       -H "Content-Type: application/json" \
       -H "X-Session-ID: not-a-valid-uuid" \
       -d '{
         "model": "evi-specialist",
         "messages": [{"role": "user", "content": "Test message"}]
       }' \
       -v
     ```

2. **Verify 400 Error Response**
   - **Expected:** HTTP 400 Bad Request
   - **Expected:** Error response in OpenAI format:
     ```json
     {
       "error": {
         "message": "Invalid session ID format: must be valid UUID",
         "type": "invalid_request_error",
         "code": "invalid_session_id"
       }
     }
     ```
   - **Expected:** No session created in database

3. **Test Non-Existent UUID**
   - Generate valid but non-existent UUID:
     ```bash
     curl -X POST http://localhost:8000/v1/chat/completions \
       -H "Content-Type: application/json" \
       -H "X-Session-ID: 00000000-0000-0000-0000-000000000000" \
       -d '{
         "model": "evi-specialist",
         "messages": [{"role": "user", "content": "Test message"}]
       }' \
       -v
     ```

4. **Verify 404 Error Response**
   - **Expected:** HTTP 404 Not Found
   - **Expected:** Error response:
     ```json
     {
       "error": {
         "message": "Session not found: 00000000-0000-0000-0000-000000000000",
         "type": "invalid_request_error",
         "code": "session_not_found"
       }
     }
     ```

5. **Test Auto-Creation (Missing Header)**
   - Send request without X-Session-ID header:
     ```bash
     curl -X POST http://localhost:8000/v1/chat/completions \
       -H "Content-Type: application/json" \
       -d '{
         "model": "evi-specialist",
         "messages": [{"role": "user", "content": "Test message"}]
       }' \
       -v
     ```

6. **Verify Auto-Creation Response**
   - **Expected:** HTTP 200 OK
   - **Expected:** Response includes X-Session-ID header with valid UUID
   - **Expected:** Response body contains agent reply
   - Extract session ID from response header

7. **Verify Session Created in Database**
   - Check database:
     ```sql
     SELECT id, user_id, created_at
     FROM sessions
     WHERE id = '<extracted-session-id>';
     ```
   - **Expected:** Session exists with extracted UUID
   - **Expected:** Message stored in database

**Pass Criteria:**
- ✅ Invalid UUID format returns 400 error
- ✅ Non-existent UUID returns 404 error
- ✅ Missing header auto-creates session
- ✅ Error messages follow OpenAI format
- ✅ Auto-created session ID returned in response header

**Screenshot Locations:**
- [ ] Screenshot 1: curl output showing 400 error
- [ ] Screenshot 2: curl output showing 404 error
- [ ] Screenshot 3: curl output showing auto-creation with header

---

## Performance Validation

### Response Time Monitoring

During all test scenarios, monitor and record response times:

**Timing Checkpoints:**
1. **Context Retrieval:** Should be <50ms (check database query logs)
2. **Total Request Time:** Should be <5 seconds (from send to response)
3. **Concurrent Users:** Test with 2 browser tabs simultaneously

**How to Measure:**
- Browser DevTools Network tab (OpenWebUI)
- curl with `-w "\nTime: %{time_total}s\n"` flag
- PostgreSQL query logs: `SET log_min_duration_statement = 0;`

**Pass Criteria:**
- ✅ 95% of requests complete in <5 seconds
- ✅ Context retrieval queries <50ms
- ✅ No timeout errors

---

## Acceptance Checklist

Before completing manual testing, verify all scenarios pass:

- [ ] **Scenario 1:** Multi-turn conversation works with context retention
- [ ] **Scenario 2:** CLI sessions are isolated (no cross-run context)
- [ ] **Scenario 3:** Container restart preserves all data (zero loss)
- [ ] **Scenario 4:** Error handling works for invalid session IDs
- [ ] **Performance:** All response times within acceptable limits
- [ ] **Screenshots:** All required screenshots captured and stored
- [ ] **Database:** All SQL queries return expected results
- [ ] **Issues:** All bugs documented and reported

---

## Issue Reporting Template

If any test fails, report using this template:

**Issue Title:** [FEAT-008] [Scenario X] Brief description

**Test Scenario:** Scenario number and name

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Result:** What should happen

**Actual Result:** What actually happened

**Screenshots:** Attach relevant screenshots

**Database State:** Include SQL query results if relevant

**Environment:**
- Docker version:
- Browser version (if OpenWebUI):
- Date/time of test:

**Severity:** Critical / High / Medium / Low

---

## Notes for Testers

**Common Issues to Watch For:**
- OpenWebUI caching old responses (clear browser cache)
- Database connection timeout after container restart (wait 30s)
- Multiple browser tabs creating different sessions (expected behavior)

**Tips:**
- Keep database terminal window open during testing
- Use different browser for each concurrent user test
- Document session IDs in test notes for traceability
- Take screenshots immediately when issues occur

**Questions?**
Contact development team with any questions about expected behavior or test setup.

---

**Test Status:** Ready for Execution
**Estimated Time:** 60-90 minutes for all scenarios
**Prerequisites:** All automated tests must pass before manual testing begins
