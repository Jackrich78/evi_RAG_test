# FEAT-008 Planning Phase Summary

**Feature:** Advanced Memory & Session Management
**Status:** Planning Complete - Ready for Reviewer Validation
**Date:** 2025-11-02

## Documents Created

### 1. Architecture Decision
**File:** `/Users/builder/dev/evi_rag_test/docs/features/FEAT-008_advanced-memory/architecture.md`
**Word Count:** 785 words (within 800 limit)
**Status:** Complete

**Key Decisions:**
- **Selected Approach:** Option 1 - X-Session-ID Header with PostgreSQL Session Storage
- **Rejected Alternatives:** Stateless API (Option 2), Hybrid approach (Option 3)
- **Trade-offs:** +30ms latency per request, clients must track session IDs
- **Spike Plan:** 5 steps (19 hours total estimated)

**Database Specialist Consultation Requested:**
- Schema optimization for last_accessed column
- Query performance with parameterized LIMIT
- Connection pool sizing (max_size=20)
- Cleanup strategy (pg_cron vs trigger)
- CASCADE delete verification

### 2. Acceptance Criteria
**File:** `/Users/builder/dev/evi_rag_test/docs/features/FEAT-008_advanced-memory/acceptance.md`
**Status:** Complete

**Criteria Breakdown:**
- **User Stories:** 7 criteria (AC-FEAT-008-001 to AC-FEAT-008-007)
- **Edge Cases:** 8 criteria (AC-FEAT-008-101 to AC-FEAT-008-108)
- **Non-Functional:** 7 criteria (AC-FEAT-008-201 to AC-FEAT-008-207)
- **Security:** 2 criteria (AC-FEAT-008-301 to AC-FEAT-008-302)
- **Testing:** 3 criteria (AC-FEAT-008-401 to AC-FEAT-008-403)
- **Total:** 28 acceptance criteria

**Critical Criteria:**
- AC-FEAT-008-107, AC-FEAT-008-301: SQL injection prevention (CRITICAL)
- AC-FEAT-008-201: Context retrieval <50ms (PERFORMANCE)
- AC-FEAT-008-203: Zero data loss on container restart (RELIABILITY)

### 3. Testing Strategy
**File:** `/Users/builder/dev/evi_rag_test/docs/features/FEAT-008_advanced-memory/testing.md`
**Status:** Complete

**Test Levels:**
- **Unit Tests:** 90% coverage target (18 test stubs created)
- **Integration Tests:** 80% coverage target (10 test stubs + 1 bash script)
- **Performance Tests:** 7 test stubs for latency and scalability
- **Security Tests:** 8 test stubs for SQL injection prevention
- **Manual E2E Tests:** 4 scenarios in manual-test.md

**Test Files Created:** 6 Python files + 1 bash script (43 total test stubs)

### 4. Manual Testing Guide
**File:** `/Users/builder/dev/evi_rag_test/docs/features/FEAT-008_advanced-memory/manual-test.md`
**Status:** Complete

**Test Scenarios:**
1. Multi-Turn Conversation in OpenWebUI (10 steps)
2. CLI Session Isolation (9 steps)
3. Container Restart Persistence (9 steps)
4. Invalid Session ID Error Handling (7 steps)

**Estimated Testing Time:** 60-90 minutes

## Test Stubs Created

### Unit Tests (18 stubs)

**File:** `/Users/builder/dev/evi_rag_test/tests/agent/test_db_utils_session.py`
- test_create_session_with_last_accessed()
- test_create_session_returns_uuid()
- test_get_session_by_id_success()
- test_get_session_by_id_not_found()
- test_add_message_updates_last_accessed()
- test_add_message_stores_correctly()
- test_get_session_messages_sql_injection_safe()
- test_get_session_messages_order_correct()
- test_get_session_messages_limit_10()
- test_get_session_messages_empty_session()
- test_get_session_messages_performance()
- test_cascade_delete_messages()

**File:** `/Users/builder/dev/evi_rag_test/tests/agent/test_api_session_header.py`
- test_x_session_id_header_valid_uuid()
- test_x_session_id_header_invalid_uuid()
- test_x_session_id_header_missing()
- test_x_session_id_header_non_existent()
- test_x_session_id_response_header()
- test_x_session_id_auto_creation_response()
- test_x_session_id_case_insensitive()
- test_x_session_id_empty_string()
- test_x_session_id_whitespace_trimmed()

**File:** `/Users/builder/dev/evi_rag_test/tests/agent/test_specialist_context.py`
- test_context_loaded_in_message_history()
- test_context_format_pydantic_ai()
- test_context_empty_for_new_session()
- test_context_includes_last_10_messages()
- test_context_message_roles_preserved()
- test_context_content_escaped()
- test_new_message_appended_after_agent_response()
- test_context_injection_not_system_prompt()

### Integration Tests (10 stubs + 1 script)

**File:** `/Users/builder/dev/evi_rag_test/tests/integration/test_session_flow.py`
- test_create_session_add_messages_retrieve()
- test_multi_turn_conversation()
- test_concurrent_sessions_isolated()
- test_session_cleanup_old_sessions()
- test_cascade_delete_messages()
- test_concurrent_writes_same_session()
- test_session_with_100_messages_limit_10()
- test_last_accessed_updates_on_message_add()
- test_session_persistence_transaction_rollback()

**File:** `/Users/builder/dev/evi_rag_test/tests/integration/test_container_persistence.sh`
- Bash script for docker-compose down/up testing (10 steps)

### Performance Tests (7 stubs)

**File:** `/Users/builder/dev/evi_rag_test/tests/performance/test_context_retrieval_speed.py`
- test_get_messages_latency_50ms()
- test_concurrent_users_20()
- test_large_session_100_messages()
- test_total_request_time_5_seconds()
- test_database_connection_pool_efficiency()
- test_query_plan_optimization()
- test_memory_usage_large_sessions()

### Security Tests (8 stubs)

**File:** `/Users/builder/dev/evi_rag_test/tests/security/test_sql_injection.py`
- test_limit_sql_injection_prevention()
- test_session_id_input_validation()
- test_message_content_escaping()
- test_parameterized_queries_all_functions()
- test_order_by_injection_prevention()
- test_where_clause_injection_prevention()
- test_user_id_injection_prevention()
- test_role_parameter_validation()

**Total Test Stubs:** 43 test functions + 1 bash script

## Files to Update (Phase 2)

### Implementation Files
- `/Users/builder/dev/evi_rag_test/agent/api.py` (lines 678-800: add X-Session-ID header support)
- `/Users/builder/dev/evi_rag_test/agent/db_utils.py` (lines 84-259: fix SQL injection, add last_accessed)
- `/Users/builder/dev/evi_rag_test/agent/specialist_agent.py` (add message_history context injection)
- `/Users/builder/dev/evi_rag_test/cli.py` (add X-Session-ID header tracking)

### Database Schema
- `/Users/builder/dev/evi_rag_test/sql/migrations/008_add_last_accessed.sql` (new migration)
  - Add last_accessed TIMESTAMP WITH TIME ZONE to sessions table
  - Create index on last_accessed for cleanup queries
  - Create cleanup trigger or pg_cron job

### Global Registry
- `/Users/builder/dev/evi_rag_test/AC.md` (append 28 acceptance criteria with unique IDs)

## Next Steps

### 1. Append to AC.md
Update global acceptance criteria registry with all 28 criteria:
- AC-FEAT-008-001 through AC-FEAT-008-007 (User Stories)
- AC-FEAT-008-101 through AC-FEAT-008-108 (Edge Cases)
- AC-FEAT-008-201 through AC-FEAT-008-207 (Non-Functional)
- AC-FEAT-008-301 through AC-FEAT-008-302 (Security)
- AC-FEAT-008-401 through AC-FEAT-008-403 (Testing)

### 2. Invoke Reviewer Agent
Validation checklist for Reviewer:
- ✅ All 4 planning documents exist (architecture, acceptance, testing, manual-test)
- ✅ Documents follow templates from docs/templates/
- ✅ Word limits respected (architecture.md: 785 words ≤ 800)
- ✅ No TODO or placeholder content in planning docs (only in test stubs)
- ✅ Test stubs created in correct locations with proper naming
- ❓ Acceptance criteria appended to /AC.md (PENDING)
- ✅ All cross-references between docs are valid

### 3. Invoke Documenter Agent (after Reviewer passes)
Update documentation index:
- Update docs/README.md with FEAT-008 entry
- Update CHANGELOG.md with planning phase entry
- Ensure cross-references in documentation are valid

## Implementation Constraints (User Approved)

### Architecture Decisions Already Made:
1. ✅ X-Session-ID Header: ADD support to /v1/chat/completions endpoint
2. ✅ Context Window: Simple LIMIT 10 approach (fix SQL injection, use DESC + reverse)
3. ✅ Session Cleanup: Automatic cleanup with last_accessed column + trigger/pg_cron
4. ✅ Session ID Schema: Use sessions.id UUID directly (NO separate session_id field)
5. ✅ Context Injection: Use PydanticAI message_history parameter (NOT system prompt prefix)
6. ✅ Index Optimization: Defer DESC index rebuild to separate task (NOT part of FEAT-008)

### Critical Bugs to Fix:
- ❗ SQL Injection: get_session_messages() line 246 uses f" LIMIT {limit}" - MUST fix with parameterized query
- ❗ Message Order: Ensure ORDER BY created_at DESC + reverse list (correct chronology)

### Performance Requirements (Strict):
- Context retrieval: <50ms (AC-FEAT-008-201)
- Total request time: <5s (AC-FEAT-008-202)
- Concurrent users: 20 without errors (AC-FEAT-008-206)

## Database Specialist Input Needed

**Requesting consultation from postgres-supabase-specialist.md:**

**Questions:**
1. Schema optimization: Should last_accessed be separate column or reuse existing timestamp?
2. Query performance: Is parameterized LIMIT with ORDER BY created_at DESC indexed properly?
3. Connection pooling: Is max_size=20 sufficient for 20 concurrent users with session queries?
4. Cleanup strategy: pg_cron vs trigger vs application-level cleanup - which is best for Supabase?
5. Cascade delete: Verify foreign key constraint on messages.session_id handles cleanup safely

**Expected Input:**
- Recommended schema changes for last_accessed column
- Index recommendations for cleanup queries
- Connection pool sizing validation
- Cleanup implementation recommendation
- Performance estimates for 20 users, 2000 sessions, 40K messages

---

**Planning Status:** Complete (pending Reviewer validation and AC.md update)
**Ready for Phase 2:** Yes (after Reviewer approval)
**Estimated Implementation Time:** 3-4 days (per spike plan)
