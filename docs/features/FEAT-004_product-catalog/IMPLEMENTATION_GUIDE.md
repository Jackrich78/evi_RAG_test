# FEAT-004 Implementation Guide - Product Catalog

**Feature ID:** FEAT-004
**Created:** 2025-11-05
**Validated:** 2025-11-04 (Spike validation complete)
**Implementation Strategy:** 4-Phase Incremental Database Writes

---

## Quick Start for Implementation Agent

**YOU ARE HERE:** All planning complete, all spikes validated, zero contradictions. Ready to implement.

**What You Need to Know:**
1. **All documentation is updated** with validated numbers (76 products, 23 CSV, 0.85 threshold)
2. **All spike findings incorporated** - selectors tested, fuzzy matching validated
3. **Manual mapping files created** - ready to use in Phase 2
4. **4-phase plan** with incremental database writes (Portal → CSV → Embeddings → Agent)
5. **Test stubs exist** - fill in as you implement

**What You Should Do:**
1. Read this guide completely (especially Phase 0 setup)
2. Start with Phase 0 to verify environment
3. Implement Phases 1-4 sequentially
4. Run tests after each phase
5. Mark todo items complete as you go

**Do NOT re-plan or re-validate** - everything is ready to code!

---

## Overview

This guide provides a clear, step-by-step implementation plan for FEAT-004 Product Catalog. All spike validation is complete, selectors are tested, and fuzzy matching strategy is validated. The implementation is broken into 4 phases with incremental database writes.

**Key Validated Numbers:**
- **76 portal products** (not ~60)
- **23 unique CSV products** from 26 rows (not 33)
- **0.85 fuzzy threshold** with normalization (not 0.9)
- **83% total match rate** (9 automated + 10 manual = 19/23)
- **4 unresolved products** for stakeholder review

**Critical Files Ready for Use:**
- `manual_product_mappings.json` - 10 validated manual mappings
- `unresolved_products.json` - 4 products for stakeholder review
- `sql/migrations/004_product_schema_update.sql` - Database migration ready

---

## Phase 0: Setup & Verification (15 minutes)

**Goal:** Verify environment and dependencies are ready for implementation.

### 0.1 Start Docker Services

```bash
# Start PostgreSQL + Neo4j
docker-compose up -d

# Verify both services are healthy
docker-compose ps
# Expected: evi_rag_postgres (healthy), evi_rag_neo4j (healthy)
```

### 0.2 Verify Database Migration

```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/evi_rag

# Check if products table exists
\d products

# Expected columns:
# - id (uuid)
# - name (text NOT NULL)
# - description (text)
# - price (text) ← Added in migration 004
# - url (text NOT NULL)
# - category (text)
# - embedding (vector(1536))
# - metadata (jsonb)
# - created_at, updated_at

# Check if search_products() function exists
\df search_products

# Exit psql
\q
```

**If migration NOT applied:**
```bash
psql postgresql://postgres:postgres@localhost:5432/evi_rag -f sql/migrations/004_product_schema_update.sql
```

### 0.3 Verify Environment Variables

```bash
# Check .env file
cat .env | grep -E "EMBEDDING_MODEL|LLM_API_KEY|DATABASE_URL"

# Expected:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/evi_rag
# EMBEDDING_MODEL=text-embedding-3-small
# LLM_API_KEY=sk-... (OpenAI key)
```

### 0.4 Verify Manual Mapping Files Exist

```bash
# Check files created in documentation update
ls -lh docs/features/FEAT-004_product-catalog/*.json

# Expected:
# manual_product_mappings.json (10 mappings)
# unresolved_products.json (4 unresolved products)
```

### 0.5 Verify Test Stubs

```bash
# Check test files exist
ls tests/unit/test_product_*.py
ls tests/integration/test_product_*.py

# Expected: 5 test files with stubs
```

**Checklist:**
- [ ] Docker services running (PostgreSQL + Neo4j)
- [ ] Database migration 004 applied (products table has `price` column)
- [ ] `.env` has `EMBEDDING_MODEL=text-embedding-3-small`
- [ ] `manual_product_mappings.json` exists with 10 mappings
- [ ] `unresolved_products.json` exists with 4 products
- [ ] Test stub files exist

**Time Estimate:** 15 minutes

---

## Phase 1: Portal Scraping (2-3 hours)

**Goal:** Scrape 76 products from portal.evi360.nl and write to database.

### 1.1 Create Scraper Module

**File:** `ingestion/scrape_portal_products.py`

**Key Requirements:**
- Use Crawl4AI `AsyncWebCrawler` for JavaScript rendering
- Scrape listing page: `https://portal.evi360.nl/products`
- Extract 76 product URLs (ignore header/footer with `main` selector)
- Click into each product page
- Extract fields using validated selectors:
  - **Name:** `h1` (HIGH confidence)
  - **Description:** `div.platform-product-description p` (CRITICAL: use container!)
  - **Price:** `.product-price` (optional, may be NULL)
  - **URL:** Canonical URL from page
  - **Category:** NULL (not available on product pages)

**Validated Selector Code:**
```python
def extract_product_details(html: str) -> Dict[str, Any]:
    """Extract product details using validated selectors."""
    soup = BeautifulSoup(html, "html.parser")

    # Name (HIGH confidence)
    name = soup.select_one("h1").text.strip()

    # Description (CRITICAL: use container to avoid generic text)
    desc_container = soup.select_one("div.platform-product-description")
    paragraphs = desc_container.find_all("p") if desc_container else []
    description = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])

    # Price (optional)
    price_elem = soup.select_one(".product-price")
    price = price_elem.text.strip() if price_elem else None

    return {
        "name": name,
        "description": description,
        "price": price,
        "category": None  # Not available on product pages
    }
```

### 1.2 Write to Database

**Database Write Strategy:** Insert products immediately after scraping (incremental write).

```python
async def scrape_and_insert_products():
    """Scrape portal and insert products into database."""
    pool = await get_db_pool()

    async with AsyncWebCrawler() as crawler:
        # Step 1: Get listing
        result = await crawler.arun("https://portal.evi360.nl/products")
        product_urls = extract_product_urls(result.html)

        # Step 2: Scrape each product
        for url in product_urls:
            product_result = await crawler.arun(url)
            product = extract_product_details(product_result.html)
            product["url"] = url

            # Step 3: Insert to database (no embedding yet)
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO products (id, name, description, price, url, category, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
                    ON CONFLICT (url) DO UPDATE
                    SET name = EXCLUDED.name, description = EXCLUDED.description, price = EXCLUDED.price
                """, uuid.uuid4(), product["name"], product["description"], product["price"], product["url"], product["category"])

            logger.info(f"Inserted product: {product['name']}")
```

### 1.3 Validation

```bash
# Run scraper
python3 -m ingestion.scrape_portal_products

# Verify 76 products inserted
psql postgresql://postgres:postgres@localhost:5432/evi_rag -c "SELECT COUNT(*) FROM products;"
# Expected: 76

# Check sample product
psql postgresql://postgres:postgres@localhost:5432/evi_rag -c "SELECT name, LENGTH(description), price, url FROM products LIMIT 5;"
```

**Acceptance Criteria:**
- [ ] 76 products scraped (AC-004-001)
- [ ] All products have non-empty name, description, URL
- [ ] Price may be NULL for some products
- [ ] Category is NULL for all scraped products
- [ ] Descriptions are product-specific (922-2662 chars, not generic 147-char platform text)
- [ ] Scraping completes in <10 minutes

**Time Estimate:** 2-3 hours (including error handling, logging, rate limiting)

---

## Phase 2: CSV Parsing & Fuzzy Matching (1-2 hours)

**Goal:** Parse CSV, fuzzy match to portal products, enrich database with problem mappings.

### 2.1 Parse Intervention_matrix.csv

**File:** `ingestion/parse_interventie_csv.py`

**Key Requirements:**
- Parse `docs/features/FEAT-004_product-catalog/Intervention_matrix.csv`
- 26 rows with 23 unique products (many-to-one: multiple problems → same product)
- Aggregate problems by product name
- Extract columns: `Probleem`, `Category`, `Soort interventie`
- Ignore `Link interventie` column (old URLs)

```python
def parse_interventie_csv() -> Dict[str, Dict]:
    """Parse CSV and aggregate problems by product name."""
    mappings = {}

    with open("docs/features/FEAT-004_product-catalog/Intervention_matrix.csv", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_name = row["Soort interventie"].strip()
            problem = row["Probleem"].strip()
            category = row["Category"].strip()

            if product_name not in mappings:
                mappings[product_name] = {"problems": [], "category": category}
            mappings[product_name]["problems"].append(problem)

    return mappings  # 23 unique products
```

### 2.2 Fuzzy Matching with Normalization

**Threshold:** 0.85 (validated)
**Strategy:** Normalize names (lowercase, remove special chars) before fuzzy matching

```python
import re
from fuzzywuzzy import fuzz

def normalize_product_name(name: str) -> str:
    """Normalize product name for fuzzy matching."""
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)  # Remove special chars
    return name.strip()

async def fuzzy_match_and_enrich():
    """Fuzzy match CSV to portal products and enrich database."""
    csv_data = parse_interventie_csv()
    pool = await get_db_pool()

    # Load manual mappings
    with open("docs/features/FEAT-004_product-catalog/manual_product_mappings.json") as f:
        manual_mappings = json.load(f)["mappings"]
    manual_map = {m["csv_product"]: m["portal_product"] for m in manual_mappings}

    # Get all portal products
    async with pool.acquire() as conn:
        portal_products = await conn.fetch("SELECT id, name FROM products")

    matched_count = 0
    unresolved = []

    for csv_product, data in csv_data.items():
        portal_match = None

        # Try manual mapping first
        if csv_product in manual_map:
            portal_name = manual_map[csv_product]
            portal_match = next((p for p in portal_products if p["name"] == portal_name), None)
            logger.info(f"Manual match: {csv_product} → {portal_name}")
        else:
            # Fuzzy match
            best_score = 0
            for portal_prod in portal_products:
                score = fuzz.token_sort_ratio(
                    normalize_product_name(csv_product),
                    normalize_product_name(portal_prod["name"])
                ) / 100.0

                if score >= 0.85 and score > best_score:
                    best_score = score
                    portal_match = portal_prod

            if portal_match:
                logger.info(f"Fuzzy match: {csv_product} → {portal_match['name']} ({best_score:.2f})")

        # Enrich matched product
        if portal_match:
            metadata = {
                "problem_mappings": data["problems"],
                "csv_category": data["category"]
            }
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE products
                    SET metadata = $1, category = $2, updated_at = NOW()
                    WHERE id = $3
                """, json.dumps(metadata), data["category"], portal_match["id"])
            matched_count += 1
        else:
            unresolved.append(csv_product)

    # Write unresolved products
    with open("docs/features/FEAT-004_product-catalog/unresolved_products.json") as f:
        unresolved_data = json.load(f)

    logger.info(f"Matched: {matched_count}/23 products ({matched_count/23*100:.0f}%)")
    logger.info(f"Unresolved: {len(unresolved)} products")

    return matched_count, unresolved
```

### 2.3 Validation

```bash
# Run CSV parsing and fuzzy matching
python3 -m ingestion.parse_interventie_csv

# Verify enrichment
psql postgresql://postgres:postgres@localhost:5432/evi_rag -c "
  SELECT COUNT(*) FROM products
  WHERE jsonb_array_length(metadata->'problem_mappings') > 0;
"
# Expected: ≥19 products

# Check sample enriched product
psql postgresql://postgres:postgres@localhost:5432/evi_rag -c "
  SELECT name, category, metadata->'problem_mappings' AS problems
  FROM products
  WHERE metadata->'problem_mappings' IS NOT NULL
  LIMIT 3;
"
```

**Acceptance Criteria:**
- [ ] 23 unique products parsed from CSV (26 rows total) (AC-004-003)
- [ ] ≥19 products matched (9 automated + 10 manual = 83%) (AC-004-003)
- [ ] ≥19 products have `problem_mappings` in metadata (AC-004-004)
- [ ] Matched products have `csv_category` in metadata
- [ ] 4 unresolved products written to `unresolved_products.json`

**Time Estimate:** 1-2 hours

---

## Phase 3: Embedding Generation (30-60 minutes)

**Goal:** Generate embeddings for all 76 products (description + problems concatenated).

### 3.1 Generate Embeddings

**File:** `ingestion/embedder.py` (reuse existing)

**Key Requirements:**
- For each product, concatenate: `description + "\n\n" + "\n".join(problem_mappings)`
- If no problem mappings, use description only
- Generate 1536-dim embedding via OpenAI `text-embedding-3-small`
- Update database with embedding

```python
from openai import AsyncOpenAI
import os

async def generate_and_store_embeddings():
    """Generate embeddings for all products."""
    client = AsyncOpenAI(api_key=os.getenv("LLM_API_KEY"))
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        products = await conn.fetch("SELECT id, description, metadata FROM products WHERE embedding IS NULL")

    for product in products:
        # Concatenate description + problems
        text = product["description"]
        if product["metadata"] and "problem_mappings" in product["metadata"]:
            problems = "\n".join(product["metadata"]["problem_mappings"])
            text = f"{text}\n\n{problems}"

        # Generate embedding
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embedding = response.data[0].embedding

        # Store in database
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE products
                SET embedding = $1, updated_at = NOW()
                WHERE id = $2
            """, embedding, product["id"])

        logger.info(f"Generated embedding for product: {product['id']}")

    logger.info(f"Embeddings generated for {len(products)} products")
```

### 3.2 Validation

```bash
# Run embedding generation
python3 -m ingestion.embedder --entity-type=products

# Verify 100% coverage
psql postgresql://postgres:postgres@localhost:5432/evi_rag -c "
  SELECT COUNT(*) AS total, COUNT(embedding) AS with_embedding
  FROM products;
"
# Expected: total=76, with_embedding=76

# Check embedding dimensions
psql postgresql://postgres:postgres@localhost:5432/evi_rag -c "
  SELECT array_length(embedding, 1) FROM products LIMIT 1;
"
# Expected: 1536
```

**Acceptance Criteria:**
- [ ] 100% of products have embeddings (AC-004-005)
- [ ] Embedding dimension is 1536
- [ ] Enriched products (with problems) have concatenated text embedded
- [ ] Non-enriched products have description-only embedded

**Time Estimate:** 30-60 minutes (depending on API latency)

---

## Phase 4: Agent Integration (1-2 hours)

**Goal:** Add `search_products()` tool to agent, remove restriction, test.

### 4.1 Add ProductSearchInput Model

**File:** `agent/tools.py`

**Location:** After `HybridSearchInput` class (around line 77)

```python
class ProductSearchInput(BaseModel):
    """Input for product search tool."""
    query: str = Field(..., description="Dutch search query for EVI 360 products (e.g., 'burn-out begeleiding', 'fysieke klachten')")
    limit: int = Field(default=5, ge=1, le=10, description="Maximum number of products to return (1-10)")
```

### 4.2 Add search_products_tool Function

**File:** `agent/tools.py`

**Location:** After existing tool functions (around line 385)

```python
async def search_products_tool(input_data: ProductSearchInput) -> List[Dict[str, Any]]:
    """
    Search EVI 360 product catalog using hybrid search.

    Combines vector similarity (70%) with Dutch full-text search (30%)
    to find relevant intervention products.

    Args:
        input_data: Product search parameters

    Returns:
        List of products with name, description, url, price, similarity
    """
    try:
        # Generate embedding for query
        embedding = await generate_embedding(input_data.query)

        # Get database pool
        from .db_utils import get_db_pool
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Call search_products SQL function
            results = await conn.fetch("""
                SELECT * FROM search_products($1::vector, $2::text, $3::int)
            """, embedding, input_data.query, input_data.limit)

        # Format for LLM consumption
        products = []
        for r in results:
            products.append({
                "product_id": str(r["product_id"]),
                "name": r["name"],
                # Truncate description to 200 chars for LLM context
                "description": r["description"][:200] + ("..." if len(r["description"]) > 200 else ""),
                "price": r["price"] if r["price"] else "Prijs op aanvraag",
                "url": r["url"],
                "category": r["category"],
                "similarity": round(float(r["similarity"]), 2),
                "problem_mappings": r["metadata"].get("problem_mappings", []) if r["metadata"] else []
            })

        logger.info(f"Product search '{input_data.query}' returned {len(products)} results")
        return products

    except Exception as e:
        logger.error(f"Product search failed: {e}")
        return []
```

### 4.3 Update Specialist Agent

**File:** `agent/specialist_agent.py`

**Change 1 - Remove Restriction (Line 51):**
```python
# BEFORE:
"- Do not recommend products (not in this version)"

# AFTER:
"- Use search_products() when query relates to interventions, begeleiding, or EVI 360 services"
```

**Change 2 - Add Product Recommendation Instructions (After line 91):**
```python
"""
**Product Recommendations:**

When user asks about interventions or workplace support services, call search_products():

Examples:
- "Welke interventies zijn er voor burn-out?"
- "Heb je begeleiding voor verzuim?"
- "Welke producten heeft EVI 360 voor fysieke klachten?"

Format products in Dutch markdown:

**[Product Name]** ([Price])
[1-2 sentence description]
🔗 [Product URL]

Example:
**Herstelcoaching** (Vanaf € 2.500)
6-9 maanden traject voor burn-out herstel met begeleiding van arbeidsdeskundige.
🔗 https://portal.evi360.nl/products/15

- Recommend 2-3 most relevant products (max 5)
- Include pricing if available, otherwise "Prijs op aanvraag"
- Always include clickable URLs
"""
```

**Change 3 - Register Tool (Around line 170):**
```python
# BEFORE:
agent = Agent(
    model=...,
    tools=[hybrid_search_tool]  # Current tools
)

# AFTER:
from .tools import search_products_tool  # Add import at top

agent = Agent(
    model=...,
    tools=[
        hybrid_search_tool,      # Existing guideline search
        search_products_tool     # NEW: Product search
    ]
)
```

### 4.4 Validation

```bash
# Run agent with test query
python3 cli.py --query "Welke interventies zijn er voor burn-out?"

# Expected response should include:
# 1. Guideline citations (existing behavior)
# 2. Product recommendations with:
#    - Bold product names
#    - Pricing
#    - URLs in markdown format
#    - 2-3 relevant products
```

**Acceptance Criteria:**
- [ ] `search_products_tool` registered with agent (AC-004-007)
- [ ] Agent calls tool when query mentions interventions
- [ ] Products formatted in Dutch markdown (AC-004-008)
- [ ] URLs are clickable (markdown format)
- [ ] Pricing included (or "Prijs op aanvraag")
- [ ] Agent restriction removed from specialist_agent.py:51

**Time Estimate:** 1-2 hours (including testing)

---

## Testing

### Run Unit Tests

```bash
# Activate venv
source venv/bin/activate

# Run all product unit tests
pytest tests/unit/test_product_*.py -v

# Expected: 18 tests (some may be skipped with TODO markers initially)
```

### Run Integration Tests

```bash
pytest tests/integration/test_product_*.py -v

# Expected: 6 tests
```

### Manual Testing

Use queries from `manual-test.md`:
1. "burn-out"
2. "fysieke klachten"
3. "conflict"
4. "verzuim"
5. "werkdruk"
6. "zwangerschap"
7. "psychische klachten"
8. "leefstijl"
9. "re-integratie"
10. "bedrijfsmaatschappelijk werk"

**Success:** ≥7/10 queries return relevant products (≥70% relevance)

---

## Troubleshooting

### Issue: Only Generic Descriptions Scraped

**Symptom:** All products have same 147-char description.

**Fix:** Verify using `div.platform-product-description p` selector (not just `p`).

### Issue: Fuzzy Matching <80%

**Symptom:** <19 products matched.

**Fix:** Check `manual_product_mappings.json` is loaded correctly. Verify 10 manual mappings exist.

### Issue: Embeddings Not Generating

**Symptom:** `embedding IS NULL` for all products.

**Fix:** Check `.env` has `LLM_API_KEY` and `EMBEDDING_MODEL=text-embedding-3-small`.

### Issue: Agent Doesn't Call search_products()

**Symptom:** Agent returns only guidelines, no products.

**Fix:** Verify:
1. Tool is registered in `specialist_agent.py`
2. Restriction removed from line 51
3. Product recommendation instructions added to system prompt

---

## Rollback

If implementation fails, rollback database:

```bash
psql postgresql://postgres:postgres@localhost:5432/evi_rag -f sql/migrations/004_rollback.sql
```

---

## Post-Implementation

After successful implementation:

1. **Update CHANGELOG.md:**
   ```
   ## [FEAT-004] - 2025-11-05
   ### Added
   - Product catalog with 76 EVI 360 intervention products
   - Fuzzy matching with manual mapping fallback (83% match rate)
   - Hybrid search (70% vector + 30% Dutch full-text)
   - Agent product recommendation capability
   ```

2. **Update docs/README.md:**
   - Add FEAT-004 to "Implemented Features" section

3. **Mark PRD as Complete:**
   - Update `prd.md` status to "Complete"

4. **Stakeholder Review:**
   - Share `unresolved_products.json` (4 products) for stakeholder input

---

## Time Summary

| Phase | Description | Estimated Time |
|-------|-------------|----------------|
| **Phase 0** | Setup & Verification | 15 minutes |
| **Phase 1** | Portal Scraping | 2-3 hours |
| **Phase 2** | CSV Parsing & Fuzzy Matching | 1-2 hours |
| **Phase 3** | Embedding Generation | 30-60 minutes |
| **Phase 4** | Agent Integration | 1-2 hours |
| **Testing** | Unit + Integration + Manual | 1-2 hours |
| **TOTAL** | | **6-10 hours** |

---

## Success Criteria

Implementation is complete when all acceptance criteria pass:
- ✅ 76 products scraped (AC-004-001)
- ✅ ≥19 products enriched with problem mappings (AC-004-003, AC-004-004)
- ✅ 100% embedding coverage (AC-004-005)
- ✅ Hybrid search function working (AC-004-006)
- ✅ Agent tool registered (AC-004-007)
- ✅ Products formatted in Dutch markdown (AC-004-008)
- ✅ Search latency <500ms (AC-004-009)
- ✅ All tests passing (AC-004-010, AC-004-011)
- ✅ Manual testing ≥70% relevance (AC-004-012)

---

**Ready to implement!** All planning validated, documentation updated, zero contradictions.
