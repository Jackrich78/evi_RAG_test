# Architecture Decision: Product Catalog Ingestion

## Feature ID
FEAT-004

## Feature Name
Product Catalog Integration

## Decision Date
2025-10-31

## Status
Proposed

---

## Context

EVI 360 specialists need access to searchable product information (PPE, safety equipment, chemical compliance products) integrated into the RAG system. Products exist in a Notion database and must be ingested with semantic embeddings to enable natural language search and recommendations.

**Key Requirements:**
- Ingest from Notion product database
- Extract: name, description, category, supplier, compliance_tags, use_cases, price_range
- Generate embeddings for semantic search
- Support compliance filtering (CE, EN standards, ATEX)
- Link products to guidelines via categories/use cases
- Performance: <500ms for top 10 search results

**Constraints:**
- Follow FEAT-002 guideline ingestion patterns for consistency
- Use existing Notion API integration (notion-client)
- PostgreSQL + pgvector for storage
- OpenAI embeddings (text-embedding-3-small)
- Support incremental updates

---

## Options Considered

### Option 1: Extend Existing Ingestion Module

**Description:**
Add product ingestion to existing `ingestion/ingest.py` module following the same pattern as guideline ingestion (FEAT-002). Create `ProductNotionParser` class similar to `NotionParser`, reuse embedding generation, database connection, and error handling.

**Implementation Approach:**
- Add `ingest_products()` function to `ingestion/ingest.py`
- Create `ProductNotionParser` class to parse Notion product properties
- Reuse `generate_embedding()` from existing code
- Add product-specific SQL queries for upsert/deduplication
- Create `product_search()` function in new `agent/product_queries.py` module

**Pros:**
- Minimal code duplication (reuse 80% of existing ingestion logic)
- Consistent patterns (same error handling, logging, batch processing)
- Single entry point for all Notion ingestion tasks
- Easy maintenance (one module for ingestion concerns)

**Cons:**
- `ingestion/ingest.py` grows larger (currently ~300 lines, would add ~150 lines)
- Mixing guidelines and products in same module (separation of concerns)
- Less flexibility for product-specific optimizations

**Estimated Effort:** 2 days implementation + 1 day testing

---

### Option 2: Separate Product Ingestion Module

**Description:**
Create new `ingestion/product_ingest.py` module dedicated to product catalog ingestion. Extract common utilities (embedding generation, database helpers) into `ingestion/utils.py` shared by both guideline and product ingestion.

**Implementation Approach:**
- Create `ingestion/product_ingest.py` with `ProductIngestion` class
- Extract shared utilities to `ingestion/utils.py` (embeddings, DB connection)
- Refactor `ingestion/ingest.py` to use shared utilities
- Add product-specific search in `agent/product_queries.py`
- Create CLI commands for both ingestion types

**Pros:**
- Clear separation of concerns (guidelines vs products)
- Easier to optimize product-specific logic independently
- Better modularity and testability
- Prevents single file from growing too large

**Cons:**
- More files to maintain (3 modules instead of 1)
- Risk of utilities duplication if not carefully extracted
- Requires refactoring existing guideline ingestion
- More complex project structure

**Estimated Effort:** 3 days implementation + 1 day testing

---

### Option 3: Unified Data Ingestion Framework

**Description:**
Build generic ingestion framework in `ingestion/framework.py` with base classes (`BaseNotionParser`, `BaseIngestionPipeline`) that both guidelines and products inherit from. Support plugins for different content types.

**Implementation Approach:**
- Create abstract base classes for ingestion pipeline stages
- Implement `GuidelineParser` and `ProductParser` as concrete implementations
- Add registry pattern for content type handlers
- Create unified CLI with subcommands (ingest guideline/product)
- Support extensibility for future content types

**Pros:**
- Most scalable solution (easy to add new content types)
- Enforces consistent patterns via base classes
- Best code reuse through inheritance
- Professional architecture for long-term growth

**Cons:**
- Over-engineering for current needs (2 content types)
- Highest complexity and learning curve
- Longer implementation time
- Risk of premature abstraction

**Estimated Effort:** 5 days implementation + 2 days testing

---

## Comparison Matrix

| Criteria | Option 1: Extend Existing | Option 2: Separate Module | Option 3: Generic Framework |
|----------|---------------------------|---------------------------|----------------------------|
| **Feasibility** | ✅ High - Proven pattern | ✅ High - Standard practice | ⚠️ Medium - More complexity |
| **Performance** | ✅ Excellent (<500ms) | ✅ Excellent (<500ms) | ✅ Excellent (<500ms) |
| **Maintainability** | ⚠️ Medium - File grows | ✅ High - Clear separation | ⚠️ Medium - More abstraction |
| **Cost** | ✅ Low (2-3 days) | ⚠️ Medium (3-4 days) | ❌ High (5-7 days) |
| **Complexity** | ✅ Low - Simple extension | ⚠️ Medium - Refactoring | ❌ High - New patterns |
| **Community/Support** | ✅ Established pattern | ✅ Standard Python practice | ⚠️ Custom implementation |
| **Integration** | ✅ Seamless - No refactor | ⚠️ Requires refactor | ❌ Major refactor needed |

**Scoring:** ✅ Strong (3 pts), ⚠️ Adequate (2 pts), ❌ Weak (1 pt)
- **Option 1:** 19 points
- **Option 2:** 18 points
- **Option 3:** 13 points

---

## Decision

**Selected Option:** Option 1 - Extend Existing Ingestion Module

**Rationale:**
For MVP scope with 2 content types (guidelines and products), extending the existing ingestion module provides the fastest, most reliable path forward. The proven pattern from FEAT-002 minimizes risk and development time while maintaining code quality.

**Key Factors:**
1. **Speed to MVP:** 2-3 days vs 5-7 days for framework approach
2. **Risk Reduction:** Reuse working code and patterns from FEAT-002
3. **Simplicity:** Team already familiar with `ingestion/ingest.py` structure
4. **Sufficient for Current Scale:** Module will be ~450 lines (under 500-line limit)

**Trade-offs Accepted:**
- Larger ingestion module (mitigated by clear function boundaries)
- Less separation of concerns (acceptable for MVP, can refactor later)
- Future refactoring if adding 3+ content types (YAGNI principle)

**Migration Path:**
If we add more content types (e.g., training materials, incident reports), we can refactor to Option 2 or 3 at that time. The current extension is compatible with future modularization.

---

## Spike Plan

### Goal
Validate that product ingestion follows guideline patterns and meets performance requirements.

### Steps

**Step 1: Notion API Product Fetch (4 hours)**
- Test Notion API with product database ID
- Verify all required fields accessible (name, description, category, supplier, compliance_tags, use_cases, price_range)
- Check data quality (missing fields, inconsistent formats)
- **Success Criteria:** Successfully fetch 10+ products with all fields

**Step 2: Embedding Generation for Products (2 hours)**
- Generate embeddings for product descriptions + use cases
- Test embedding concatenation strategy (name + description + use_cases)
- Measure embedding quality with sample searches
- **Success Criteria:** Embeddings generated with <2s per product

**Step 3: Product Schema Validation (2 hours)**
- Verify `products` table schema matches Notion fields
- Test upsert logic for duplicate detection (by Notion page_id)
- Validate compliance_tags storage (array vs JSON)
- **Success Criteria:** Products stored without schema errors

**Step 4: Semantic Search Performance (3 hours)**
- Implement basic product search with pgvector
- Test with 100+ products in database
- Measure query latency for top 10 results
- Test combined semantic + compliance filter queries
- **Success Criteria:** <500ms average query time

**Step 5: Integration with Existing Codebase (3 hours)**
- Add product ingestion function to `ingestion/ingest.py`
- Create product search in `agent/product_queries.py`
- Test end-to-end: Notion → PostgreSQL → Search
- Verify no conflicts with guideline ingestion
- **Success Criteria:** Full pipeline runs without errors

**Total Spike Time:** 14 hours (~2 days)

---

## Implementation Notes

### File Structure
```
ingestion/
  ingest.py              # Add product ingestion functions (~150 lines)
agent/
  product_queries.py     # New file for product search (~100 lines)
tests/
  test_product_ingest.py # Unit tests for product ingestion
  test_product_search.py # Unit tests for product queries
```

### Key Functions to Add
- `ingest_products(notion_database_id: str) -> int` - Main ingestion entry point
- `parse_product_notion_page(page: dict) -> dict` - Extract product fields
- `upsert_product(conn, product_data: dict) -> bool` - Insert/update product
- `search_products(query: str, filters: dict, limit: int) -> list` - Semantic search

### Reused Components
- `generate_embedding()` from existing code
- Database connection from `config/database.py`
- Logging and error handling patterns
- Batch processing logic (100 products per batch)

### Configuration
Add to `config/notion_config.py`:
```python
PRODUCT_DATABASE_ID = "notion-product-db-id-here"
PRODUCT_FIELDS = ["Name", "Description", "Category", "Supplier", ...]
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Notion API rate limits with large catalog | Medium | Implement rate limiting, batch processing |
| Inconsistent product data in Notion | Medium | Add validation layer, log warnings for missing fields |
| Compliance tags format inconsistencies | Low | Normalize tags during ingestion (uppercase, strip spaces) |
| Search performance degrades with 1000+ products | Low | Add pgvector indexes, monitor query plans |
| Module exceeds 500-line limit | Low | Extract utilities if needed, or refactor to Option 2 |

---

## References

- [FEAT-002 Guideline Ingestion](../FEAT-002_notion-guideline-ingestion/) - Established pattern
- [pgvector Documentation](https://github.com/pgvector/pgvector) - Vector similarity search
- [Notion API Reference](https://developers.notion.com/reference/intro) - Database queries
- [PostgreSQL Products Schema](../../../sql/evi_schema_additions.sql) - Table definition

---

**Word Count:** 794 words (under 800-word limit)
