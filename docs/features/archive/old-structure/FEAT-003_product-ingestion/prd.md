# PRD: FEAT-003 - Product Ingestion

**Feature ID:** FEAT-003
**Phase:** 4 (Product Catalog)
**Status:** Planned
**Priority:** Medium
**Owner:** TBD

## Overview

Build automated product catalog ingestion by scraping ~100 product listings from the EVI 360 website. The system must extract product details (name, description, URL), use AI-assisted categorization to assign categories/subcategories, generate compliance tags (e.g., CE_certified, EN_397), create embeddings for semantic product search, and store in PostgreSQL's `products` table.

## Scope

**In Scope:**
- Web scraping of EVI 360 product pages using beautifulsoup4 4.12.3 + httpx 0.28.1
- Extract: product name, Dutch description, URL, category (if available)
- AI-assisted categorization using OpenAI GPT-4 (LLM_MODEL):
  - Assign category and subcategory based on Dutch product descriptions
  - Generate compliance_tags array (e.g., ["EN_361", "CE_certified", "ISO_9001"])
- Generate embeddings for product descriptions (text-embedding-3-small)
- Store in `products` table with all fields populated
- Rate limiting (0.5 req/sec for web scraping, respect robots.txt)
- Fallback: Manual CSV upload if scraping is blocked or infeasible

**Out of Scope:**
- Real-time product inventory sync
- Product pricing or availability tracking
- Product image scraping or storage
- Product relationship graph (deferred to future phase)

## Success Criteria

- ✅ At least 100 products successfully ingested
- ✅ All products have: name, description, URL, category, subcategory, compliance_tags (if applicable)
- ✅ AI categorization accuracy: 90%+ (validated by spot checks against known categories)
- ✅ Compliance tags correctly identify relevant standards (e.g., EN_397 for helmets)
- ✅ Embeddings generated for all product descriptions (no nulls)
- ✅ Test suite validates: web scraping, AI categorization, compliance tag generation, database insertion
- ✅ Ingestion pipeline completes in < 45 minutes for 100 products (accounting for LLM API calls)

## Dependencies

- **Infrastructure:** PostgreSQL 17 + pgvector with `products` table (FEAT-001 ✅)
- **External Services:** OpenAI API key for embeddings + categorization (pending configuration)
- **External Services:** EVI 360 website accessible (confirm URL with user)

## Technical Notes

- Use GPT-4 for categorization with Dutch system prompt
- Prompt engineering: Provide category examples based on common Dutch safety equipment
- Compliance tags: Use regex/keyword detection + LLM validation
- Store original product URL in `products.url` for reference
- Handle missing data gracefully (e.g., if category not available from website)

## Next Steps

1. Confirm EVI 360 product URL with user (e.g., https://evi360.nl/producten)
2. Implement web scraper (`ingestion/product_scraper.py`)
3. Implement AI categorization logic (`ingestion/product_categorizer.py`)
4. Implement compliance tag generation (`ingestion/compliance_tagger.py`)
5. Write tests for scraping, categorization, tagging
6. Run end-to-end ingestion and validate results
7. Create fallback CSV upload script if scraping blocked
