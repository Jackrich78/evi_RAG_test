# PRD: FEAT-004 - Product Catalog with Interventie Wijzer Integration

**Feature ID:** FEAT-004
**Feature Name:** Product Catalog with Interventie Wijzer Integration
**Status:** Ready for Implementation
**Priority:** High
**Created:** 2025-11-03
**Updated:** 2025-11-03 (Merged FEAT-011 scope)
**Dependencies:** FEAT-002 (Notion Guidelines) ✅ Complete, FEAT-003 (Specialist Agent) ✅ Complete
**Blocks:** FEAT-012 (Two-Stage Search Protocol)

---

## Executive Summary

Ingest EVI 360's 76 intervention products by scraping portal.evi360.nl and enrich them with problem-to-product mappings from the Interventie Wijzer CSV matrix. Enable the specialist agent to recommend relevant products through hybrid search (vector + problem matching), providing actionable intervention recommendations beyond guideline citations.

**Value Proposition:** Enables agent to recommend EVI 360 intervention products with working URLs and problem-context mapping, expanding beyond guideline citations to actionable service recommendations.

**Scope Change:** This PRD **merges FEAT-011** (Interventie Wijzer integration) into FEAT-004. The combined feature includes:
- ✅ **Portal.evi360.nl web scraping** (all 76 products with Crawl4AI)
- ✅ **Interventie Wijzer CSV ingestion** (26 rows with 23 unique problem-to-product mappings)
- ✅ **Problem mapping enrichment** (store problems in product metadata)
- ✅ **Hybrid search** (vector similarity on description + problems)
- ❌ **Two-stage search protocol** → Deferred to FEAT-012
- ❌ **Query expansion with LLM ranking** → Deferred to FEAT-012

---

## Background & Context

### Current State (Before FEAT-004)

**Specialist Agent Capabilities:**
- ✅ Search Dutch workplace safety guidelines (FEAT-002 + FEAT-003)
- ✅ Provide citations to NVAB, UWV, STECR guidelines
- ❌ **Cannot** recommend EVI 360 intervention products
- ❌ **Cannot** provide product URLs for booking

**Current Agent Restriction:**
```python
# agent/specialist_agent.py (line 44, 74)
"Geen producten aanbevelen (niet in deze versie)"
```

### What FEAT-004 Adds

**1. Product Web Scraping from Portal.evi360.nl (Crawl4AI)**
   - Scrape 76 EVI 360 intervention products from portal.evi360.nl/products
   - Click into each product page for full details (ignore header/footer)
   - Extract: name, description, price, canonical URL
   - Store as **source of truth** for all product data

**2. Interventie Wijzer CSV Integration**
   - Parse Intervention_matrix.csv (26 rows with 23 unique problem-to-product mappings)
   - Extract: problem descriptions, categories, product names
   - Fuzzy match CSV products to scraped portal products (0.85 similarity threshold with normalization)
   - Enrich portal products with problem mappings in metadata (39% automated + 43% manual = 83% total match rate)

**3. Problem-to-Product Metadata Enrichment**
   - Store problem descriptions as array in `metadata.problem_mappings`
   - Store CSV category in `metadata.csv_category`
   - Many-to-one relationship: multiple problems → same product
   - Example: "Vroegconsult Arbeidsdeskundige" linked to 3 different problems

**4. Hybrid Search Tool**
   - `search_products()` agent tool with **hybrid search**:
     - Vector similarity on embeddings (description + problems concatenated)
     - PostgreSQL hybrid_search function (70% vector + 30% text)
   - Returns top 3-5 products with name, description, URL, price, category
   - Agent decides when to call (triggered by intervention/product queries)

**5. Agent Integration**
   - Remove "Geen producten aanbevelen" restriction from specialist_agent.py
   - Add system prompt instruction to call search_products() when appropriate
   - Format products in Dutch markdown with URLs and pricing

### What FEAT-004 Does NOT Include (Deferred to FEAT-012)

- ❌ **Two-stage search protocol**
  - LLM-based ranking with weighted scoring (impact, fit, feasibility)
  - Product-guideline linking at search time
  - Canonicalization & deduplication logic
- ❌ **Query expansion with LLM**
  - Using LLM to expand user query with interventie wijzer keywords
  - Synonym expansion for better recall
- ❌ **Advanced search features** (Future phases)
  - Multi-modal search (images, videos)
  - User feedback integration
  - A/B testing different search strategies

**Design Philosophy:** "Get it working first, optimize later" - Start with simple hybrid search, add LLM ranking in FEAT-012.

---

## Goals & Success Metrics

### Goals

1. **Data Availability:** All 76 products scraped from portal.evi360.nl with embeddings
2. **URL Accuracy:** 100% of products have canonical portal.evi360.nl URLs (source of truth)
3. **Problem Mapping:** ≥80% of CSV products fuzzy-matched to portal products
4. **Search Functionality:** Agent can retrieve products via hybrid search (vector + text)
5. **Performance:** Product search completes in <500ms (95th percentile)
6. **Agent Integration:** Products embedded in Dutch responses with URLs and pricing

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Products Scraped** | 76 products | Count scraped from portal.evi360.nl/products (validated 2025-11-04) |
| **Embedding Coverage** | 100% | All products have non-null embedding (description + problems) |
| **URL Coverage** | 100% | All products have canonical portal.evi360.nl URL |
| **URL Validity** | ≥95% | % URLs returning HTTP 200 when scraped |
| **CSV Match Rate** | ≥80% (≥19/23) | 9 automated (39%) + 10 manual (43%) = 83% total |
| **Problem Mapping Coverage** | ≥19 products | # products with problem_mappings in metadata |
| **Search Latency** | <500ms (p95) | PostgreSQL hybrid_search query timing |
| **Agent Adoption** | ≥3 calls/conversation | Avg search_products() calls when relevant |
| **Response Quality** | ≥70% relevance | Human evaluation on 10 test queries |

### Non-Goals (Explicitly Out of Scope)

- ❌ Real-time portal monitoring (batch scraping only, manual re-scrape trigger)
- ❌ Product versioning or change tracking
- ❌ Product images or multimedia (text-only for now)
- ❌ User-generated product reviews or ratings
- ❌ Inventory management or availability status
- ❌ Multi-language support (Dutch only)
- ❌ LLM-based query expansion (deferred to FEAT-012)
- ❌ Product-guideline linking at search time (deferred to FEAT-012)

---

## User Stories & Use Cases

### User Story 1: EVI Specialist Needs Product Recommendations

**As an** EVI intervention specialist
**I want** the agent to recommend relevant EVI 360 products
**So that** I can provide actionable solutions beyond just guideline citations

**Scenario:**
```
User query: "Werknemer heeft last van burn-out klachten"

Agent response (before FEAT-004):
"Volgens de NVAB Richtlijn Overspanning en burn-out..."
[Only guidelines, no products]

Agent response (after FEAT-004):
"Volgens de NVAB Richtlijn Overspanning en burn-out...

Relevante EVI 360 interventies:
1. **Herstelcoaching** - 6-9 maanden traject voor burn-out herstel
   [https://portal.evi360.nl/products/15]
2. **Psychologische Ondersteuning** - Diepgaande begeleiding
   [https://portal.evi360.nl/products/9]"
```

**Acceptance Criteria:**
- Agent calls `search_products()` when query relates to interventions
- Products formatted in Dutch with descriptions
- URLs displayed in markdown format
- At least 2-3 relevant products shown

---

### User Story 2: Easy Access to Product Information

**As an** EVI specialist
**I want** direct URLs to product pages on portal.evi360.nl
**So that** I can immediately book services without manual searching

**Acceptance Criteria:**
- 100% of products include URL
- URLs are canonical (prefer `/products/<id>` format)
- Clicking URL opens correct product page
- Broken URLs logged for investigation

---

### User Story 3: Consistent Product Data

**As a** system administrator
**I want** products re-scraped easily when portal.evi360.nl updates
**So that** product catalog stays current without manual database editing

**Acceptance Criteria:**
- `python3 -m ingestion.ingest_products --refresh` re-scrapes portal.evi360.nl
- Existing products updated (upsert by name or URL)
- New products added automatically
- Removed products marked inactive (soft delete)
- Re-scraping completes in <10 minutes for ~60 products (including Crawl4AI clicks)

---

## Technical Architecture

### Data Sources

#### 1. Portal.evi360.nl Website (Primary Source - Crawl4AI)

**Base URL:** `https://portal.evi360.nl/products`
**Target:** Product listing page → click into each product page for full details
**Tool:** Crawl4AI (intelligent web scraping with JavaScript rendering)

**Scraping Strategy:**
```python
# ingestion/scrape_portal_products.py
from crawl4ai import AsyncWebCrawler

async def scrape_all_products() -> List[Dict[str, Any]]:
    """
    Scrape all 76 products from portal.evi360.nl using Crawl4AI.

    Returns:
        List of products with name, description, price, url
    """
    products = []

    async with AsyncWebCrawler() as crawler:
        # Step 1: Get product listing page
        result = await crawler.arun(
            url="https://portal.evi360.nl/products",
            bypass_cache=True
        )

        # Step 2: Extract product URLs from listing (ignore header/footer)
        soup = BeautifulSoup(result.html, "html.parser")
        product_links = []

        # Find main content area (ignore nav, header, footer)
        main_content = soup.select("main") or soup.select(".products-grid")
        for link in main_content[0].select("a[href*='/products/']"):
            product_url = urljoin("https://portal.evi360.nl", link["href"])
            product_links.append(product_url)

        # Step 3: Click into each product page
        for product_url in product_links:
            product_result = await crawler.arun(
                url=product_url,
                bypass_cache=True
            )

            # Extract product details from individual page
            product = extract_product_details(product_result.html)
            product["url"] = product_url  # Store canonical URL
            products.append(product)

    return products

def extract_product_details(html: str) -> Dict[str, Any]:
    """
    Extract name, description, price from product page HTML.

    Validated selectors (2025-11-04):
    - name: h1 (product title)
    - description: div.platform-product-description p (product-specific content)
    - price: .product-price (optional, may be NULL)
    - category: NOT AVAILABLE on product pages

    Returns:
        {"name": str, "description": str, "price": str | None}
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract name
    name = soup.select_one("h1").text.strip()

    # Extract description (CRITICAL: use container to avoid generic platform text)
    desc_container = soup.select_one("div.platform-product-description")
    paragraphs = desc_container.find_all("p") if desc_container else []
    description = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])

    # Extract price (optional)
    price_elem = soup.select_one(".product-price")
    price = price_elem.text.strip() if price_elem else None

    return {
        "name": name,
        "description": description,
        "price": price
    }
```

**Key Requirements:**
- ✅ Ignore header/footer elements (use `main` or `.products-grid` selectors)
- ✅ Click into each product page for full description (not just listing preview)
- ✅ Extract: name (h1), description (div.platform-product-description p), price (.product-price), canonical URL
- ✅ Handle JavaScript-rendered content (Crawl4AI handles this automatically)
- ⚠️ Category NOT available on product pages - will be NULL for scraped products (enriched from CSV where matched)

---

#### 2. Interventie Wijzer CSV (Secondary Source - Problem Mappings)

**File:** `docs/features/FEAT-004_product-catalog/Intervention_matrix.csv`
**Structure:** 26 rows with 23 unique product names (many-to-one: multiple problems → same product)

| Column | Description | Example |
|--------|-------------|---------|
| `Probleem` | Problem description (Dutch) | "Mijn werknemer heeft burn-out klachten" |
| `Category` | Category label | "Verbetering belastbaarheid" |
| `Link interventie` | **IGNORE** (old URLs) | ~~https://vitaalondernemen.interventieaanvragen.nl/...~~ |
| `Soort interventie` | Product name | "Multidisciplinaire burnout aanpak" |

**CSV Parsing Strategy:**
```python
# ingestion/parse_interventie_csv.py
import csv
from fuzzywuzzy import fuzz

def parse_interventie_csv() -> List[Dict[str, Any]]:
    """
    Parse Intervention_matrix.csv and extract problem-product mappings.

    Returns:
        [{"product_name": str, "problems": [str], "category": str}, ...]
    """
    mappings = {}  # product_name → {"problems": [], "category": str}

    with open("docs/features/FEAT-004_product-catalog/Intervention_matrix.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_name = row["Soort interventie"].strip()
            problem = row["Probleem"].strip()
            category = row["Category"].strip()

            # Aggregate problems by product (many-to-one relationship)
            if product_name not in mappings:
                mappings[product_name] = {"problems": [], "category": category}
            mappings[product_name]["problems"].append(problem)

    return [
        {"product_name": name, **data}
        for name, data in mappings.items()
    ]

def fuzzy_match_products(csv_products: List[Dict],
                         portal_products: List[Dict],
                         threshold: float = 0.85) -> List[Dict]:
    """
    Fuzzy match CSV products to portal products with normalization.

    Validated strategy (2025-11-04):
    - Threshold: 0.85 (not 0.9 - too strict)
    - Normalization: lowercase, strip whitespace, remove special chars
    - Expected: 39% automated matches (9/23)
    - Manual fallback: manual_product_mappings.json (10 products)
    - Total match rate: 83% (19/23)

    Args:
        csv_products: From parse_interventie_csv()
        portal_products: From scrape_all_products()
        threshold: Minimum similarity score (0.85 = 85%)

    Returns:
        List of matches with portal product enriched with CSV data
    """
    matched = []
    unmatched = []

    for csv_prod in csv_products:
        csv_name = normalize_product_name(csv_prod["product_name"])
        best_match = None
        best_score = 0

        for portal_prod in portal_products:
            portal_name = normalize_product_name(portal_prod["name"])
            score = fuzz.ratio(csv_name, portal_name) / 100.0

            if score > best_score:
                best_score = score
                best_match = portal_prod

        if best_score >= threshold:
            # Enrich portal product with CSV data
            best_match["metadata"] = {
                "problem_mappings": csv_prod["problems"],
                "csv_category": csv_prod["category"]
            }
            matched.append(best_match)
        else:
            unmatched.append(csv_prod["product_name"])

    # Log unmatched for manual review
    if unmatched:
        print(f"⚠️  Unmatched CSV products ({len(unmatched)}): {unmatched}")

    return matched

def normalize_product_name(name: str) -> str:
    """
    Normalize product names for fuzzy matching.

    Examples:
    - "Herstelcoaching" → "herstelcoaching"
    - "Bedrijfsmaatschappelijk Werk" → "bedrijfsmaatschappelijk werk"
    """
    return name.lower().strip()
```

**Key Requirements:**
- ✅ Parse 26 CSV rows (23 unique products) into problem-product mappings
- ✅ Ignore CSV URLs (old/irrelevant)
- ✅ Use fuzzy matching (0.85 threshold with normalization) to match CSV → portal products
- ✅ Load manual_product_mappings.json for manual matches (10 products)
- ✅ Write unmatched to unresolved_products.json (4 products for stakeholder review)
- ✅ Store problems as array in `metadata.problem_mappings`

---

### Database Schema

**Table Schema** (from Phase 1-2, `sql/evi_schema_additions.sql`):

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price TEXT,  -- NEW: Price field from portal scraping
    url TEXT NOT NULL,  -- Canonical URL from portal.evi360.nl (source of truth)
    category TEXT,  -- From portal OR CSV category
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    metadata JSONB DEFAULT '{}',  -- Contains problem_mappings, csv_category
    source TEXT DEFAULT 'portal',  -- Changed from 'notion' to 'portal'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_products_embedding ON products
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_url ON products(url);
CREATE INDEX idx_products_metadata ON products USING GIN(metadata);

-- Updated trigger
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Changes from Existing Schema:**
- ✅ Added `price TEXT` field (from portal scraping)
- ✅ Made `url TEXT NOT NULL` (canonical URLs always present)
- ✅ Changed `source` default from `'notion'` to `'portal'`
- ❌ **REMOVED** `subcategory TEXT` (not needed)
- ❌ **REMOVED** `compliance_tags TEXT[]` (not in scope)
- ❌ **REMOVED** `idx_products_compliance_tags` index

**Metadata Field Structure:**
```json
{
  "problem_mappings": [
    "Mijn werknemer heeft psychische klachten",
    "Mijn werknemer heeft burn-out klachten"
  ],
  "csv_category": "Verbetering belastbaarheid"
}
```

---

**SQL Function** (updated for hybrid search):

```sql
CREATE OR REPLACE FUNCTION search_products(
    query_embedding vector(1536),
    query_text TEXT,
    match_limit INT DEFAULT 5
)
RETURNS TABLE (
    product_id UUID,
    name TEXT,
    description TEXT,
    price TEXT,
    url TEXT,
    category TEXT,
    similarity FLOAT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        p.description,
        p.price,
        p.url,
        p.category,
        -- Hybrid similarity: 70% vector + 30% text search
        (0.7 * (1 - (p.embedding <=> query_embedding)) +
         0.3 * ts_rank(to_tsvector('dutch', p.description),
                       plainto_tsquery('dutch', query_text))) AS similarity,
        p.metadata
    FROM products p
    ORDER BY similarity DESC
    LIMIT match_limit;
END;
$$;
```

**Changes from Existing Function:**
- ✅ Hybrid search: 70% vector + 30% Dutch full-text search
- ✅ Added `price` field to return
- ✅ Removed `compliance_tags` return field
- ✅ Removed `compliance_tags_filter` parameter (not in scope)

---

### Data Models

**Updated Models** (`agent/models.py` - needs updates):

```python
class EVIProduct(BaseModel):
    """EVI 360 intervention product from portal.evi360.nl"""
    id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    price: Optional[str] = Field(None, description="Price from portal scraping")
    url: str = Field(..., description="Canonical URL from portal.evi360.nl (required)")
    category: Optional[str] = None
    embedding: Optional[List[float]] = None  # 1536-dim vector
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains problem_mappings (list) and csv_category (str)"
    )
    source: str = "portal"  # Changed from "notion"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Removed fields:
    # - subcategory (not needed)
    # - compliance_tags (out of scope)

class ProductSearchResult(BaseModel):
    """Product search result from hybrid search."""
    product_id: UUID
    name: str
    description: str
    price: Optional[str]
    url: str  # Required (canonical URL)
    category: Optional[str]
    similarity: float  # Hybrid similarity (70% vector + 30% text)
    metadata: Dict[str, Any]  # Contains problem_mappings, csv_category

    # Removed fields:
    # - compliance_tags (out of scope)
```

**Embedding Strategy:**
- **What to embed:** `description + "\n\n" + "\n".join(problem_mappings)`
- **Chunking:** **NO CHUNKING** - Each product = 1 single embedding (entire text embedded as-is)
- **Rationale:** Products are already atomic units; concatenating problems with description improves semantic matching
- **Example text to embed:**
  ```
  "Multidisciplinaire begeleiding door fysiotherapeut en psycholoog voor complexe burn-out gevallen.

  Mijn werknemer heeft burn-out klachten
  Het gaat slecht met mijn werknemer, hoe krijgt hij gericht advies?"
  ```
- **Dimension:** 1536 (OpenAI text-embedding-3-small)
- **Storage:** 1 embedding per product in `products.embedding` field (vector(1536))

---

## Implementation Plan

**7-Step Implementation Flow:**

```
Step 1: Scrape portal.evi360.nl/products
  → Extract ~60 products (name, description, price, URL)

Step 2: Parse Intervention_matrix.csv
  → Extract 33 problem-product mappings with categories

Step 3: Match CSV products to portal products
  → Method: Fuzzy matching (0.85 threshold) + manual_product_mappings.json (10 products)

Step 4: Enrich portal products with CSV data
  → Add problem_mappings and csv_category to metadata

Step 5: Generate embeddings
  → Embed: description + problems concatenated

Step 6: Insert into products table
  → Upsert by: name + URL + description

Step 7: Agent calls search_products(query)
  → Search strategy: Hybrid (70% vector + 30% Dutch text)
```

---

### Phase 1: Portal Scraping with Crawl4AI (4 hours)

**Tasks:**
1. Create `ingestion/scrape_portal_products.py` module
2. Implement `scrape_all_products()` using Crawl4AI AsyncWebCrawler
3. Extract product listing from /products page (ignore header/footer)
4. Click into each of ~60 product pages
5. Extract: name, description, price, category, canonical URL
6. Handle errors gracefully (retry failed scrapes, log issues)
7. Save to intermediate JSON file for inspection
8. Test: Verify ~60 products scraped with all fields

**Deliverables:**
- `ingestion/scrape_portal_products.py`
- CLI command: `python3 -m ingestion.scrape_portal_products`
- Output: `portal_products.json` (scraped data)

**Example Usage:**
```bash
python3 -m ingestion.scrape_portal_products
# Output: Scraped 58 products from portal.evi360.nl
#         Saved to: portal_products.json
#         Failed: 2 products (timeouts, will retry)
```

---

### Phase 2: CSV Parsing & Fuzzy Matching (2 hours)

**Tasks:**
1. Create `ingestion/parse_interventie_csv.py` module
2. Parse `Intervention_matrix.csv` (26 rows with 23 unique products)
3. Extract problem descriptions, categories, product names
4. Aggregate problems by product (many-to-one)
5. Implement fuzzy matching (0.85 threshold with normalization) using fuzzywuzzy
6. Match CSV products to portal products from Phase 1
7. Log unmatched products for manual review
8. Test: Verify ≥80% match rate

**Deliverables:**
- `ingestion/parse_interventie_csv.py`
- Functions: `parse_interventie_csv()`, `fuzzy_match_products()`
- Matching report showing successful/failed matches

**Example Output:**
```bash
python3 -m ingestion.parse_interventie_csv
# Output: Parsed 33 product-problem mappings from CSV
#         Fuzzy matched: 19/23 products (83% success rate: 9 automated + 10 manual)
#         Unmatched: ["Adviesgesprek P&O Adviseur", "Inzet vertrouwenspersoon", ...]
#         (Unmatched products logged for manual mapping)
```

---

### Phase 3: Product Enrichment & Embedding (2.5 hours)

**Tasks:**
1. Create `ingestion/ingest_products.py` module (orchestrator)
2. Enrich portal products with CSV data (add problem_mappings to metadata)
3. Generate embeddings: `description + "\n\n" + "\n".join(problem_mappings)`
4. Upsert products into database (by name + URL + description)
5. Update `agent/models.py` (remove subcategory, compliance_tags, add price)
6. Update SQL schema (add price field, remove compliance_tags index)
7. Test: Verify all products have embeddings and metadata

**Deliverables:**
- `ingestion/ingest_products.py`
- Updated `agent/models.py`
- Migration script for schema changes (if needed)

**Example Usage:**
```bash
python3 -m ingestion.ingest_products
# Output: Processing 58 portal products...
#         Enriched 27 products with CSV problem mappings
#         Generating embeddings (description + problems)...
#         Ingested 58 products into database
#         Success: 58, Failed: 0
#         Average embedding length: 450 tokens
```

---

### Phase 4: Hybrid Search Tool Implementation (2 hours)

**Tasks:**
1. Update `search_products()` SQL function for hybrid search (70% vector + 30% text)
2. Create `search_products_tool()` in `agent/tools.py`
3. Generate embedding for query using OpenAI
4. Call hybrid search SQL function
5. Format results as List[Dict] for LLM (include price, URL, similarity)
6. Register tool with `@specialist_agent.tool` decorator
7. Test: Verify hybrid search returns relevant products

**Implementation:**
```python
# agent/tools.py
@specialist_agent.tool
async def search_products(
    ctx: RunContext[SpecialistDeps],
    query: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Search EVI 360 intervention products using hybrid search.

    Args:
        query: Search query in Dutch (e.g., "burn-out begeleiding")
        limit: Max number of products to return (default 3)

    Returns:
        List of products with name, description, price, url, similarity
    """
    # Generate embedding for query
    embedding = await generate_embedding(query)

    # Call hybrid search function
    async with ctx.deps.db_pool.acquire() as conn:
        results = await conn.fetch(
            "SELECT * FROM search_products($1, $2, $3)",
            embedding,
            query,  # For text search component
            limit
        )

    # Format for LLM
    return [
        {
            "name": row["name"],
            "description": row["description"][:200] + "...",  # Truncate
            "price": row["price"],
            "url": row["url"],
            "category": row["category"],
            "similarity": round(row["similarity"], 2)
        }
        for row in results
    ]
```

---

### Phase 5: Agent Integration (1.5 hours)

**Tasks:**
1. Update `SPECIALIST_SYSTEM_PROMPT` in `agent/specialist_agent.py`
2. Remove "Geen producten aanbevelen" restriction
3. Add instruction to call `search_products()` when appropriate
4. Add output formatting guideline (markdown, Dutch, include pricing)
5. Test: Agent calls tool and formats products correctly with URLs

**System Prompt Addition:**
```python
# agent/specialist_agent.py (add to SPECIALIST_SYSTEM_PROMPT)

"""
**Product Recommendations:**

When the user asks about EVI 360 interventions or workplace solutions, call the search_products() tool.

**When to call search_products():**
- User asks about interventions (e.g., "Welke interventies zijn er voor burn-out?")
- User needs product recommendations (e.g., "Wat kan EVI 360 bieden?")
- After citing guidelines, suggest related products

**Output Format:**
Format products in Dutch with markdown:

Relevante EVI 360 interventies:

1. **[Product Name]** ([Price])
   [Description in 1-2 sentences]
   [URL]

Example:
1. **Herstelcoaching** (€2.500 - €3.500)
   6-9 maanden traject voor burn-out herstel met arbeidsdeskundige.
   https://portal.evi360.nl/products/15
"""
```

---

### Phase 6: Testing & Validation (2 hours)

**Tasks:**
1. Create test suite in `tests/unit/test_product_ingest.py` (use existing stubs)
2. Test ingestion, URL scraping, search tool
3. Integration test: End-to-end query → product search → response
4. Manual testing: 10 test queries, verify relevance
5. Document results in validation report

**Test Queries:**
1. "Burn-out begeleiding"
2. "Fysieke klachten door tilwerk"
3. "Conflict met leidinggevende"
4. "Lange termijn verzuim"
5. "Werkdruk problemen"
6. "Zwangerschap en werk"
7. "Psychische klachten"
8. "Leefstijl coaching"
9. "Re-integratie traject"
10. "Bedrijfsmaatschappelijk werk"

**Acceptance:**
- ≥7/10 queries return relevant products
- All products have working URLs
- Agent formats output correctly

---

## User Experience Examples

### Example 1: Burn-out Query

**User:** "Werknemer heeft burn-out klachten, 6 maanden verzuim"

**Agent Response:**
```
Volgens de NVAB Richtlijn Overspanning en burn-out is het belangrijk om...
[Guidelines section]

Relevante EVI 360 interventies:

1. **Herstelcoaching**
   Gestructureerd traject van 6-9 maanden met arbeidsdeskundige, gericht op veerkracht
   en geleidelijke werkhervatting bij burn-out.
   https://portal.evi360.nl/products/15

2. **Multidisciplinaire Burnout Aanpak**
   Gecombineerde begeleiding door fysiotherapeut en psycholoog voor complexe burn-out gevallen.
   https://portal.evi360.nl/products/27

3. **Psychologische Ondersteuning**
   Diepgaande psychologische begeleiding voor onderliggende factoren.
   https://portal.evi360.nl/products/9
```

---

### Example 2: Physical Complaints Query

**User:** "Fysieke klachten door tilwerk"

**Agent Response:**
```
Voor fysieke klachten door tilwerk adviseert de NVAB Richtlijn Tillen...

Relevante EVI 360 interventies:

1. **Bedrijfsfysiotherapie**
   Arbeidsgerichte fysiotherapie voor herstel en preventie van bewegingsklachten.
   https://portal.evi360.nl/products/8

2. **Werkplekonderzoek**
   Ergonomisch onderzoek van de werkplek om fysieke belasting te verminderen.
   https://portal.evi360.nl/products/22

3. **Vroegconsult Arbeidsfysiotherapeut**
   Snelle beoordeling van belastbaarheid en advies over aanpassingen.
   https://portal.evi360.nl/products/11
```

---

## Testing Strategy

### Unit Tests (18 tests - use existing stubs)

**File:** `tests/unit/test_product_ingest.py`

1. **Portal Scraping (Crawl4AI)**
   - ✅ Scrape product listing page
   - ✅ Extract product URLs (ignore header/footer)
   - ✅ Click into individual product pages
   - ✅ Parse product details (name, description, price, URL)
   - ✅ Handle scraping errors gracefully

2. **CSV Parsing & Fuzzy Matching**
   - ✅ Parse Intervention_matrix.csv
   - ✅ Extract problem-product mappings
   - ✅ Aggregate problems by product (many-to-one)
   - ✅ Fuzzy match CSV → portal products (0.85 threshold + manual mappings)
   - ✅ Log unmatched products

3. **Product Enrichment**
   - ✅ Enrich products with problem_mappings metadata
   - ✅ Generate embeddings (description + problems)
   - ✅ Handle products without CSV matches

4. **Database Operations**
   - ✅ Insert new products
   - ✅ Update existing products (upsert)
   - ✅ Handle duplicate names

5. **Hybrid Search Tool**
   - ✅ Generate query embedding
   - ✅ Call hybrid search SQL function
   - ✅ Format results for LLM (with price)
   - ✅ Return top N products

### Integration Tests (6 tests)

**File:** `tests/integration/test_product_ingestion_flow.py`

1. ✅ End-to-end: Portal scraping → CSV matching → Database → Hybrid search
2. ✅ Agent calls search_products() tool
3. ✅ Agent formats products in response
4. ✅ Products include working URLs
5. ✅ Search latency <500ms

### Manual Testing (10 scenarios)

1. Query: "Burn-out" → Expect: Herstelcoaching, Psychologische ondersteuning
2. Query: "Fysieke klachten" → Expect: Bedrijfsfysiotherapie, Werkplekonderzoek
3. Query: "Conflict" → Expect: Mediation, Conflictbemiddeling
4. Query: "Verzuim" → Expect: Re-integratietraject, Herstelcoaching
5. Query: "Werkdruk" → Expect: Coaching, Werkdrukanalyse
6. Query: "Leefstijl" → Expect: Leefstijlprogramma's, Gewichtsconsulent
7. Query: "Zwangerschap" → Expect: Arbeidsdeskundige advies
8. Query: "Psychische klachten" → Expect: Psychologische ondersteuning, BMW
9. Query: "Loopbaan" → Expect: Loopbaanbegeleiding, Executive coaching
10. Query: "Onbekende term xyz" → Expect: Graceful fallback (no products or best guess)

---

## Dependencies & Blockers

### Dependencies (Must Be Complete)

✅ **FEAT-002:** Notion Guidelines Integration - Database schema ready
✅ **FEAT-003:** Specialist Agent - Agent system functional with tool support
✅ **Infrastructure:** PostgreSQL + pgvector installed and configured
✅ **Database Schema:** `products` table exists (needs price field added)
✅ **Intervention_matrix.csv:** File present in `docs/features/FEAT-004_product-catalog/`

### Blockers (Critical Inputs Needed)

**Technical Prerequisites:**
1. **Crawl4AI installed** (`pip install crawl4ai`)
2. **fuzzywuzzy installed** (`pip install fuzzywuzzy python-Levenshtein`)
3. **OpenAI API key** (for embeddings, ~$0.30 for 60 products × 1536 dims)
4. **Network access to portal.evi360.nl** (for web scraping)

**No User Input Required:**
- ❌ No Notion database ID needed (using CSV + portal scraping)
- ❌ No Notion API token needed (descoped)
- ✅ Intervention_matrix.csv already provided

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Portal.evi360.nl HTML changes** | High | Medium | Document selectors with comments, add scraping tests, version Crawl4AI |
| **Product name mismatch (CSV vs portal)** | Medium | High | Fuzzy matching (0.85 with normalization), manual_product_mappings.json (10 products), log unresolved to unresolved_products.json (4 products) |
| **CSV contains outdated products** | Low | Medium | Portal is source of truth, CSV only adds metadata, won't break if mismatch |
| **Embedding cost exceeds budget** | Low | Low | Estimate: $0.0001/1K tokens × 450 avg tokens × 60 products = ~$0.30 total |
| **Search relevance poor (<70%)** | Medium | Medium | Test with 10 queries, iterate on embedding strategy (description + problems validated) |
| **Crawl4AI fails or rate-limited** | High | Low | Add retry logic, exponential backoff, cache scraped results to JSON |

---

## Open Questions

**All Resolved:**
1. ~~Notion Database ID~~ → **Resolved:** Using portal scraping + CSV, no Notion needed
2. ~~Web Scraping Frequency~~ → **Resolved:** Manual trigger only (`python3 -m ingestion.ingest_products --refresh`)
3. ~~Product Deprecation~~ → **Resolved:** Portal is source of truth, inactive products won't appear in scraping
4. ~~Embedding Model~~ → **Resolved:** text-embedding-3-small (1536 dim) for cost efficiency

---

## Acceptance Criteria (Summary)

**FEAT-004 is COMPLETE when:**

1. ✅ ~60 products scraped from portal.evi360.nl with Crawl4AI
2. ✅ 100% of products have canonical portal.evi360.nl URLs (source of truth)
3. ✅ ≥80% of CSV products fuzzy-matched to portal products
4. ✅ ≥25 products enriched with problem_mappings in metadata
5. ✅ 100% of products have embeddings (description + problems concatenated)
6. ✅ Hybrid search SQL function updated (70% vector + 30% Dutch text)
7. ✅ `search_products()` tool registered with specialist agent (returns price + URL)
8. ✅ Agent can call tool and format products in Dutch markdown with pricing
9. ✅ Search latency <500ms (95th percentile)
10. ✅ Test suite passes (18 unit + 6 integration tests)
11. ✅ Manual testing shows ≥70% relevance (7/10 queries)
12. ✅ Documentation updated (this PRD, CHANGELOG)

---

## Timeline Estimate

**Total Effort:** 14 hours (1.75 working days)

- Phase 1 (Portal Scraping with Crawl4AI): 4 hours
- Phase 2 (CSV Parsing & Fuzzy Matching): 2 hours
- Phase 3 (Product Enrichment & Embedding): 2.5 hours
- Phase 4 (Hybrid Search Tool): 2 hours
- Phase 5 (Agent Integration): 1.5 hours
- Phase 6 (Testing & Validation): 2 hours

**Scope Expansion:** Original PRD estimated 10 hours for "Notion + basic search." This updated estimate reflects the **merged FEAT-011 scope** (CSV integration, problem mappings, hybrid search) and **portal scraping complexity** (Crawl4AI, clicking into pages).

---

## Future Enhancements (Post-MVP)

**Deferred to FEAT-012:**
- Two-stage search protocol (candidate generation + LLM ranking)
- Product-guideline linking at search time
- Weighted scoring (impact, fit, guidelines, feasibility)
- Canonicalization & deduplication
- Query expansion with LLM (using interventie wijzer keywords)

**Future Phases (Beyond FEAT-012):**
- Real-time portal monitoring (automated re-scraping on schedule)
- Product images and multimedia
- User feedback (thumbs up/down)
- A/B testing different search strategies
- Multi-language support (English, German)

---

## Appendix

### Product Catalog Examples (From Portal Scraping)

**Example 1: Herstelcoaching** (from portal.evi360.nl)
- Name: "Herstelcoaching"
- Price: "€2.500 - €3.500"
- Category: "Coaching"
- Description: "6-9 maanden traject voor werknemers met burn-out of overspanning..."
- URL: https://portal.evi360.nl/products/15
- Problem Mappings: ["Mijn werknemer heeft burn-out klachten", "Het gaat slecht met mijn werknemer"]
- CSV Category: "Verbetering belastbaarheid"

**Example 2: Bedrijfsfysiotherapie** (from portal.evi360.nl)
- Name: "Bedrijfsfysiotherapie"
- Price: "€150 - €200 per sessie"
- Category: "Fysio"
- Description: "Arbeidsgerichte fysiotherapie voor preventie en behandeling van bewegingsklachten..."
- URL: https://portal.evi360.nl/products/8
- Problem Mappings: ["Mijn werknemer heeft fysieke klachten"]
- CSV Category: "Verbetering belastbaarheid"

### References

- **Archived Original PRD:** `docs/features/FEAT-004_product-catalog/archive/prd-v1-broad-scope.md`
- **Interventie Wijzer CSV:** `docs/features/FEAT-004_product-catalog/Intervention_matrix.csv`
- **FEAT-012 PRD:** `docs/features/FEAT-012_two-stage-search/prd.md` (two-stage search + linking)
- **Database Schema:** `sql/evi_schema_additions.sql` (needs price field addition)
- **Data Models:** `agent/models.py` (needs compliance_tags/subcategory removal, price addition)

---

**Document Version:** 3.0 (Merged FEAT-011 Scope)
**Last Updated:** 2025-11-03
**Major Changes:**
- Merged FEAT-011 (Interventie Wijzer integration) into FEAT-004
- Removed all Notion product ingestion (using portal scraping + CSV)
- Added Crawl4AI web scraping strategy
- Added fuzzy matching for CSV-to-portal product mapping
- Updated to hybrid search (70% vector + 30% Dutch text)
- Added price field to schema
- Removed compliance_tags and subcategory

**Status:** Ready for Implementation
**Next Step:** Run implementation → `/build FEAT-004`
