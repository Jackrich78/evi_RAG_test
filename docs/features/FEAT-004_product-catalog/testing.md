# Testing Strategy: Product Catalog with Interventie Wijzer Integration

**Feature ID:** FEAT-004
**Created:** 2025-11-04
**Test Coverage Goal:** ≥80% for ingestion pipeline

## Test Strategy Overview

This feature requires comprehensive testing across portal scraping, CSV parsing, fuzzy matching, embedding generation, hybrid search, and agent integration. We follow Test-Driven Development (TDD) principles: write test stubs first (Phase 1 - Planning), then implement code to make tests pass (Phase 2 - Build). Testing focuses on data quality, search relevance, and performance.

**Testing Levels:**
- ✅ Unit Tests: Individual functions (scraping, CSV parsing, enrichment, database ops, search tool)
- ✅ Integration Tests: End-to-end flows (portal → CSV → DB → search → agent)
- ✅ Manual Tests: 10 Dutch query scenarios for relevance validation

**Philosophy:** Test data quality first (URLs, embeddings, fuzzy matching), then search quality (hybrid similarity, latency), then agent integration (tool calling, formatting).

## Unit Tests

### Test Files to Create

#### `tests/unit/test_product_ingest.py`

**Purpose:** Test ingestion pipeline components in isolation (mocked dependencies)

**Test Stubs:**

1. **Test: Portal Scraping - Product Listing Fetch (AC-004-001)**
   - **Given:** Mocked Crawl4AI returns HTML with product links
   - **When:** `scrape_all_products()` is called
   - **Then:** Product URLs are extracted (55-65 count), header/footer links ignored
   - **Mocks:** AsyncWebCrawler.arun() returns fixture HTML

2. **Test: Portal Scraping - Product URLs Extraction (AC-004-001)**
   - **Given:** Mocked product listing HTML contains <main> with product links
   - **When:** Product URLs are extracted using BeautifulSoup selectors
   - **Then:** Only portal.evi360.nl/products/* URLs returned, navigation links excluded
   - **Mocks:** BeautifulSoup with fixture HTML

3. **Test: Portal Scraping - Individual Product Click (AC-004-001)**
   - **Given:** Mocked Crawl4AI clicks into product page
   - **When:** `extract_product_details()` parses product HTML
   - **Then:** name, description, price, category extracted correctly
   - **Mocks:** AsyncWebCrawler.arun() returns single product HTML

4. **Test: Portal Scraping - Missing Price Field Handling (AC-004-103)**
   - **Given:** Product HTML lacks price element
   - **When:** `extract_product_details()` is called
   - **Then:** Product returned with price=None, other fields intact
   - **Mocks:** Product HTML fixture without .product-price element

5. **Test: Portal Scraping - Error Handling for Failed Requests (AC-004-101)**
   - **Given:** Crawl4AI raises timeout error for product page
   - **When:** Scraping is attempted with retry logic
   - **Then:** Error logged, product skipped, scraping continues
   - **Mocks:** AsyncWebCrawler.arun() raises asyncio.TimeoutError

6. **Test: CSV Parsing - Problem-Product Mapping Extraction (AC-004-003)**
   - **Given:** Intervention_matrix.csv with 33 rows
   - **When:** `parse_interventie_csv()` is called
   - **Then:** 33 product-problem mappings extracted, problems aggregated by product name
   - **Mocks:** CSV file with sample data

7. **Test: CSV Parsing - Many-to-One Problem Aggregation (AC-004-004)**
   - **Given:** CSV has 3 rows with same "Soort interventie" value
   - **When:** Problems are aggregated
   - **Then:** Single product with 3 problems in array
   - **Mocks:** CSV fixture with duplicate product names

8. **Test: Fuzzy Matching - High Similarity Match (≥0.9) (AC-004-003)**
   - **Given:** CSV product "Herstelcoaching" and portal product "Herstelcoaching (6-9 maanden)"
   - **When:** `fuzzy_match_products(threshold=0.9)` is called
   - **Then:** Products matched, problem_mappings enriched
   - **Mocks:** Mocked portal and CSV products

9. **Test: Fuzzy Matching - Low Similarity Rejection (<0.9) (AC-004-102)**
   - **Given:** CSV product "BMW Gesprek" and portal product "Psychiatric Support"
   - **When:** Fuzzy matching is attempted
   - **Then:** No match, product logged to unmatched list
   - **Mocks:** Dissimilar product names

10. **Test: Fuzzy Matching - Unmatched Products Logged (AC-004-102)**
    - **Given:** 5 CSV products cannot be matched (similarity <0.9)
    - **When:** Fuzzy matching completes
    - **Then:** Warning logged: "⚠️  Unmatched CSV products (5): [...]"
    - **Mocks:** CSV with mismatched names

11. **Test: Product Enrichment - Metadata with Problem Mappings (AC-004-004)**
    - **Given:** Portal product matched to CSV product with 2 problems
    - **When:** Product is enriched
    - **Then:** metadata contains {"problem_mappings": ["Problem 1", "Problem 2"], "csv_category": "Category"}
    - **Mocks:** Matched product pair

12. **Test: Product Enrichment - Embedding Generation with Problems (AC-004-005)**
    - **Given:** Product with description and 2 problem mappings
    - **When:** Embedding text is generated
    - **Then:** Text = "description\n\nProblem 1\nProblem 2"
    - **Mocks:** Product dict with metadata

13. **Test: Product Enrichment - No CSV Match Fallback (AC-004-102)**
    - **Given:** Portal product with no CSV match
    - **When:** Product is enriched
    - **Then:** Embedding generated from description only, metadata.problem_mappings = []
    - **Mocks:** Unmatched portal product

14. **Test: Database Operations - Insert New Product (AC-004-001)**
    - **Given:** Product dict with all fields
    - **When:** `insert_product()` is called
    - **Then:** Product inserted into database, UUID returned
    - **Mocks:** asyncpg connection

15. **Test: Database Operations - Update Existing Product (AC-004-203)**
    - **Given:** Product with same name+URL exists in database
    - **When:** `upsert_product()` is called
    - **Then:** Existing product updated, not duplicated
    - **Mocks:** asyncpg connection with existing row

16. **Test: Database Operations - Handle Duplicate Names (AC-004-203)**
    - **Given:** Two products with same name but different URLs
    - **When:** Both inserted
    - **Then:** Two separate products created (URL distinguishes)
    - **Mocks:** asyncpg connection

17. **Test: Hybrid Search Tool - Query Embedding Generation (AC-004-007)**
    - **Given:** Dutch query "burn-out begeleiding"
    - **When:** `search_products_tool()` generates embedding
    - **Then:** 1536-dim embedding vector returned
    - **Mocks:** OpenAI API client

18. **Test: Hybrid Search Tool - Result Formatting for LLM (AC-004-008)**
    - **Given:** SQL function returns 3 products with long descriptions
    - **When:** `search_products_tool()` formats results
    - **Then:** Descriptions truncated to 200 chars, similarity rounded to 2 decimals
    - **Mocks:** Database query results

---

### Unit Test Coverage Goals

- **Functions:** All public functions tested (scrape_all_products, parse_interventie_csv, fuzzy_match_products, generate_embedding, search_products_tool)
- **Branches:** All conditional branches covered (price present/missing, CSV match success/fail, embedding with/without problems)
- **Edge Cases:** Boundary conditions tested (empty portal response, fuzzy match at 0.89 vs 0.90, NULL price)
- **Error Handling:** All error paths tested (network timeout, CSV parse error, missing required fields)

**Target Coverage:** ≥80% line coverage for ingestion pipeline

## Integration Tests

### Test Files to Create

#### `tests/integration/test_product_ingestion_flow.py`

**Purpose:** Test end-to-end flows with real database and minimal mocking

**Test Stubs:**

1. **Test: End-to-End Ingestion Flow (AC-004-001 through AC-004-005)**
   - **Components:** Portal scraper → CSV parser → fuzzy matcher → embedder → database
   - **Setup:** Clean test database, mocked portal HTML (5 products), real CSV file
   - **Scenario:** Run full ingestion pipeline (`ingest_products.py`)
   - **Assertions:**
     - 5 products inserted into database
     - ≥4 products have problem_mappings (≥80% match rate)
     - All 5 products have embeddings (vector length 1536)
     - All 5 products have canonical URLs

2. **Test: Agent Calls search_products() Tool (AC-004-007, AC-004-105)**
   - **Components:** Specialist agent → search_products_tool → database
   - **Setup:** Database with 10 test products (including burn-out products)
   - **Scenario:** Agent receives query "Welke interventies voor burn-out?"
   - **Assertions:**
     - Agent tool_calls includes "search_products"
     - Tool returns 3-5 products
     - Response includes product names and URLs

3. **Test: Agent Formats Products in Dutch Markdown (AC-004-008)**
   - **Components:** Specialist agent → response formatter
   - **Setup:** Agent with search_products() tool, query with known results
   - **Scenario:** Query "burn-out", verify markdown formatting
   - **Assertions:**
     - Response contains bold product names (**Herstelcoaching**)
     - Response contains URLs (https://portal.evi360.nl/...)
     - Response contains pricing if available (€2.500 - €3.500)
     - Dutch language used

4. **Test: Product URL Validation (AC-004-002)**
   - **Components:** Database → HTTP client
   - **Setup:** Database with 10 test products
   - **Scenario:** Fetch all product URLs, make HEAD requests
   - **Assertions:**
     - ≥95% of URLs return HTTP 200 or 30X
     - Broken URLs logged for investigation
     - All URLs have portal.evi360.nl domain

5. **Test: Search Latency Performance (AC-004-009)**
   - **Components:** Database → hybrid search function
   - **Setup:** Database with 60 test products, IVFFLAT index built
   - **Scenario:** Run 100 search queries, measure latency
   - **Assertions:**
     - 95th percentile (p95) latency <500ms
     - 50th percentile (p50) latency <200ms
     - All queries complete without errors

6. **Test: Re-scraping with --refresh Flag (AC-004-203)**
   - **Components:** CLI → scraper → database upsert
   - **Setup:** Database with 5 existing products, mocked portal with 7 products (5 updated + 2 new)
   - **Scenario:** Run `python3 -m ingestion.ingest_products --refresh`
   - **Assertions:**
     - 5 existing products updated (timestamps changed)
     - 2 new products inserted
     - No duplicate products created
     - Re-scraping completes in <10 minutes

---

### Integration Test Scope

**Internal Integrations:**
- Scraper → CSV parser: Portal products enriched with CSV problem mappings
- Embedder → Database: Embeddings inserted correctly into vector column
- Database → Agent: Hybrid search returns products to agent tool
- Agent → Response: Products formatted in Dutch markdown

**External Integrations:**
- Portal.evi360.nl: Web scraping (mocked in tests, validated in spike)
- OpenAI API: Embedding generation (mocked with fixture embeddings)
- PostgreSQL: Vector similarity search (real database in test container)

**Mock Strategy:**
- **Fully Mocked:** Portal HTTP requests (BeautifulSoup fixtures), OpenAI API (fixed embeddings)
- **Partially Mocked:** Agent (real tool calls, mocked LLM response)
- **Real:** PostgreSQL database (test container with pgvector), CSV file (real Intervention_matrix.csv)

## Manual Testing

### Manual Test Scenarios

*See `manual-test.md` for detailed step-by-step instructions.*

**Quick Reference:**
1. **Burn-out begeleiding**: Verify Herstelcoaching, Multidisciplinaire burnout aanpak, Psychologische ondersteuning
2. **Fysieke klachten door tilwerk**: Verify Bedrijfsfysiotherapie, Werkplekonderzoek, Vroegconsult arbeidsfysiotherapeut
3. **Conflict met leidinggevende**: Verify Mediation, Inzet mediator
4. **Lange termijn verzuim**: Verify Re-integratietraject, Arbeidsdeskundig onderzoek
5. **Werkdruk problemen**: Verify Coaching, Werkdrukanalyse
6. **Zwangerschap en werk**: Verify Vroegconsult arbeidsdeskundige, Arbeidsvoorwaarden advies
7. **Psychische klachten**: Verify Vroegconsult arbeidspsycholoog, Psychologische ondersteuning, Bedrijfsmaatschappelijk werk
8. **Leefstijl coaching**: Verify Leefstijlprogramma's, Inzet leefstijlcoach, Gewichtsconsulent
9. **Re-integratie traject**: Verify Re-integratietraject 2e/3e spoor, Loopbaanbegeleiding
10. **Bedrijfsmaatschappelijk werk**: Verify Inzet BMW, Emotionele ondersteuning

**Manual Test Focus:**
- **Search Relevance:** ≥7/10 queries return products matching the problem domain
- **URL Accuracy:** All product URLs clickable and open correct product page
- **Dutch Formatting:** Products formatted in natural Dutch markdown with pricing
- **Agent Behavior:** Agent calls search_products() when contextually appropriate

**Target:** ≥70% relevance (7/10 queries return relevant products)

## Test Data Requirements

### Fixtures & Seed Data

**Unit Test Fixtures:**
```python
# tests/fixtures/portal_html.py
PRODUCT_LISTING_HTML = """
<html>
  <main>
    <a href="/products/15">Herstelcoaching</a>
    <a href="/products/27">Multidisciplinaire Burnout Aanpak</a>
    <!-- 58 more product links -->
  </main>
  <footer><!-- ignore --></footer>
</html>
"""

PRODUCT_DETAIL_HTML = """
<html>
  <h1 class="product-title">Herstelcoaching</h1>
  <div class="product-description">6-9 maanden traject...</div>
  <div class="product-price">€2.500 - €3.500</div>
  <div class="product-category">Coaching</div>
</html>
"""
```

**Integration Test Data:**
- **Database seeding script:** `tests/fixtures/seed_products.sql` (10 sample products with embeddings)
- **CSV data:** Real `Intervention_matrix.csv` (33 rows)
- **Mock embeddings:** Fixed 1536-dim vectors (test determinism)

**E2E Test Data:**
- **Test accounts:** Not required (no authentication)
- **Sample queries:** 10 Dutch test queries (defined above)
- **Cleanup:** Truncate products table after each test

## Mocking Strategy

### What to Mock

**Always Mock:**
- Portal HTTP requests (avoid hitting live site in CI)
- OpenAI API calls (avoid costs, ensure determinism)
- Slow operations (Crawl4AI async calls >1s)

**Sometimes Mock:**
- Database (mock for unit tests, real for integration tests)
- Agent LLM calls (mock for formatting tests, real for end-to-end tests)

**Never Mock:**
- Core feature logic (fuzzy matching, embedding concatenation, hybrid search formula)
- CSV parsing (real file read)
- Product data models (Pydantic validation)

### Mocking Approach

**Framework:** pytest with pytest-asyncio, pytest-mock

**Mock Examples:**
```python
# Mock Crawl4AI scraping
@pytest.fixture
def mock_crawler(mocker):
    mock = mocker.patch("crawl4ai.AsyncWebCrawler.arun")
    mock.return_value = MagicMock(html=PRODUCT_LISTING_HTML)
    return mock

# Mock OpenAI embeddings
@pytest.fixture
def mock_openai_embeddings(mocker):
    mock = mocker.patch("openai.embeddings.create")
    mock.return_value.data[0].embedding = [0.1] * 1536  # Fixed embedding
    return mock

# Mock database connection (unit tests only)
@pytest.fixture
def mock_db_pool(mocker):
    pool = mocker.AsyncMock()
    pool.acquire.return_value.__aenter__.return_value.fetch.return_value = []
    return pool
```

## Test Execution

### Running Tests Locally

**Unit Tests:**
```bash
# Activate virtual environment
source venv/bin/activate  # or venv_linux/bin/activate

# Run all unit tests
pytest tests/unit/test_product_ingest.py -v

# Run with coverage
pytest tests/unit/test_product_ingest.py --cov=ingestion --cov-report=html
```

**Integration Tests:**
```bash
# Start test database
docker-compose up -d

# Run integration tests (real database)
pytest tests/integration/test_product_ingestion_flow.py -v

# Run with performance profiling
pytest tests/integration/ --durations=10
```

**All Tests:**
```bash
# Run entire FEAT-004 test suite
pytest tests/unit/test_product_ingest.py tests/integration/test_product_ingestion_flow.py -v
```

### CI/CD Integration (Phase 2)

**Pipeline Stages:**
1. Unit tests (run on every commit) - ~2 minutes
2. Integration tests (run on every commit) - ~5 minutes
3. Manual test reminder (comment on PR) - automated
4. Coverage report generation (upload to Codecov)
5. Test result artifacts (JUnit XML)

**Failure Handling:**
- Failing tests block merge
- Coverage drops below 80% trigger warning (not block)
- Flaky test detection: test retried 3 times before failing

## Coverage Goals

### Coverage Targets

| Test Level | Target Coverage | Minimum Acceptable |
|------------|----------------|-------------------|
| Unit | ≥80% | 70% |
| Integration | ≥60% | 50% |
| E2E | N/A (workflow-based) | 10 workflows |

### Critical Paths

**Must Have 100% Coverage:**
- `fuzzy_match_products()` (data quality critical)
- `search_products_tool()` (agent integration)
- Hybrid search SQL function (search relevance)

**Can Have Lower Coverage:**
- HTML parsing selectors (brittle, spike-validated)
- Error logging functions (non-critical)
- CLI argument parsing (simple, manually tested)

## Performance Testing

**Requirement:** From AC-004-009 (search latency <500ms p95)

**Test Approach:**
- **Tool:** pytest-benchmark for latency measurement
- **Scenarios:**
  1. Hybrid search with 60 products: Target <200ms p50, <500ms p95
  2. Concurrent searches (10 queries): Target no degradation
  3. Database index usage: EXPLAIN ANALYZE confirms IVFFLAT index used

**Acceptance:**
- <500ms response time for 95% of queries (p95)
- <200ms response time for 50% of queries (p50)
- No out-of-memory errors under load

## Security Testing

**Requirement:** Ensure safe handling of portal HTML and CSV data

### Security Test Scenarios

1. **Input Validation:** Verify product names sanitized (no XSS in stored data)
2. **URL Validation:** Confirm all URLs are portal.evi360.nl domain (no open redirect)
3. **CSV Injection:** Test CSV with formula injection attempts (=cmd|...)
4. **SQL Injection:** Verify parameterized queries (no raw SQL concatenation)

**Tools:**
- Manual code review for SQL parameterization
- Bandit (Python security linter)

## Test Stub Generation (Phase 1)

*These test files will be created with TODO stubs during planning:*

```
tests/
├── unit/
│   └── test_product_ingest.py (18 unit test stubs)
└── integration/
    └── test_product_ingestion_flow.py (6 integration test stubs)
```

**Total Test Stubs:** 24 test functions with TODO comments

**Test Stub Format:**
```python
@pytest.mark.asyncio
async def test_portal_scraping_product_listing_fetch():
    """
    Test: Portal Scraping - Product Listing Fetch (AC-004-001)

    Given: Mocked Crawl4AI returns HTML with product links
    When: scrape_all_products() is called
    Then: Product URLs are extracted (55-65 count), header/footer links ignored
    """
    # TODO: Implement test
    # 1. Mock AsyncWebCrawler.arun() to return fixture HTML
    # 2. Call scrape_all_products()
    # 3. Assert 55-65 product URLs returned
    # 4. Assert no header/footer links in results
    pytest.skip("Test stub - implement in Phase 2")
```

## Out of Scope

*What we're explicitly NOT testing in this phase:*

- **Product images or multimedia** (text-only feature)
- **User authentication** (portal scraping doesn't require auth)
- **Notion database integration** (descoped, using portal scraping)
- **LLM-based query expansion** (deferred to FEAT-012)
- **Product-guideline linking** (deferred to FEAT-012)

---

**Next Steps:**
1. Planner will generate test stub files based on this strategy
2. Phase 2: Implementer will make stubs functional
3. Phase 2: Tester will execute and validate
