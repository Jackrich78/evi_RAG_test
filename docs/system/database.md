# Database Schema - EVI 360 RAG

**Last Updated:** 2025-10-25
**Status:** Phase 1-2 Complete - Infrastructure Operational

## Overview

The EVI 360 RAG system uses two databases working together:
- **PostgreSQL 17 + pgvector 0.8.1**: Vector similarity search, Dutch full-text search, relational data
- **Neo4j 5.26.1 + APOC**: Knowledge graph for guideline and product relationships

Both databases run in Docker containers with persistent volumes for data retention.

**Database Type:** Hybrid (PostgreSQL + Neo4j)
**Deployment:** Docker Compose (local)
**Connection:** asyncpg (PostgreSQL), neo4j driver (graph)

---

## PostgreSQL Schema

### Connection Details

```bash
# Connection string
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/evi_rag

# Container name
evi_rag_postgres

# Health check
docker exec -it evi_rag_postgres psql -U postgres -d evi_rag
```

### Extensions

```sql
-- Installed extensions
CREATE EXTENSION IF NOT EXISTS vector;           -- pgvector 0.8.1
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS pg_trgm;          -- Trigram matching
```

---

## Tables

### Table: `documents`

**Purpose:** Store source document metadata for guidelines and references

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique document identifier |
| title | TEXT | NOT NULL | Document title (Dutch) |
| source | TEXT | NOT NULL | Source (NVAB, STECR, UWV, etc.) |
| url | TEXT | UNIQUE | Source URL if available |
| content | TEXT | | Full document content |
| metadata | JSONB | DEFAULT '{}' | Additional metadata |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Document creation time |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update time |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `url`
- GIN INDEX on `metadata` (JSONB indexing)

---

### Table: `chunks` ⭐ (with tier support)

**Purpose:** Store document chunks with embeddings and tier metadata for 3-tier guideline hierarchy

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique chunk identifier |
| document_id | UUID | REFERENCES documents(id) | Parent document |
| content | TEXT | NOT NULL | Chunk text content |
| **tier** | **INTEGER** | **CHECK (tier IN (1, 2, 3))** | **Tier: 1=Summary, 2=Key Facts, 3=Details** |
| embedding | vector(1536) | | OpenAI text-embedding-3-small |
| token_count | INTEGER | | Approximate token count |
| chunk_index | INTEGER | | Chunk position in document |
| metadata | JSONB | DEFAULT '{}' | Additional metadata |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Chunk creation time |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update time |

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `document_id` → documents(id)
- IVFFLAT INDEX on `embedding` (vector similarity search)
- INDEX on `tier` (filter by tier)
- INDEX on `(tier, document_id)` (composite for efficient tier+doc queries)

**Tier Semantics:**
- **Tier 1**: Summary (1-2 sentences, ~50-100 words) - Single chunk per guideline
- **Tier 2**: Key Facts (3-5 points, ~200-500 words) - 3-5 chunks per guideline
- **Tier 3**: Full Details (complete docs, ~1000-5000 words) - 10-20 chunks per guideline

---

### Table: `products`

**Purpose:** EVI 360 product catalog with embeddings and compliance tags

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique product identifier |
| name | TEXT | NOT NULL | Product name |
| description | TEXT | NOT NULL | Product description (Dutch) |
| url | TEXT | UNIQUE, NOT NULL | Product page URL |
| category | TEXT | | Product category |
| subcategory | TEXT | | Product subcategory |
| embedding | vector(1536) | | Product description embedding |
| **compliance_tags** | **TEXT[]** | **DEFAULT '{}'** | **Safety standards (e.g., ["EN_361", "CE_certified"])** |
| metadata | JSONB | DEFAULT '{}' | Additional metadata |
| source | TEXT | DEFAULT 'evi360_website' | Scraping source |
| last_scraped_at | TIMESTAMP WITH TIME ZONE | | Last scrape timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Product creation time |
| updated_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last update time |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `url`
- IVFFLAT INDEX on `embedding` (vector similarity search)
- INDEX on `category`
- GIN INDEX on `compliance_tags` (array matching)
- GIN INDEX on `metadata` (JSONB indexing)

**Compliance Tags Examples:**
- `["fall_protection", "EN_361", "CE_certified"]`
- `["manual_handling", "ergonomics", "ISO_11228"]`
- `["hearing_protection", "EN_352", "SNR_30"]`

---

### Table: `sessions`

**Purpose:** Store conversation sessions for context management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique session identifier |
| user_id | TEXT | | User identifier (optional) |
| started_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Session start time |
| last_activity_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Last activity timestamp |
| metadata | JSONB | DEFAULT '{}' | Session metadata |

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `user_id`
- INDEX on `last_activity_at` (for cleanup queries)

---

### Table: `messages`

**Purpose:** Store chat message history for conversation context

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique message identifier |
| session_id | UUID | REFERENCES sessions(id) | Parent session |
| role | TEXT | NOT NULL | Message role (user, assistant, system) |
| content | TEXT | NOT NULL | Message content (Dutch) |
| metadata | JSONB | DEFAULT '{}' | Additional metadata (tool calls, etc.) |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Message timestamp |

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `session_id` → sessions(id)
- INDEX on `(session_id, created_at)` (fetch conversation history)

---

## SQL Functions

### Function: `hybrid_search()`

**Purpose:** Combined vector + Dutch full-text search for chunks

**Signature:**
```sql
hybrid_search(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 10,
    text_weight FLOAT DEFAULT 0.3
) RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    combined_score FLOAT,
    vector_similarity FLOAT,
    text_similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT
)
```

**Implementation Details:**
- Vector search: Cosine similarity on embeddings
- Text search: `to_tsvector('dutch', content)` with Dutch stemming
- Combined score: `(vector_sim * (1 - text_weight)) + (text_sim * text_weight)`
- Dutch language features:
  - Stemming (werken → werk, bescherming → beschermd)
  - Stop words removed (de, het, een, van, etc.)

**Usage Example:**
```sql
SELECT * FROM hybrid_search(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    query_text := 'werken op hoogte valbescherming',
    match_count := 10,
    text_weight := 0.3
);
```

---

### Function: `search_guidelines_by_tier()` ⭐

**Purpose:** Tier-aware hybrid search for 3-tier guideline hierarchy

**Signature:**
```sql
search_guidelines_by_tier(
    query_embedding vector(1536),
    query_text TEXT,
    tier_filter INTEGER DEFAULT NULL,  -- NULL = search all tiers
    match_count INT DEFAULT 10,
    text_weight FLOAT DEFAULT 0.3
) RETURNS TABLE (
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
```

**Implementation Details:**
- Filters chunks by tier if `tier_filter` is specified
- Prioritizes lower tiers (1=summary, 2=key facts) when no filter
- Uses Dutch full-text search (`to_tsvector('dutch', content)`)
- Combines vector and text similarity with weighted scoring

**Usage Examples:**
```sql
-- Search only Tier 1 (summaries)
SELECT * FROM search_guidelines_by_tier(
    query_embedding := '[...]'::vector,
    query_text := 'persoonlijke beschermingsmiddelen',
    tier_filter := 1,
    match_count := 5
);

-- Search all tiers (prioritizes Tier 1-2)
SELECT * FROM search_guidelines_by_tier(
    query_embedding := '[...]'::vector,
    query_text := 'arbeidsongevallen meldingsplicht',
    tier_filter := NULL,
    match_count := 10
);
```

---

### Function: `search_products()`

**Purpose:** Semantic search for products with compliance tag filtering

**Signature:**
```sql
search_products(
    query_embedding vector(1536),
    query_text TEXT,
    compliance_tags_filter TEXT[] DEFAULT NULL,
    match_count INT DEFAULT 10
) RETURNS TABLE (
    product_id UUID,
    name TEXT,
    description TEXT,
    url TEXT,
    category TEXT,
    similarity FLOAT,
    compliance_tags TEXT[],
    metadata JSONB
)
```

**Implementation Details:**
- Vector similarity search on product descriptions
- Optional filtering by compliance tags (array overlap: `&&`)
- Returns products sorted by embedding similarity

**Usage Examples:**
```sql
-- Search all products
SELECT * FROM search_products(
    query_embedding := '[...]'::vector,
    query_text := 'veiligheidshelm',
    compliance_tags_filter := NULL,
    match_count := 10
);

-- Search only CE-certified fall protection products
SELECT * FROM search_products(
    query_embedding := '[...]'::vector,
    query_text := 'valbescherming harnas',
    compliance_tags_filter := ARRAY['fall_protection', 'CE_certified'],
    match_count := 5
);
```

---

## Views

### View: `document_summaries`

**Purpose:** Quick document statistics with chunk counts

**Columns:**
- `document_id` - Document UUID
- `title` - Document title
- `source` - Source organization
- `chunk_count` - Number of chunks
- `has_embeddings` - Boolean (all chunks have embeddings)
- `created_at` - Document creation date

**Usage:**
```sql
SELECT * FROM document_summaries
WHERE source = 'NVAB'
ORDER BY created_at DESC;
```

---

### View: `guideline_tier_stats`

**Purpose:** Statistics on guideline tier distribution

**Columns:**
- `tier` - Tier number (1, 2, or 3)
- `chunk_count` - Number of chunks in tier
- `document_count` - Number of unique documents
- `avg_token_count` - Average tokens per chunk
- `oldest_chunk` - Earliest chunk creation date
- `newest_chunk` - Latest chunk creation date

**Usage:**
```sql
SELECT * FROM guideline_tier_stats
ORDER BY tier;

-- Example output:
-- tier | chunk_count | document_count | avg_token_count
-- -----|-------------|----------------|----------------
--  1   |    100      |     100        |      75
--  2   |    450      |      95        |     320
--  3   |   2100      |     100        |    1850
```

---

### View: `product_catalog_summary`

**Purpose:** Product catalog overview by category

**Columns:**
- `category` - Product category
- `product_count` - Number of products in category
- `subcategory_count` - Number of unique subcategories
- `all_compliance_tags` - Array of all compliance tags in category
- `oldest_product` - Earliest product creation date
- `last_scrape` - Most recent scrape timestamp

**Usage:**
```sql
SELECT * FROM product_catalog_summary
ORDER BY product_count DESC;
```

---

## Neo4j Graph Database

### Connection Details

```bash
# Web interface
http://localhost:7474
Username: neo4j
Password: password123

# Bolt connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Container name
evi_rag_neo4j
```

### Graph Schema (Phase 3+ - Planned)

**Nodes:**
- `Guideline` - Safety guideline documents
- `Product` - EVI 360 products
- `Concept` - Safety concepts (extracted from guidelines)
- `Regulation` - Legal requirements (EN standards, UWV rules, etc.)

**Relationships:**
- `REFERENCES` - Guideline → Regulation
- `REQUIRES` - Guideline → Concept
- `SUPPORTS` - Product → Guideline (product aligns with guideline)
- `COMPLIES_WITH` - Product → Regulation (product meets standard)
- `RELATED_TO` - Guideline → Guideline (cross-references)

**Example Cypher Query (Planned):**
```cypher
// Find products that support a specific guideline
MATCH (g:Guideline {title: "Werken op hoogte"})-[:SUPPORTS]-(p:Product)
RETURN p.name, p.url, p.compliance_tags

// Find related guidelines via shared concepts
MATCH (g1:Guideline {title: "Valbescherming"})-[:REQUIRES]->(c:Concept)<-[:REQUIRES]-(g2:Guideline)
WHERE g1 <> g2
RETURN g2.title, c.name
```

**APOC Plugin:**
- Installed and enabled in Neo4j
- Procedures unrestricted (`apoc.*`)
- Used for advanced graph operations and algorithms

---

## Migrations

**Migration Tool:** SQL files executed in Docker initialization

**Migration Files Location:**
- [`sql/00_init.sql`](../../sql/00_init.sql) - Initial setup (extensions, helper functions)
- [`sql/schema.sql`](../../sql/schema.sql) - Base schema (documents, chunks, sessions, messages)
- [`sql/evi_schema_additions.sql`](../../sql/evi_schema_additions.sql) - EVI-specific schema (tier column, products table, Dutch functions)

**Running Migrations:**
```bash
# Auto-run on container first start (via docker-compose.yml volume mount)
docker-compose up -d

# Manual execution (if needed)
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/schema.sql
docker exec -i evi_rag_postgres psql -U postgres -d evi_rag < sql/evi_schema_additions.sql
```

**Creating Migrations:**
- Add new `.sql` files to `sql/` directory
- Mount in `docker-compose.yml` under `volumes` → `/docker-entrypoint-initdb.d`
- Files run in alphabetical order on first container start

---

## Data Integrity

### Constraints

- **Foreign Keys:** Enabled with CASCADE on delete for chunks → documents, messages → sessions
- **NOT NULL:** All required fields enforce NOT NULL constraint
- **UNIQUE:** URLs must be unique for documents and products
- **CHECK:** Tier column restricted to values (1, 2, 3)
- **Array Constraints:** compliance_tags default to empty array '{}'

### Triggers

**`update_updated_at_column()`:**
- Updates `updated_at` timestamp on row modification
- Applied to: documents, chunks, products, sessions

```sql
-- Example trigger definition
CREATE TRIGGER update_products_updated_at
BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Performance

### Indexes

**Vector Indexes (IVFFLAT):**
- `chunks.embedding` - Guideline chunk similarity search
- `products.embedding` - Product similarity search
- Configuration: `lists = 1` (for datasets < 100K rows)

**Full-Text Search:**
- Dutch language configuration: `to_tsvector('dutch', content)`
- GIN indexes automatically used for `@@` queries

**Category/Tag Indexes:**
- `products.category` - BTREE for category filtering
- `products.compliance_tags` - GIN for array overlap queries
- `chunks.tier` - BTREE for tier filtering

**Composite Indexes:**
- `(tier, document_id)` on chunks - Efficient tier+document queries
- `(session_id, created_at)` on messages - Fast conversation history retrieval

### Query Optimization

**Vector Search Performance:**
- IVFFLAT approximate nearest neighbor (ANN) search
- Trade-off: 95-98% accuracy for 10-100x speed improvement vs. exact search
- Tune `lists` parameter based on dataset size (future scaling)

**Dutch Full-Text Search:**
- `ts_rank_cd()` for relevance scoring
- `plainto_tsquery()` for simple query parsing
- Stemming reduces index size and improves recall

**Hybrid Search Strategy:**
- Default `text_weight = 0.3` (70% vector, 30% text)
- Adjustable per query for tuning precision/recall

---

## Backup & Recovery

### PostgreSQL Backup

**Automated Backup (Recommended):**
```bash
# Backup entire database
docker exec evi_rag_postgres pg_dump -U postgres evi_rag > backup_$(date +%Y%m%d).sql

# Backup schema only
docker exec evi_rag_postgres pg_dump -U postgres -s evi_rag > schema_backup.sql

# Backup data only
docker exec evi_rag_postgres pg_dump -U postgres -a evi_rag > data_backup.sql
```

**Docker Volume Backup:**
```bash
# Backup PostgreSQL volume
docker run --rm -v evi_rag_test_postgres_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres_backup.tar.gz /data

# Restore PostgreSQL volume
docker run --rm -v evi_rag_test_postgres_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/postgres_backup.tar.gz -C /
```

### Neo4j Backup

**Database Dump:**
```bash
# Backup Neo4j database
docker exec evi_rag_neo4j neo4j-admin database dump neo4j --to-path=/var/lib/neo4j/dumps
docker cp evi_rag_neo4j:/var/lib/neo4j/dumps/neo4j.dump ./neo4j_backup.dump

# Restore Neo4j database
docker cp ./neo4j_backup.dump evi_rag_neo4j:/var/lib/neo4j/dumps/
docker exec evi_rag_neo4j neo4j-admin database load neo4j --from-path=/var/lib/neo4j/dumps
```

**Backup Schedule (Production):**
- Daily automated backups at 2 AM
- 7-day retention for daily backups
- Monthly backups retained for 1 year

**Recovery Process:**
1. Stop containers: `docker-compose down`
2. Restore volumes or SQL dump (see commands above)
3. Start containers: `docker-compose up -d`
4. Verify data integrity: `python3 tests/test_data_persistence.py`

---

## Security

- **Encryption at Rest:** Not enabled (local development)
- **Encryption in Transit:** TLS not configured (local development)
- **Access Control:** Default PostgreSQL authentication, Neo4j basic auth
- **Sensitive Data:** No PII stored in Phase 1-2 (guidelines and products only)
- **Credentials:** Stored in `.env` file (`.gitignore`'d)

**Production Security Recommendations (Future):**
- Enable TLS for PostgreSQL and Neo4j connections
- Use strong passwords (not default `postgres`/`password123`)
- Restrict network access (bind to localhost only)
- Enable pgcrypto for sensitive data encryption
- Regular security updates via Docker image updates

---

## Development

### Local Database Setup

```bash
# 1. Start databases
docker-compose up -d

# 2. Verify health
docker-compose ps  # Both should show (healthy)

# 3. Run connection tests
python3 tests/test_supabase_connection.py
python3 tests/test_data_persistence.py
```

### Test Database

**Approach:** Same database with test data cleanup
- No separate test database (local development)
- Tests use transactions with rollback (future implementation)
- Manual cleanup: `TRUNCATE chunks, documents, products, sessions, messages CASCADE;`

**Test Suite:**
- [`tests/test_supabase_connection.py`](../../tests/test_supabase_connection.py) - Validates schema, functions, views
- [`tests/test_data_persistence.py`](../../tests/test_data_persistence.py) - Verifies Docker volume persistence

### Useful Queries

```sql
-- Check tier distribution
SELECT tier, COUNT(*) FROM chunks GROUP BY tier ORDER BY tier;

-- Find documents without embeddings
SELECT d.title FROM documents d
LEFT JOIN chunks c ON d.id = c.document_id
WHERE c.embedding IS NULL;

-- Product compliance tag analysis
SELECT
    unnest(compliance_tags) AS tag,
    COUNT(*) AS product_count
FROM products
GROUP BY tag
ORDER BY product_count DESC;

-- Recent conversation activity
SELECT s.id, COUNT(m.id) AS message_count, MAX(m.created_at) AS last_message
FROM sessions s
LEFT JOIN messages m ON s.id = m.session_id
WHERE s.last_activity_at > NOW() - INTERVAL '7 days'
GROUP BY s.id
ORDER BY last_message DESC;
```

---

## Data Persistence

**Docker Volumes (Critical):**
- `evi_rag_test_postgres_data` - All PostgreSQL data (tables, indexes, embeddings)
- `evi_rag_test_neo4j_data` - All Neo4j graph data

**Persistence Guarantee:**
- Data survives container restarts
- Data survives `docker-compose down`
- Data survives Docker daemon restarts
- Data survives system reboots

**Data is ONLY lost if:**
- ⚠️ `docker-compose down -v` (explicit volume deletion)
- ⚠️ `docker volume rm evi_rag_test_postgres_data`
- ⚠️ Manual deletion of Docker volumes

**Verification:**
```bash
# Verify volumes exist
docker volume ls | grep evi_rag

# Expected output:
# evi_rag_test_postgres_data
# evi_rag_test_neo4j_data
# evi_rag_test_neo4j_logs
# evi_rag_test_neo4j_import
# evi_rag_test_neo4j_plugins
```

---

**Note:** Update this document when:
- Tables are added, modified, or removed
- Indexes change (performance tuning)
- SQL functions are updated
- Relationships change
- Migration process changes
- Neo4j graph schema is implemented (Phase 3+)

**See Also:**
- [architecture.md](architecture.md) - System architecture overview
- [stack.md](stack.md) - Technology stack details
- [LOCAL_SETUP_COMPLETE.md](../../LOCAL_SETUP_COMPLETE.md) - Setup guide
- [docker-compose.yml](../../docker-compose.yml) - Database configuration
