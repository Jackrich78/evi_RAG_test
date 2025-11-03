# PRD: FEAT-004 - Product Catalog Ingestion

**Feature ID:** FEAT-004
**Phase:** 4 (Product Knowledge)
**Status:** 🚀 Ready for Planning
**Priority:** Medium
**Owner:** TBD
**Dependencies:** FEAT-003 (Specialist Agent - complete)
**Created:** 2025-10-25
**Last Updated:** 2025-10-31

---

## Problem Statement

Build a searchable catalog of ~100 EVI 360 safety products to enable contextually relevant product recommendations alongside guideline results. Products must be semantically searchable to support workplace safety specialists in finding relevant equipment and services.

**Quick MVP Approach:** Ingest products from existing Notion database with minimal transformation, enable semantic search, integrate with specialist agent for contextual recommendations.

---

## Goals

1. **Product Ingestion:** Import ~100 products from Notion database (https://www.notion.so/29dedda2a9a081409224e46bd48c5bc6)
2. **Semantic Search:** Enable vector similarity search for product discovery
3. **Agent Integration:** Allow specialist agent to retrieve products when contextually relevant
4. **Simple Categories:** Extract existing "type" and "tags" from Notion (no AI categorization needed for MVP)
5. **Quick Time-to-Value:** Operational within 7-10 hours of development

---

## User Stories

### Story 1: Product Data Ingestion
**As a** system administrator
**I want** to ingest all EVI 360 products from Notion into PostgreSQL
**So that** products are searchable via semantic search

**Acceptance Criteria:**
- [ ] ~100 products ingested from Notion database (ID: 29dedda2a9a081409224e46bd48c5bc6)
- [ ] All products have: name, description, URL, embedding
- [ ] Categories extracted from Notion "type" field
- [ ] Tags extracted from Notion "tags" field

### Story 2: Contextual Product Recommendations
**As a** workplace safety specialist using the RAG system
**I want** relevant products to appear automatically when my query relates to equipment or services
**So that** I can discover EVI 360 solutions without explicitly asking for products

**Acceptance Criteria:**
- [ ] Query "Welke producten zijn er voor bedrijfsfysiotherapie?" returns relevant products
- [ ] Query about guidelines only (e.g., "Wat zegt de richtlijn over werken op hoogte?") prioritizes guidelines, shows products only if contextually relevant
- [ ] Top 3 most relevant products returned with similarity scores
- [ ] Products include: name, description, URL, category

### Story 3: Semantic Product Search
**As a** specialist agent
**I want** to search products by semantic similarity to user queries
**So that** I can recommend products even when exact keyword matches don't exist

**Acceptance Criteria:**
- [ ] Query "fysieke klachten" matches "Bedrijfsfysiotherapie" products
- [ ] Query "stress en burn-out" matches "Bedrijfsmaatschappelijk werk" products
- [ ] Vector similarity search returns products ranked by relevance

---

## Scope

### In Scope ✅

**Quick MVP Approach (7-10 hours):**

- **Notion Product Ingestion** (`ingestion/ingest_products.py`):
  - Fetch all products from Notion database (ID: 29dedda2a9a081409224e46bd48c5bc6)
  - Extract fields: name, description, URL (or construct from portal.evi360.nl)
  - Map Notion "type" → products.category
  - Map Notion "tags" → products.metadata (or compliance_tags if safety-related)
  - Generate embeddings using existing embedder (OpenAI text-embedding-3-small)
  - Store in dedicated `products` table (NOT chunks table)

- **Product Search Tool** (`agent/tools.py`):
  - Create `product_search_tool()` function
  - Query products table using vector similarity
  - Return top N products as `ProductSearchResult` list
  - Reuse existing `search_products()` SQL function

- **Specialist Agent Integration** (`agent/specialist_agent.py`):
  - Add `@specialist_agent.tool` decorator for product search
  - Remove "Geen producten aanbevelen" restriction
  - Update prompt: products shown when contextually relevant (not forced)
  - Extend response model to include `product_recommendations: List[ProductRecommendation]`
  - Agent decides when to retrieve products based on query intent

- **Testing & Validation**:
  - Verify ~100 products ingested with embeddings
  - Test semantic search ("bedrijfsfysiotherapie", "stress", "fysieke klachten")
  - Validate agent returns top 3 products when relevant

### Out of Scope ❌
- **AI categorization** (Notion already has "type" field)
- **Compliance tag detection** (descoped for MVP - nice to have)
- **Web scraping** (Notion database is faster)
- Real-time inventory sync (static catalog)
- Product pricing or availability
- Product images
- Product-to-guideline knowledge graph (future enhancement)

---

## Success Criteria

**Ingestion:**
- ✅ ~100 products successfully ingested from Notion
- ✅ All products have: name, description, URL, embedding
- ✅ Category extracted from Notion "type" field
- ✅ 100% products have embeddings (no NULL embeddings)

**Search Quality:**
- ✅ Query "bedrijfsfysiotherapie" returns relevant physiotherapy products
- ✅ Query "stress en burn-out" returns "Bedrijfsmaatschappelijk werk" products
- ✅ Top 3 products returned ranked by semantic similarity

**Agent Integration:**
- ✅ Specialist agent can retrieve products via `search_products()` tool
- ✅ Products appear in responses when contextually relevant
- ✅ Queries without product relevance don't force product recommendations
- ✅ Agent returns Dutch product reasoning/descriptions

---

## Dependencies

**Infrastructure:**
- ✅ PostgreSQL 17 + pgvector with `products` table (FEAT-001 - complete)
- ✅ `search_products()` SQL function exists (sql/evi_schema_additions.sql lines 210-245)
- ✅ Pydantic models: EVIProduct, ProductRecommendation, ProductSearchResult (agent/models.py)

**External Services:**
- ✅ Notion API access (NOTION_API_TOKEN configured in FEAT-002)
- ✅ OpenAI API key for embeddings (EMBEDDING_API_KEY configured)
- ✅ Notion products database accessible (ID: 29dedda2a9a081409224e46bd48c5bc6)

**Code Dependencies:**
- ✅ Existing Notion client (ingestion/notion_to_markdown.py)
- ✅ Existing embedder (ingestion/embedder.py)
- ✅ Specialist agent framework (agent/specialist_agent.py)

---

## Technical Notes

### Notion Database Schema (CONFIRMED 2025-10-31)

- **URL:** https://www.notion.so/29dedda2a9a081409224e46bd48c5bc6
- **Database ID:** 29dedda2a9a081409224e46bd48c5bc6

**Known Fields:**
- `id` - Notion page ID (UUID)
- `name` - Product name (string)
- `type` - Product category (string) - e.g., "Fysio", "Juridisch"
- `tags` - Product tags (format TBD - array or string?)
- `visible` - Visibility flag (boolean?) - **IMPORTANT:** Filter by this?
- `URL` - Portal URL (string) - ✅ Exists in Notion (no construction needed!)
- `price_type` - Pricing model (string) - Not using for MVP
- `description` - Product description (assumed, format TBD)
- Other fields exist but not relevant for MVP

**Example Product:** Bedrijfsmaatschappelijk werk (see: big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md)

### Data Mapping Strategy

**Option A: Description Only (Simple)**
```python
products.name = notion_page["name"]
products.description = notion_page["description"]  # Just description
products.category = notion_page["type"]
products.url = notion_page["URL"]  # Extract directly from Notion
products.embedding = generate_embedding(description)
products.metadata = {"tags": notion_page["tags"], "price_type": notion_page["price_type"]}
products.source = "notion_database"
```

**Option B: Name + Description (Better Semantic Matching)**
```python
embedding_text = f"{notion_page['name']}\n\n{notion_page['description']}"
products.embedding = generate_embedding(embedding_text)
```

**Option C: Name + Description + Type + Tags (Maximum Context)**
```python
embedding_text = f"{notion_page['name']}\n\nType: {notion_page['type']}\n\n{notion_page['description']}\n\nTags: {', '.join(notion_page['tags'])}"
products.embedding = generate_embedding(embedding_text)
```

**Decision:** Test all three in pilot phase, choose best performing

### Storage & Search Strategy

**Storage:**
- ✅ Use dedicated `products` table (NOT chunks table)
- Rationale: Product-specific fields (URL, category), clean separation from guidelines

**Search Options:**
- **Option 1:** Vector-only search (simple, like current `search_products()` SQL function)
- **Option 2:** Hybrid search (vector + Dutch full-text, like guidelines)

**Decision:** Test both in pilot, compare retrieval quality

### Agent Integration Logic

**Trigger:** Automatic when contextually relevant (agent decides)

**Contextual Relevance Algorithm (TBD - refine during implementation):**
```python
# Pseudocode for agent decision logic
if query_explicitly_requests_products:  # Keywords: "producten", "aanbevelingen", "diensten"
    retrieve_products(query, limit=3, threshold=0.5)  # Lower threshold for explicit requests
elif semantic_similarity > 0.75:  # High relevance threshold
    retrieve_products(query, limit=3)
else:
    # No products shown
    pass
```

**Output Format:**
- Top 3 products maximum per response
- Separate section in response (not inline with guidelines)
- Include: name, brief description, URL, relevance reasoning (in Dutch)

---

## Implementation Plan (REVISED - 8-12 hours with pilot testing)

### Phase 0: Database Inspection & Schema Analysis (30 min)

**Objective:** Understand actual database structure before writing ingestion code

**Steps:**
1. Add `NOTION_PRODUCTS_DATABASE_ID=29dedda2a9a081409224e46bd48c5bc6` to `.env`
2. Write quick script to inspect Notion database:
   - Query total product count
   - Query products where `visible=true` (or similar filter)
   - Fetch 3-5 sample products to inspect field formats
   - Check for NULL/missing values in required fields
3. Document findings in implementation notes

**Deliverables:**
- Database schema doc with field formats
- Product count (total vs. visible)
- Decision on filter strategy (visible=true only, or all products?)

---

### Phase 1: Pilot Test - Product Ingestion (2-3 hours)

**Objective:** Validate retrieval quality with small subset before full ingestion

**Step 1: Create Dedicated Product Ingestion Script**
- **File:** `ingestion/ingest_products.py` (NEW - don't reuse guidelines ingestion)
- Create `NotionProductIngestion` class (pattern inspired by NotionToMarkdown)
- Implement field mapping based on Phase 0 findings
- Add data validation (skip products with missing description/URL)

**Step 2: Ingest Pilot Subset (10-20 products)**
- Select diverse products (mix of types: Fysio, Juridisch, etc.)
- Test 3 embedding strategies:
  - A: Description only
  - B: Name + description
  - C: Name + description + type + tags
- Insert into products table with metadata flag `"pilot_test": true`

**Step 3: Test Retrieval Quality**
- **File:** `tests/ingestion/test_product_retrieval.py` (NEW)
- Create 10-15 test queries representing real user needs:
  - "bedrijfsfysiotherapie" (should match physiotherapy products)
  - "stress en burn-out" (should match mental health services)
  - "juridisch advies" (should match legal services)
  - "fysieke klachten" (should match ergonomics products)
- For each embedding strategy, query products and check:
  - Are top 3 products relevant?
  - What are similarity scores?
  - Which strategy performs best?

**Step 4: Measure Quality & Decide**
- **Manual validation:** Spot-check top 3 results for each query
- **Metrics:** Average similarity score, relevance rate
- **Decision point:**
  - ✅ If quality acceptable (>70% relevance): Proceed to full ingestion with winning strategy
  - ❌ If quality poor: Iterate on embedding strategy or data enrichment

**Deliverables:**
- `ingestion/ingest_products.py`
- Pilot test results document
- Winning embedding strategy selected

---

### Phase 2: Full Product Ingestion (1-2 hours)

**Conditional:** Only proceed if Phase 1 pilot test successful

**Steps:**
1. Update ingestion script with winning embedding strategy from pilot
2. Add filter logic (e.g., `visible=true` if decided in Phase 0)
3. Run full ingestion: `python3 -m ingestion.ingest_products --full`
4. Validate:
   - Product count matches expected (~100 or filtered count)
   - 100% products have embeddings (no NULLs)
   - Sample 5 random products and verify data quality

**Deliverables:**
- ~100 products in database with embeddings
- Ingestion log with success/error counts

---

### Phase 3: Agent Tool Integration (2-3 hours)

**Step 1: Create Product Search Tool**
- **File:** `agent/tools.py` (add function)
- Implement `product_search_tool(query, limit=3)`
- Generate query embedding
- Query products table using vector similarity
- Return top N products

**Step 2: Register Tool with Specialist Agent**
- **File:** `agent/specialist_agent.py` (modify)
- Add `@specialist_agent.tool` decorator for product search
- Remove "Geen producten aanbevelen" restriction
- Update prompt: products shown when contextually relevant

**Step 3: Extend Response Model**
- **File:** `agent/specialist_agent.py` or `agent/models.py`
- Add `product_recommendations: List[ProductRecommendation]` to response

### Phase 3: Testing & Validation (1-2 hours)

**Step 1: Database Validation**
- Verify products table populated
- Check all products have embeddings
- Test vector search directly

**Step 2: Agent Testing**
- Test: "Welke producten zijn er voor bedrijfsfysiotherapie?"
- Test: "Wat zijn de richtlijnen voor stress en burn-out?" (should show guidelines + maybe products)
- Verify top 3 products returned

**Step 3: Edge Cases**
- Query with no relevant products → no products returned
- Guidelines-only query → products optional

---

## Testing Strategy

**Ingestion:**
- Verify ~100 products from Notion
- Check embeddings generated (no NULLs)
- Spot-check category/tags mapping

**Search Quality:**
- Query "bedrijfsfysiotherapie" → physiotherapy products
- Query "stress" → "Bedrijfsmaatschappelijk werk"
- Query "fysieke klachten" → "Bedrijfsfysiotherapie"

**Agent Integration:**
- Product-focused queries return top 3 products
- Guideline queries don't force products
- Products include name, description, URL

---

## Constraints & Assumptions

### Technical Constraints
- Must use existing products table schema (cannot modify for MVP)
- Must create dedicated product ingestion script (cannot directly reuse guidelines ingestion)
- Specialist agent framework limits (tool registration, response format)
- Use vector-only search (no hybrid for MVP)
- Option B embedding only (name + description)

### Business Constraints
- **Timeline:** 6-9 hours total (reduced from 8-12 - simpler approach, no pilot phase)
- **Data Source:** Notion database only (no web scraping for MVP)
- **Scope:** Basic product search only (no complex recommendations algorithm)
- **Quality optimization:** Deferred to future phase

### Assumptions ✅ VALIDATED
- ✅ Notion database has ~60 products (confirmed by user)
- ✅ Existing Notion API token has access to products database
- ✅ Products don't change frequently (monthly re-ingestion acceptable)
- ✅ Agent prompt modifications won't break existing guideline functionality
- ✅ Option B embedding (name + description) will provide acceptable search quality

---

## Open Questions ✅ RESOLVED (2025-10-31)

*All critical uncertainties resolved via user clarification:*

### 1. Notion Database Schema ✅ RESOLVED
**Known fields:** id, name, type, tags, visible, URL, price_type

**RESOLVED ANSWERS:**
- ✅ Q1.1: **Product count:** ~60 products (not ~100 as initially estimated)
- ✅ Q1.2: **Tags format:** Multi-select (comma separated)
- ✅ Q1.3: **Type values:** Select field with "service" or "product" (just 2 values!)
- ✅ Q1.4: **Missing fields:** Allow empty fields EXCEPT for name (required)
- ✅ Q1.5: **Filter strategy:** Ingest all products (no `visible` filtering needed)

### 2. Embedding Strategy ✅ RESOLVED
**DECISION:** Use Option B - Name + description (concatenated)

**Rationale:** "Keep it simple and effective for now"

**Implementation:**
```python
embedding_text = f"{product['name']}\n\n{product['description']}"
embedding = generate_embedding(embedding_text)
```

### 3. Search Strategy ✅ RESOLVED
**DECISION:** Vector-only search (no hybrid)

**Rationale:** Simplicity - don't add Dutch full-text search complexity for MVP

**Implementation:** Use existing `search_products()` SQL function (vector similarity only)

### 4. Agent Integration Logic ✅ RESOLVED
**DECISION:** Use specialist prompt as-is, agent decides when to call products

**Rationale:** "This feature is more focused on just ingesting and integrating the product catalogue... the specialist agent can call it whenever it needs"

**Optimization:** Will improve agent decision logic AFTER first phases complete

### 5. Data Validation & Error Handling ✅ RESOLVED
**VALIDATION RULES:**
- ✅ **Required fields:** name, URL, description
- ✅ **Skip if missing:** Don't ingest products missing any required field
- ✅ **Empty fields OK:** All other fields can be empty/NULL
- ✅ **API failures:** Retry on embedding generation failure
- ✅ **Logging:** Log skipped products with reason

**Implementation:**
```python
def validate_product(product):
    if not product.get('name'):
        return False, "Missing required field: name"
    if not product.get('URL'):
        return False, "Missing required field: URL"
    if not product.get('description'):
        return False, "Missing required field: description"
    return True, "Valid"
```

### 6. Quality Optimization Strategy ✅ RESOLVED
**DECISION:** Two-phase approach

**Phase 1 (This feature):** Get it working
- Ingest products with Option B embedding
- Basic integration with agent
- Vector-only search

**Phase 2 (Future feature):** Optimize quality
- Refine similarity thresholds
- Improve agent decision logic
- Consider hybrid search if needed
- Test different embedding strategies

**Rationale:** "Yes we should optimise the quality... but we will optimise that once the first phases are done"

---

## Implementation Decisions Summary

| Decision | Value | Rationale |
|----------|-------|-----------|
| **Product count** | ~60 products | Confirmed by user |
| **Embedding strategy** | Option B: Name + description | Simple & effective |
| **Search method** | Vector-only | No hybrid complexity for MVP |
| **Agent integration** | Specialist prompt decides | Focus on ingestion first |
| **Validation rules** | Skip if missing name/URL/description | Clear error handling |
| **Retry logic** | Retry on API failures | Resilience |
| **Empty fields** | Allow (except name) | Flexible data handling |
| **Quality optimization** | Defer to Phase 2 | Get working first |

---

## Simplified Implementation Plan

**No pilot phase needed** - decisions made up front, Option B embedding is the approach.

### Phase 0: Database Inspection (15 min - simplified)
- Connect to Notion products database
- Confirm ~60 product count
- Inspect 2-3 sample products to verify field formats
- **Deliverable:** Quick validation that schema matches expectations

### Phase 1: Product Ingestion (3-4 hours)
1. Create `ingestion/ingest_products.py`
2. Implement field mapping: tags (comma-separated), type (service/product)
3. Implement validation: skip if missing name/URL/description
4. Generate embeddings: Option B (name + description concatenated)
5. Insert into products table
6. Add retry logic for API failures
7. Log skipped products with reasons

**Deliverable:** ~60 products ingested with embeddings

### Phase 2: Agent Tool Integration (2-3 hours)
1. Create `product_search_tool()` in `agent/tools.py`
2. Register tool with specialist agent
3. Update agent prompt to enable products
4. Test: Agent can retrieve products when needed

**Deliverable:** Agent can call products via tool

### Phase 3: Testing & Validation (1-2 hours)
1. Database validation (product count, embeddings)
2. Manual testing with 10+ queries
3. Validate agent integration works
4. Document any issues for Phase 2 optimization

**Deliverable:** Feature working end-to-end

**TOTAL ESTIMATED TIME:** 6-9 hours (reduced from 8-12 hours)

---

## Next Steps

1. ✅ Exploration complete (PRD updated with clarifications)
2. ⏭️ Run `/plan FEAT-004` to create detailed planning documentation:
   - architecture.md (implementation approach, data flow)
   - acceptance.md (testable acceptance criteria)
   - testing.md (test strategy and stubs)
   - manual-test.md (human validation checklist)
3. ⏭️ Implementation (7-10 hours)
4. ⏭️ Testing & validation
5. ⏭️ Commit with `/commit FEAT-004`

---

**Last Updated:** 2025-10-31 (Exploration Phase Complete - All Uncertainties RESOLVED)
**Status:** ✅ Ready for Planning - Run `/plan FEAT-004`
**Estimated Effort:** 6-9 hours (simplified from 8-12 hours - no pilot phase needed)

**Key Decisions Made (2025-10-31 Final Update):**
- ✅ Product count: ~60 products (not ~100)
- ✅ Embedding: Option B (name + description concatenated)
- ✅ Search: Vector-only (no hybrid)
- ✅ Validation: Skip if missing name/URL/description, retry on API failures
- ✅ Agent: Use specialist prompt as-is, agent decides when to call products
- ✅ Notion fields confirmed: tags (multi-select comma-separated), type (service/product)
- ✅ Quality optimization: Defer to future phase, focus on working integration first

**Simplified Approach:**
- No pilot testing phase (decisions made up front)
- Straightforward ingestion with clear validation rules
- Simple vector search
- Agent integration via tool registration
- Total time reduced to 6-9 hours
