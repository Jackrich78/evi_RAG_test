# PRD: FEAT-002 - Notion-to-Database Pipeline

**Feature ID:** FEAT-002
**Phase:** 2 (Data Ingestion)
**Status:** 🔄 In Progress
**Priority:** High
**Owner:** TBD

---

## Problem Statement

Fetch ~100 Dutch workplace safety guidelines from EVI 360's Notion database and ingest them into the local PostgreSQL knowledge base. The guidelines have a 3-tier structure (Summary → Key Facts → Full Details) that must be preserved during chunking and storage.

**Challenge:** Notion API returns pages as blocks (not plain text), requiring parsing logic. The 3-tier structure must be detected from Dutch heading markers and stored with tier metadata for tier-aware search.

---

## Goals

1. **Fetch Guidelines:** Pull all pages from Notion guidelines database
2. **Parse Tiers:** Detect 3-tier structure from Dutch headings
3. **Reuse Pipeline:** Adapt Notion data to existing ingestion pipeline (chunker → embedder → storage)
4. **Preserve Metadata:** Store tier information in `chunks.tier` column
5. **Handle Errors:** Robust error handling for Notion API rate limits and parsing failures

---

## User Stories

### Fetch Guidelines from Notion
**Given** I have Notion API credentials configured in `.env`
**When** I run the Notion fetcher
**Then** All ~100 guideline pages are downloaded with their block content

### Parse 3-Tier Structure
**Given** A Notion page with Dutch headings (## Samenvatting, ## Kerninformatie, ## Volledige Details)
**When** The tier parser processes the page
**Then** Content is split into 3 tiers with correct tier labels (1, 2, 3)

### Chunk by Tier
**Given** Guideline content separated into tiers
**When** The chunker processes each tier
**Then** Tier 1 = 1 chunk, Tier 2 = 3-5 chunks, Tier 3 = 10-20 chunks

### Store with Tier Metadata
**Given** Chunks with tier labels
**When** Stored in PostgreSQL
**Then** `chunks.tier` column contains correct values (1, 2, or 3)

### Search by Tier
**Given** Guidelines ingested with tier metadata
**When** I search using `search_guidelines_by_tier(tier_filter=2)`
**Then** Only Tier 2 chunks are returned (Key Facts, not summaries or full details)

---

## Scope

### In Scope ✅
- **Notion Fetcher** (`ingestion/notion_fetcher.py`):
  - Fetch all pages from Notion database using `notion-client 2.2.1`
  - Handle pagination (100 results per page)
  - Rate limiting: 3 req/sec (Notion API limit)
  - Retry logic with exponential backoff

- **Tier Parser** (`ingestion/tier_parser.py`):
  - Detect Dutch headings: `## Samenvatting`, `## Kerninformatie`, `## Volledige Details`
  - Extract content for each tier
  - Fallback: If tier markers not found, treat entire page as Tier 2

- **Tier-Aware Chunking Adapter** (extend `ingestion/chunker.py`):
  - Tier 1 (Summary): Keep as single chunk (~50-150 words)
  - Tier 2 (Key Facts): Chunk by sections (3-5 chunks, ~200-500 words each)
  - Tier 3 (Full Details): Semantic chunking (10-20 chunks, ~500-1000 words each)
  - Add `{"tier": 1|2|3}` to chunk metadata

- **Storage** (reuse `ingestion/ingest.py`):
  - Store tier value in `chunks.tier` column
  - Link all tier chunks to same `document_id`
  - Generate embeddings for all chunks (reuse existing embedder)

### Out of Scope ❌
- Manual guideline editing or validation (one-time ingestion only)
- Automatic updates from Notion (future enhancement)
- Knowledge graph relationships (deferred to future phase)
- Image extraction from Notion pages

---

## Success Criteria

**Fetching:**
- ✅ All ~100 guidelines fetched from Notion database
- ✅ No pages skipped due to pagination errors
- ✅ Rate limiting respected (no 429 errors)

**Parsing:**
- ✅ Tier detection accuracy: 100% for pages with clear headings
- ✅ Fallback handling: Pages without tier markers processed as Tier 2
- ✅ No content lost during tier splitting

**Chunking:**
- ✅ Tier 1: Exactly 1 chunk per guideline
- ✅ Tier 2: 3-7 chunks per guideline (average 5)
- ✅ Tier 3: 10-25 chunks per guideline (average 15)
- ✅ All chunks have `tier` value in metadata

**Storage:**
- ✅ All chunks stored in PostgreSQL with `chunks.tier` populated
- ✅ Embeddings generated for 100% of chunks
- ✅ `search_guidelines_by_tier(tier_filter=1)` returns only Tier 1 chunks
- ✅ `search_guidelines_by_tier(tier_filter=2)` returns only Tier 2 chunks

**Performance:**
- ✅ Ingestion completes in < 30 minutes for 100 guidelines
- ✅ No duplicate chunks created

---

## Dependencies

**Infrastructure:**
- ✅ PostgreSQL 17 + pgvector with tier column (FEAT-001 complete)
- ✅ `NotionConfig` class already implemented

**External Services:**
- Notion API token and database ID configured in `.env`
- OpenAI API key for embeddings (already configured)

**Libraries:**
- `notion-client==2.2.1` (add to requirements.txt)
- `pydantic>=2.0` (already installed)

---

## Technical Notes

**Notion API Structure:**
```python
# Notion pages have:
- page_id (UUID)
- properties (title, tags, etc.)
- children (blocks of content)

# Block types:
- heading_2, heading_3 (for tier markers)
- paragraph (main content)
- bulleted_list_item, numbered_list_item
```

**Dutch Tier Markers:**
```
## Samenvatting          → Tier 1
## Kerninformatie        → Tier 2
## Volledige Details     → Tier 3
```

**Chunking Strategy:**
```python
if tier == 1:
    # Single chunk - keep entire summary together
    chunks = [entire_tier_content]
elif tier == 2:
    # Chunk by sections (H3 headings or paragraphs)
    chunks = split_by_sections(content)
elif tier == 3:
    # Semantic chunking (reuse existing SemanticChunker)
    chunks = semantic_chunker.chunk(content)
```

**Reuse Existing Code:**
- ✅ `ingestion/chunker.py` - Semantic chunking logic
- ✅ `ingestion/embedder.py` - Embedding generation
- ✅ `ingestion/ingest.py` - Orchestration and storage
- ✅ `agent/db_utils.py` - Database operations

---

## Implementation Plan

### Step 1: Notion Fetcher (4-6 hours)
**File:** `ingestion/notion_fetcher.py`

```python
class NotionFetcher:
    async def fetch_all_guidelines() -> List[NotionPage]:
        """Fetch all pages from Notion database."""

    async def fetch_page_content(page_id: str) -> Dict:
        """Fetch full content (blocks) for a page."""

    def blocks_to_markdown(blocks: List) -> str:
        """Convert Notion blocks to markdown."""
```

### Step 2: Tier Parser (3-4 hours)
**File:** `ingestion/tier_parser.py`

```python
class TierParser:
    def parse_tiered_content(markdown: str) -> TieredGuideline:
        """Extract 3-tier structure from markdown."""

    def detect_tier_markers(content: str) -> Dict[int, int]:
        """Find positions of tier heading markers."""

    def extract_tier(content: str, start: int, end: int) -> str:
        """Extract content for a specific tier."""
```

### Step 3: Tier-Aware Chunking Adapter (2-3 hours)
**Extend:** `ingestion/chunker.py`

Add `tier` parameter to `chunk_document()` method:
```python
async def chunk_document(
    content: str,
    title: str,
    source: str,
    metadata: Dict,
    tier: Optional[int] = None  # NEW
) -> List[DocumentChunk]:
```

### Step 4: Integration (2-3 hours)
**File:** `ingestion/ingest_notion.py`

Orchestrate: Fetch → Parse → Chunk → Embed → Store

### Step 5: Testing (3-4 hours)
- Unit tests for tier parser (Dutch heading detection)
- Integration test with 5 sample Notion pages
- Validation: Check tier distribution in database

---

## Testing Strategy

**Unit Tests:**
- `tests/ingestion/test_notion_fetcher.py` - Mock Notion API responses
- `tests/ingestion/test_tier_parser.py` - Test Dutch heading detection
- `tests/ingestion/test_tier_chunking.py` - Verify chunk counts per tier

**Integration Tests:**
- Fetch 5 sample guidelines from Notion
- Verify tier distribution (1 Tier 1 chunk, 3-5 Tier 2 chunks, 10-20 Tier 3 chunks)
- Query `search_guidelines_by_tier()` for each tier and validate results

**Manual Testing:**
- Run full ingestion on ~100 guidelines
- Spot-check 10 random guidelines for correct tier assignment
- Measure ingestion time

---

## Next Steps

1. Add `notion-client==2.2.1` to requirements.txt
2. Configure Notion API credentials in `.env` (get from user)
3. Implement Notion fetcher
4. Implement tier parser with Dutch heading detection
5. Extend chunker for tier-aware chunking
6. Create integration script `ingest_notion.py`
7. Test with 5 sample guidelines
8. Run full ingestion on 100 guidelines
9. Validate tier distribution in database

---

**Last Updated:** 2025-10-25
**Status:** 🔄 Ready to Implement
**Estimated Effort:** 14-20 hours
