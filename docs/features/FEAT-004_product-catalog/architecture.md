# Architecture Decision: Product Catalog with Interventie Wijzer Integration

**Feature ID:** FEAT-004
**Decision Date:** 2025-11-04
**Status:** Accepted

## Context

The EVI 360 specialist agent currently cannot recommend intervention products - it only cites workplace safety guidelines. To provide actionable recommendations, we need to ingest 76 EVI 360 products from portal.evi360.nl and enrich them with problem-to-product mappings from the Interventie Wijzer CSV. The challenge is choosing the optimal data source and ingestion strategy that provides canonical URLs, current pricing, and problem context while minimizing maintenance overhead and integration complexity.

## Options Considered

### Option 1: Portal Scraping + CSV Enrichment (Crawl4AI)

**Description:** Scrape all 76 products from portal.evi360.nl using Crawl4AI (JavaScript-capable web scraper), clicking into each product page for full details. Enrich scraped products with problem-to-product mappings from Interventie Wijzer CSV using fuzzy matching (0.85 threshold with normalization + manual mappings). Store enriched products in dedicated products table with hybrid search (70% vector + 30% Dutch full-text).

**Key Characteristics:**
- Crawl4AI AsyncWebCrawler handles JavaScript rendering automatically
- Scrapes product listing → clicks into 76 individual product pages
- Extracts: name, description, price, category, canonical URL
- Fuzzy matches CSV products to portal products (fuzzywuzzy library)
- Enriches metadata with problem_mappings array and csv_category
- One embedding per product (description + problems concatenated)

**Example Implementation:**
```python
async with AsyncWebCrawler() as crawler:
    # Step 1: Get listing page
    result = await crawler.arun("https://portal.evi360.nl/products")
    soup = BeautifulSoup(result.html, "html.parser")

    # Step 2: Extract product URLs (ignore header/footer)
    main_content = soup.select("main")[0]
    product_links = [link["href"] for link in main_content.select("a[href*='/products/']")]

    # Step 3: Click into each product page
    for url in product_links:
        product_result = await crawler.arun(url)
        product = extract_product_details(product_result.html)
        products.append(product)
```

---

### Option 2: Notion Database + Manual Portal URLs

**Description:** Create a Notion database with 76 product entries manually populated by EVI 360 staff. Each entry includes product name, description, category, and manually-entered portal.evi360.nl URLs. Ingest products via Notion API (reusing existing guidelines ingestion code from FEAT-002). Problem mappings from CSV matched to Notion products via fuzzy matching.

**Key Characteristics:**
- Reuses existing Notion API integration (notion-client library)
- Manual data entry by EVI 360 staff in Notion UI
- Requires maintaining Notion database parallel to portal.evi360.nl
- No automated price scraping (manual entry or omitted)
- CSV enrichment via fuzzy matching (same as Option 1)
- Notion API rate limits (3 requests/second)

**Example Implementation:**
```python
async def fetch_products_from_notion(database_id: str):
    notion = AsyncClient(auth=NOTION_TOKEN)
    results = await notion.databases.query(database_id=database_id)

    products = []
    for page in results["results"]:
        props = page["properties"]
        product = {
            "name": props["Name"]["title"][0]["text"]["content"],
            "description": props["Description"]["rich_text"][0]["text"]["content"],
            "url": props["URL"]["url"],  # Manually entered
            "category": props["Category"]["select"]["name"]
        }
        products.append(product)
```

---

### Option 3: Manual CSV-Only Ingestion

**Description:** Rely solely on Interventie Wijzer CSV as the single source of truth. Extract 33 product names from CSV (unique values in "Soort interventie" column) and manually add descriptions, URLs, and pricing via a configuration file. No web scraping or Notion dependency - pure CSV + manual JSON configuration.

**Key Characteristics:**
- Simplest implementation (CSV parsing only)
- No external dependencies (Crawl4AI, Notion API)
- Requires manual creation of product_config.json (60 entries)
- No automated URL validation or price updates
- CSV provides problem mappings directly (no fuzzy matching needed)
- High risk of URL rot and stale pricing

**Example Implementation:**
```python
# Parse CSV for product names
csv_products = parse_interventie_csv()  # 23 unique products (26 rows)

# Load manually-maintained config
with open("product_config.json") as f:
    manual_data = json.load(f)  # {"Herstelcoaching": {"url": "...", "description": "...", "price": "..."}}

# Merge
for csv_prod in csv_products:
    product_name = csv_prod["product_name"]
    if product_name in manual_data:
        product = {**csv_prod, **manual_data[product_name]}
        products.append(product)
```

---

## Comparison Matrix

| Criteria | Option 1: Portal Scraping + CSV | Option 2: Notion + Manual URLs | Option 3: CSV-Only Manual |
|----------|----------|----------|----------|
| **Feasibility** | ✅ Crawl4AI tested, 4 hours effort | ⚠️ Notion API ready, but manual data entry required | ✅ Simple CSV parsing, but manual config needed |
| **Performance** | ✅ <500ms search (hybrid SQL function) | ✅ <500ms search, but Notion API slow (3 req/sec ingestion) | ✅ <500ms search, no ingestion bottleneck |
| **Maintainability** | ✅ Re-scrape via CLI (`--refresh`), automated | ❌ Manual Notion updates required when portal changes | ❌ Manual JSON edits required for all updates |
| **Cost** | ✅ Free (Crawl4AI open-source, embeddings ~$0.30) | ⚠️ Free Notion tier OK, but embeddings ~$0.30 | ✅ Free (no external services) |
| **Complexity** | ⚠️ Moderate (Crawl4AI, fuzzy matching, 2 data sources) | ⚠️ Moderate (Notion API, fuzzy matching, manual sync) | ✅ Low (CSV + JSON config) |
| **Community/Support** | ✅ Crawl4AI active (GitHub 11k stars), fuzzywuzzy mature | ✅ Notion API official, excellent docs | ✅ Standard libraries only (csv, json) |
| **Integration** | ✅ Clean separation (portal = source of truth) | ❌ Notion becomes additional system to maintain | ⚠️ CSV = source of truth, but missing data dependencies |

### Criteria Definitions

- **Feasibility:** Can we implement this with current resources/skills/timeline?
- **Performance:** Will it meet performance requirements (speed, scale, resource usage)?
- **Maintainability:** How easy will it be to modify, debug, and extend over time?
- **Cost:** Financial cost (licenses, services, infrastructure)?
- **Complexity:** Implementation and operational complexity?
- **Community/Support:** Quality of documentation, community, and ecosystem?
- **Integration:** How well does it integrate with existing systems?

## Recommendation

**Chosen Approach:** Option 1 - Portal Scraping + CSV Enrichment (Crawl4AI)

**Rationale:**

Option 1 provides canonical URLs directly from portal.evi360.nl (the authoritative source), current pricing from live product pages, and problem context via CSV enrichment. Re-scraping is automated via CLI command, eliminating manual maintenance overhead. Crawl4AI handles JavaScript rendering and clicking into product pages automatically, avoiding brittle BeautifulSoup selectors. Fuzzy matching (0.85 threshold with normalization + manual mappings) gracefully handles naming variations between CSV and portal (83% match rate). The hybrid search (70% vector + 30% Dutch text) balances semantic similarity with keyword matching for optimal retrieval quality.

### Why Not Other Options?

**Option 2 (Notion + Manual URLs):**
- Requires manual Notion database maintenance parallel to portal.evi360.nl
- Manual URL entry prone to errors and staleness
- No automated price scraping capability
- Adds unnecessary Notion dependency when portal is already the source of truth

**Option 3 (CSV-Only Manual):**
- No automated URL validation - high risk of broken links
- No pricing data without manual updates
- Manual JSON configuration difficult to maintain at scale (76 products)
- CSV only has 23 unique products, missing ~53 portal products

### Trade-offs Accepted

- **Trade-off 1:** Web scraping fragility - Portal HTML changes could break scraping. Acceptable because Crawl4AI is robust, we'll document selectors thoroughly, and re-scraping takes only 4 hours to fix if broken.

- **Trade-off 2:** Initial development time - Portal scraping takes 4 hours vs. 1 hour for CSV-only. Acceptable because automated re-scraping saves ongoing maintenance time (estimated 2 hours/quarter vs. 1 hour/month manual updates).

- **Trade-off 3:** Fuzzy matching imprecision - Some CSV products may not match portal products if names differ significantly. Acceptable because ≥80% target allows for manual mapping of the remaining ~20%, and unmatched products are logged for review.

## Spike Plan

### Step 1: Test Crawl4AI on Portal Product Listing
- **Action:** Install Crawl4AI (`pip install crawl4ai`), write minimal script to fetch https://portal.evi360.nl/products, print HTML length and check for JavaScript rendering
- **Success Criteria:** HTML contains product listing elements (not empty page), size >10KB, no authentication errors
- **Time Estimate:** 30 minutes

### Step 2: Extract 5 Sample Product URLs
- **Action:** Parse listing page HTML with BeautifulSoup, identify selectors for product links (ignore header/footer), extract first 5 product URLs
- **Success Criteria:** Extract exactly 5 portal.evi360.nl/products/* URLs, verify they return HTTP 200, log selector patterns used
- **Time Estimate:** 45 minutes

### Step 3: Click Into Sample Product Pages and Extract Fields
- **Action:** Use Crawl4AI to click into 5 sample product URLs, extract name, description, price, category using BeautifulSoup selectors
- **Success Criteria:** All 5 products have non-empty name and description, ≥3 have price field, canonical URLs preserved
- **Time Estimate:** 1 hour

### Step 4: Parse CSV and Fuzzy Match to Samples
- **Action:** Parse Intervention_matrix.csv (26 rows with 23 unique products), extract product names and problems, fuzzy match to 5 sample products using fuzzywuzzy (0.85 threshold with normalization)
- **Success Criteria:** ≥4 of 5 samples successfully matched to CSV products, problem_mappings populated in metadata, unmatched logged
- **Time Estimate:** 45 minutes

### Step 5: Generate Embeddings and Test Hybrid Search
- **Action:** Concatenate description + problems for 5 samples, generate OpenAI embeddings (text-embedding-3-small), insert into products table, test hybrid search SQL function (70% vector + 30% text)
- **Success Criteria:** All 5 products have 1536-dim embeddings, hybrid search query returns products ranked by similarity, search completes <100ms
- **Time Estimate:** 1 hour

**Total Spike Time:** 4 hours

## Implementation Notes

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     Data Sources                              │
│                                                               │
│  ┌─────────────────────┐      ┌────────────────────────┐   │
│  │ portal.evi360.nl    │      │ Intervention_matrix.csv│   │
│  │ /products (listing) │      │ (33 problem mappings)  │   │
│  └──────────┬──────────┘      └───────────┬────────────┘   │
└─────────────┼──────────────────────────────┼─────────────────┘
              │                               │
              │ Crawl4AI                      │ CSV Parser
              │ AsyncWebCrawler               │ + fuzzywuzzy
              ↓                               ↓
       ┌──────────────┐              ┌──────────────┐
       │ scrape_      │              │ parse_       │
       │ portal_      │              │ interventie_ │
       │ products.py  │              │ csv.py       │
       └──────┬───────┘              └──────┬───────┘
              │                             │
              │ 76 products                 │ fuzzy_match_products()
              │ (name, desc, price, URL)    │ (0.85 threshold + manual)
              │                             │
              └──────────┬──────────────────┘
                         │
                         ↓
                  ┌──────────────┐
                  │ ingest_      │
                  │ products.py  │
                  │ (orchestrator)│
                  └──────┬───────┘
                         │
                         │ 1. Enrich with problem_mappings
                         │ 2. Generate embeddings (description + problems)
                         │ 3. Upsert to products table
                         │
                         ↓
              ┌──────────────────────┐
              │ PostgreSQL           │
              │ products table       │
              │ - embedding vector(1536)
              │ - metadata.problem_mappings[]
              │ - metadata.csv_category
              └──────────┬───────────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       │   User Query    │                 │
       │   (Dutch)       │                 │
       └─────────────────┘                 │
              │                            │
              ↓                            │
       ┌──────────────┐                   │
       │ Agent calls  │                   │
       │ search_      │                   │
       │ products()   │                   │
       └──────┬───────┘                   │
              │                            │
              │ Hybrid Search              │
              │ (70% vector + 30% text)    │
              ↓                            │
       ┌──────────────────┐               │
       │ search_products()│◄──────────────┘
       │ SQL function     │
       └──────┬───────────┘
              │
              │ Top 3-5 products
              │ (name, desc, URL, price, similarity)
              ↓
       ┌──────────────┐
       │ Specialist   │
       │ Agent        │
       │ (Dutch       │
       │ markdown)    │
       └──────────────┘
```

### Key Components

- **scrape_portal_products.py:** Crawl4AI-based scraper that fetches product listing, extracts URLs, clicks into 76 product pages, parses name (h1) / description (div.platform-product-description p) / price (.product-price) / URL, saves to database

- **parse_interventie_csv.py:** CSV parser that reads Intervention_matrix.csv (26 rows, 23 unique products), aggregates problems by product name (many-to-one), fuzzy matches to portal products (0.85 threshold with normalization), loads manual mappings from manual_product_mappings.json, enriches metadata

- **ingest_products.py:** Orchestrator that combines portal and CSV data, generates embeddings (description + problems concatenated), upserts to products table with metadata enrichment

- **search_products() SQL function:** Hybrid search combining vector cosine similarity (70%) with Dutch full-text search (30%), returns top N products sorted by similarity score

- **search_products_tool():** Agent tool (agent/tools.py) that generates query embedding, calls SQL function, formats results for LLM with truncated descriptions

### Data Flow

1. **Portal Scraping (Phase 1):** Crawl4AI fetches product listing → extracts 76 product URLs → clicks into each page → extracts name (h1), description (div.platform-product-description p), price (.product-price), canonical URL → writes to database (category = NULL for scraped products)

2. **CSV Parsing (Phase 2):** Parse Intervention_matrix.csv (26 rows with 23 unique products) → aggregate problems by product name → fuzzy match CSV products to portal products using fuzzywuzzy (0.85 threshold with normalization) → load manual_product_mappings.json (10 products) → total 19 products matched (83%) → enrich database with problem_mappings and csv_category in metadata → write unmatched products to unresolved_products.json (4 products for stakeholder review)

3. **Embedding Generation:** For each product, concatenate description + "\n\n" + "\n".join(problem_mappings) → generate 1536-dim embedding via OpenAI text-embedding-3-small → store single embedding per product (no chunking)

4. **Database Upsert:** Insert or update products table by (name, URL, description) → store embedding in vector(1536) column → store problem_mappings and csv_category in JSONB metadata field

5. **Agent Query:** User query → specialist agent calls search_products(query, limit=3) → generate query embedding → execute hybrid search SQL function (70% vector + 30% Dutch text) → return top 3-5 products with name, description (truncated), URL, price, similarity score

6. **Response Formatting:** Agent formats products in Dutch markdown: "**[Name]** ([Price])\n[Description]\n[URL]" → returns full response with guideline citations + product recommendations

### Portal Scraping Selectors (Validated 2025-11-04)

**CRITICAL FIX - Description Selector:**
- ❌ **WRONG:** `soup.find("p")` - Returns generic platform text (same for ALL products)
- ✅ **CORRECT:** `div.platform-product-description p` - Returns product-specific content

**Validated Selectors:**
```python
# Name (HIGH confidence)
name = soup.select_one("h1").text.strip()

# Description (HIGH confidence - CRITICAL: use container)
desc_container = soup.select_one("div.platform-product-description")
paragraphs = desc_container.find_all("p") if desc_container else []
description = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])

# Price (HIGH confidence - optional, may be NULL)
price_elem = soup.select_one(".product-price")
price = price_elem.text.strip() if price_elem else None

# Category (NOT AVAILABLE on product pages)
category = None  # Will be enriched from CSV where matched
```

**Validation Results:**
- Tested on 5 products: 100% success rate
- Description lengths: 922-2662 chars (all unique, product-specific)
- Price formats: "Vanaf € 1297/stuk", "Offerte op maat", NULL

### Fuzzy Matching Strategy (Validated 2025-11-04)

**Threshold & Normalization:**
```python
def normalize_product_name(name: str) -> str:
    """Normalize product name for fuzzy matching."""
    # Lowercase
    name = name.lower()
    # Remove special characters
    name = re.sub(r'[^\w\s]', '', name)
    # Strip whitespace
    return name.strip()

# Fuzzy match with 0.85 threshold (not 0.9 - too strict)
similarity = fuzz.token_sort_ratio(
    normalize_product_name(csv_product),
    normalize_product_name(portal_product)
) / 100.0

if similarity >= 0.85:
    # Match found
```

**Expected Results:**
- Automated matches: 9/23 (39%)
- Manual mappings (from manual_product_mappings.json): 10/23 (43%)
- Total match rate: 19/23 (83%)
- Unresolved: 4/23 (17% - stakeholder review required)

**Manual Mapping File:** `docs/features/FEAT-004_product-catalog/manual_product_mappings.json`
**Unresolved File:** `docs/features/FEAT-004_product-catalog/unresolved_products.json`

### Technical Dependencies

- **crawl4ai:** Version 0.7.6 (JavaScript rendering, async support) - ✅ Validated
- **fuzzywuzzy:** Version 0.18.0 (fuzzy string matching) - ✅ Validated
- **python-Levenshtein:** Version 0.27.3 (fuzzywuzzy speedup) - ✅ Validated
- **beautifulsoup4:** Version 4.12.3 (HTML parsing)
- **openai:** Version 1.90.0 (embeddings API)
- **asyncpg:** Version 0.30.0 (database driver)
- **pydantic-ai:** Version 0.3.2 (agent framework)

### Configuration Required

- **Environment Variables:**
  - `OPENAI_API_KEY`: OpenAI API key for embeddings (text-embedding-3-small)
  - `DATABASE_URL`: PostgreSQL connection string with pgvector extension

- **Database Schema:**
  - Add `price TEXT` field to products table
  - Remove `subcategory TEXT` and `compliance_tags TEXT[]` fields (not in scope)
  - Ensure `url TEXT NOT NULL` constraint
  - JSONB metadata index for problem_mappings filtering

- **CLI Commands:**
  - `python3 -m ingestion.ingest_products`: Initial ingestion (portal + CSV)
  - `python3 -m ingestion.ingest_products --refresh`: Re-scrape portal and refresh products

## Risks & Mitigation

### Risk 1: Portal HTML Structure Changes
- **Impact:** High (scraping breaks, ingestion fails)
- **Likelihood:** Medium (portals update 1-2 times/year)
- **Mitigation:** Document selectors with comments in code, add scraping validation tests, log selector patterns during spike, version Crawl4AI to avoid breaking changes, re-scraping only takes 4 hours to fix

### Risk 2: Fuzzy Matching Fails for <80% of CSV Products
- **Impact:** Medium (products lack problem context, reduced retrieval quality)
- **Likelihood:** Low (research shows naming conventions align well)
- **Mitigation:** Use aggressive normalization (lowercase, strip whitespace, remove special chars), log all unmatched products with similarity scores for manual review, create manual_product_mappings.json override file

### Risk 3: Crawl4AI Rate-Limited or Blocked by Portal
- **Impact:** High (cannot complete scraping, ingestion blocked)
- **Likelihood:** Low (portal.evi360.nl is EVI 360's own site)
- **Mitigation:** Add exponential backoff (1s, 2s, 4s delays), retry failed scrapes up to 3 times, use Crawl4AI's `bypass_cache=True` and `user_agent` configuration, cache scraped results to JSON for manual inspection

## References

- Research findings: `docs/features/FEAT-004_product-catalog/research.md`
- PRD requirements: `docs/features/FEAT-004_product-catalog/prd.md`
- System architecture: `docs/system/architecture.md`
- Database schema: `sql/evi_schema_additions.sql`
- Existing product models: `agent/models.py` (lines 308-391)
- Crawl4AI documentation: https://crawl4ai.com/docs
- fuzzywuzzy documentation: https://github.com/seatgeek/fuzzywuzzy

---

**Decision Status:** Accepted
**Next Steps:** Proceed to acceptance criteria and testing strategy
