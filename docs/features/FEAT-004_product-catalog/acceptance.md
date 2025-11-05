# Acceptance Criteria: Product Catalog with Interventie Wijzer Integration

**Feature ID:** FEAT-004
**Created:** 2025-11-04
**Status:** Draft

## Overview

This feature is complete when:
- All 76 EVI 360 products are scraped from portal.evi360.nl with canonical URLs and pricing (validated 2025-11-04)
- ≥80% of 23 unique CSV products are fuzzy-matched and enriched (target: ≥19 products = 9 automated + 10 manual)
- The specialist agent can search and recommend products via hybrid search (<500ms)
- Products are formatted in Dutch markdown with working URLs
- All tests pass (18 unit + 6 integration) and manual testing shows ≥70% relevance

## Functional Acceptance Criteria

### AC-004-001: Portal Scraping Completeness

**Given** portal.evi360.nl/products listing page is accessible
**When** `python3 -m ingestion.scrape_portal_products` is executed
**Then** 76 products are scraped with all required fields populated (validated 2025-11-04)

**Validation:**
- [ ] Count of scraped products is 76 (exact count validated via full portal scan)
- [ ] Automated test: `test_scrape_portal_products_count()`
- [ ] All products have non-empty name, description, and URL fields
- [ ] Price field may be NULL (optional)
- [ ] Category will be NULL for scraped products (enriched from CSV where matched)
- [ ] Scraping completes in <10 minutes

**Priority:** Must Have

---

### AC-004-002: Canonical URL Coverage

**Given** products have been scraped from portal.evi360.nl
**When** products are inserted into the database
**Then** 100% of products have a canonical portal.evi360.nl URL in the format `https://portal.evi360.nl/products/{id}`

**Validation:**
- [ ] SQL query: `SELECT COUNT(*) FROM products WHERE url NOT LIKE 'https://portal.evi360.nl/products/%'` returns 0
- [ ] Automated test: `test_all_products_have_canonical_urls()`
- [ ] Manual spot-check: 5 random product URLs return HTTP 200

**Priority:** Must Have

---

### AC-004-003: CSV Fuzzy Matching Success Rate

**Given** Intervention_matrix.csv contains 26 rows with 23 unique products
**When** `parse_interventie_csv.py` fuzzy matches CSV products to portal products
**Then** ≥80% (≥19 of 23) CSV products are matched via automated (0.85 threshold) + manual mapping

**Validation:**
- [ ] Total match rate: ≥19/23 products (83%) = 9 automated (39%) + 10 manual (43%)
- [ ] Automated fuzzy matching at 0.85 threshold: 9 products matched
- [ ] Manual mappings loaded from `manual_product_mappings.json`: 10 products matched
- [ ] Automated test: `test_fuzzy_match_success_rate_above_threshold()`
- [ ] Unmatched products (4 expected) written to `unresolved_products.json` for stakeholder review
- [ ] Matched products have problem_mappings in metadata

**Note:** Manual mapping file must be validated by stakeholder before ingestion.

**Priority:** Must Have

---

### AC-004-004: Problem Mapping Enrichment

**Given** CSV products are fuzzy-matched to portal products (≥19 products matched)
**When** products are enriched with metadata
**Then** ≥19 products have `problem_mappings` array in metadata with ≥1 problem each

**Validation:**
- [ ] SQL query: `SELECT COUNT(*) FROM products WHERE jsonb_array_length(metadata->'problem_mappings') > 0` returns ≥19
- [ ] Automated test: `test_problem_mappings_enrichment()`
- [ ] Manual inspection: Sample product has readable Dutch problem descriptions in metadata
- [ ] Metadata structure: `{"problem_mappings": ["Problem 1", "Problem 2"], "csv_category": "Category"}`

**Priority:** Must Have

---

### AC-004-005: Embedding Coverage

**Given** products are enriched with problem mappings
**When** embeddings are generated using description + problems concatenated
**Then** 100% of products have a non-null 1536-dimensional embedding

**Validation:**
- [ ] SQL query: `SELECT COUNT(*) FROM products WHERE embedding IS NULL` returns 0
- [ ] Automated test: `test_all_products_have_embeddings()`
- [ ] Embedding dimension check: `SELECT array_length(embedding, 1) FROM products LIMIT 1` returns 1536

**Priority:** Must Have

---

### AC-004-006: Hybrid Search SQL Function Updated

**Given** products table contains products with embeddings
**When** `search_products(query_embedding, query_text, limit)` SQL function is called
**Then** function returns products ranked by hybrid similarity (70% vector + 30% Dutch text)

**Validation:**
- [ ] SQL function definition includes: `0.7 * (1 - (p.embedding <=> query_embedding)) + 0.3 * ts_rank(to_tsvector('dutch', p.description), plainto_tsquery('dutch', query_text))`
- [ ] Automated test: `test_hybrid_search_returns_ranked_results()`
- [ ] Manual query: "burn-out" returns relevant products (Herstelcoaching, Psychologische ondersteuning)

**Priority:** Must Have

---

### AC-004-007: search_products() Tool Registered

**Given** specialist agent is initialized
**When** agent tools are registered
**Then** `search_products()` tool is available with correct signature (ctx, query: str, limit: int)

**Validation:**
- [ ] Agent tool list contains "search_products"
- [ ] Automated test: `test_search_products_tool_registered()`
- [ ] Tool docstring describes purpose: "Search EVI 360 intervention products"
- [ ] Tool accepts Dutch query strings

**Priority:** Must Have

---

### AC-004-008: Agent Formats Products in Dutch Markdown

**Given** agent calls `search_products("burn-out", limit=3)`
**When** agent formats the response
**Then** products are displayed in Dutch markdown: "**[Name]** ([Price])\n[Description]\n[URL]"

**Validation:**
- [ ] Response includes bold product names (surrounded by **)
- [ ] Response includes URLs in markdown format [https://portal.evi360.nl/...]
- [ ] Response includes pricing if available (e.g., "€2.500 - €3.500")
- [ ] Automated test: `test_agent_formats_products_in_dutch_markdown()`

**Priority:** Must Have

---

### AC-004-009: Search Latency Performance

**Given** products table has 76 products with embeddings and IVFFLAT index
**When** hybrid search query is executed
**Then** search completes in <500ms at 95th percentile (p95)

**Validation:**
- [ ] Run 100 test queries, measure latency, calculate p95
- [ ] Automated test: `test_search_latency_under_500ms()`
- [ ] Performance log: "Search latency p95: 342ms" (example)

**Priority:** Must Have

---

### AC-004-010: Unit Test Suite Passes

**Given** 18 unit tests are implemented in `tests/unit/test_product_ingest.py`
**When** `pytest tests/unit/test_product_ingest.py` is executed
**Then** all 18 tests pass (100% pass rate)

**Validation:**
- [ ] Pytest output: "18 passed in X.XXs"
- [ ] No skipped or xfailed tests
- [ ] Tests cover: portal scraping (5), CSV parsing (5), enrichment (3), database (4), search tool (1)

**Priority:** Must Have

---

### AC-004-011: Integration Test Suite Passes

**Given** 6 integration tests are implemented in `tests/integration/test_product_ingestion_flow.py`
**When** `pytest tests/integration/test_product_ingestion_flow.py` is executed
**Then** all 6 tests pass (100% pass rate)

**Validation:**
- [ ] Pytest output: "6 passed in X.XXs"
- [ ] End-to-end flow test validates: scraping → CSV → DB → search
- [ ] Agent integration test confirms search_products() tool works

**Priority:** Must Have

---

### AC-004-012: Manual Testing Relevance

**Given** 10 Dutch test queries are defined in `manual-test.md`
**When** each query is tested manually via OpenWebUI or API
**Then** ≥7 queries (≥70%) return relevant products

**Validation:**
- [ ] Test queries: "burn-out", "fysieke klachten", "conflict", "verzuim", "werkdruk", "zwangerschap", "psychische klachten", "leefstijl", "re-integratie", "bedrijfsmaatschappelijk werk"
- [ ] Manual testing checklist: ≥7/10 marked as "relevant"
- [ ] All returned product URLs are working (HTTP 200)

**Priority:** Must Have

---

### AC-004-013: Documentation Updated

**Given** FEAT-004 implementation is complete
**When** documentation files are reviewed
**Then** PRD, CHANGELOG.md, and docs/README.md reflect completed feature

**Validation:**
- [ ] CHANGELOG.md includes entry: "FEAT-004: Product Catalog with Interventie Wijzer Integration - Complete"
- [ ] docs/README.md lists FEAT-004 as "Implemented"
- [ ] PRD status updated to "Complete"

**Priority:** Should Have

---

## Edge Cases & Error Handling

### AC-004-101: Empty Portal Response

**Scenario:** Portal.evi360.nl returns empty product listing (network issue, site down, authentication required)

**Given** portal.evi360.nl/products is inaccessible or returns empty HTML
**When** scraping is attempted
**Then** scraper logs error "No products found on listing page" and exits gracefully without crashing

**Validation:**
- [ ] Automated test: `test_scraper_handles_empty_portal_response()`
- [ ] Error message logged to console
- [ ] No partial database inserts occur

**Priority:** Must Have

---

### AC-004-102: CSV Fuzzy Match Failure (<80%)

**Scenario:** Fuzzy matching achieves <80% success rate due to naming mismatches

**Given** portal products have significantly different names than CSV products
**When** fuzzy matching is executed
**Then** unmatched products are logged with similarity scores for manual review

**Validation:**
- [ ] Log output: "⚠️  Unmatched CSV products (8): ['Product A', 'Product B', ...]"
- [ ] Automated test: `test_unmatched_products_logged()`
- [ ] Products without CSV matches still have embeddings (description only)

**Priority:** Should Have

---

### AC-004-103: Missing Price or URL Field

**Scenario:** Some portal products are missing price or URL fields after scraping

**Given** portal HTML for a product lacks price element or URL is malformed
**When** product details are extracted
**Then** product is still inserted with `price=None` or URL validation error logged

**Validation:**
- [ ] Products with NULL price are accepted (price is optional)
- [ ] Products with missing URLs are rejected and logged: "Product X missing required URL field"
- [ ] Automated test: `test_missing_price_field_handled()`

**Priority:** Should Have

---

### AC-004-104: Slow Search Latency (>500ms)

**Scenario:** Hybrid search query exceeds 500ms latency threshold

**Given** products table has poor indexing or query is complex
**When** search query is executed
**Then** slow query is logged with warning: "Search latency 780ms exceeds 500ms threshold"

**Validation:**
- [ ] Latency logged to console or monitoring system
- [ ] Automated test: `test_slow_search_latency_logged()` (mock slow query)
- [ ] Recommendations logged: "Consider rebuilding IVFFLAT index"

**Priority:** Should Have

---

### AC-004-105: Agent Doesn't Call search_products()

**Scenario:** Agent receives intervention-related query but doesn't call search_products() tool

**Given** user query is "Welke interventies zijn er voor burn-out?"
**When** agent processes query
**Then** agent response includes products (via search_products() call) or logs "No products tool call made"

**Validation:**
- [ ] Agent system prompt explicitly instructs: "Call search_products() when user asks about interventions"
- [ ] Automated test: `test_agent_calls_search_products_on_intervention_query()`
- [ ] Manual testing: intervention queries trigger product recommendations

**Priority:** Must Have

---

## Non-Functional Requirements

### AC-004-201: Search Performance

**Requirement:** Hybrid search must complete in <500ms for p95 latency

**Criteria:**
- **Response Time:** <500ms for 95% of queries
- **Throughput:** ≥10 queries per second (concurrent)
- **Resource Usage:** <100MB memory per query

**Validation:**
- [ ] Performance tests demonstrate meeting targets
- [ ] Load testing completed (100 concurrent queries)
- [ ] Monitoring logs search latency

---

### AC-004-202: Data Quality

**Requirement:** Product data must be accurate and complete

**Criteria:**
- **URL Accuracy:** 100% of products have canonical portal.evi360.nl URLs
- **Embedding Coverage:** 100% of products have embeddings
- **CSV Enrichment:** ≥80% of CSV products matched to portal products
- **Problem Context:** ≥25 products have problem_mappings

**Validation:**
- [ ] Data quality checks run during ingestion
- [ ] SQL validation queries pass
- [ ] Manual spot-checks confirm accuracy

---

### AC-004-203: Maintainability

**Requirement:** Product catalog can be easily refreshed when portal updates

**Criteria:**
- **Re-scraping:** CLI command `python3 -m ingestion.ingest_products --refresh` re-scrapes portal
- **Upsert Logic:** Existing products updated by (name, URL, description)
- **New Products:** Automatically added during re-scraping
- **Removed Products:** Gracefully handled (no hard deletes, mark inactive)

**Validation:**
- [ ] Re-scraping completes in <10 minutes
- [ ] Upsert logic tested with modified products
- [ ] No duplicate products created

---

## Integration Requirements

### AC-004-301: Agent Tool Integration

**Requirement:** search_products() tool integrates seamlessly with specialist agent

**Given** specialist agent is initialized with search_products() tool
**When** agent receives query: "Welke interventies zijn er voor burn-out?"
**Then** agent calls tool, receives products, formats in Dutch markdown

**Validation:**
- [ ] Integration test passes: `test_specialist_agent_product_search_integration()`
- [ ] No breaking changes to existing guideline search functionality
- [ ] Agent can call both search_guidelines() and search_products() in same response

---

### AC-004-302: Database Schema Integration

**Requirement:** Products table integrates with existing database schema

**Given** products table exists with embedding and metadata fields
**When** hybrid search query is executed
**Then** search leverages IVFFLAT index and JSONB metadata index

**Validation:**
- [ ] EXPLAIN ANALYZE shows index usage
- [ ] Schema migration adds price field, removes compliance_tags
- [ ] Backward compatibility: existing product queries still work

---

## Data Requirements

### AC-004-401: CSV Data Validation

**Requirement:** Intervention_matrix.csv must be valid and parsable

**Criteria:**
- **Format:** Valid CSV with headers: Probleem, Category, Link interventie, Soort interventie
- **Row Count:** 26 rows with 23 unique products (excluding header)
- **Encoding:** UTF-8 with Dutch characters (UTF-8-with-BOM)
- **Required Fields:** All rows have non-empty Probleem and Soort interventie

**Validation:**
- [ ] CSV parses without errors
- [ ] All 26 rows processed
- [ ] 23 unique products extracted (many-to-one: multiple problems → same product)
- [ ] Dutch characters (ë, ü, etc.) handled correctly

---

### AC-004-402: Database Storage

**Requirement:** Products are persisted correctly in PostgreSQL

**Criteria:**
- **Schema:** products table with embedding vector(1536), metadata JSONB, price TEXT
- **Indexes:** IVFFLAT index on embedding, GIN index on metadata
- **Constraints:** url NOT NULL, name NOT NULL
- **Migrations:** Schema updates applied via migration script

**Validation:**
- [ ] Schema matches specification: `\d products` in psql
- [ ] Indexes exist: `\di products*`
- [ ] Data integrity maintained: no NULL urls

---

## Acceptance Checklist

### Development Complete
- [ ] All functional criteria met (AC-004-001 through AC-004-013)
- [ ] All edge cases handled (AC-004-101 through AC-004-105)
- [ ] Non-functional requirements met (AC-004-201 through AC-004-203)
- [ ] Integration requirements met (AC-004-301 through AC-004-302)
- [ ] Data requirements met (AC-004-401 through AC-004-402)

### Testing Complete
- [ ] Unit tests written and passing (18 tests)
- [ ] Integration tests written and passing (6 tests)
- [ ] Manual testing completed per manual-test.md (≥7/10 relevant)
- [ ] Performance testing completed (<500ms p95 latency)
- [ ] Data quality validation completed (100% URLs, ≥80% CSV match)

### Documentation Complete
- [ ] Code documented (inline comments, docstrings)
- [ ] Architecture decision documented (architecture.md)
- [ ] Testing strategy documented (testing.md)
- [ ] Manual test guide created (manual-test.md)
- [ ] CHANGELOG.md updated
- [ ] docs/README.md updated

### Deployment Ready
- [ ] Schema migration script created (add price, remove compliance_tags)
- [ ] CLI commands tested (ingest_products, --refresh flag)
- [ ] Agent restriction removed ("Geen producten aanbevelen" deleted)
- [ ] search_products() tool registered and tested
- [ ] Portal scraping validated on live site

---

**Appended to `/AC.md`:** Pending (will be appended after review)
**Next Steps:** Proceed to testing strategy and test stub generation
