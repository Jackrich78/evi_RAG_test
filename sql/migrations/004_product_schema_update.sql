-- Migration 004: Product Schema Update for FEAT-004
-- Updates products table schema and search_products() function for hybrid search
--
-- Changes:
--   1. ADD price TEXT column
--   2. DROP subcategory column (not used)
--   3. DROP compliance_tags column (replaced by metadata)
--   4. DROP compliance_tags index
--   5. UPDATE search_products() function to use hybrid search (70% vector + 30% Dutch text)
--
-- Author: Claude Code
-- Date: 2025-11-04
-- FEAT: FEAT-004

BEGIN;

-- =============================================================================
-- STEP 1: Schema Changes
-- =============================================================================

-- Add price column (nullable, as not all products have pricing)
ALTER TABLE products
ADD COLUMN IF NOT EXISTS price TEXT;

-- Drop unused columns
ALTER TABLE products
DROP COLUMN IF EXISTS subcategory CASCADE;

ALTER TABLE products
DROP COLUMN IF EXISTS compliance_tags CASCADE;

-- Drop compliance_tags index (cascade already handled it, but explicit is good)
DROP INDEX IF EXISTS idx_products_compliance_tags;

-- Add comment to price column
COMMENT ON COLUMN products.price IS 'Product price (e.g., "Vanaf € 1297/stuk" or NULL if not available)';

-- =============================================================================
-- STEP 2: Update search_products() Function
-- =============================================================================

-- Drop old function (with old signature)
DROP FUNCTION IF EXISTS search_products(vector, TEXT, TEXT[], INT);
DROP FUNCTION IF EXISTS search_products(vector, TEXT, INT);

-- Create new hybrid search function
-- Combines vector similarity (70%) with Dutch full-text search (30%)
CREATE OR REPLACE FUNCTION search_products(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    product_id UUID,
    name TEXT,
    description TEXT,
    price TEXT,
    url TEXT,
    category TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        -- Vector similarity search
        SELECT
            p.id,
            p.name,
            p.description,
            p.price,
            p.url,
            p.category,
            1 - (p.embedding <=> query_embedding) AS vector_sim,
            p.metadata
        FROM products p
        WHERE p.embedding IS NOT NULL
    ),
    text_results AS (
        -- Dutch full-text search
        SELECT
            p.id,
            p.name,
            p.description,
            p.price,
            p.url,
            p.category,
            ts_rank_cd(
                to_tsvector('dutch', p.description),
                plainto_tsquery('dutch', query_text)
            ) AS text_sim,
            p.metadata
        FROM products p
        WHERE to_tsvector('dutch', p.description) @@ plainto_tsquery('dutch', query_text)
    )
    -- Combine results with 70/30 weighting
    SELECT
        COALESCE(v.id, t.id) AS product_id,
        COALESCE(v.name, t.name) AS name,
        COALESCE(v.description, t.description) AS description,
        COALESCE(v.price, t.price) AS price,
        COALESCE(v.url, t.url) AS url,
        COALESCE(v.category, t.category) AS category,
        -- Hybrid similarity: 70% vector + 30% text
        CAST(
            (COALESCE(v.vector_sim, 0) * 0.7 + COALESCE(t.text_sim, 0) * 0.3)
            AS DOUBLE PRECISION
        ) AS similarity,
        COALESCE(v.metadata, t.metadata) AS metadata
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.id = t.id
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

-- Add function comment
COMMENT ON FUNCTION search_products IS 'Hybrid product search: 70% vector similarity + 30% Dutch full-text search';

-- =============================================================================
-- STEP 3: Validation
-- =============================================================================

-- Verify schema changes
DO $$
DECLARE
    price_exists BOOLEAN;
    subcategory_exists BOOLEAN;
    compliance_tags_exists BOOLEAN;
BEGIN
    -- Check price column exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'price'
    ) INTO price_exists;

    IF NOT price_exists THEN
        RAISE EXCEPTION 'Migration failed: price column not added';
    END IF;

    -- Check subcategory removed
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'subcategory'
    ) INTO subcategory_exists;

    IF subcategory_exists THEN
        RAISE EXCEPTION 'Migration failed: subcategory column not removed';
    END IF;

    -- Check compliance_tags removed
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'compliance_tags'
    ) INTO compliance_tags_exists;

    IF compliance_tags_exists THEN
        RAISE EXCEPTION 'Migration failed: compliance_tags column not removed';
    END IF;

    RAISE NOTICE 'Schema validation: ✅ PASSED';
END;
$$;

-- Verify function exists
DO $$
DECLARE
    function_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_proc
        WHERE proname = 'search_products'
    ) INTO function_exists;

    IF NOT function_exists THEN
        RAISE EXCEPTION 'Migration failed: search_products function not created';
    END IF;

    RAISE NOTICE 'Function validation: ✅ PASSED';
END;
$$;

COMMIT;

-- =============================================================================
-- Post-Migration Notes
-- =============================================================================

-- Migration complete!
--
-- Next steps:
-- 1. Run ingestion: python3 -m ingestion.ingest_products
-- 2. Verify 60 products inserted
-- 3. Test hybrid search: SELECT * FROM search_products('[embedding]', 'burn-out', 5);
--
-- Rollback script: sql/migrations/004_rollback.sql
