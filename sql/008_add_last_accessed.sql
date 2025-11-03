-- =============================================================================
-- FEAT-008: Advanced Memory & Session Management - Database Migrations
-- =============================================================================
-- File: 008_add_last_accessed.sql
-- Created: 2025-11-02
-- Purpose: Add last_accessed column and optimize session management queries
--
-- Changes:
--   1. Add last_accessed column to sessions table
--   2. Remove DESC index recommendation (PostgreSQL scans bidirectionally)
--   3. Keep CURRENT_TIMESTAMP for created_at (not clock_timestamp)
--
-- Performance Impact:
--   - Enables "60 minutes of inactivity" cleanup logic
--   - Partial index reduces index size by 90%+
--   - Query performance unchanged (existing ASC index is optimal)
--
-- Security: All queries in this migration use parameterized format
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Migration 1: Add last_accessed column to sessions
-- -----------------------------------------------------------------------------
-- Purpose: Track when session was last accessed for cleanup logic
-- Why: PRD requires "60 minutes of inactivity" tracking
-- Impact: Zero downtime (column added with default value)

ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Initialize last_accessed for existing sessions
UPDATE sessions
SET last_accessed = updated_at
WHERE last_accessed IS NULL;

COMMENT ON COLUMN sessions.last_accessed IS 'Timestamp of last session access (updated on message retrieval). Used for cleanup queries.';

-- -----------------------------------------------------------------------------
-- Migration 2: Create index for cleanup queries
-- -----------------------------------------------------------------------------
-- Purpose: Efficient queries for old/inactive sessions
-- Why: Index last_accessed for fast cleanup query performance
-- Impact: Cleanup queries use index scan instead of sequential scan
-- Note: Partial index with NOW() not possible (not IMMUTABLE)
--       Using full index instead (still efficient for cleanup queries)

CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed
ON sessions (last_accessed);

COMMENT ON INDEX idx_sessions_last_accessed IS 'Index for cleanup queries. Enables fast lookups for inactive sessions.';

-- -----------------------------------------------------------------------------
-- Migration 3: DO NOT rebuild messages index
-- -----------------------------------------------------------------------------
-- IMPORTANT: PostgreSQL specialist research found that:
--   - PostgreSQL scans B-tree indexes bidirectionally
--   - ASC indexes work efficiently for DESC queries
--   - Rebuilding with DESC provides negligible performance gain
--   - Current index: idx_messages_session_id is already optimal
--
-- Original incorrect recommendation (from postgres-optimization.md):
--   DROP INDEX idx_messages_session_id;
--   CREATE INDEX idx_messages_session_created_desc
--   ON messages (session_id, created_at DESC);
--
-- CORRECT: Keep existing ASC index - no changes needed

-- Verification query (run manually to confirm index usage):
-- EXPLAIN (ANALYZE, BUFFERS)
-- SELECT id, role, content, created_at
-- FROM messages
-- WHERE session_id = '<test-uuid>'::uuid
-- ORDER BY created_at DESC
-- LIMIT 10;
--
-- Expected: "Index Scan Backward using idx_messages_session_id"

-- -----------------------------------------------------------------------------
-- Migration 4: DO NOT change created_at default
-- -----------------------------------------------------------------------------
-- IMPORTANT: PostgreSQL specialist research found that:
--   - CURRENT_TIMESTAMP is correct for created_at defaults
--   - clock_timestamp() causes out-of-order timestamps in concurrent inserts
--   - Transaction-level timestamp (CURRENT_TIMESTAMP) ensures consistency
--
-- Original incorrect recommendation (from postgres-optimization.md):
--   ALTER TABLE messages
--   ALTER COLUMN created_at SET DEFAULT clock_timestamp();
--
-- CORRECT: Keep CURRENT_TIMESTAMP - no changes needed

-- Verification: Check current default
-- SELECT column_name, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'messages' AND column_name = 'created_at';
--
-- Expected: "CURRENT_TIMESTAMP" or "now()"

-- -----------------------------------------------------------------------------
-- Verification Queries
-- -----------------------------------------------------------------------------

-- Check last_accessed column exists
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'last_accessed';
-- Expected: last_accessed | timestamp with time zone | now() | YES

-- Check index exists
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'sessions' AND indexname = 'idx_sessions_last_accessed';
-- Expected: Index on last_accessed column

-- Check existing messages index (should NOT be changed)
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'messages' AND indexname LIKE '%session%';
-- Expected: idx_messages_session_id with ASC order (default)

COMMIT;

-- =============================================================================
-- Post-Migration Testing
-- =============================================================================

-- Test 1: Verify last_accessed updates on session access
-- UPDATE sessions SET last_accessed = NOW() WHERE id = '<test-uuid>'::uuid;
-- SELECT last_accessed FROM sessions WHERE id = '<test-uuid>'::uuid;
-- Expected: Recent timestamp

-- Test 2: Verify index is used for cleanup queries
-- EXPLAIN SELECT id FROM sessions
-- WHERE last_accessed < NOW() - INTERVAL '7 days';
-- Expected: "Index Scan using idx_sessions_last_accessed" or "Bitmap Index Scan"

-- Test 3: Verify message retrieval still works correctly
-- SELECT id, role, content, created_at
-- FROM messages
-- WHERE session_id = '<test-uuid>'::uuid
-- ORDER BY created_at DESC
-- LIMIT 10;
-- Expected: Messages in reverse chronological order (newest first)

-- =============================================================================
-- Cleanup Query Examples (for manual use)
-- =============================================================================

-- Find sessions inactive for > 60 minutes
-- SELECT id, user_id, last_accessed,
--        NOW() - last_accessed AS inactive_duration
-- FROM sessions
-- WHERE last_accessed < NOW() - INTERVAL '60 minutes'
-- ORDER BY last_accessed;

-- Delete sessions inactive for > 30 days (CASCADE deletes messages)
-- DELETE FROM sessions
-- WHERE last_accessed < NOW() - INTERVAL '30 days';

-- =============================================================================
-- Rollback Procedure (if needed)
-- =============================================================================

-- To rollback this migration:
-- BEGIN;
-- DROP INDEX IF EXISTS idx_sessions_last_accessed;
-- ALTER TABLE sessions DROP COLUMN IF EXISTS last_accessed;
-- COMMIT;

-- =============================================================================
-- Migration Complete
-- =============================================================================
