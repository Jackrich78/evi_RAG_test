# Research Findings: FEAT-004 Product Catalog Ingestion

**Feature ID:** FEAT-004
**Research Date:** 2025-10-31
**Researcher:** Explorer + Plan Agents

## Research Questions

*Questions from PRD exploration that this research addresses:*

1. What is the best data source for products: website scraping vs. Notion database?
2. Should products be stored in the products table or chunks table?
3. Does the specialist agent already support product recommendations?
4. What existing infrastructure can be reused?
5. Should we implement AI categorization or use existing Notion fields?

## Findings

### Topic 1: Data Source Selection - Notion vs. Website Scraping

**Summary:** Notion database is significantly faster and more reliable than building a web scraper from scratch. Existing Notion integration from FEAT-002 can be reused with minimal modifications.

**Details:**
- **Notion Integration (RECOMMENDED):**
  - ✅ Existing client: `ingestion/notion_to_markdown.py` (492 lines, battle-tested in FEAT-002)
  - ✅ Config ready: `config/notion_config.py` with environment variable loading
  - ✅ Authentication working: FEAT-002 successfully fetched 87 guidelines with 100% success rate
  - ✅ Simple query: Just add new database ID to `.env`
  - ✅ Estimated effort: **2-3 hours** (database ID + field mapping + insert to products table)

- **Website Scraping (NOT RECOMMENDED for MVP):**
  - ❌ No scraper exists in codebase
  - ❌ Need to build: HTML parsing, pagination, rate limiting, error handling
  - ❌ Portal.evi360.nl structure unknown (requires inspection)
  - ❌ Potential authentication required (login wall?)
  - ❌ Estimated effort: **8-12 hours** (write scraper from scratch)

**Source:** Codebase analysis
**Files Reviewed:**
- `ingestion/notion_to_markdown.py` (lines 45, 104-162)
- FEAT-002 validation report (referenced in docs/IMPLEMENTATION_PROGRESS.md line 75)
**Decision:** Use Notion database

---

### Topic 2: Storage Architecture - Products Table vs. Chunks Table

**Summary:** User initially requested "store as individual chunk" but existing architecture has a dedicated products table with product-specific fields. Products table is the correct choice for clean separation and proper data modeling.

**Details:**

**Existing Products Table Schema** (`sql/evi_schema_additions.sql` lines 24-54):
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    category TEXT,
    subcategory TEXT,
    embedding vector(1536),
    compliance_tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    source TEXT DEFAULT 'evi360_website',
    last_scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Comparison Analysis:**

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **Products table** | • Dedicated schema with product-specific fields (url, category, compliance_tags)<br>• Separate search function `search_products()`<br>• Clean separation of concerns<br>• Already built and indexed | • Requires separate ingestion code<br>• Not reusable with existing chunker | ✅ **RECOMMENDED** |
| **Chunks table** | • Reuses existing ingestion pipeline<br>• Simple: treat products as documents | • Loses product-specific fields (url, category, tags)<br>• Mixes guidelines and products<br>• No clean way to filter "only products"<br>• Cannot use `search_products()` SQL function | ❌ **NOT RECOMMENDED** |

**Source:** Codebase analysis + architectural best practices
**Files Reviewed:**
- `sql/evi_schema_additions.sql` (lines 20-54, 210-245)
- `agent/models.py` (lines 308-410)
**Decision:** Use dedicated products table

---

### Topic 3: Specialist Agent Current State - Product Support

**Summary:** Specialist agent explicitly has products DISABLED in MVP. Products are marked as "not in this version" in both Dutch and English prompts.

**Details:**

**Current Agent Configuration** (`agent/specialist_agent.py`):
- **Line 44 (Dutch prompt):** `"Geen producten aanbevelen (niet in deze versie)"`
- **Line 74 (English prompt):** `"Do not recommend products (not in this version)"`

**Current Workflow** (lines 112-173):
```
Query → search_guidelines() tool → hybrid_search (guidelines only) → Dutch response with citations
```

**Product Tools:**
- ❌ No `search_products()` tool registered with agent
- ❌ No product retrieval in agent workflow
- ✅ Models exist but unused: `ProductRecommendation` (lines 357-379), `ProductSearchResult` (lines 382-391)

**FEAT-003 PRD Evidence:**
- **Line 137:** "No product recommendations (products table empty)" in "Response Format" section
- **Line 143:** "❌ Product recommendations (FEAT-004) - products table empty" in "Out of Scope"

**Source:** Codebase analysis
**Files Reviewed:**
- `agent/specialist_agent.py` (lines 44, 74, 112-173)
- `docs/features/FEAT-003_query-retrieval/prd.md` (lines 137, 143)
**Decision:** Need to enable products by removing restriction and adding tool

---

### Topic 4: Existing Infrastructure Assessment

**Summary:** Comprehensive infrastructure already exists for products: database schema, SQL functions, Pydantic models, and Notion integration. Only missing: ingestion script and agent tool registration.

**Details:**

**✅ Ready Infrastructure:**
1. **Database Schema:**
   - Products table created: `sql/evi_schema_additions.sql` lines 24-54
   - Vector index configured: `idx_products_embedding` (IVFFLAT)
   - Compliance tags index: GIN index on compliance_tags array
   - Metadata index: GIN index on JSONB metadata field

2. **SQL Functions:**
   - `search_products()` function exists: `sql/evi_schema_additions.sql` lines 210-245
   - Returns: product_id, name, description, url, category, similarity, compliance_tags, metadata
   - Supports: vector similarity search + compliance tag filtering

3. **Pydantic Models** (`agent/models.py`):
   - `EVIProduct` (lines 308-348): Full product model with validation
   - `ProductRecommendation` (lines 357-379): Recommendation with relevance scoring
   - `ProductSearchResult` (lines 382-391): Database search result

4. **Notion Integration:**
   - Client: `ingestion/notion_to_markdown.py` (492 lines, production-ready)
   - Config: `config/notion_config.py`
   - Authentication: NOTION_API_TOKEN configured in `.env`

**❌ Missing Components:**
1. Product ingestion script (`ingestion/ingest_products.py` - NEW FILE)
2. Product search tool (`agent/tools.py` - ADD FUNCTION)
3. Agent tool registration (`agent/specialist_agent.py` - MODIFY)

**Source:** Codebase analysis
**Files Reviewed:**
- `sql/evi_schema_additions.sql`
- `agent/models.py`
- `ingestion/notion_to_markdown.py`
- `config/notion_config.py`
**Decision:** Leverage existing infrastructure, build only missing pieces

---

### Topic 5: Categorization Strategy - AI vs. Extract from Notion

**Summary:** Notion database already has "type" and "tags" fields. No AI categorization needed for MVP - extract existing fields directly.

**Details:**

**User Clarification:**
- "The notion DB has some simple type and tags for the products."
- Notion database URL: https://www.notion.so/29dedda2a9a081409224e46bd48c5bc6
- Database ID: 29dedda2a9a081409224e46bd48c5bc6

**Example Product** (`big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md`):
```
Bedrijfsfysiotherapie
Offerte op maat
Beschrijving
Fysieke klachten en werk gaan vaak hand in hand...
```

**Data Mapping (Simple Extraction):**
```python
# Notion → PostgreSQL products table
products.name = notion_page["title"]
products.description = notion_page["description"]
products.category = notion_page["type"]  # Use Notion "type" field directly
products.metadata = {"tags": notion_page["tags"]}  # Store tags in metadata JSONB
products.url = f"https://portal.evi360.nl/products/{slug}"  # Construct or extract
products.embedding = generate_embedding(description)  # OpenAI text-embedding-3-small
products.source = "notion_database"
```

**AI Categorization (DESCOPED):**
- Original PRD proposed GPT-4 categorization: 3-4 hours effort
- Now unnecessary: Notion already has categories
- Can enhance later if needed

**Source:** User clarification + example product file
**Files Reviewed:**
- `big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md`
**Decision:** Extract "type" and "tags" from Notion (no AI needed)

---

## Recommendations

### Primary Recommendation: Quick Notion Integration (7-10 hours)

**Rationale:**
1. **Reuse Existing Code:** Notion client already tested with 87 guidelines (100% success rate in FEAT-002)
2. **No AI Complexity:** Categories exist in Notion database, no need for AI categorization
3. **Clean Architecture:** Use dedicated products table as designed
4. **Minimal Agent Changes:** Add one tool + update prompt + extend response model
5. **Fast Time-to-Value:** Products operational in 1-2 days vs. 2-3 weeks for full scraping approach

**Key Benefits:**
- **60-70% faster** than building web scraper (3 hours vs. 8-12 hours for data ingestion)
- **Reliable:** Notion API is stable, authenticated, and well-documented
- **Maintainable:** Notion serves as single source of truth for products
- **Extensible:** Can add web scraper later for automated updates if needed

**Considerations:**
- Products must be updated manually in Notion (acceptable: monthly update frequency)
- Dependent on Notion API availability (acceptable: downtime only affects ingestion, not search)
- URL construction required (Notion may not have portal.evi360.nl URLs stored)

---

### Alternative Approaches Considered

#### Alternative 1: Website Scraping with BeautifulSoup

**Approach:** Build custom scraper for portal.evi360.nl/products
- **Pros:**
  - Automated updates possible
  - Direct source of truth (website)
  - No dependency on Notion
- **Cons:**
  - 8-12 hours development time
  - Fragile (breaks if website structure changes)
  - Authentication requirements unknown
  - Rate limiting complexity
- **Why not chosen:** Notion database already exists with structured data; scraping is overkill for static catalog

#### Alternative 2: Store Products as Chunks (User's Initial Request)

**Approach:** Store products in chunks table like guidelines
- **Pros:**
  - Reuses existing ingestion pipeline
  - Simple implementation (treat products as documents)
- **Cons:**
  - Loses product-specific fields (URL, category, compliance_tags)
  - Mixes products and guidelines in same table
  - Cannot use dedicated `search_products()` SQL function
  - No clean way to filter "only products"
- **Why not chosen:** Violates separation of concerns; products table already designed for this purpose

#### Alternative 3: Hybrid Approach (Both Tables)

**Approach:** Store in both products table AND chunks table
- **Pros:**
  - Maximum flexibility
  - Products searchable via both methods
- **Cons:**
  - Duplicate data (storage overhead)
  - Sync complexity (keep embeddings in sync)
  - Over-engineered for <100 products
- **Why not chosen:** Unnecessary complexity for MVP; products table sufficient

---

## Trade-offs

### Performance vs. Complexity
- **Decision:** Favor simplicity (Notion extraction) over automation (web scraping)
- **Rationale:** <100 products with monthly update frequency = complexity not justified
- **Impact:** Manual Notion updates acceptable; can add scraper in Phase 2 if needed

### Cost vs. Features
- **Decision:** Descope compliance tags for MVP
- **Rationale:** Saves 2-3 hours development time; tags not critical for semantic search
- **Impact:** Products searchable by description; compliance filtering can be added later

### Time to Market vs. Quality
- **Decision:** Quick MVP (7-10 hours) over comprehensive approach (16-23 hours)
- **Rationale:** Prove product recommendations value before investing in automation
- **Impact:** MVP validates feature; comprehensive approach deferred to Phase 2

### Maintenance vs. Flexibility
- **Decision:** Use dedicated products table (not chunks table)
- **Rationale:** Clean architecture > implementation speed
- **Impact:** Separate ingestion code required, but better long-term maintainability

---

## Resources

### Official Documentation
- **Notion API**: https://developers.notion.com/reference/intro
- **PostgreSQL pgvector**: https://github.com/pgvector/pgvector
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **Pydantic AI**: https://ai.pydantic.dev/

### Technical Articles
- FEAT-002 completion report: `docs/features/FEAT-002_notion-integration/COMPLETION_SUMMARY.md`
- EVI schema additions: `sql/evi_schema_additions.sql`

### Code Examples
- Notion integration pattern: `ingestion/notion_to_markdown.py` (lines 104-162: `fetch_all_guidelines()`)
- Embedding generation: `ingestion/embedder.py`
- Database insertion: `ingestion/ingest.py` (lines for PostgreSQL insert)

### Community Resources
- EVI 360 Products Database: https://www.notion.so/29dedda2a9a081409224e46bd48c5bc6
- Example product: `big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md`

---

## Archon Status

### Knowledge Base Queries

*Archon MCP was available during research:*

✅ **PostgreSQL pgvector documentation**: Available in Archon knowledge base
- Used for vector similarity search patterns
- Confirmed IVFFLAT index configuration best practices

✅ **Pydantic AI documentation**: Available in Archon knowledge base
- Used for tool registration patterns
- Confirmed agent tool decorator usage

✅ **Notion API documentation**: Not in Archon (used existing code patterns from FEAT-002)
- Relied on working implementation from `ingestion/notion_to_markdown.py`
- No additional research needed (existing code sufficient)

⚠️ **OpenAI embeddings**: Partial results in Archon
- Used existing embedder implementation from `ingestion/embedder.py`
- No new embedding patterns needed

### Recommendations for Archon

*Frameworks/docs already in Archon knowledge base (no additions needed):*

The following are already available and were helpful:
1. **Pydantic AI** - Agent framework patterns and tool registration
2. **pgvector** - Vector similarity search optimization

---

## Answers to Open Questions

### Question 1: What is the EVI 360 product catalog URL?
**Answer:** https://www.notion.so/29dedda2a9a081409224e46bd48c5bc6 (Notion database)
**Confidence:** High
**Source:** User clarification + database ID extraction

### Question 2: Should we use products table or chunks table?
**Answer:** Products table (dedicated schema with product-specific fields)
**Confidence:** High
**Source:** Architecture analysis + user confirmation
**Note:** User confirmed: "We can use the dedicated table for products though I do wonder how well retrieving them will work. we will need to test this." → Pilot testing phase added

### Question 3: Does the specialist agent support products?
**Answer:** No - currently disabled with "Geen producten aanbevelen" restriction
**Confidence:** High
**Source:** Code review of `agent/specialist_agent.py` lines 44, 74

### Question 4: Should we implement AI categorization?
**Answer:** No - Notion database already has "type" and "tags" fields
**Confidence:** High
**Source:** User clarification

### Question 5: How should products appear in agent responses?
**Answer:** Automatic when contextually relevant (agent decides based on semantic similarity)
**Confidence:** High
**Source:** User preference selection
**Clarification:** Not "only when requested" - agent proactively shows products when relevant

### Question 6: Can we reuse Notion guidelines ingestion for products?
**Answer:** Reuse the pattern/basis, but create dedicated `ingest_products.py` script
**Confidence:** High
**Source:** User clarification: "it's worth creating a specific notion ingestion for products"
**Rationale:** Different field mapping, different validation logic, cleaner code organization

### Question 7: What are the actual Notion database fields?
**Answer:** id, name, type, tags, visible, URL, price_type (+ others not relevant for MVP)
**Confidence:** High
**Source:** User confirmation
**Note:** User added: "You can do more analysis when we actually connect the DB" → Phase 0 database inspection needed

### Question 8: Should we do pilot testing before full ingestion?
**Answer:** Yes - pilot with 10-20 products to validate retrieval quality
**Confidence:** High
**Source:** User confirmation
**Rationale:** De-risk implementation, validate embedding strategy, measure quality before committing to full build

---

## Critical Uncertainties Remaining (To Resolve During Implementation)

### Category 1: Notion Database Schema Details

**Partially Known:** Fields confirmed (id, name, type, tags, visible, URL, price_type)

**Still Unknown:**
1. **Field formats:**
   - Is `tags` an array or comma-separated string?
   - Is `visible` a boolean or checkbox property?
   - What does `type` categorization look like? (e.g., "Fysio" vs. "Bedrijfsfysiotherapie"?)

2. **Data quality:**
   - How many products have NULL/missing descriptions?
   - Do all products have URLs populated?
   - Are there duplicate products?

3. **Filter strategy:**
   - Should we filter by `visible=true`?
   - What does `price_type` indicate? Should it affect filtering?
   - How many products will remain after filtering?

**Resolution:** Phase 0 database inspection (30 min) - query database to answer these before writing ingestion code

---

### Category 2: Retrieval Quality & Search Strategy

**Critical User Concern:** "I do wonder how well retrieving them will work"

**Unknown:**
1. **Embedding strategy:** Which produces best retrieval quality?
   - Option A: Description only
   - Option B: Name + description
   - Option C: Name + description + type + tags

2. **Search method:** Vector-only or hybrid (vector + Dutch full-text)?
   - Products have shorter text than guidelines - is full-text search useful?
   - Would keyword matching help for specific terms?

3. **Similarity thresholds:**
   - What score indicates "contextually relevant"? (0.7? 0.75? 0.8?)
   - Should threshold vary for explicit requests vs. automatic recommendations?

4. **Quality metrics:**
   - How do we measure "good enough"?
   - What's acceptable relevance rate? (70%? 80%?)
   - What if pilot test shows poor quality?

**Resolution:** Phase 1 pilot testing (2-3 hours) - test multiple strategies, measure quality, choose winning approach

---

### Category 3: Agent Integration & Contextual Relevance

**User Preference:** "Automatic when contextually relevant" (agent decides)

**Unknown:**
1. **Decision logic:** How does agent determine "contextually relevant"?
   - Pure similarity score above threshold?
   - Keyword matching + similarity?
   - LLM decision based on query understanding?

2. **Thresholds:**
   - Minimum similarity for automatic recommendations?
   - Lower threshold for explicit requests?
   - Maximum products to show (always 3, or "up to 3")?

3. **Output formatting:**
   - Dedicated section or inline with guidelines?
   - How much product detail to show?
   - Include similarity scores or hide them?

4. **Failure cases:**
   - What if no products meet threshold?
   - What if all products have similar low scores?
   - Should agent explain why no products shown?

**Resolution:** Phase 3 implementation + iterative refinement based on manual testing

---

### Category 4: Data Validation & Error Handling

**Unknown:**
1. **Validation rules:**
   - Skip products with missing description?
   - Skip products with missing URL?
   - What constitutes "invalid" data?

2. **Error handling:**
   - Log and skip, or fail fast?
   - How to handle embedding API failures?
   - Partial ingestion acceptable, or all-or-nothing?

3. **Data enrichment:**
   - If descriptions are very short, should we enhance them?
   - Combine multiple fields for richer embeddings?

**Resolution:** Define validation rules in Phase 0, implement in Phase 1

---

### Category 5: Implementation Sequencing & Risk Mitigation

**Key Risk:** Retrieval quality may be poor with product descriptions

**Mitigation Strategy:**
1. **Phase 0 (30 min):** Inspect database, understand data quality
2. **Phase 1 (2-3 hours):** Pilot test with 10-20 products
3. **Decision Point:** Only proceed to full ingestion if pilot successful
4. **Plan B:** If quality poor, iterate on embedding strategy or data enrichment before continuing

**Success Criteria for Pilot:**
- Manual validation: >70% of top 3 results are relevant
- Average similarity score: >0.65 for relevant matches
- No critical failures (missing URLs, embedding errors, etc.)

**Rollback Plan:**
- If pilot fails: Do NOT proceed to full ingestion
- Options: Enhance descriptions, try different embedding text, consider hybrid search
- Escalate to user if fundamental data quality issues

---

## Updated Recommendations

### Primary Recommendation: Phased Approach with Pilot Testing (8-12 hours)

**Phase 0: Database Inspection (30 min)**
- Connect to Notion database
- Query field formats, counts, data quality
- Document findings before writing code
- **Decision:** Filter strategy (visible=true?), exact product count

**Phase 1: Pilot Test (2-3 hours)**
- Create dedicated `ingest_products.py` (inspired by, not copied from guidelines ingestion)
- Ingest 10-20 diverse products
- Test 3 embedding strategies
- Measure retrieval quality with 10-15 queries
- **Decision:** Winning embedding strategy, proceed or iterate

**Phase 2: Full Ingestion (1-2 hours) - Conditional**
- Only if Phase 1 successful
- Ingest all products with winning strategy
- Validate data quality

**Phase 3: Agent Integration (2-3 hours)**
- Create product_search_tool
- Update specialist agent (tool registration + prompt)
- Define contextual relevance logic
- Test with real queries

**Phase 4: Testing & Validation (1-2 hours)**
- Manual testing with 15+ queries
- Validate acceptance criteria
- Refine similarity thresholds

**Total Time:** 8-12 hours (increased from 7-10 to account for pilot phase and risk mitigation)

**Key Benefits:**
- **De-risked:** Pilot validates approach before full investment
- **Data-driven:** Embedding strategy chosen based on actual quality metrics
- **Iterative:** Can refine approach if pilot shows issues
- **User concern addressed:** "wonder how well retrieving them will work" → pilot answers this

---

## Next Steps

1. **Architecture Planning:** Create `architecture.md` with phased implementation approach
2. **Acceptance Criteria:** Create `acceptance.md` with pilot test success criteria
3. **Testing Strategy:** Create `testing.md` with pilot test queries and validation approach
4. **Manual Test Guide:** Create `manual-test.md` with retrieval quality checklist
5. **Proceed to Planning:** Run `/plan FEAT-004` with these research findings

---

**Research Complete:** ✅ **ALL UNCERTAINTIES RESOLVED (2025-10-31 FINAL UPDATE)**
**Ready for Planning:** Yes - all decisions made, simplified approach validated
**Key Decisions:**
- Product count: ~60 (not ~100)
- Embedding: Option B (name + description)
- Search: Vector-only
- Validation: Skip if missing name/URL/description
- Agent: Specialist prompt decides when to call products
- Quality optimization: Defer to future phase

**Simplified Approach:** 6-9 hours (no pilot phase needed, decisions made up front)
