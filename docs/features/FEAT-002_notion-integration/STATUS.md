# FEAT-002 Status: Next Session Kickoff Brief

**Last Updated:** 2025-10-26
**Current Phase:** MVP Implementation - Testing Ingestion Pipeline
**Next Task:** AC-FEAT-002-005 (Existing Pipeline Integration)

---

## Quick Context

FEAT-002 is implementing Notion integration to fetch 87 Dutch workplace safety guidelines and ingest them into the PostgreSQL RAG system.

**Approach Taken:** MVP (Simple Fetch + Existing Pipeline)
- We chose to defer tier parsing (3-tier structure detection)
- Focus: Get working end-to-end pipeline first
- Then decide if tier parsing is needed based on search quality

---

## What's Been Completed ✅

### 1. Notion Fetcher Implementation
**File:** `ingestion/notion_to_markdown.py`

**What it does:**
- Fetches pages from Notion database with filters:
  - `Status = "Latest"`
  - `Add to KB? = True`
- Extracts metadata from Notion properties
- Converts Notion blocks to markdown
- Saves with YAML frontmatter for metadata

**Filters Applied:**
```python
filter={
    'and': [
        {'property': 'Status', 'status': {'equals': 'Latest'}},
        {'property': 'Add to KB?', 'checkbox': {'equals': True'}}
    ]
}
```

**Metadata Extracted:**
- `title` - Dutch title from `Page_title` property
- `source_url` - URL from `URL` property
- `summary` - Dutch summary from `page_summary_nl` (~293 chars)
- `guideline_category` - Derived from URL (NVAB, UWV, Arboportaal, etc.)
- `tags` - From `Tags` multi_select
- `status` - Should all be "Latest"
- `notion_page_id` - Page UUID
- `fetched_at` - Timestamp

**Category Mapping Logic:**
```python
def extract_category_from_url(url: str) -> str:
    if 'nvab-online.nl' in url: return 'NVAB'
    elif 'stecr.nl' in url: return 'STECR'
    elif 'uwv.nl' in url: return 'UWV'
    elif 'arboportaal.nl' in url: return 'Arboportaal'
    elif 'wikipedia.org' in url: return 'Wikipedia'
    elif url.startswith('http'): return 'External'
    else: return 'Manual'
```

### 2. Files Created
**Location:** `documents/notion_guidelines/`

**Count:** 87 markdown files (exactly as expected)

**Category Distribution:**
- 57 NVAB (Dutch occupational health guidelines)
- 19 UWV (Dutch social security/unemployment)
- 7 Arboportaal (Workplace safety portal)
- 2 Manual (internal/custom documents)
- 1 Wikipedia
- 1 External

**Total Size:** 9.0 MB

**Sample File Structure:**
```yaml
---
title: "Richtlijn omgaan met medische gegevens (KNMG)"
source_url: "https://nvab-online.nl/kennisbank/richtlijn-omgaan-met-medische-gegevens/"
summary: "In de KNMG-richtlijn omgaan met medische gegevens..."
guideline_category: "NVAB"
tags: ['Externe richtlijn']
status: "Latest"
notion_page_id: "26cedda2-a9a0-8116-acc2-d35b0c1c5b93"
fetched_at: "2025-10-26"
---

# Richtlijn omgaan met medische gegevens (KNMG)

[Markdown content here...]
```

### 3. Acceptance Criteria Met

✅ **AC-FEAT-002-001:** Notion API Authentication
✅ **AC-FEAT-002-002:** Fetch All Guidelines (87 pages with correct filters)
✅ **AC-FEAT-002-003:** Block-to-Markdown Conversion (Dutch characters preserved)
✅ **AC-FEAT-002-004:** Save Markdown Files (with YAML frontmatter)

---

## What's NEXT (Current Task) ⏳

### AC-FEAT-002-005: Existing Pipeline Integration

**Objective:** Test that the existing ingestion pipeline processes Notion markdown files correctly.

**What needs to happen:**
1. Run existing ingestion pipeline on Notion markdown files
2. Verify chunks are created in PostgreSQL
3. Verify embeddings are generated
4. Verify YAML frontmatter flows into `documents.metadata` JSONB field

**Command to run:**
```bash
source venv/bin/activate
python3 -m ingestion.ingest --documents documents/notion_guidelines --verbose
```

**What to check after ingestion:**

1. **Documents created:**
```sql
SELECT COUNT(*) FROM documents WHERE source LIKE '%notion_guidelines%';
-- Expected: 87
```

2. **Metadata captured:**
```sql
SELECT
    title,
    metadata->>'guideline_category' as category,
    metadata->>'source_url' as url,
    metadata->>'summary' as summary
FROM documents
WHERE source LIKE '%notion_guidelines%'
LIMIT 3;
-- Expected: All fields populated from YAML frontmatter
```

3. **Chunks created:**
```sql
SELECT COUNT(*) FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%';
-- Expected: Thousands of chunks (depends on chunking config)
```

4. **Embeddings generated:**
```sql
SELECT COUNT(*) FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%'
AND c.embedding IS NOT NULL;
-- Expected: Same as chunk count (100% should have embeddings)
```

5. **Tier column status:**
```sql
SELECT DISTINCT tier FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%';
-- Expected: NULL (tier parsing deferred in MVP)
```

**Validation Checklist:**
- [ ] Ingestion completes without errors
- [ ] All 87 documents in database
- [ ] YAML frontmatter → `metadata` JSONB (category, URL, summary, tags)
- [ ] Chunks created for all documents
- [ ] Embeddings generated (100% of chunks)
- [ ] `tier` column is NULL for all chunks (expected)

---

## What's After This

### AC-FEAT-002-006: Dutch Content Search

**Objective:** Test that Dutch search queries return relevant results.

**Test queries to try:**
```python
# Sample Dutch queries:
- "veiligheid op de werkplek"
- "beschermingsmiddelen"
- "arbeidsongeschiktheid"
- "werkdruk en stress"
- "medische gegevens privacy"
```

**What to validate:**
- Search returns relevant chunks
- Dutch language processing works correctly
- Similarity scores are reasonable (> 0.5 for relevant results)

---

## Important Files to Reference

### Planning Documentation
1. **PRD:** `docs/features/FEAT-002_notion-integration/prd.md`
   - Original scope (includes tier parsing - deferred)
   - Success criteria
   - Technical notes

2. **Architecture:** `docs/features/FEAT-002_notion-integration/architecture.md`
   - MVP approach chosen (Option 1: Simple Fetch + Existing Pipeline)
   - Data flow diagram
   - Trade-offs accepted

3. **Acceptance Criteria:** `docs/features/FEAT-002_notion-integration/acceptance.md`
   - All 17 acceptance criteria
   - Validation steps for each

4. **Global AC:** `AC.md`
   - Quick reference for all acceptance criteria

### Implementation Files
1. **Notion Fetcher:** `ingestion/notion_to_markdown.py` (460 lines)
   - Complete implementation with filters and metadata extraction

2. **Notion Config:** `config/notion_config.py`
   - Configuration class for Notion API

3. **Existing Pipeline:** `ingestion/ingest.py`
   - Already handles YAML frontmatter extraction (lines 307-329)
   - Stores in `documents.metadata` JSONB field

### Database Schema
1. **Base Schema:** `sql/schema.sql`
   - `documents` table with `metadata JSONB`
   - `chunks` table with `metadata JSONB`

2. **EVI Extensions:** `sql/evi_schema_additions.sql`
   - `chunks.tier` column (will be NULL for now)
   - Dutch language support in `hybrid_search` function

### Test Data
**Location:** `documents/notion_guidelines/`
- 87 markdown files ready for ingestion
- All have YAML frontmatter with metadata
- Total 9.0 MB of Dutch content

---

## Key Decisions Made

### 1. MVP Approach (Deferred Tier Parsing)
**Decision:** Implement simple fetch-to-markdown pipeline first, defer tier parsing.

**Rationale:**
- Get working end-to-end system faster (2-3 hours vs 12+ hours)
- Existing chunker may work fine without tier-specific logic
- Can add tier parsing later if search quality requires it

**Impact:**
- `chunks.tier` will be NULL for all Notion-sourced chunks
- All content chunked using existing semantic chunker
- No tier-based filtering in search (yet)

### 2. YAML Frontmatter for Metadata
**Decision:** Use YAML frontmatter to pass Notion metadata into ingestion pipeline.

**Rationale:**
- Existing pipeline already parses YAML frontmatter
- Automatically flows into `documents.metadata` JSONB
- No code changes needed to ingestion pipeline
- Clean separation of concerns

**Impact:**
- Metadata queryable via `metadata->>'field_name'`
- Can filter/search by category, URL, tags in SQL

### 3. Category Derived from URL
**Decision:** Extract guideline category from source URL pattern.

**Rationale:**
- NVAB, UWV, Arboportaal are identifiable by domain
- Provides useful filtering/grouping capability
- Simple pattern matching logic

**Impact:**
- Added `guideline_category` field to YAML frontmatter
- Can query by source organization

---

## Common Issues & Solutions

### Issue: Databases not running
**Solution:**
```bash
docker-compose up -d
docker-compose ps  # Both should show (healthy)
```

### Issue: Port 5432 already in use
**Solution:**
```bash
docker stop $(docker ps -q --filter "publish=5432") 2>/dev/null
docker-compose up -d
```

### Issue: OpenAI API key needed for embeddings
**Check:**
```bash
grep -E "LLM_API_KEY|EMBEDDING_API_KEY" .env
```

### Issue: Long ingestion time
**Expected:** ~15-30 minutes for 87 files (depends on API rate limits for embeddings)

**Monitor progress:**
```bash
# In another terminal:
tail -f /tmp/ingestion.log
```

---

## Environment Setup

### Required Services
```bash
# PostgreSQL + Neo4j must be running
docker-compose ps
# Expected: evi_rag_postgres (healthy), evi_rag_neo4j (healthy)
```

### Virtual Environment
```bash
source venv/bin/activate
# Or on Windows: venv\Scripts\activate
```

### Database Connection
```bash
# PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/evi_rag

# Or via Python:
python3 -c "
import asyncio
from agent.db_utils import initialize_database, db_pool
asyncio.run(initialize_database())
print('✅ Database connected')
"
```

---

## Questions for Next Session

1. **Should we run ingestion with or without knowledge graph building?**
   - `--fast` flag skips Neo4j graph building (faster)
   - Without flag: builds relationships (slower, more complete)

2. **Should we clean existing data first?**
   - `--clean` flag removes existing documents/chunks
   - Without flag: appends to existing data

3. **Do we want verbose logging?**
   - `--verbose` flag for detailed progress
   - Without flag: standard INFO logging

---

## Recommended Next Command

**Start with safe test run (fast mode, verbose):**
```bash
source venv/bin/activate
docker-compose up -d  # Ensure databases running
python3 -m ingestion.ingest \
  --documents documents/notion_guidelines \
  --fast \
  --verbose \
  2>&1 | tee /tmp/ingestion_notion.log
```

**Then validate in PostgreSQL:**
```bash
psql postgresql://postgres:postgres@localhost:5432/evi_rag

-- Check documents created
SELECT COUNT(*) FROM documents WHERE source LIKE '%notion_guidelines%';

-- Check metadata
SELECT title, metadata->>'guideline_category', metadata->>'source_url'
FROM documents
WHERE source LIKE '%notion_guidelines%'
LIMIT 5;

-- Check chunks
SELECT COUNT(*) FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%';
```

---

## Success Criteria for This Session

At the end of testing AC-FEAT-002-005, you should have:

✅ All 87 Notion guidelines ingested into PostgreSQL
✅ YAML frontmatter metadata in `documents.metadata` JSONB field
✅ Chunks created with embeddings (100% coverage)
✅ `tier` column NULL (expected for MVP)
✅ No ingestion errors
✅ Ready to test Dutch search queries (AC-FEAT-002-006)

---

## Documentation That Needs Updating (After Completion)

Once AC-FEAT-002-005 and AC-FEAT-002-006 are validated:

1. **PRD:** Update status to "MVP Complete", note tier parsing deferred
2. **Architecture:** Add actual performance metrics (ingestion time, chunk counts)
3. **Acceptance Criteria:** Check off completed ACs
4. **IMPLEMENTATION_PROGRESS.md:** Update FEAT-002 status

---

**Ready to proceed with AC-FEAT-002-005!** 🚀
