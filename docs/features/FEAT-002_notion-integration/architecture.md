# Architecture Decision: Notion Integration

**Feature ID:** FEAT-002
**Decision Date:** 2025-10-25
**Status:** Proposed

## Context

EVI 360 needs to ingest ~100 Dutch workplace safety guidelines from their Notion database into the PostgreSQL RAG system. The challenge is converting Notion's block-based API response into markdown text that can flow through the existing ingestion pipeline (chunker → embedder → storage). The MVP approach prioritizes getting a working system quickly while descoping tier-parsing complexity for future iteration.

**Document Storage:** Following the existing pattern (see `big_tech_docs/`), markdown files will be saved to a new `documents/notion_guidelines/` directory that the ingestion pipeline can read from.

## Options Considered

### Option 1: Simple Fetch + Existing Pipeline (Recommended)

**Description:** Create lightweight Notion fetcher that converts blocks to markdown files, saves to `documents/notion_guidelines/`, then reuses 100% of existing `ingestion/ingest.py` pipeline without modification.

**Key Characteristics:**
- Separate fetch step from ingestion step
- Notion API → markdown files → existing pipeline
- No code changes to chunker, embedder, or storage
- Inspectable markdown output for validation

**Example Implementation:**
```python
# ingestion/notion_to_markdown.py (~150 lines)
class NotionToMarkdown:
    async def fetch_and_save():
        pages = await fetch_all_pages()
        for page in pages:
            md = blocks_to_markdown(page.blocks)
            save_file(f"documents/notion_guidelines/{page.title}.md", md)

# Then run existing pipeline:
# python3 -m ingestion.ingest documents/notion_guidelines
```

### Option 2: Integrated Notion Pipeline

**Description:** Build Notion-aware extension to `ingestion/ingest.py` that fetches, converts, and processes in a single flow without intermediate files.

**Key Characteristics:**
- Fetch → convert → chunk → embed → store in one process
- Requires modifying existing `DocumentIngestionPipeline` class
- Memory-efficient (no disk writes)
- Tighter coupling between Notion and ingestion logic

**Example Implementation:**
```python
# Extend ingestion/ingest.py
class NotionIngestionPipeline(DocumentIngestionPipeline):
    async def ingest_from_notion():
        async for page in fetch_pages_stream():
            md = blocks_to_markdown(page.blocks)
            chunks = await self.chunk_document(md, ...)
            # Continue pipeline...
```

### Option 3: Full-Featured Notion Sync System

**Description:** Build comprehensive sync solution with tier parsing, incremental updates, webhook listeners, and automated re-ingestion when Notion content changes.

**Key Characteristics:**
- Detects Dutch tier markers during fetch
- Stores sync state for incremental updates
- Webhooks for real-time Notion → DB sync
- Complex tier-aware chunking logic

**Example Implementation:**
```python
# Multi-file system: fetcher, parser, sync_manager
class NotionSyncManager:
    def sync():
        changes = detect_changes_since_last_sync()
        for change in changes:
            tier_content = parse_tiers(change.blocks)
            tier_aware_chunks = chunk_by_tier(tier_content)
            # Store with tier metadata...
```

## Comparison Matrix

| Criteria | Option 1 | Option 2 | Option 3 |
|----------|----------|----------|----------|
| **Feasibility** | ✅ Very easy (60-90 min) | ⚠️ Moderate (3-4 hours) | ❌ High complexity (12+ hours) |
| **Performance** | ⚠️ Disk I/O overhead | ✅ Memory-efficient | ⚠️ Complex processing overhead |
| **Maintainability** | ✅ Isolated, simple code | ⚠️ Couples Notion to pipeline | ❌ Many moving parts |
| **Cost** | ✅ No new dependencies | ✅ No new dependencies | ⚠️ Infrastructure for webhooks |
| **Complexity** | ✅ One simple script | ⚠️ Pipeline modifications | ❌ Multi-component system |
| **Community/Support** | ✅ Standard patterns | ✅ Standard patterns | ⚠️ Custom architecture |
| **Integration** | ✅ Zero changes to existing code | ⚠️ Modifies existing pipeline | ⚠️ New infrastructure layer |

### Criteria Definitions

- **Feasibility:** Can we implement this with current resources/skills/timeline?
- **Performance:** Will it meet performance requirements (speed, scale, resource usage)?
- **Maintainability:** How easy will it be to modify, debug, and extend over time?
- **Cost:** Financial cost (licenses, services, infrastructure)?
- **Complexity:** Implementation and operational complexity?
- **Community/Support:** Quality of documentation, community, and ecosystem?
- **Integration:** How well does it integrate with existing systems?

## Recommendation

**Chosen Approach:** Option 1 - Simple Fetch + Existing Pipeline

**Rationale:**

This approach gets us a working RAG system in 2-3 hours while maintaining clean separation of concerns. The existing `ingestion/ingest.py` pipeline (483 lines, battle-tested) handles chunking, embedding, and storage perfectly. By saving markdown files to `documents/notion_guidelines/` first, we gain inspectability for debugging and can iterate on the Notion fetcher independently. The disk I/O overhead is negligible for a one-time ingestion of ~100 documents. Most importantly, this approach lets us validate the RAG system end-to-end quickly, then enhance with tier parsing in a future iteration without touching the fetch logic.

### Why Not Other Options?

**Option 2 (Integrated Pipeline):**
- Requires modifying proven ingestion code (risk of regression)
- Memory efficiency gain is minimal for 100 documents
- Harder to debug when fetch and ingestion are coupled

**Option 3 (Full Sync System):**
- Massive scope creep (12+ hours vs. 2-3 hours)
- Tier parsing deferred per MVP decision
- Webhooks/incremental sync not needed for one-time ingestion
- Violates simplicity principle for Phase 1

### Trade-offs Accepted

- **Trade-off 1:** Disk I/O overhead - Acceptable because one-time ingestion is not performance-critical, and inspectable markdown files aid debugging
- **Trade-off 2:** Two-step process (fetch then ingest) - Acceptable because separation enables independent iteration and testing of each component
- **Trade-off 3:** No automatic updates from Notion - Acceptable because requirement is one-time ingestion, and future webhook support can be added without changing this architecture

## Spike Plan

### Step 1: Validate Notion API Connection
- **Action:** Create minimal script to authenticate and fetch 1 page from Notion database
- **Success Criteria:** Successfully retrieve page metadata (title, ID) without errors
- **Time Estimate:** 15 minutes

### Step 2: Test Block-to-Markdown Conversion
- **Action:** Fetch 1 page's blocks and convert to markdown using simple text extraction
- **Success Criteria:** Markdown output contains heading markers (#, ##), paragraphs, and list items; Dutch content preserved
- **Time Estimate:** 30 minutes

### Step 3: Save and Inspect Sample Markdown
- **Action:** Create `documents/notion_guidelines/` directory, save 2-3 sample pages as markdown files
- **Success Criteria:** Files are readable, properly formatted markdown with no garbled Dutch characters
- **Time Estimate:** 15 minutes

### Step 4: Test Existing Pipeline on Sample
- **Action:** Run `python3 -m ingestion.ingest documents/notion_guidelines` on sample files
- **Success Criteria:** Chunks created in database with embeddings, no errors, search returns Dutch content
- **Time Estimate:** 20 minutes

### Step 5: Full Ingestion of ~100 Pages
- **Action:** Fetch all guidelines, save to markdown, run full ingestion
- **Success Criteria:** All pages ingested within 30 minutes, no pagination errors, database query shows expected document count
- **Time Estimate:** 30 minutes

**Total Spike Time:** 110 minutes (1h 50m)

## Implementation Notes

### Architecture Diagram
```
Notion API
    ↓
notion_to_markdown.py (fetch + convert)
    ↓
documents/notion_guidelines/*.md (disk storage)
    ↓
ingestion/ingest.py (existing pipeline)
    ↓
chunks → embeddings → PostgreSQL
```

### Key Components
- **NotionToMarkdown** (ingestion/notion_to_markdown.py): Fetches pages from Notion database, converts blocks to markdown, saves to `documents/notion_guidelines/` directory
- **Existing Ingestion Pipeline** (ingestion/ingest.py): Reused without modification - chunks, embeds, stores markdown files from documents folder
- **PostgreSQL Storage** (via existing db_utils): Stores chunks with `tier=NULL` for MVP (tier parsing deferred)

### Data Flow
1. Create `documents/notion_guidelines/` directory if not exists
2. `NotionToMarkdown.fetch_all_guidelines()` queries Notion database with pagination
3. For each page: `fetch_page_blocks()` retrieves content blocks
4. `blocks_to_markdown()` converts blocks to simple markdown (headings, paragraphs, lists)
5. Save markdown file: `documents/notion_guidelines/{sanitized_title}.md`
6. Run existing pipeline: `python3 -m ingestion.ingest documents/notion_guidelines`
7. Pipeline chunks, embeds, and stores in PostgreSQL as normal

### Technical Dependencies
- `notion-client==2.2.1` (already in requirements.txt)
- `NotionConfig` class (already exists in config/notion_config.py)
- Existing ingestion pipeline (ingestion/ingest.py - no changes needed)
- **Directory:** `documents/notion_guidelines/` (created by fetch script)

### Configuration Required
- `NOTION_API_TOKEN` in .env (user must provide from Notion integration)
- `NOTION_GUIDELINES_DATABASE_ID` in .env (32-char hex from database URL)
- Notion database shared with integration (user action required)

## Risks & Mitigation

### Risk 1: Notion API Rate Limits
- **Impact:** Medium (slower ingestion)
- **Likelihood:** Low (3 req/sec limit is generous for 100 pages)
- **Mitigation:** notion-client SDK handles rate limiting automatically with exponential backoff

### Risk 2: Markdown Conversion Quality
- **Impact:** Low (search works on text content regardless of formatting)
- **Likelihood:** Medium (some complex Notion blocks may not convert perfectly)
- **Mitigation:** Inspect sample output in spike step 3; iterate on conversion logic if Dutch content garbled; complex blocks (tables, embeds) skipped for MVP

### Risk 3: Duplicate Ingestion
- **Impact:** Low (duplicate chunks in database)
- **Likelihood:** Medium (if script run multiple times)
- **Mitigation:** Check if document already exists before re-ingesting; document cleanup procedure in manual-test.md; can delete `documents/notion_guidelines/` folder and re-fetch if needed

## References

- [Research findings]: `docs/features/FEAT-002_notion-integration/research.md`
- [Existing ingestion pipeline]: `ingestion/ingest.py` (483 lines)
- [Document storage pattern]: `big_tech_docs/` directory (reference for markdown file structure)
- [Notion SDK documentation]: https://github.com/ramnes/notion-sdk-py

---

**Decision Status:** Proposed
**Next Steps:** Proceed to acceptance criteria and testing strategy
