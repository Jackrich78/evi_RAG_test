# Research Findings: FEAT-002 - Notion Integration (MVP)

**Feature ID:** FEAT-002
**Research Date:** 2025-10-25
**Completed:** 2025-10-26
**Researcher:** Claude Code
**Status:** ✅ Complete - See Final Implementation

**NOTE:** This research informed FEAT-002 planning. The actual implementation was even simpler than researched - pre-fetched markdown files + existing pipeline. See [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) for what was actually built.

---

## Research Questions

Based on PRD open questions and descoped MVP approach:

1. **How to fetch pages from Notion API?** (Notion blocks → markdown conversion)
2. **What markdown conversion strategy?** (Simple vs. complex block handling)
3. **How to integrate with existing pipeline?** (Reuse ingestion/ingest.py)
4. **What's the minimal viable implementation?** (Defer tier parsing to future)

---

## Key Findings

### 1. Notion API Integration

**Official Notion Python SDK:**
- **Library:** `notion-client==2.2.1` (already in requirements.txt ✅)
- **Documentation:** https://github.com/ramnes/notion-sdk-py
- **API Limits:** 3 requests/second (built-in rate limiting)
- **Authentication:** Integration token (configured in `.env.example` ✅)

**Key Methods:**
```python
from notion_client import AsyncClient

# Initialize
notion = AsyncClient(auth=config.api_token)

# Query database for all pages
pages = await notion.databases.query(
    database_id=config.guidelines_database_id,
    page_size=100  # Max per request
)

# Fetch page content (blocks)
blocks = await notion.blocks.children.list(
    block_id=page_id
)
```

**Pagination:**
- Notion returns max 100 results per request
- Use `has_more` and `next_cursor` for pagination
- ~100 guidelines = 1-2 API requests

**Source:** Notion SDK documentation (Retrieved 2025-10-25)

---

### 2. Block-to-Markdown Conversion

**Approach Comparison:**

**Option A: Simple Text Extraction** (Recommended for MVP)
- Extract plain text from all block types
- Convert headings to markdown (#, ##, ###)
- Convert lists to markdown (-, 1.)
- Ignore complex blocks (images, embeds)
- **Pros:** Fast, simple, works immediately
- **Cons:** Loses some formatting
- **Effort:** ~30-60 minutes

**Option B: Full Block Parser**
- Handle all Notion block types
- Preserve rich formatting
- Convert tables, images, embeds
- **Pros:** Complete conversion
- **Cons:** Complex, time-consuming
- **Effort:** ~4-6 hours

**Option C: Use Existing Library** (notion-to-md)
- Third-party library for conversion
- **Pros:** Maintained, feature-complete
- **Cons:** Additional dependency
- **Effort:** ~15 minutes integration

**Recommendation:** **Option A** for MVP - Simple text extraction
- Gets us working fast (60 minutes)
- Good enough for RAG search (text is what matters)
- Can upgrade to Option B/C later if needed

**Source:** Notion SDK block types documentation

---

### 3. Integration with Existing Pipeline

**Current Pipeline (✅ Already Working):**

File: `ingestion/ingest.py` (483 lines, battle-tested)

```python
# Existing flow:
DocumentIngestionPipeline:
  ├─ chunk_document()      # SemanticChunker (517 lines)
  ├─ embed_chunks()        # EmbeddingGenerator (417 lines)
  └─ save_to_postgres()    # Stores in documents + chunks tables
```

**Integration Strategy:**

```
Notion API → notion_to_markdown.py → Save to /documents/notion_guidelines/*.md
                                                      ↓
                                    Existing ingestion/ingest.py reads files
                                                      ↓
                                    Chunks → Embeds → PostgreSQL
```

**Key Decision:** **Separate fetch from ingestion**
- Fetch Notion → Save markdown files locally
- Run existing `python3 -m ingestion.ingest --documents documents/notion_guidelines`
- **Benefits:**
  - Can inspect markdown before ingesting
  - Can re-run ingestion without re-fetching
  - Reuses 100% of existing pipeline code
  - Can ingest incrementally (test with 2-3 pages first)

**Source:** Existing codebase analysis (ingestion/ingest.py)

---

### 4. Tier Handling (Descoped for MVP)

**MVP Decision:** Ignore tier structure initially

**Current State:**
- Database has `chunks.tier` column (✅ exists, nullable)
- SQL function `search_guidelines_by_tier()` exists (✅ works)
- Pydantic models `TieredGuideline` exist (✅ defined)

**MVP Approach:**
- Fetch all Notion pages as plain markdown
- Store in PostgreSQL with `chunks.tier = NULL`
- Search works fine with tier=NULL (hybrid_search ignores it)

**Future Enhancement (Phase 3):**
- Add tier parser (`ingestion/tier_parser.py`)
- Detect Dutch headings (## Samenvatting, ## Kerninformatie, ## Volledige Details)
- Update existing chunks with tier values
- Enable tier-aware search

**Rationale:** Get working RAG system NOW, optimize tier search LATER

---

## Recommendations

### Chosen Approach: Ultra-Simple MVP

**Architecture:**
1. **Create** `ingestion/notion_to_markdown.py` (~150 lines)
   - Fetch pages from Notion database
   - Convert blocks to simple markdown
   - Save to `/documents/notion_guidelines/{page_title}.md`

2. **Reuse** existing `ingestion/ingest.py` (unchanged!)
   - Run: `python3 -m ingestion.ingest --documents documents/notion_guidelines`
   - Chunks, embeds, stores automatically

3. **Test** with 2-3 sample pages first
   - Verify markdown looks reasonable
   - Verify ingestion works
   - Then run full 100-page ingestion

**Why This Approach:**
- ✅ Minimal code (150 lines, not 500+)
- ✅ Reuses existing pipeline 100%
- ✅ Can iterate quickly (test → fix → rerun)
- ✅ Working RAG system in 2-3 hours
- ✅ Foundation for future tier optimization

---

## Trade-offs Accepted

**What We're Giving Up (For Now):**
- ❌ No tier-aware chunking (chunks.tier = NULL)
- ❌ No tier-based search (search works, just not filtered by tier)
- ❌ No rich Notion formatting (tables, images, embeds)
- ❌ No automatic updates from Notion (one-time fetch)

**Why It's Acceptable:**
- 🎯 Priority: Get working RAG system FAST
- 🎯 Text content is what matters for search
- 🎯 Can add tier parsing in future session (2-3 hours)
- 🎯 Can enhance markdown conversion later if needed

---

## Implementation Notes

### Notion Block Types (Simplified Handling)

**Handle These:**
- `heading_1`, `heading_2`, `heading_3` → `#`, `##`, `###`
- `paragraph` → Plain text
- `bulleted_list_item` → `- Item`
- `numbered_list_item` → `1. Item`

**Ignore These (MVP):**
- `image`, `file` → Skip (add "[Image]" placeholder)
- `table` → Extract as plain text rows
- `code` → Preserve as code block
- `quote` → Convert to `> Quote`
- `embed`, `bookmark` → Skip

### Error Handling

**Notion API Errors:**
- **429 Rate Limit:** Built-in retry with exponential backoff (notion-client handles this)
- **401 Unauthorized:** Check API token in `.env`
- **404 Database Not Found:** Verify database ID and sharing settings

**Markdown Conversion:**
- Unknown block type → Log warning, skip block
- Empty content → Skip silently
- Malformed blocks → Extract what's possible, continue

### Testing Strategy

**Phase 1: Validation (15 min)**
1. Test Notion API connection
2. Fetch 1 page, print JSON
3. Verify authentication works

**Phase 2: Sample Pages (30 min)**
1. Fetch 2-3 sample pages
2. Convert to markdown
3. Inspect output manually
4. Verify Dutch content preserved

**Phase 3: Full Ingestion (45 min)**
1. Fetch all ~100 guidelines
2. Save to `/documents/notion_guidelines/`
3. Run existing ingestion pipeline
4. Test search with Dutch queries

---

## Technical Dependencies

**Already Configured:**
- ✅ `notion-client==2.2.1` in requirements.txt
- ✅ `NotionConfig` class in `config/notion_config.py`
- ✅ `.env.example` has Notion credentials template
- ✅ PostgreSQL schema supports tier column (nullable)
- ✅ Existing ingestion pipeline tested and working

**User Must Provide:**
- Notion API token (from https://www.notion.so/my-integrations)
- Notion database ID (32-char hex from database URL)
- Database shared with integration

---

## Risks & Mitigation

### Risk 1: Notion API Rate Limits
- **Impact:** Medium (slower ingestion)
- **Likelihood:** Low (3 req/sec is generous for 100 pages)
- **Mitigation:** Use notion-client's built-in rate limiting

### Risk 2: Markdown Quality Issues
- **Impact:** Low (search works on text content)
- **Likelihood:** Medium (some formatting may be lost)
- **Mitigation:** Inspect sample output, iterate if needed

### Risk 3: Missing Tier Structure
- **Impact:** Low (tier column exists but unused)
- **Likelihood:** Certain (by design for MVP)
- **Mitigation:** Phase 2 enhancement planned

---

## Resources

**Official Documentation:**
- Notion API Reference: https://developers.notion.com/reference/intro (Retrieved 2025-10-25)
- notion-client SDK: https://github.com/ramnes/notion-sdk-py (Retrieved 2025-10-25)

**Project Files:**
- Existing ingestion pipeline: `ingestion/ingest.py` (483 lines, reviewed 2025-10-25)
- Notion config: `config/notion_config.py` (complete, reviewed 2025-10-25)
- Database schema: `sql/evi_schema_additions.sql` (tier column exists)

**Code Examples:**
- Notion pagination: notion-client documentation
- Block traversal: Notion API reference
- Markdown conversion: Standard markdown spec

---

## Next Steps

**Ready for Planning:**
1. Architecture decision: Simple fetch-and-store vs. complex parsing
2. Acceptance criteria: API connection, markdown conversion, ingestion success
3. Testing strategy: Unit tests for block conversion, integration test for full flow
4. Manual testing: Inspect markdown output, test search queries

**Estimated Effort (MVP):**
- notion_to_markdown.py: 60-90 min
- Testing (sample pages): 30 min
- Full ingestion: 15 min
- Search validation: 15 min
- **Total: 2-2.5 hours**

---

**Status:** ✅ Research Complete - Ready for `/plan FEAT-002`
**Recommendation:** Proceed with ultra-simple MVP approach
**Decision:** Defer tier parsing to future phase, focus on working RAG system
