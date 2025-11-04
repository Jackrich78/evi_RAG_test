# Implementation Guide: FEAT-004 - Product Catalog with Interventie Wijzer Integration

**Feature ID:** FEAT-004
**Last Updated:** 2025-11-04
**Estimated Effort:** 14 hours (6 phases)

---

## Overview

This guide provides a quick-start roadmap for implementing product catalog ingestion with portal scraping and CSV enrichment. Follow the 6 phases sequentially, using TDD (Test-Driven Development) throughout.

**What You'll Build:**
1. Portal scraper using Crawl4AI (~60 products from portal.evi360.nl)
2. CSV parser for Intervention_matrix.csv (33 problem mappings)
3. Fuzzy matching to enrich products with problem_mappings
4. Hybrid search tool for agent integration
5. Agent integration with search_products() tool

**Prerequisites:**
- Read [prd.md](./prd.md) and [architecture.md](./architecture.md) first
- PostgreSQL container running with products table schema
- OpenAI API key configured in `.env`
- Python 3.11+ with dependencies: `crawl4ai`, `fuzzywuzzy`, `asyncpg`

---

## File Structure Overview

### New Files to Create

```
ingestion/
├── ingest_products.py          # Main CLI script (Phase 1-4)
├── scrape_portal_products.py   # Portal scraper with Crawl4AI (Phase 1)
├── parse_interventie_csv.py    # CSV parser (Phase 2)
├── fuzzy_matcher.py            # Fuzzy matching logic (Phase 2)
└── product_embedder.py         # Embedding generation (Phase 3)

agent/
└── tools.py                    # Add search_products() function (Phase 5)

agent/
└── specialist_agent.py         # Update system prompt (Phase 5)
```

### Existing Files to Modify

```
agent/tools.py                  # Add search_products() tool
agent/specialist_agent.py       # Remove "Geen producten aanbevelen" restriction
```

### Data Files

```
docs/features/FEAT-004_product-catalog/
└── Intervention_matrix.csv     # 33 problem-to-product mappings (already exists)
```

---

## Phase 1: Portal Scraping (3 hours)

**Goal:** Scrape ~60 products from portal.evi360.nl with Crawl4AI

### Step 1.1: Install Crawl4AI

```bash
source venv_linux/bin/activate
pip3 install crawl4ai
```

### Step 1.2: Create Portal Scraper Module

**File:** `ingestion/scrape_portal_products.py` (NEW)

**Key Functions:**
- `async def scrape_all_products() -> List[Dict]` - Main entry point
- `async def scrape_product_listing() -> List[str]` - Get product URLs
- `async def scrape_product_page(url: str) -> Dict` - Extract product details

**Implementation Tips:**
- Use `AsyncWebCrawler` from crawl4ai
- Parse with BeautifulSoup: `soup.select("main")` to ignore header/footer
- Extract: name, description, price, url (canonical), category
- Handle missing fields gracefully (price may be None)
- Add retry logic for timeout errors (AC-004-101)

**Test First (TDD):** Run `pytest tests/unit/test_product_ingest.py::test_portal_scraping_product_listing_fetch -v` to see failure, then implement.

### Step 1.3: Create Main Ingestion Script

**File:** `ingestion/ingest_products.py` (NEW)

**Structure:**
```python
import asyncio
from scrape_portal_products import scrape_all_products
from parse_interventie_csv import parse_interventie_csv
from fuzzy_matcher import fuzzy_match_products
from product_embedder import generate_embeddings
from db_utils import insert_products

async def main():
    print("🔍 Step 1/5: Scraping portal.evi360.nl...")
    products = await scrape_all_products()
    print(f"✅ Scraped {len(products)} products")

    # Phase 2-4 steps will be added here

if __name__ == "__main__":
    asyncio.run(main())
```

**CLI Usage:**
```bash
python3 -m ingestion.ingest_products           # Normal run
python3 -m ingestion.ingest_products --refresh # Re-scrape all
```

**Validation:** Scrape 55-65 products (AC-004-001)

---

## Phase 2: CSV Parsing & Fuzzy Matching (2 hours)

**Goal:** Parse Intervention_matrix.csv and enrich products with problem mappings

### Step 2.1: Create CSV Parser

**File:** `ingestion/parse_interventie_csv.py` (NEW)

**Key Function:**
```python
def parse_interventie_csv(csv_path: str) -> List[Dict]:
    """
    Parse Intervention_matrix.csv and aggregate problems by product.

    Returns: List of dicts with:
        - product_name: str (from "Soort interventie")
        - problems: List[str] (aggregated from "Probleem")
        - category: str (from "Category")
    """
```

**Implementation Tips:**
- Use pandas or csv module
- Aggregate many-to-one: same product_name → multiple problems in array
- Expected: 33 CSV rows → ≤33 unique products (due to aggregation)

**Test First:** Run `pytest tests/unit/test_product_ingest.py::test_csv_parsing_problem_product_mapping_extraction -v`

### Step 2.2: Create Fuzzy Matcher

**File:** `ingestion/fuzzy_matcher.py` (NEW)

**Key Function:**
```python
from fuzzywuzzy import fuzz

def fuzzy_match_products(
    csv_products: List[Dict],
    portal_products: List[Dict],
    threshold: float = 0.9
) -> Tuple[List[Dict], List[str]]:
    """
    Match CSV products to portal products using fuzzy string matching.

    Returns:
        - enriched_products: Portal products with problem_mappings added
        - unmatched: List of CSV product names that couldn't be matched
    """
```

**Implementation Tips:**
- Use `fuzz.ratio()` for similarity scoring (0-100 scale)
- Normalize names: lowercase, remove punctuation/parentheses
- Threshold ≥90% for match acceptance
- Store in `product["metadata"]["problem_mappings"]` as array
- Store in `product["metadata"]["csv_category"]` as string
- Log unmatched CSV products (AC-004-102)

**Expected Match Rate:** ≥80% (≥25 of 33 CSV products matched)

**Test First:** Run `pytest tests/unit/test_product_ingest.py::test_fuzzy_matching_high_similarity_match -v`

### Step 2.3: Integrate into Main Script

Update `ingestion/ingest_products.py`:
```python
print("📊 Step 2/5: Parsing Intervention_matrix.csv...")
csv_path = "docs/features/FEAT-004_product-catalog/Intervention_matrix.csv"
csv_products = parse_interventie_csv(csv_path)

print("🔗 Step 3/5: Fuzzy matching products to CSV...")
enriched_products, unmatched = fuzzy_match_products(csv_products, products)
print(f"✅ Matched {len(enriched_products)} products")
if unmatched:
    print(f"⚠️  Unmatched CSV products ({len(unmatched)}): {unmatched}")
```

---

## Phase 3: Embedding Generation (2 hours)

**Goal:** Generate embeddings (description + problems concatenated)

### Step 3.1: Create Product Embedder

**File:** `ingestion/product_embedder.py` (NEW)

**Key Functions:**
```python
def generate_embedding_text(product: Dict) -> str:
    """
    Generate embedding text: description + problems.

    Format:
        "{description}\\n\\n{problem1}\\n{problem2}\\n..."
    """

async def generate_embeddings(products: List[Dict]) -> List[Dict]:
    """
    Generate OpenAI embeddings for all products.
    Uses text-embedding-3-small (1536 dimensions).
    """
```

**Implementation Tips:**
- Concatenate description + problems (double newline separator)
- Use existing `embedder.py` functions if available
- Handle products without problem_mappings (description-only)
- Batch API calls (e.g., 10 products per request)

**Test First:** Run `pytest tests/unit/test_product_ingest.py::test_product_enrichment_embedding_generation_with_problems -v`

### Step 3.2: Integrate into Main Script

```python
print("🧮 Step 4/5: Generating embeddings...")
products_with_embeddings = await generate_embeddings(enriched_products)
print(f"✅ Generated {len(products_with_embeddings)} embeddings")
```

**Validation:** 100% embedding coverage (AC-004-005)

---

## Phase 4: Database Operations (3 hours)

**Goal:** Insert products into database with hybrid search support

### Step 4.1: Add Database Functions

**Option A:** Reuse existing `agent/db_utils.py` functions
**Option B:** Create new `ingestion/product_db.py` module

**Key Functions:**
```python
async def insert_product(conn, product: Dict) -> str:
    """Insert product into database, return UUID."""

async def upsert_product(conn, product: Dict) -> str:
    """
    Insert or update product (by name + url).
    For --refresh flag support.
    """
```

**SQL Insert:**
```sql
INSERT INTO products (name, description, url, price, category, embedding, metadata)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT (url) DO UPDATE SET
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    embedding = EXCLUDED.embedding,
    updated_at = NOW()
RETURNING id;
```

**Test First:** Run `pytest tests/unit/test_product_ingest.py::test_database_operations_insert_new_product -v`

### Step 4.2: Verify Hybrid Search SQL Function

**Check Existing:** Hybrid search function should already exist from FEAT-002 architecture. Verify:

```sql
-- Check if function exists
SELECT routine_name, routine_definition
FROM information_schema.routines
WHERE routine_name = 'hybrid_search_products';
```

**If Missing:** Create hybrid search function (see `sql/schema.sql` or `sql/evi_schema_additions.sql` for reference).

### Step 4.3: Integrate into Main Script

```python
print("💾 Step 5/5: Inserting products into database...")
async with asyncpg.create_pool(DATABASE_URL) as pool:
    async with pool.acquire() as conn:
        for product in products_with_embeddings:
            await upsert_product(conn, product)
print(f"✅ Inserted {len(products_with_embeddings)} products")
```

**Validation:** Run `SELECT COUNT(*) FROM products` → expect 55-65 rows

---

## Phase 5: Agent Integration (2 hours)

**Goal:** Add search_products() tool and update agent prompt

### Step 5.1: Add search_products() Tool

**File:** `agent/tools.py` (MODIFY)

**Add Function:**
```python
async def search_products(
    ctx: RunContext[SpecialistDeps],
    query: str,
    limit: int = 5
) -> List[Dict]:
    """
    Search product catalog using hybrid search.

    Args:
        query: Dutch search query (e.g., "burn-out begeleiding")
        limit: Max products to return (default: 5)

    Returns:
        List of products with name, description, url, price, similarity
    """
    # Generate embedding for query
    # Call hybrid_search_products() SQL function
    # Return top results with truncated descriptions (≤200 chars)
```

**Implementation Tips:**
- Reuse embedding generation from `embedder.py`
- Truncate descriptions to 200 chars for LLM context (AC-004-008)
- Round similarity scores to 2 decimals
- Include URL, price (if available), category in response

**Test First:** Run `pytest tests/unit/test_product_ingest.py::test_hybrid_search_tool_result_formatting -v`

### Step 5.2: Update Agent Prompt

**File:** `agent/specialist_agent.py` (MODIFY)

**Changes:**
1. Remove restriction: Delete lines containing `"Geen producten aanbevelen"` (lines 44, 74)
2. Add tool registration: `tools=[search_guidelines, search_products]`
3. Update system prompt to include product recommendation protocol:

```python
SPECIALIST_SYSTEM_PROMPT = """Je bent een deskundige arbeidsveiligheidsadviseur voor EVI 360.

**Beschikbare tools:**
1. search_guidelines(query) - Zoek in richtlijnen (NVAB, UWV, STECR)
2. search_products(query) - Zoek EVI 360 interventieproducten

**Wanneer producten aanbevelen:**
- Gebruik search_products() wanneer de vraag gaat over interventies of begeleiding
- Voorbeelden: "burn-out begeleiding", "re-integratie", "coaching"

**Productpresentatie:**
- Presenteer producten in Nederlandse markdown met:
  - **Productnaam** (vetgedrukt)
  - URL: [Productpagina](https://portal.evi360.nl/products/...)
  - Prijs (indien beschikbaar)
- Geef 2-3 producten, niet meer dan 5

[... rest of prompt ...]
"""
```

**Test:** Run `pytest tests/integration/test_product_ingestion_flow.py::test_agent_calls_search_products_tool -v`

---

## Phase 6: Testing & Validation (2 hours)

**Goal:** Validate all acceptance criteria and manual test scenarios

### Step 6.1: Run Automated Tests

```bash
# Unit tests (18 tests)
pytest tests/unit/test_product_ingest.py -v

# Integration tests (6 tests)
pytest tests/integration/test_product_ingestion_flow.py -v

# Expected: 24/24 passing
```

### Step 6.2: Manual Testing

Follow [manual-test.md](./manual-test.md) scenarios:

1. **Test Scenario 1: Burn-out Query**
   - Query: "Werknemer heeft burn-out klachten, 6 maanden verzuim"
   - Expected: 2-3 products (Herstelcoaching, Multidisciplinaire Burnout Aanpak)
   - Verify: Working URLs, Dutch markdown formatting, pricing

2. **Test Scenario 2: Physical Complaints**
   - Query: "Medewerker heeft fysieke klachten, nek- en rugpijn"
   - Expected: 2-3 products related to physical health

... (Continue with all 10 scenarios)

**Pass Criteria:** ≥7/10 queries return relevant products (AC-004-011)

### Step 6.3: Validate Acceptance Criteria

Check [acceptance.md](./acceptance.md) for all 25 criteria:

**Core Functional (13 criteria):**
- ✅ AC-004-001: ~60 products scraped
- ✅ AC-004-002: 100% canonical URLs
- ✅ AC-004-003: ≥80% CSV match rate
- ✅ AC-004-004: ≥25 products with problem_mappings
- ✅ AC-004-005: 100% embeddings
- ... (continue through AC-004-013)

**Edge Cases (5 criteria):**
- ✅ AC-004-101: Portal inaccessible handling
- ... (continue through AC-004-105)

**Non-Functional (3 criteria):**
- ✅ AC-004-201: <500ms search latency (p95)
- ... (continue through AC-004-203)

### Step 6.4: Performance Validation

```bash
# Run performance test
pytest tests/integration/test_product_ingestion_flow.py::test_search_latency_performance -v

# Expected: p95 < 500ms, p50 < 200ms
```

---

## Troubleshooting

### Portal Scraping Issues

**Problem:** Crawl4AI returns empty HTML
**Solution:** Check if portal requires authentication or has rate limiting. Add delays between requests.

**Problem:** Product URLs extracted include header/footer links
**Solution:** Use `soup.select("main")` to target only main content area.

### Fuzzy Matching Issues

**Problem:** Low match rate (<80%)
**Solution:**
- Normalize strings: lowercase, remove punctuation
- Try `fuzz.partial_ratio()` instead of `fuzz.ratio()`
- Lower threshold to 0.85 (document deviation in AC)

### Database Issues

**Problem:** Duplicate products created
**Solution:** Ensure upsert logic uses `ON CONFLICT (url)` clause

**Problem:** Slow hybrid search
**Solution:**
- Build IVFFLAT index: `CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops)`
- Check query plan: `EXPLAIN ANALYZE SELECT * FROM hybrid_search_products(...)`

---

## Validation Checklist

Before marking FEAT-004 complete:

- [ ] 55-65 products in database (`SELECT COUNT(*) FROM products`)
- [ ] ≥80% CSV match rate (check logs for unmatched count)
- [ ] 100% embeddings (`SELECT COUNT(*) FROM products WHERE embedding IS NOT NULL`)
- [ ] 24/24 automated tests passing
- [ ] ≥7/10 manual test scenarios passing
- [ ] Agent successfully calls search_products() tool
- [ ] Product URLs clickable in agent response
- [ ] Dutch markdown formatting correct
- [ ] Search latency <500ms (p95)
- [ ] Documentation updated (docs/README.md, CHANGELOG.md)

---

## Next Steps After FEAT-004

Once FEAT-004 is complete and validated:

1. **FEAT-012: Two-Stage Search Protocol** (blocked by FEAT-004)
   - LLM-based ranking with weighted scoring
   - Product-guideline linking
   - Query expansion

2. **Performance Optimization**
   - Build IVFFLAT index for faster vector search
   - Implement caching for frequently searched products

3. **Data Refresh Automation**
   - Schedule weekly re-scraping with `--refresh` flag
   - Monitor for new products or price changes

---

**Last Updated:** 2025-11-04
**Estimated Total Effort:** 14 hours
**Status:** Ready for Implementation
