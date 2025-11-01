-- EVI 360 RAG System - Schema Extensions
-- This file contains schema additions specific to the EVI workplace safety system
-- Run this AFTER the base schema.sql

-- =============================================================================
-- 1. Add tier column to chunks table for guideline hierarchy
-- =============================================================================

-- Add tier column to chunks table (1=summary, 2=key facts, 3=details)
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS tier INTEGER CHECK (tier IN (1, 2, 3));

-- Create index on tier for efficient filtering
CREATE INDEX IF NOT EXISTS idx_chunks_tier ON chunks (tier);

-- Create composite index for tier + embedding searches
CREATE INDEX IF NOT EXISTS idx_chunks_tier_document ON chunks (tier, document_id);

-- =============================================================================
-- 2. Create products table for EVI 360 product catalog
-- =============================================================================

DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    category TEXT,
    subcategory TEXT,
    -- Product embedding for semantic search
    embedding vector(1536),
    -- Compliance and safety tags (e.g., ["fall_protection", "EN_361", "CE_certified"])
    compliance_tags TEXT[] DEFAULT '{}',
    -- Additional metadata (price, availability, specifications, etc.)
    metadata JSONB DEFAULT '{}',
    -- Scraping metadata
    source TEXT DEFAULT 'evi360_website',
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for product table
CREATE INDEX idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_compliance_tags ON products USING GIN (compliance_tags);
CREATE INDEX idx_products_metadata ON products USING GIN (metadata);
CREATE INDEX idx_products_url ON products (url);

-- Trigger for updated_at
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 3. Update hybrid_search function for Dutch language support
-- =============================================================================

-- Drop and recreate hybrid_search with Dutch language support
DROP FUNCTION IF EXISTS hybrid_search(vector, TEXT, INT, FLOAT);

CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 10,
    text_weight FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    combined_score FLOAT,
    vector_similarity FLOAT,
    text_similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT,
    source_url TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            1 - (c.embedding <=> query_embedding) AS vector_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source,
            d.metadata->>'source_url' AS source_url
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL
    ),
    text_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            -- Updated to use Dutch language for full-text search
            ts_rank_cd(to_tsvector('dutch', c.content), plainto_tsquery('dutch', query_text)) AS text_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source,
            d.metadata->>'source_url' AS source_url
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        -- Updated to use Dutch language for full-text search
        WHERE to_tsvector('dutch', c.content) @@ plainto_tsquery('dutch', query_text)
    )
    SELECT
        COALESCE(v.chunk_id, t.chunk_id) AS chunk_id,
        COALESCE(v.document_id, t.document_id) AS document_id,
        COALESCE(v.content, t.content) AS content,
        CAST((COALESCE(v.vector_sim, 0) * (1 - text_weight) + COALESCE(t.text_sim, 0) * text_weight) AS DOUBLE PRECISION) AS combined_score,
        CAST(COALESCE(v.vector_sim, 0) AS DOUBLE PRECISION) AS vector_similarity,
        CAST(COALESCE(t.text_sim, 0) AS DOUBLE PRECISION) AS text_similarity,
        COALESCE(v.metadata, t.metadata) AS metadata,
        COALESCE(v.doc_title, t.doc_title) AS document_title,
        COALESCE(v.doc_source, t.doc_source) AS document_source,
        COALESCE(v.source_url, t.source_url) AS source_url
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.chunk_id = t.chunk_id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;

-- =============================================================================
-- 4. Create tier-aware search function for guidelines
-- =============================================================================

CREATE OR REPLACE FUNCTION search_guidelines_by_tier(
    query_embedding vector(1536),
    query_text TEXT,
    tier_filter INTEGER DEFAULT NULL,  -- NULL means search all tiers
    match_count INT DEFAULT 10,
    text_weight FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    tier INTEGER,
    combined_score FLOAT,
    vector_similarity FLOAT,
    text_similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            c.tier,
            1 - (c.embedding <=> query_embedding) AS vector_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL
            AND (tier_filter IS NULL OR c.tier = tier_filter)
    ),
    text_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            c.tier,
            ts_rank_cd(to_tsvector('dutch', c.content), plainto_tsquery('dutch', query_text)) AS text_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE to_tsvector('dutch', c.content) @@ plainto_tsquery('dutch', query_text)
            AND (tier_filter IS NULL OR c.tier = tier_filter)
    )
    SELECT
        COALESCE(v.chunk_id, t.chunk_id) AS chunk_id,
        COALESCE(v.document_id, t.document_id) AS document_id,
        COALESCE(v.content, t.content) AS content,
        COALESCE(v.tier, t.tier) AS tier,
        CAST((COALESCE(v.vector_sim, 0) * (1 - text_weight) + COALESCE(t.text_sim, 0) * text_weight) AS DOUBLE PRECISION) AS combined_score,
        CAST(COALESCE(v.vector_sim, 0) AS DOUBLE PRECISION) AS vector_similarity,
        CAST(COALESCE(t.text_sim, 0) AS DOUBLE PRECISION) AS text_similarity,
        COALESCE(v.metadata, t.metadata) AS metadata,
        COALESCE(v.doc_title, t.doc_title) AS document_title,
        COALESCE(v.doc_source, t.doc_source) AS document_source
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.chunk_id = t.chunk_id
    ORDER BY
        -- Prioritize lower tiers (1=summary, 2=key facts) when no tier filter
        CASE WHEN tier_filter IS NULL THEN COALESCE(v.tier, t.tier) ELSE 0 END ASC,
        combined_score DESC
    LIMIT match_count;
END;
$$;

-- =============================================================================
-- 5. Create product search function
-- =============================================================================

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

-- =============================================================================
-- 6. Create view for guideline statistics by tier
-- =============================================================================

CREATE OR REPLACE VIEW guideline_tier_stats AS
SELECT
    tier,
    COUNT(*) AS chunk_count,
    COUNT(DISTINCT document_id) AS document_count,
    AVG(token_count) AS avg_token_count,
    MIN(created_at) AS oldest_chunk,
    MAX(created_at) AS newest_chunk
FROM chunks
WHERE tier IS NOT NULL
GROUP BY tier
ORDER BY tier;

-- =============================================================================
-- 7. Create view for product catalog summary
-- =============================================================================

CREATE OR REPLACE VIEW product_catalog_summary AS
WITH unnested_tags AS (
    SELECT
        category,
        unnest(compliance_tags) AS tag,
        created_at,
        last_scraped_at,
        subcategory
    FROM products
    WHERE category IS NOT NULL
)
SELECT
    category,
    COUNT(*) AS product_count,
    COUNT(DISTINCT subcategory) AS subcategory_count,
    array_agg(DISTINCT tag) AS all_compliance_tags,
    MIN(created_at) AS oldest_product,
    MAX(last_scraped_at) AS last_scrape
FROM unnested_tags
GROUP BY category
ORDER BY product_count DESC;

-- =============================================================================
-- 8. Comments for documentation
-- =============================================================================

COMMENT ON COLUMN chunks.tier IS 'Guideline tier: 1=Summary, 2=Key Facts, 3=Detailed Content';
COMMENT ON TABLE products IS 'EVI 360 product catalog with embeddings for semantic search';
COMMENT ON COLUMN products.compliance_tags IS 'Safety standards and compliance tags (e.g., EN_361, CE_certified)';
COMMENT ON FUNCTION search_guidelines_by_tier IS 'Tier-aware hybrid search for guidelines with Dutch language support';
COMMENT ON FUNCTION search_products IS 'Semantic search for products with compliance tag filtering';
