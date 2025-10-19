-- =============================================================================
-- PostgreSQL + pgvector Initialization Script
-- =============================================================================
-- This script runs FIRST when the PostgreSQL container starts for the first time.
-- It ensures the pgvector extension is available.
--
-- Files in /docker-entrypoint-initdb.d/ run in alphabetical order:
--   1. 00_init.sql (this file) - Enable pgvector extension
--   2. schema.sql - Create base tables
--   3. evi_schema_additions.sql - Create EVI-specific additions
--
-- =============================================================================

-- Enable the pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is loaded
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION 'pgvector extension failed to load!';
    END IF;
    RAISE NOTICE 'pgvector extension loaded successfully';
END $$;

-- Also ensure other useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

RAISE NOTICE 'All required extensions loaded. Ready for schema creation.';
