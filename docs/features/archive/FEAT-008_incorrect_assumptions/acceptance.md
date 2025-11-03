# Acceptance Criteria: Advanced Memory & Session Management

**Feature ID:** FEAT-008
**Created:** 2025-11-02
**Status:** Planning Phase

## User Stories

### Story 1: Multi-Turn Conversation in OpenWebUI

**As a** workplace safety specialist
**I want to** ask follow-up questions that reference previous context
**So that** I can have natural conversations without repeating information

**Acceptance Criteria:**

**AC-FEAT-008-001:** Multi-Turn Context Retention
- **Given** a user has asked "Wat zijn de vereisten voor valbeveiliging?" in OpenWebUI
- **When** the user asks a follow-up question "Welke producten heb je daarvoor?"
- **Then** the agent references the previous context (valbeveiliging) in its response
- **And** both messages are stored in the same session in PostgreSQL
- **And** the response includes relevant products for fall protection

**AC-FEAT-008-002:** Session Persistence Across Requests
- **Given** a user has an active session with 5 previous messages
- **When** the user sends a new message
- **Then** the agent loads the last 10 messages from the session as context
- **And** the new message is stored in the same session
- **And** the session's last_accessed timestamp is updated

**AC-FEAT-008-003:** Session ID Header Handling
- **Given** OpenWebUI sends a request with X-Session-ID header containing a valid UUID
- **When** the /v1/chat/completions endpoint processes the request
- **Then** the server retrieves the existing session from PostgreSQL
- **And** the response includes the same X-Session-ID header value
- **And** the context from that session is used in the agent response

### Story 2: CLI Session Isolation

**As a** developer using the CLI
**I want** each CLI run to start a fresh conversation
**So that** testing scenarios don't interfere with each other

**Acceptance Criteria:**

**AC-FEAT-008-004:** New Session Per CLI Execution
- **Given** a user runs cli.py and asks 3 questions
- **When** the user exits and runs cli.py again
- **Then** a new session is created in PostgreSQL
- **And** the new session has a different UUID than the previous session
- **And** no context from the previous CLI run is available

**AC-FEAT-008-005:** CLI Session Auto-Creation
- **Given** cli.py starts without an X-Session-ID header
- **When** the first message is sent to /v1/chat/completions
- **Then** the server creates a new session automatically
- **And** returns the session UUID in the X-Session-ID response header
- **And** cli.py uses this session ID for subsequent messages in the same run

### Story 3: Container Restart Persistence

**As a** system administrator
**I want** conversation history to survive container restarts
**So that** users don't lose context during deployments or maintenance

**Acceptance Criteria:**

**AC-FEAT-008-006:** Session Persistence After Container Restart
- **Given** a session exists with 5 messages in PostgreSQL
- **When** docker-compose down is executed followed by docker-compose up
- **Then** all 5 messages are still present in the database
- **And** the session can be resumed with full context
- **And** new messages can be added to the session

**AC-FEAT-008-007:** No Data Loss on Restart
- **Given** a user is actively using OpenWebUI with an ongoing conversation
- **When** the container restarts (docker-compose restart)
- **Then** the user can continue the conversation from where they left off
- **And** all previous messages are available as context
- **And** no messages are lost or corrupted

## Edge Cases

**AC-FEAT-008-101:** Invalid UUID Format in X-Session-ID Header
- **Given** a client sends X-Session-ID header with value "not-a-uuid"
- **When** the /v1/chat/completions endpoint validates the header
- **Then** the server returns HTTP 400 Bad Request
- **And** the error message states "Invalid session ID format: must be valid UUID"
- **And** the response follows OpenAI error format

**AC-FEAT-008-102:** Missing X-Session-ID Header
- **Given** a client sends a request without X-Session-ID header
- **When** the /v1/chat/completions endpoint processes the request
- **Then** the server creates a new session automatically
- **And** returns the new session UUID in X-Session-ID response header
- **And** the message is stored in the new session

**AC-FEAT-008-103:** Concurrent Requests with Same Session ID
- **Given** two requests are sent simultaneously with the same X-Session-ID
- **When** both requests attempt to add messages to the session
- **Then** PostgreSQL handles the concurrent writes safely
- **And** both messages are stored in the session
- **And** no data corruption or race conditions occur
- **And** last_accessed timestamp reflects the latest request

**AC-FEAT-008-104:** Session with 100+ Messages
- **Given** a session has 150 messages stored in PostgreSQL
- **When** the agent loads context for a new message
- **Then** only the last 10 messages are retrieved (LIMIT 10)
- **And** context retrieval completes in <50ms
- **And** the agent response uses only those 10 messages as context

**AC-FEAT-008-105:** Empty Session (Zero Messages)
- **Given** a newly created session has 0 messages
- **When** the first message is sent to the session
- **Then** the agent processes the message without errors
- **And** returns an empty context (no previous messages)
- **And** the response is based only on the current query

**AC-FEAT-008-106:** Non-Existent Session ID
- **Given** a client sends X-Session-ID header with a valid UUID that doesn't exist in database
- **When** the /v1/chat/completions endpoint tries to retrieve the session
- **Then** the server returns HTTP 404 Not Found
- **And** the error message states "Session not found: {session_id}"
- **And** suggests creating a new session by omitting the header

**AC-FEAT-008-107:** SQL Injection Attempt via LIMIT Parameter
- **Given** get_session_messages() is called with malicious limit value "10; DROP TABLE messages;"
- **When** the database query is executed
- **Then** the query uses parameterized query (no f-string interpolation)
- **And** no SQL injection occurs
- **And** the malicious input is treated as invalid parameter

**AC-FEAT-008-108:** Message Order Correctness
- **Given** a session has messages with timestamps: t1, t2, t3, t4, t5 (oldest to newest)
- **When** get_session_messages(session_id, limit=3) is called
- **Then** messages returned are [t3, t4, t5] in chronological order (oldest first)
- **And** the query uses ORDER BY created_at DESC with result reversal
- **And** messages are passed to PydanticAI in correct order for context

## Non-Functional Requirements

**AC-FEAT-008-201:** Context Retrieval Performance
- **Given** a session with 50 messages
- **When** get_session_messages(session_id, limit=10) is executed
- **Then** the query completes in less than 50 milliseconds
- **And** database connection pool handles 20 concurrent queries
- **And** no query timeout errors occur

**AC-FEAT-008-202:** Total Query Time Budget
- **Given** a user sends a message to /v1/chat/completions
- **When** the request includes context loading, agent processing, and message storage
- **Then** the total time from request to response is less than 5 seconds
- **And** context loading takes <50ms
- **And** agent processing + RAG takes <4s
- **And** message storage takes <100ms

**AC-FEAT-008-203:** Zero Data Loss on Container Restart
- **Given** 100 sessions with 1000 total messages exist in PostgreSQL
- **When** docker-compose down and docker-compose up are executed
- **Then** all 100 sessions are still present
- **And** all 1000 messages are still present
- **And** SELECT COUNT(*) FROM sessions and messages returns correct counts

**AC-FEAT-008-204:** Token Limit Awareness (Not Enforced in v1)
- **Given** a session has 10 messages with combined context of 6K tokens
- **When** a new 2K token query is added
- **Then** the system is aware total is 8K tokens (context + query)
- **And** no enforcement is applied in FEAT-008 (future feature)
- **And** PydanticAI handles token limits internally

**AC-FEAT-008-205:** Session Cleanup Automation
- **Given** a session has last_accessed timestamp of 31 days ago
- **When** the automatic cleanup job runs (pg_cron or trigger)
- **Then** the session is deleted from the sessions table
- **And** all associated messages are deleted via CASCADE
- **And** no orphaned messages remain in the database

**AC-FEAT-008-206:** Concurrent User Scalability
- **Given** 20 users are actively sending messages simultaneously
- **When** each user has their own session
- **Then** all 20 sessions can retrieve context in <50ms
- **And** database connection pool (max_size=20) handles the load
- **And** no connection pool exhaustion errors occur

**AC-FEAT-008-207:** Database Schema Integrity
- **Given** the sessions table has last_accessed column added
- **When** a new message is added with add_message()
- **Then** the last_accessed column is updated to NOW()
- **And** the column has type TIMESTAMP WITH TIME ZONE
- **And** the column is indexed for cleanup query performance

## Security Requirements

**AC-FEAT-008-301:** SQL Injection Prevention
- **Given** any function that accepts user input for database queries
- **When** the query is executed (especially get_session_messages with LIMIT)
- **Then** parameterized queries are used (no f-string interpolation)
- **And** all user inputs are sanitized
- **And** SQL injection attempts are prevented

**AC-FEAT-008-302:** Session ID Validation
- **Given** a client sends X-Session-ID header
- **When** the server validates the header value
- **Then** only valid UUID v4 format is accepted
- **And** any invalid format returns 400 error
- **And** no arbitrary strings can be used as session IDs

## Testing Requirements

**AC-FEAT-008-401:** Unit Test Coverage
- **Given** session management functions (create_session, add_message, get_session_messages)
- **When** unit tests are executed
- **Then** code coverage is at least 90%
- **And** all edge cases have dedicated test cases
- **And** all error paths are tested

**AC-FEAT-008-402:** Integration Test Coverage
- **Given** the full session lifecycle (create → add messages → retrieve context)
- **When** integration tests are executed
- **Then** end-to-end flows are validated
- **And** database interactions are tested with real PostgreSQL
- **And** container restart persistence is verified

**AC-FEAT-008-403:** Manual Testing Completion
- **Given** the manual testing guide in manual-test.md
- **When** a tester follows all test scenarios
- **Then** all scenarios pass successfully
- **And** screenshots/evidence are captured
- **And** any issues are documented and resolved

## Traceability

**Related Documents:**
- PRD: docs/features/FEAT-008_advanced-memory/prd.md
- Architecture: docs/features/FEAT-008_advanced-memory/architecture.md
- Testing Strategy: docs/features/FEAT-008_advanced-memory/testing.md
- Manual Test Guide: docs/features/FEAT-008_advanced-memory/manual-test.md

**Implementation Files:**
- agent/api.py (lines 678-800: /v1/chat/completions endpoint)
- agent/db_utils.py (lines 84-259: session management functions)
- agent/specialist_agent.py (context injection)
- sql/migrations/008_add_last_accessed.sql (schema change)

**Global Registry:**
- All acceptance criteria appended to /AC.md with unique IDs

---

**Total Acceptance Criteria:** 28 criteria (3 user stories + 8 edge cases + 7 non-functional + 2 security + 3 testing)
**Status:** Ready for Implementation
