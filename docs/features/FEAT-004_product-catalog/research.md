# Research Findings: FEAT-004 Product Catalog with Interventie Wijzer Integration

**Feature ID:** FEAT-004
**Research Date:** 2025-11-03 (Updated to align with PRD v3.0)
**Researcher:** Explorer + Plan Agents
**Status:** Aligned with PRD v3.0 - Portal Scraping + CSV Enrichment

---

## Research Questions

*Questions addressed based on PRD v3.0 requirements:*

1. What web scraping technology should be used for portal.evi360.nl?
2. Should products be stored in the products table or chunks table?
3. Does the specialist agent already support product recommendations?
4. What existing infrastructure can be reused?
5. How should CSV problem mappings be integrated with portal products?
6. What is the optimal embedding strategy for products?

---

## Executive Summary

**PRD v3.0 Decision:** Use **portal.evi360.nl web scraping** as primary data source, enriched with **Interventie Wijzer CSV** for problem-to-product mappings. This approach provides:

- ✅ **Canonical URLs** from portal.evi360.nl (source of truth)
- ✅ **Current pricing** from live portal pages
- ✅ **Problem context** from CSV enrichment
- ✅ **No Notion dependency** (simplified architecture)

**Key Change from Earlier Research:** Original research recommended Notion database, but PRD v3.0 shifted to portal scraping for better URL accuracy and pricing data.

---

## Findings

### Topic 1: Web Scraping Technology - Crawl4AI vs. BeautifulSoup

**Summary:** Crawl4AI is the recommended technology for scraping portal.evi360.nl due to JavaScript rendering support and intelligent content extraction.

**Details:**

**Crawl4AI (RECOMMENDED):**
- ✅ **JavaScript rendering:** Handles modern web apps with dynamic content
- ✅ **Intelligent extraction:** Can ignore header/footer automatically
- ✅ **Async support:** Compatible with existing async codebase (asyncpg, httpx)
- ✅ **Click simulation:** Can navigate from listing → individual product pages
- ✅ **Error handling:** Built-in retry logic and timeout management
- ✅ **Estimated effort:** 4 hours (scraping strategy + extraction logic)

**BeautifulSoup (Alternative):**
- ⚠️ **Static HTML only:** Fails if portal uses JavaScript rendering
- ⚠️ **Manual navigation:** Requires custom logic for clicking into pages
- ⚠️ **No retry logic:** Must build error handling from scratch
- ⚠️ **Estimated effort:** 6-8 hours (build all infrastructure)

**Source:** PRD v3.0 Technical Architecture (lines 206-273)
**Decision:** Use Crawl4AI for portal scraping

---

### Topic 2: Storage Architecture - Products Table vs. Chunks Table

**Summary:** Existing architecture has a dedicated products table with product-specific fields. Products table is the correct choice for clean separation and proper data modeling.

**Details:**

**Existing Products Table Schema** (`sql/evi_schema_additions.sql`):
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    category TEXT,
    subcategory TEXT,
    embedding vector(1536),
    compliance_tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    source TEXT DEFAULT 'evi360_website',
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**PRD v3.0 Schema Updates Required:**
- ✅ Add `price TEXT` field (from portal scraping)
- ✅ Change `source` default from `'evi360_website'` to `'portal'`
- ❌ Remove `subcategory TEXT` (not in scope)
- ❌ Remove `compliance_tags TEXT[]` (not in scope)
- ✅ Use `metadata JSONB` for `problem_mappings` array and `csv_category`

**Comparison Analysis:**

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Products table** | • Dedicated schema with product-specific fields (url, price, category)<br>• Separate search function `search_products()`<br>• Clean separation of concerns<br>• Already built and indexed | • Requires separate ingestion code<br>• Not reusable with existing chunker | ✅ **RECOMMENDED** (PRD v3.0) |
| **Chunks table** | • Reuses existing ingestion pipeline<br>• Simple: treat products as documents | • Loses product-specific fields (url, price, category)<br>• Mixes guidelines and products<br>• No clean way to filter "only products"<br>• Cannot use `search_products()` SQL function | ❌ **NOT RECOMMENDED** |

**Source:** Codebase analysis + PRD v3.0 Database Schema (lines 394-444)
**Decision:** Use dedicated products table with schema updates

---

### Topic 3: Specialist Agent Current State - Product Support

**Summary:** Specialist agent explicitly has products DISABLED. Products are marked as "not in this version" in both Dutch and English prompts.

**Details:**

**Current Agent Configuration** (`agent/specialist_agent.py`):
- **Line 44 (Dutch prompt):** `"Geen producten aanbevelen (niet in deze versie)"`
- **Line 74 (English prompt):** `"Do not recommend products (not in this version)"`

**Current Workflow:**
```
Query → search_guidelines() tool → hybrid_search (guidelines only) → Dutch response with citations
```

**Product Tools Status:**
- ❌ No `search_products()` tool registered with agent
- ❌ No product retrieval in agent workflow
- ✅ Models exist but unused: `ProductRecommendation`, `ProductSearchResult`

**PRD v3.0 Requirements (Phase 5):**
- ✅ Remove "Geen producten aanbevelen" restriction from prompts
- ✅ Add `search_products()` tool to agent toolkit
- ✅ Add system prompt instruction to call tool when contextually relevant
- ✅ Format products in Dutch markdown with URLs and pricing

**Source:** Code review + PRD v3.0 Phase 5 (lines 723-762)
**Decision:** Enable products by removing restriction and adding tool

---

### Topic 4: Existing Infrastructure Assessment

**Summary:** Comprehensive infrastructure already exists for products: database schema, SQL functions, Pydantic models. Only missing: portal scraper, CSV parser, and agent tool registration.

**Details:**

**✅ Ready Infrastructure:**

1. **Database Schema:**
   - Products table created: `sql/evi_schema_additions.sql`
   - Vector index configured: `idx_products_embedding` (IVFFLAT)
   - Metadata index: GIN index on JSONB metadata field
   - **Needs:** Price field addition, compliance_tags removal

2. **SQL Functions:**
   - `search_products()` function exists (needs hybrid search update)
   - Returns: product_id, name, description, url, category, similarity, metadata
   - **Needs:** 70% vector + 30% Dutch text hybrid search update

3. **Pydantic Models** (`agent/models.py`):
   - `EVIProduct`: Full product model with validation
   - `ProductRecommendation`: Recommendation with relevance scoring
   - `ProductSearchResult`: Database search result
   - **Needs:** Remove `compliance_tags`, `subcategory`; add `price`

4. **Embedding Infrastructure:**
   - `ingestion/embedder.py` ready for product embeddings
   - OpenAI text-embedding-3-small (1536 dimensions)
   - **Reusable:** No changes needed

**❌ Missing Components (To Build):**

1. **Portal Scraper:**
   - `ingestion/scrape_portal_products.py` (NEW FILE)
   - Crawl4AI implementation for portal.evi360.nl
   - Extract: name, description, price, URL, category

2. **CSV Parser:**
   - `ingestion/parse_interventie_csv.py` (NEW FILE)
   - Parse `Intervention_matrix.csv` (33 rows)
   - Fuzzy matching (fuzzywuzzy, ≥0.9 threshold)

3. **Product Ingestion Orchestrator:**
   - `ingestion/ingest_products.py` (NEW FILE)
   - Combine portal + CSV data
   - Generate embeddings (description + problems)
   - Upsert to database

4. **Agent Tool:**
   - `search_products_tool()` in `agent/tools.py` (NEW FUNCTION)
   - Hybrid search: 70% vector + 30% Dutch text
   - Return top 3-5 products with URLs and pricing

**Source:** Codebase analysis + PRD v3.0 Implementation Plan (lines 556-792)
**Decision:** Build missing components, leverage existing infrastructure

---

### Topic 5: CSV Integration Strategy - Fuzzy Matching Products

**Summary:** Interventie Wijzer CSV provides problem-to-product mappings. Use fuzzy matching to enrich portal products with problem context.

**Details:**

**CSV Structure** (`Intervention_matrix.csv` - 33 rows):

| Column | Description | Usage |
|--------|-------------|-------|
| `Probleem` | Problem description in Dutch | Store in `metadata.problem_mappings` |
| `Category` | Category label | Store in `metadata.csv_category` |
| `Link interventie` | **IGNORE** (old URLs) | Not used |
| `Soort interventie` | Product name | Fuzzy match to portal product names |

**Fuzzy Matching Strategy:**

```python
from fuzzywuzzy import fuzz

def fuzzy_match_products(csv_products, portal_products, threshold=0.9):
    """
    Match CSV products to portal products by name similarity.

    Args:
        csv_products: From parse_interventie_csv()
        portal_products: From scrape_all_products()
        threshold: Minimum similarity (0.9 = 90%)

    Returns:
        Enriched portal products with problem_mappings
    """
    for csv_prod in csv_products:
        csv_name = normalize_product_name(csv_prod["product_name"])

        for portal_prod in portal_products:
            portal_name = normalize_product_name(portal_prod["name"])
            score = fuzz.ratio(csv_name, portal_name) / 100.0

            if score >= threshold:
                # Enrich portal product with CSV data
                portal_prod["metadata"]["problem_mappings"] = csv_prod["problems"]
                portal_prod["metadata"]["csv_category"] = csv_prod["category"]
                break
```

**Many-to-One Relationship:**
- Multiple problems can map to same product
- Example: "Vroegconsult Arbeidsdeskundige" linked to 3 different problems
- Aggregate all problems into single `problem_mappings` array

**PRD v3.0 Requirements:**
- ✅ Parse 33 CSV rows into problem-product mappings
- ✅ Ignore CSV URLs (old/irrelevant)
- ✅ Use fuzzy matching (≥0.9 threshold)
- ✅ Log unmatched products for manual review
- ✅ Target: ≥80% match rate (27+ of 33 products)

**Source:** PRD v3.0 Technical Architecture (lines 283-390)
**Decision:** Fuzzy match CSV → portal products, enrich metadata

---

### Topic 6: Embedding Strategy - Description + Problems Concatenation

**Summary:** Embed products as concatenation of description + problem mappings for richer semantic matching. No chunking - one embedding per product.

**Details:**

**Embedding Text Construction:**
```python
# For products WITH CSV enrichment
embedding_text = f"{description}\n\n{'\n'.join(problem_mappings)}"

# For products WITHOUT CSV enrichment
embedding_text = description
```

**Example Embedding Text:**
```
Multidisciplinaire begeleiding door fysiotherapeut en psycholoog voor complexe burn-out gevallen.

Mijn werknemer heeft burn-out klachten
Het gaat slecht met mijn werknemer, hoe krijgt hij gericht advies?
```

**Rationale:**
- ✅ **Richer semantics:** Problems provide query-like context
- ✅ **Better matching:** Product descriptions + user problem phrasing
- ✅ **No chunking needed:** Products are atomic units (~450 tokens avg)
- ✅ **Efficient:** 1 embedding per product (not 3-5 chunks)

**PRD v3.0 Specifications:**
- **Model:** OpenAI text-embedding-3-small
- **Dimensions:** 1536
- **Chunking:** NONE (products are atomic)
- **Storage:** 1 embedding in `products.embedding` vector(1536)

**Source:** PRD v3.0 Data Models (lines 536-549)
**Decision:** Embed description + problems, no chunking

---

### Topic 7: Hybrid Search Strategy - 70% Vector + 30% Dutch Text

**Summary:** Use hybrid search combining vector similarity with Dutch full-text search for optimal recall and precision.

**Details:**

**Hybrid Search SQL Function:**
```sql
CREATE OR REPLACE FUNCTION search_products(
    query_embedding vector(1536),
    query_text TEXT,
    match_limit INT DEFAULT 5
)
RETURNS TABLE (...) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ...,
        -- Hybrid similarity: 70% vector + 30% text search
        (0.7 * (1 - (p.embedding <=> query_embedding)) +
         0.3 * ts_rank(to_tsvector('dutch', p.description),
                       plainto_tsquery('dutch', query_text))) AS similarity
    FROM products p
    ORDER BY similarity DESC
    LIMIT match_limit;
END;
$$;
```

**Rationale:**
- ✅ **Vector (70%):** Captures semantic similarity (burn-out ≈ overspanning)
- ✅ **Text (30%):** Captures keyword matching (exact terms like "fysiotherapie")
- ✅ **Dutch support:** `to_tsvector('dutch', ...)` handles Dutch stemming
- ✅ **Balanced:** Avoids pure vector issues (low recall) and pure text issues (low precision)

**PRD v3.0 Requirements:**
- Hybrid search: 70% vector + 30% text (line 476)
- Dutch full-text search configuration
- Return top 3-5 products by similarity
- Include price, URL, metadata in results

**Source:** PRD v3.0 Database Schema (lines 449-485)
**Decision:** Hybrid search with 70/30 split

---

## Recommendations

### Primary Recommendation: Portal Scraping + CSV Enrichment (14 hours)

**Rationale (PRD v3.0):**
1. **Canonical URLs:** Portal provides accurate, working URLs (source of truth)
2. **Current pricing:** Scraped from live portal pages
3. **Problem context:** CSV enrichment adds user-problem semantics
4. **No Notion dependency:** Simplified architecture, fewer moving parts
5. **Automated updates:** Re-scraping via `python3 -m ingestion.ingest_products --refresh`

**Implementation Phases (PRD v3.0):**

**Phase 1: Portal Scraping with Crawl4AI (4 hours)**
- Scrape product listing from portal.evi360.nl/products
- Click into each of ~60 product pages
- Extract: name, description, price, category, canonical URL
- Save to intermediate JSON file

**Phase 2: CSV Parsing & Fuzzy Matching (2 hours)**
- Parse Intervention_matrix.csv (33 rows)
- Extract problem descriptions, categories, product names
- Fuzzy match (≥0.9 threshold) CSV → portal products
- Log unmatched products for manual review

**Phase 3: Product Enrichment & Embedding (2.5 hours)**
- Enrich portal products with CSV problem_mappings
- Generate embeddings: description + problems
- Update schema (add price, remove compliance_tags)
- Upsert to products table

**Phase 4: Hybrid Search Tool (2 hours)**
- Update search_products() SQL function (70% vector + 30% text)
- Create search_products_tool() in agent/tools.py
- Test hybrid search with sample queries

**Phase 5: Agent Integration (1.5 hours)**
- Remove "Geen producten aanbevelen" restriction
- Add search_products() tool to specialist agent
- Update system prompt with product formatting guidelines

**Phase 6: Testing & Validation (2 hours)**
- Unit tests (18 tests from existing stubs)
- Integration tests (6 tests)
- Manual testing (10 test queries)

**Total Time:** 14 hours (PRD v3.0 estimate)

**Key Benefits:**
- **100% URL coverage** (canonical portal URLs)
- **Current pricing** (scraped from live site)
- **Problem context** (CSV enrichment)
- **No manual updates** (re-scrape when needed)

---

## Trade-offs

### Portal Scraping vs. Notion Database

**Decision (PRD v3.0):** Portal scraping (not Notion)

**Rationale:**
- Portal provides canonical URLs (source of truth)
- Portal has current pricing
- No Notion API dependency
- Re-scraping ensures data freshness

**Impact:**
- +4 hours development (Crawl4AI scraping)
- +Better URL accuracy (100% vs. ~80% with Notion)
- +Current pricing (vs. potentially stale in Notion)

### Hybrid Search vs. Vector-Only

**Decision (PRD v3.0):** Hybrid search (70% vector + 30% text)

**Rationale:**
- Products have shorter text than guidelines
- Keyword matching helps for specific terms (e.g., "fysiotherapie")
- Dutch full-text search adds minimal overhead
- Better recall and precision balance

**Impact:**
- +30 min development (update SQL function)
- +Better relevance for keyword-heavy queries
- -Negligible performance impact (<10ms)

### CSV Enrichment vs. Portal-Only

**Decision (PRD v3.0):** CSV enrichment (problem mappings)

**Rationale:**
- Problem descriptions provide query-like context
- Improves semantic matching (user problems → products)
- Many-to-one relationship (multiple problems → 1 product)
- Only 2 hours additional effort

**Impact:**
- +2 hours development (fuzzy matching)
- +Better retrieval quality (~15-20% improvement expected)
- +≥25 products enriched with problem context

---

## Resources

### Official Documentation
- **Crawl4AI**: https://crawl4ai.com/docs (web scraping)
- **fuzzywuzzy**: https://github.com/seatgeek/fuzzywuzzy (fuzzy matching)
- **PostgreSQL pgvector**: https://github.com/pgvector/pgvector (vector search)
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **Pydantic AI**: https://ai.pydantic.dev/ (agent framework)

### PRD v3.0 References
- **Implementation Plan**: PRD lines 556-792
- **Database Schema**: PRD lines 394-493
- **Embedding Strategy**: PRD lines 536-549
- **Success Metrics**: PRD lines 97-130

### Existing Infrastructure
- **Embedding generation**: `ingestion/embedder.py`
- **Database utilities**: `agent/db_utils.py`
- **Product models**: `agent/models.py` (lines 308-391)
- **SQL schema**: `sql/evi_schema_additions.sql`

---

## Answers to Key Questions

### Question 1: What is the data source for products?
**Answer:** Portal.evi360.nl web scraping (primary) + Intervention_matrix.csv (enrichment)
**Confidence:** High
**Source:** PRD v3.0 lines 48-53

### Question 2: Should we use products table or chunks table?
**Answer:** Products table (dedicated schema with product-specific fields)
**Confidence:** High
**Source:** PRD v3.0 Database Schema (lines 394-444)

### Question 3: Does the specialist agent support products?
**Answer:** No - currently disabled with "Geen producten aanbevelen" restriction
**Confidence:** High
**Source:** Code review + PRD v3.0 Phase 5 requirements

### Question 4: What web scraping technology to use?
**Answer:** Crawl4AI (JavaScript rendering, async support, intelligent extraction)
**Confidence:** High
**Source:** PRD v3.0 Technical Architecture (lines 206-273)

### Question 5: How to integrate CSV problem mappings?
**Answer:** Fuzzy match (≥0.9 threshold) CSV products → portal products, store in metadata
**Confidence:** High
**Source:** PRD v3.0 lines 283-390

### Question 6: What embedding strategy for products?
**Answer:** Embed description + problems concatenated, no chunking (1 embedding per product)
**Confidence:** High
**Source:** PRD v3.0 Data Models (lines 536-549)

### Question 7: Vector-only or hybrid search?
**Answer:** Hybrid search (70% vector + 30% Dutch full-text)
**Confidence:** High
**Source:** PRD v3.0 SQL Function (lines 449-485)

### Question 8: What are the success metrics?
**Answer:** ~60 products, 100% URL coverage, ≥80% CSV match, <500ms latency, ≥70% relevance
**Confidence:** High
**Source:** PRD v3.0 Success Metrics (lines 107-119)

---

## Critical Implementation Notes

**⚠️ IMPORTANT - PRD v3.0 is Source of Truth:**

1. **No Notion Database Integration**
   - Earlier research recommended Notion
   - PRD v3.0 changed to portal scraping
   - Do NOT implement Notion ingestion

2. **Portal.evi360.nl is Source of Truth**
   - Canonical URLs from portal
   - Current pricing from portal
   - CSV only adds problem_mappings metadata

3. **Crawl4AI Required (Not BeautifulSoup)**
   - JavaScript rendering support
   - Click into individual product pages
   - Ignore header/footer elements

4. **Fuzzy Matching Required**
   - Use fuzzywuzzy library
   - ≥0.9 threshold (90% similarity)
   - Log unmatched products for manual review

5. **Hybrid Search Required**
   - 70% vector + 30% Dutch text
   - Not vector-only
   - Update existing SQL function

6. **No Compliance Tags**
   - Removed from scope (PRD v3.0)
   - Remove from schema and models
   - Focus on description + problem_mappings

---

## Next Steps

1. ✅ **Research Complete** - PRD v3.0 approach validated
2. ⏳ **Architecture Planning** - Create `architecture.md` with portal scraping flow
3. ⏳ **Acceptance Criteria** - Create `acceptance.md` with success metrics
4. ⏳ **Testing Strategy** - Create `testing.md` with 10 test queries
5. ⏳ **Manual Test Guide** - Create `manual-test.md` with validation checklist

**Ready for Planning:** Yes - `/plan FEAT-004` with PRD v3.0 approach

---

**Research Complete:** ✅ **ALIGNED WITH PRD v3.0 (2025-11-03)**
**Data Source:** Portal.evi360.nl scraping + Intervention_matrix.csv enrichment
**Technology:** Crawl4AI for web scraping, fuzzywuzzy for matching
**Storage:** Products table with price field, problem_mappings in metadata
**Search:** Hybrid (70% vector + 30% Dutch text)
**Effort:** 14 hours (6 phases)
