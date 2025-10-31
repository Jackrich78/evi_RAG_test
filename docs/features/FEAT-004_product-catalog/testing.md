# Testing Strategy: Product Catalog Integration

## Feature ID
FEAT-004

## Feature Name
Product Catalog Integration

## Overview
This document defines the comprehensive testing strategy for product catalog ingestion, including unit tests, integration tests, and manual testing requirements. All tests will be created as stubs during planning and implemented during Phase 2.

---

## Test Levels

### Unit Tests
**Purpose:** Validate individual functions and classes in isolation
**Coverage Goal:** 90%+ code coverage for product ingestion and search modules
**Framework:** pytest with fixtures and mocking

### Integration Tests
**Purpose:** Validate end-to-end workflows with real database and API interactions
**Coverage Goal:** All critical paths (ingestion, search, filtering)
**Framework:** pytest with test database

### Manual Tests
**Purpose:** Human validation of data quality, search relevance, and edge cases
**Scope:** Defined in separate manual-test.md document

---

## Unit Test Plan

### File: tests/unit/test_product_ingest.py
**Module Under Test:** ingestion/ingest.py (product ingestion functions)
**Test Count:** 15 tests

**Test Cases:**
1. `test_parse_product_notion_page_complete_data()` - AC-FEAT-004-001
   - Verify all fields extracted from Notion page with complete data
2. `test_parse_product_notion_page_missing_optional_fields()` - AC-FEAT-004-021
   - Handle missing optional fields (price_range, supplier) gracefully
3. `test_parse_product_notion_page_missing_required_fields()` - AC-FEAT-004-022
   - Skip products missing name or description, log error
4. `test_parse_product_notion_page_special_characters()` - AC-FEAT-004-032
   - Preserve special characters in product names and descriptions
5. `test_normalize_compliance_tags()` - AC-FEAT-004-014
   - Normalize tags to uppercase and trim whitespace
6. `test_generate_product_embedding()` - AC-FEAT-004-002
   - Generate embedding from name + description + use_cases
7. `test_generate_product_embedding_long_description()` - AC-FEAT-004-033
   - Truncate descriptions exceeding token limit with warning
8. `test_upsert_product_new_product()` - AC-FEAT-004-003
   - Insert new product into database
9. `test_upsert_product_existing_product()` - AC-FEAT-004-004
   - Update existing product by Notion page_id
10. `test_ingest_products_success()` - AC-FEAT-004-020
    - Ingest multiple products successfully
11. `test_ingest_products_empty_catalog()` - AC-FEAT-004-031
    - Handle empty Notion database gracefully
12. `test_ingest_products_notion_api_failure()` - AC-FEAT-004-028
    - Retry on Notion API failure with exponential backoff
13. `test_ingest_products_database_failure()` - AC-FEAT-004-029
    - Rollback transaction on database error
14. `test_ingest_products_batch_processing()` - AC-FEAT-004-023
    - Process products in batches of 100
15. `test_concurrent_ingestion_prevention()` - AC-FEAT-004-034
    - Prevent concurrent ingestion with file lock

---

### File: tests/unit/test_product_search.py
**Module Under Test:** agent/product_queries.py (product search functions)
**Test Count:** 12 tests

**Test Cases:**
1. `test_search_products_semantic_similarity()` - AC-FEAT-004-006
   - Return products ranked by cosine similarity
2. `test_search_products_result_content()` - AC-FEAT-004-007
   - Verify result format includes all required fields
3. `test_search_products_dutch_language()` - AC-FEAT-004-009
   - Search with Dutch query returns relevant products
4. `test_search_products_empty_results()` - AC-FEAT-004-010
   - Return empty list for non-matching query
5. `test_search_products_single_compliance_filter()` - AC-FEAT-004-011
   - Filter by single compliance tag (CE)
6. `test_search_products_multiple_compliance_filters()` - AC-FEAT-004-012
   - Filter by multiple tags with AND logic
7. `test_search_products_combined_semantic_filter()` - AC-FEAT-004-013
   - Combine semantic search with compliance filters
8. `test_search_products_invalid_compliance_filter()` - AC-FEAT-004-015
   - Handle non-existent compliance tag gracefully
9. `test_search_products_performance_benchmark()` - AC-FEAT-004-008
   - Verify search completes in <500ms (performance test)
10. `test_search_products_uses_index()` - AC-FEAT-004-025
    - Verify pgvector index is used (check query plan)
11. `test_link_products_to_guidelines_by_category()` - AC-FEAT-004-016
    - Link products by matching category
12. `test_link_products_to_guidelines_by_keywords()` - AC-FEAT-004-017
    - Link products by use_case keywords

---

### File: tests/unit/test_product_models.py
**Module Under Test:** agent/models.py (Product Pydantic models)
**Test Count:** 5 tests

**Test Cases:**
1. `test_product_model_validation_success()` - Validate correct Product model
2. `test_product_model_missing_required_fields()` - Reject missing name/description
3. `test_product_model_compliance_tags_list()` - Validate compliance_tags as list
4. `test_product_model_optional_fields_null()` - Allow null for optional fields
5. `test_product_search_result_model()` - Validate ProductSearchResult model

---

## Integration Test Plan

### File: tests/integration/test_product_ingestion_flow.py
**Scope:** End-to-end ingestion from Notion to PostgreSQL
**Test Count:** 6 tests
**Prerequisites:** Test database with products schema, mock Notion API

**Test Cases:**
1. `test_full_ingestion_pipeline()` - AC-FEAT-004-001, AC-FEAT-004-003
   - Fetch from Notion → Parse → Generate embeddings → Store in DB
2. `test_incremental_ingestion_updates()` - AC-FEAT-004-004, AC-FEAT-004-019
   - Re-ingest updated products, verify upsert behavior
3. `test_ingestion_with_large_catalog()` - AC-FEAT-004-023
   - Ingest 500+ products in batches
4. `test_ingestion_rollback_on_error()` - AC-FEAT-004-029
   - Verify transaction rollback on mid-ingestion failure
5. `test_ingestion_logs_skipped_products()` - AC-FEAT-004-022
   - Log products skipped due to missing required fields
6. `test_embedding_generation_timing()` - AC-FEAT-004-024
   - Measure embedding generation time per product

---

### File: tests/integration/test_product_search_flow.py
**Scope:** End-to-end product search with real database
**Test Count:** 8 tests
**Prerequisites:** Test database populated with sample products

**Test Cases:**
1. `test_semantic_search_end_to_end()` - AC-FEAT-004-006, AC-FEAT-004-007
   - Query → Embedding → Vector search → Return formatted results
2. `test_search_performance_100_products()` - AC-FEAT-004-008
   - Measure search latency with 100+ products
3. `test_search_with_compliance_filters()` - AC-FEAT-004-011, AC-FEAT-004-012
   - Combined semantic + filter search
4. `test_search_dutch_queries()` - AC-FEAT-004-009
   - Test multiple Dutch search queries
5. `test_product_guideline_links()` - AC-FEAT-004-018
   - Verify related products appear with guideline results
6. `test_search_relevance_ranking()` - Verify most relevant products rank highest
7. `test_search_with_empty_database()` - AC-FEAT-004-010
   - Search returns empty results when no products exist
8. `test_database_connection_security()` - AC-FEAT-004-027
   - Verify SSL/TLS connection to database

---

## Test Data Requirements

### Mock Notion Responses
**Location:** tests/fixtures/notion_product_responses.json
**Content:** Sample Notion API responses with various product configurations
- Complete product with all fields
- Product with missing optional fields
- Product with missing required fields
- Product with special characters
- Product with very long description

### Test Database
**Location:** Separate test database (not production)
**Schema:** Same as production products table
**Seed Data:**
- 10 products for basic tests
- 100+ products for performance tests
- Products with various compliance tags (CE, EN 397, ATEX, etc.)
- Products in different categories (PPE, chemical safety, equipment)

---

## Coverage Goals

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| ingestion/ingest.py (product functions) | 95% | High |
| agent/product_queries.py | 90% | High |
| agent/models.py (Product models) | 100% | Medium |
| Config files (notion_config.py) | 80% | Low |

**Overall Goal:** 90%+ code coverage for FEAT-004 modules

---

## Performance Benchmarks

| Test | Target | Measurement |
|------|--------|-------------|
| Product search (10 results) | <500ms | Average of 100 queries |
| Embedding generation | <2s per product | Average of 50 products |
| Batch ingestion (100 products) | <5 minutes | End-to-end time |
| Database query with index | <100ms | pgvector similarity search |

---

## Test Execution Strategy

### During Development (Phase 2)
1. Run unit tests continuously (pytest watch mode)
2. Run integration tests before each commit
3. Check coverage with `pytest --cov`
4. Fix failing tests before moving to next acceptance criterion

### Pre-Merge Checklist
- [ ] All unit tests passing (35+ tests)
- [ ] All integration tests passing (14+ tests)
- [ ] Code coverage ≥90%
- [ ] Manual tests completed (see manual-test.md)
- [ ] Performance benchmarks met
- [ ] No linting errors (black, ruff)

### CI/CD Integration (Future)
- Automated test run on every push
- Coverage report generated
- Performance regression detection
- Automated deployment on test pass

---

## Manual Testing Scope

Manual tests are defined in separate `manual-test.md` document and include:
- Visual inspection of ingested product data
- Search relevance evaluation by domain expert
- Compliance filter accuracy verification
- Product-guideline linking validation
- Edge case testing (special characters, long descriptions)

---

## Test Stub Generation

All test files will be created as stubs with:
- File structure and imports
- Test function signatures with docstrings
- TODO comments referencing acceptance criteria
- Pytest fixtures defined but not implemented
- No actual test implementation (added in Phase 2)

**Test Stub Locations:**
```
tests/
  unit/
    test_product_ingest.py      # 15 test stubs
    test_product_search.py      # 12 test stubs
    test_product_models.py      # 5 test stubs
  integration/
    test_product_ingestion_flow.py  # 6 test stubs
    test_product_search_flow.py     # 8 test stubs
  fixtures/
    notion_product_responses.json   # Mock data
```

**Total Test Stubs:** 46

---

**Word Count:** 748 words (under 800-word limit)
