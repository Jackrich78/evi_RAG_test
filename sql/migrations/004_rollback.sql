-- Rollback for Migration 004: Product Schema Update
-- Reverts changes from 004_product_schema_update.sql
--
-- WARNING: This will DROP the price column and data will be lost!
--
-- Author: Claude Code
-- Date: 2025-11-04

BEGIN;

-- Restore old columns (will be empty)
ALTER TABLE products
ADD COLUMN IF NOT EXISTS subcategory TEXT;

ALTER TABLE products
ADD COLUMN IF NOT EXISTS compliance_tags TEXT[] DEFAULT '{}';

-- Remove price column
ALTER TABLE products
DROP COLUMN IF EXISTS price;

-- Recreate compliance_tags index
CREATE INDEX IF NOT EXISTS idx_products_compliance_tags
ON products USING GIN (compliance_tags);

-- Restore old search_products function (vector-only)
DROP FUNCTION IF EXISTS search_products(vector, TEXT, INT);

CREATE OR REPLACE FUNCTION search_products(
    query_embedding vector(1536),
    query_text TEXT,
    compliance_tags_filter TEXT[] DEFAULT NULL,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    product_id UUID,
    name TEXT,
    description TEXT,
    url TEXT,
    category TEXT,
    similarity FLOAT,
    compliance_tags TEXT[],
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id AS product_id,
        p.name,
        p.description,
        p.url,
        p.category,
        1 - (p.embedding <=> query_embedding) AS similarity,
        p.compliance_tags,
        p.metadata
    FROM products p
    WHERE p.embedding IS NOT NULL
        AND (compliance_tags_filter IS NULL OR p.compliance_tags && compliance_tags_filter)
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMIT;

-- Rollback complete
-- Note: Price data is LOST. Backup before rollback if needed.
