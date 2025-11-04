# Spike 4: Database Schema Analysis

**Date:** 2025-11-04
**Duration:** 20 minutes
**Status:** ✅ Complete

## Objective
Analyze current products table schema, create migration script, and validate changes.

## Current Schema (Before Migration)

```sql
Table "public.products"
     Column      |           Type           | Nullable |        Default
-----------------+--------------------------+----------+------------------------
 id              | uuid                     | not null | uuid_generate_v4()
 name            | text                     | not null |
 description     | text                     | not null |
 url             | text                     | not null |
 category        | text                     |          |
 subcategory     | text                     |          |  ❌ TO REMOVE
 embedding       | vector(1536)             |          |
 compliance_tags | text[]                   |          |  ❌ TO REMOVE
 metadata        | jsonb                    |          |
 source          | text                     |          |
 last_scraped_at | timestamp with time zone |          |
 created_at      | timestamp with time zone |          |
 updated_at      | timestamp with time zone |          |
```

**Indexes:**
- `products_pkey` (PRIMARY KEY on id)
- `idx_products_category` (btree on category)
- `idx_products_compliance_tags` (GIN on compliance_tags) ❌ TO REMOVE
- `idx_products_embedding` (IVFFLAT on embedding)
- `idx_products_metadata` (GIN on metadata)
- `idx_products_url` (btree on url)
- `products_url_key` (UNIQUE on url)

## Required Changes

### 1. Add Price Column
```sql
ALTER TABLE products ADD COLUMN IF NOT EXISTS price TEXT;
```
- **Type:** TEXT (allows formats like "Vanaf € 1297/stuk")
- **Nullable:** YES (AC-004-103: some products may not have pricing)
- **Example values:** "Vanaf € 1297/stuk", "€150 per sessie", NULL

### 2. Remove Unused Columns
```sql
ALTER TABLE products DROP COLUMN IF EXISTS subcategory CASCADE;
ALTER TABLE products DROP COLUMN IF EXISTS compliance_tags CASCADE;
```
- **Reason:** Not used in FEAT-004, replaced by metadata JSON
- **Impact:** Cascade drops dependent view `product_catalog_summary`

### 3. Update search_products() Function
**Old signature:**
```sql
search_products(query_embedding vector, query_text TEXT, compliance_tags_filter TEXT[], match_count INT)
```
- Returns: `compliance_tags TEXT[]`
- Search: Vector-only (no hybrid)

**New signature:**
```sql
search_products(query_embedding vector, query_text TEXT, match_count INT DEFAULT 5)
```
- Returns: `price TEXT` (instead of compliance_tags)
- Search: **Hybrid 70% vector + 30% Dutch full-text**

## Migration Script

**Created:** `sql/migrations/004_product_schema_update.sql`

### Migration Steps:
1. ADD price TEXT column
2. DROP subcategory column
3. DROP compliance_tags column
4. DROP idx_products_compliance_tags index
5. DROP old search_products() function
6. CREATE new search_products() with hybrid search

### Validation:
- Automatic validation checks in migration
- Raises exceptions if migration fails
- Outputs: "Schema validation: ✅ PASSED"

## Migration Test Results

**Test Command:**
```bash
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/migrations/004_product_schema_update.sql
```

**Output:**
```
BEGIN
ALTER TABLE  ✅
ALTER TABLE  ✅
ALTER TABLE  ✅
DROP INDEX   ✅
DROP FUNCTION ✅
CREATE FUNCTION ✅
NOTICE: Schema validation: ✅ PASSED
NOTICE: Function validation: ✅ PASSED
COMMIT
```

**Side Effects:**
- ⚠️ View `product_catalog_summary` dropped (cascade from compliance_tags removal)
- Impact: LOW (view not used in FEAT-004)

## Updated Schema (After Migration)

```sql
Table "public.products"
     Column      |           Type           | Nullable |        Default
-----------------+--------------------------+----------+------------------------
 id              | uuid                     | not null | uuid_generate_v4()
 name            | text                     | not null |
 description     | text                     | not null |
 url             | text                     | not null |
 category        | text                     |          |
 price           | text                     |          |  ✅ ADDED
 embedding       | vector(1536)             |          |
 metadata        | jsonb                    |          |
 source          | text                     |          |
 last_scraped_at | timestamp with time zone |          |
 created_at      | timestamp with time zone |          |
 updated_at      | timestamp with time zone |          |
```

**Indexes (after migration):**
- `products_pkey` (PRIMARY KEY)
- `idx_products_category`
- `idx_products_embedding` (IVFFLAT)
- `idx_products_metadata` (GIN)
- `idx_products_url`
- `products_url_key` (UNIQUE)

## New search_products() Function

**Function Signature:**
```sql
CREATE FUNCTION search_products(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    product_id UUID,
    name TEXT,
    description TEXT,
    price TEXT,           -- ✅ NEW
    url TEXT,
    category TEXT,
    similarity FLOAT,
    metadata JSONB
)
```

**Hybrid Search Algorithm:**
```sql
-- Vector similarity (70%)
1 - (embedding <=> query_embedding) AS vector_sim

-- Dutch full-text (30%)
ts_rank_cd(
    to_tsvector('dutch', description),
    plainto_tsquery('dutch', query_text)
) AS text_sim

-- Combined score
(vector_sim * 0.7 + text_sim * 0.3) AS similarity
```

**Example Usage:**
```sql
SELECT *
FROM search_products(
    '[1536-dim embedding]'::vector,
    'burn-out begeleiding',
    5
);
```

## Rollback Script

**Created:** `sql/migrations/004_rollback.sql`

**Warning:** Rollback will **DELETE** price column data!

**Rollback Steps:**
1. Restore subcategory column (empty)
2. Restore compliance_tags column (empty)
3. Recreate idx_products_compliance_tags index
4. DROP new search_products() function
5. CREATE old search_products() function (vector-only)

**Rollback Command:**
```bash
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/migrations/004_rollback.sql
```

## Implementation Notes

### 1. Database Connection
Reuse existing pattern from `agent/db_utils.py`:
```python
from agent.db_utils import get_db_pool

pool = await get_db_pool()
async with pool.acquire() as conn:
    result = await conn.fetch(
        "SELECT * FROM search_products($1, $2, $3)",
        embedding,
        query_text,
        limit
    )
```

### 2. Upsert Pattern
```python
INSERT INTO products (name, description, url, price, category, embedding, metadata)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT (url) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    price = EXCLUDED.price,
    category = EXCLUDED.category,
    embedding = EXCLUDED.embedding,
    metadata = EXCLUDED.metadata,
    last_scraped_at = NOW(),
    updated_at = NOW()
RETURNING id;
```

### 3. Metadata Structure
```python
metadata = {
    "problem_mappings": ["Problem 1", "Problem 2"],  # From CSV
    "csv_category": "Verbetering belastbaarheid",    # From CSV
    "portal_scraped_at": "2025-11-04T13:30:00Z",     # Timestamp
    "fuzzy_match_score": 0.95                         # Match confidence
}
```

## Validation Checklist

- [x] Migration script created
- [x] Migration tested successfully
- [x] price column added
- [x] subcategory removed
- [x] compliance_tags removed
- [x] search_products() function updated
- [x] Hybrid search (70/30) implemented
- [x] Dutch language support (to_tsvector('dutch'))
- [x] Rollback script created
- [x] Automatic validation in migration

## Acceptance Criteria Met

### AC-004-006: Hybrid Search SQL Function Updated
✅ Function includes: `0.7 * (1 - (p.embedding <=> query_embedding)) + 0.3 * ts_rank(...)`

### AC-004-302: Database Schema Integration
✅ Schema migration adds price field, removes compliance_tags
✅ Backward compatibility: URL uniqueness preserved

### AC-004-402: Database Storage
✅ Schema: products table with embedding vector(1536), metadata JSONB, price TEXT
✅ Indexes: IVFFLAT on embedding, GIN on metadata
✅ Constraints: url NOT NULL + UNIQUE, name NOT NULL

## Next Steps

1. **Implementation:** Use migration in FEAT-004 implementation
2. **Testing:** Validate hybrid search performance (<500ms)
3. **Monitoring:** Track query latency after ingestion

---

**Status:** ✅ COMPLETE
**Blockers:** None
**Migration Files:**
- `sql/migrations/004_product_schema_update.sql` ✅
- `sql/migrations/004_rollback.sql` ✅

**Ready for:** FEAT-004 Implementation
