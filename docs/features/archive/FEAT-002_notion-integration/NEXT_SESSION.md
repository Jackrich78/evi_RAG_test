# Next Session Quick Start

**Task:** Test ingestion pipeline with Notion guidelines (AC-FEAT-002-005)

## 1-Minute Context

- ✅ We fetched 87 Dutch guidelines from Notion → saved as markdown files
- ✅ Files have YAML frontmatter with metadata (category, URL, summary, tags)
- ⏳ Need to test existing ingestion pipeline processes them correctly
- ⏳ Then test Dutch search queries work

## Quick Commands

**Read full context first:**
```bash
cat docs/features/FEAT-002_notion-integration/STATUS.md
```

**Then run ingestion:**
```bash
source venv/bin/activate
docker-compose up -d  # Start databases
python3 -m ingestion.ingest \
  --documents documents/notion_guidelines \
  --fast \
  --verbose \
  2>&1 | tee /tmp/ingestion_notion.log
```

**Validate results:**
```bash
psql postgresql://postgres:postgres@localhost:5432/evi_rag

-- Check: 87 documents created
SELECT COUNT(*) FROM documents WHERE source LIKE '%notion_guidelines%';

-- Check: Metadata from YAML frontmatter
SELECT title, metadata->>'guideline_category', metadata->>'source_url'
FROM documents WHERE source LIKE '%notion_guidelines%' LIMIT 5;

-- Check: Chunks with embeddings
SELECT COUNT(*) FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.source LIKE '%notion_guidelines%'
AND c.embedding IS NOT NULL;
```

## What to Check

- [ ] All 87 documents in database
- [ ] Metadata (category, URL, summary) in `documents.metadata` JSONB
- [ ] Chunks created with embeddings
- [ ] `tier` column is NULL (expected - tier parsing deferred)
- [ ] No errors during ingestion

## If Issues

**Databases not running:**
```bash
docker-compose ps  # Check status
docker-compose up -d  # Start if needed
```

**Port conflicts:**
```bash
docker stop $(docker ps -q --filter "publish=5432")
docker-compose up -d
```

**Need more context:**
- Full details: `docs/features/FEAT-002_notion-integration/STATUS.md`
- Acceptance criteria: `docs/features/FEAT-002_notion-integration/acceptance.md`
- Implementation: `ingestion/notion_to_markdown.py`

## After Ingestion Works

Test Dutch search queries (AC-FEAT-002-006):
- "veiligheid op de werkplek"
- "beschermingsmiddelen"
- "arbeidsongeschiktheid"

---

**Location of test files:** `documents/notion_guidelines/` (87 markdown files, 9.0 MB)
