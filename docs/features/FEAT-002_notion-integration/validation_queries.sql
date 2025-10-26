-- ============================================================================
-- FEAT-002 Validation Queries
--
-- Run these queries after ingestion to validate results
-- Usage: psql $DATABASE_URL -f validation_queries.sql
-- ============================================================================

\echo ''
\echo '╔════════════════════════════════════════════════════════════════╗'
\echo '║           FEAT-002 INGESTION VALIDATION REPORT                 ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo ''

-- ============================================================================
-- 1. Document Counts
-- ============================================================================
\echo '📊 DOCUMENT COUNTS'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    'Total Documents' as metric,
    COUNT(*) as count
FROM documents
UNION ALL
SELECT
    'Notion Guidelines',
    COUNT(*)
FROM documents
WHERE source LIKE '%notion_guidelines%'
UNION ALL
SELECT
    'Other Documents',
    COUNT(*)
FROM documents
WHERE source NOT LIKE '%notion_guidelines%';

\echo ''

-- ============================================================================
-- 2. Chunk Statistics
-- ============================================================================
\echo '📊 CHUNK STATISTICS'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    'Total Chunks' as metric,
    COUNT(*) as count
FROM chunks
UNION ALL
SELECT
    'Chunks from Notion',
    COUNT(*)
FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%'
UNION ALL
SELECT
    'Chunks with Embeddings',
    COUNT(*)
FROM chunks
WHERE embedding IS NOT NULL
UNION ALL
SELECT
    'Chunks with NULL tier',
    COUNT(*)
FROM chunks
WHERE tier IS NULL;

\echo ''

-- ============================================================================
-- 3. Embedding Coverage
-- ============================================================================
\echo '📊 EMBEDDING COVERAGE'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    ROUND((COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END)::NUMERIC /
           NULLIF(COUNT(*), 0) * 100), 2) as embedding_percentage,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embedding,
    COUNT(CASE WHEN embedding IS NULL THEN 1 END) as without_embedding,
    COUNT(*) as total
FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%';

\echo ''

-- ============================================================================
-- 4. Category Distribution
-- ============================================================================
\echo '📊 CATEGORY DISTRIBUTION'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    COALESCE(metadata->>'guideline_category', 'MISSING') as category,
    COUNT(*) as document_count
FROM documents
WHERE source LIKE '%notion_guidelines%'
GROUP BY metadata->>'guideline_category'
ORDER BY COUNT(*) DESC;

\echo ''

-- ============================================================================
-- 5. Metadata Validation
-- ============================================================================
\echo '📊 METADATA VALIDATION'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    'Documents with category' as metric,
    COUNT(*) as count
FROM documents
WHERE source LIKE '%notion_guidelines%'
AND metadata->>'guideline_category' IS NOT NULL
UNION ALL
SELECT
    'Documents with source_url',
    COUNT(*)
FROM documents
WHERE source LIKE '%notion_guidelines%'
AND metadata->>'source_url' IS NOT NULL
UNION ALL
SELECT
    'Documents with summary',
    COUNT(*)
FROM documents
WHERE source LIKE '%notion_guidelines%'
AND metadata->>'summary' IS NOT NULL
UNION ALL
SELECT
    'Documents with tags',
    COUNT(*)
FROM documents
WHERE source LIKE '%notion_guidelines%'
AND metadata->'tags' IS NOT NULL;

\echo ''

-- ============================================================================
-- 6. Chunk Size Statistics
-- ============================================================================
\echo '📊 CHUNK SIZE STATISTICS'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    ROUND(AVG(LENGTH(content))) as avg_chunk_size,
    MIN(LENGTH(content)) as min_chunk_size,
    MAX(LENGTH(content)) as max_chunk_size,
    COUNT(*) as total_chunks
FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%';

\echo ''

-- ============================================================================
-- 7. Sample Documents
-- ============================================================================
\echo '📊 SAMPLE DOCUMENTS (First 5)'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    LEFT(title, 60) as title,
    metadata->>'guideline_category' as category,
    (SELECT COUNT(*) FROM chunks WHERE document_id = d.id) as chunk_count,
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
FROM documents d
WHERE source LIKE '%notion_guidelines%'
ORDER BY created_at DESC
LIMIT 5;

\echo ''

-- ============================================================================
-- 8. Tier Column Check
-- ============================================================================
\echo '📊 TIER COLUMN CHECK'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    COALESCE(tier::TEXT, 'NULL') as tier_value,
    COUNT(*) as count
FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%'
GROUP BY tier
ORDER BY tier;

\echo ''

-- ============================================================================
-- 9. Recent Ingestion Activity
-- ============================================================================
\echo '📊 RECENT INGESTION ACTIVITY (Last 10 documents)'
\echo '────────────────────────────────────────────────────────────────'

SELECT
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as ingested_at,
    LEFT(title, 50) as title,
    (SELECT COUNT(*) FROM chunks WHERE document_id = d.id) as chunks
FROM documents d
WHERE source LIKE '%notion_guidelines%'
ORDER BY created_at DESC
LIMIT 10;

\echo ''

-- ============================================================================
-- 10. Health Check Summary
-- ============================================================================
\echo '✅ HEALTH CHECK SUMMARY'
\echo '────────────────────────────────────────────────────────────────'

WITH stats AS (
    SELECT
        COUNT(DISTINCT d.id) as doc_count,
        COUNT(c.id) as chunk_count,
        COUNT(CASE WHEN c.embedding IS NOT NULL THEN 1 END) as embedded_count,
        COUNT(CASE WHEN d.metadata->>'guideline_category' IS NOT NULL THEN 1 END) as with_category,
        COUNT(CASE WHEN d.metadata->>'source_url' IS NOT NULL THEN 1 END) as with_url
    FROM documents d
    LEFT JOIN chunks c ON d.id = c.document_id
    WHERE d.source LIKE '%notion_guidelines%'
)
SELECT
    CASE
        WHEN doc_count > 0 AND chunk_count > 0 AND embedded_count = chunk_count
             AND with_category = doc_count AND with_url = doc_count
        THEN '✅ ALL CHECKS PASSED'
        ELSE '⚠️  SOME CHECKS FAILED - Review output above'
    END as status,
    doc_count,
    chunk_count,
    embedded_count,
    ROUND((embedded_count::NUMERIC / NULLIF(chunk_count, 0) * 100), 1) as embedding_pct
FROM stats;

\echo ''
\echo '╔════════════════════════════════════════════════════════════════╗'
\echo '║                     VALIDATION COMPLETE                        ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo ''
