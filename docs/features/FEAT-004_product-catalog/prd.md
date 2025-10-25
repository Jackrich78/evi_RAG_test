# PRD: FEAT-004 - Product Catalog Ingestion

**Feature ID:** FEAT-004
**Phase:** 4 (Product Knowledge)
**Status:** ⏳ Planned
**Priority:** Medium
**Owner:** TBD

---

## Problem Statement

Build a searchable catalog of ~100 EVI 360 safety products to enable product recommendations linked to safety guidelines. Products must be categorized, tagged with compliance standards, and searchable via semantic search.

**Challenge:** Products on website may lack structured data (categories, compliance tags). AI-assisted categorization needed to enrich product metadata for better search and recommendations.

---

## Goals

1. **Product Ingestion:** Scrape or import ~100 products from EVI 360 website
2. **AI Categorization:** Use LLM to assign categories/subcategories based on Dutch descriptions
3. **Compliance Tagging:** Automatically detect safety standards (EN, ISO, CE) in product descriptions
4. **Semantic Search:** Enable "find products for fall protection" style queries
5. **Fallback Option:** Support manual CSV upload if web scraping is blocked

---

## User Stories

### Scrape Product Catalog
**Given** EVI 360 website has product listings
**When** The product scraper runs
**Then** ~100 products are extracted with name, description, URL

### AI-Assisted Categorization
**Given** A product with Dutch description "Veiligheidshelm voor bouwplaatsen, CE-gecertificeerd"
**When** The AI categorizer processes it
**Then** Category = "Persoonlijke Beschermingsmiddelen", Subcategory = "Hoofdbescherming"

### Compliance Tag Detection
**Given** Product description mentions "EN 397", "CE gecertificeerd", "ISO 9001"
**When** The compliance tagger processes it
**Then** compliance_tags = ["EN_397", "CE_certified", "ISO_9001"]

### Semantic Product Search
**Given** Query "producten voor valbeveiliging"
**When** The system searches products
**Then** Returns helmets, harnesses, safety nets with compliance tags

---

## Scope

### In Scope ✅
- **Web Scraper** (`ingestion/product_scraper.py`):
  - Scrape EVI 360 product pages using beautifulsoup4 + httpx
  - Extract: name, description, URL, category (if available)
  - Rate limiting: 0.5 req/sec (respectful scraping)
  - Handle pagination

- **AI Categorizer** (`ingestion/product_categorizer.py`):
  - Use GPT-4 to assign category and subcategory
  - Dutch system prompt with category examples
  - Confidence scoring for manual review

- **Compliance Tagger** (`ingestion/compliance_tagger.py`):
  - Regex detection for EN, ISO, CE standards
  - LLM validation for ambiguous cases
  - Generate compliance_tags array

- **Product Ingestion Pipeline** (`ingestion/ingest_products.py`):
  - Orchestrate: Scrape → Categorize → Tag → Embed → Store
  - Reuse existing embedder for descriptions
  - Store in `products` table

- **Fallback CSV Import** (`scripts/import_products_csv.py`):
  - Accept CSV with columns: name, description, url, category, subcategory, compliance_tags
  - Validate and import into database

### Out of Scope ❌
- Real-time inventory sync (static catalog for MVP)
- Product pricing or availability
- Product images
- Product-to-guideline knowledge graph (future enhancement)

---

## Success Criteria

**Ingestion:**
- ✅ At least 100 products successfully ingested
- ✅ All products have: name, description, URL
- ✅ 90%+ products have category and subcategory assigned
- ✅ Embeddings generated for all product descriptions

**Categorization:**
- ✅ AI categorization accuracy: 90%+ (validated by spot checks)
- ✅ Categories align with EVI 360 product domains (e.g., Fysio, Juridisch, Training)

**Compliance Tags:**
- ✅ 70%+ products with compliance-related descriptions have tags
- ✅ Tags correctly identify EN, ISO, CE standards

**Search Quality:**
- ✅ Query "valbeveiliging" returns relevant fall protection products
- ✅ Query "geluidsbescherming" returns hearing protection products
- ✅ Top 5 results include products with matching compliance tags

---

## Dependencies

**Infrastructure:**
- ✅ PostgreSQL 17 + pgvector with `products` table and `search_products()` function (FEAT-001)

**External Services:**
- OpenAI API key for AI categorization and embeddings
- EVI 360 website accessible (confirm URL with user)

---

## Technical Notes

**Product Categories (Dutch):**
```
- Persoonlijke Beschermingsmiddelen (PPE)
  - Hoofdbescherming (Helmets)
  - Gehoorbescherming (Hearing protection)
  - Oogbescherming (Eye protection)
  - Valbeveiliging (Fall protection)
- Bedrijfsfysiotherapie (Workplace Physiotherapy)
- Juridische Diensten (Legal Services)
- Trainingen (Training)
- Arbeidshygiëne (Occupational Hygiene)
```

**AI Categorization Prompt:**
```
Je bent een expert in Nederlandse arbeidsveiligheid.
Categoriseer het volgende product:

Product: {name}
Beschrijving: {description}

Kies de meest passende categorie en subcategorie uit:
[list of categories]

Antwoord in JSON formaat:
{"category": "...", "subcategory": "...", "confidence": 0.0-1.0}
```

**Compliance Tag Regex:**
```python
EN_PATTERN = r'EN\s*\d{3,5}'         # EN 397, EN 361
ISO_PATTERN = r'ISO\s*\d{4,5}'       # ISO 9001
CE_PATTERN = r'CE[- ]?gecertificeerd|CE[- ]?markering'
```

---

## Implementation Plan

### Step 1: Product Scraper (4-6 hours)
**File:** `ingestion/product_scraper.py`

```python
class ProductScraper:
    async def scrape_products(base_url: str) -> List[Product]:
        """Scrape product listings."""

    async def extract_product_details(url: str) -> ProductDetails:
        """Extract details from product page."""
```

### Step 2: AI Categorizer (3-4 hours)
**File:** `ingestion/product_categorizer.py`

Use GPT-4 with Dutch prompt to categorize.

### Step 3: Compliance Tagger (2-3 hours)
**File:** `ingestion/compliance_tagger.py`

Regex + LLM validation.

### Step 4: Product Ingestion Pipeline (2-3 hours)
**File:** `ingestion/ingest_products.py`

Orchestrate full pipeline.

### Step 5: CSV Fallback (2 hours)
**File:** `scripts/import_products_csv.py`

Manual import option.

### Step 6: Testing (3-4 hours)
- Unit tests for scraping, categorization, tagging
- Integration test with 10 sample products
- Validate search quality

---

## Testing Strategy

**Scraping:**
- Test with 10 sample product URLs
- Verify extraction accuracy

**Categorization:**
- Test with 20 products across different categories
- Spot-check AI category assignments against expected

**Compliance Tags:**
- Test with products mentioning EN, ISO, CE standards
- Verify tag extraction accuracy

---

## Next Steps

1. Confirm EVI 360 product URL with user
2. Implement web scraper with rate limiting
3. Implement AI categorizer with Dutch prompt
4. Implement compliance tagger
5. Create product ingestion pipeline
6. Test with 10-20 sample products
7. Run full ingestion on 100 products
8. Validate search quality

---

**Last Updated:** 2025-10-25
**Status:** ⏳ Ready to Plan
**Estimated Effort:** 16-23 hours
