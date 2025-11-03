# Manual Testing Guide: Notion Integration

**Feature ID:** FEAT-002
**Created:** 2025-10-25
**Intended Audience:** Non-technical testers, QA, EVI 360 team members

## Overview

This guide provides step-by-step instructions for manually testing the Notion integration feature. The goal is to verify that Dutch workplace safety guidelines can be fetched from Notion and successfully ingested into the RAG system for search.

**Prerequisites:**
- Access to EVI 360 Notion workspace with guidelines database
- Notion API token (from https://www.notion.so/my-integrations)
- Local development environment with project set up
- PostgreSQL database running (via Docker or local install)

**Estimated Time:** 45 minutes for all scenarios

## Test Setup

### Before You Begin

1. **Environment:** Local development machine
2. **Data Reset:** Clear `documents/notion_guidelines/` directory before each test run
3. **Database:** PostgreSQL instance running (check with `docker ps` if using Docker)
4. **Virtual Environment:** Activate venv with `source venv/bin/activate`

### Test Account Setup

**Notion Integration Setup:**
1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name: "EVI 360 RAG Test"
4. Select workspace: EVI 360
5. Copy "Internal Integration Token"

**Database Sharing:**
1. Open EVI 360 guidelines database in Notion
2. Click "..." menu → "Add connections"
3. Select "EVI 360 RAG Test" integration
4. Copy database ID from URL (32-char hex after last slash)

### Configuration File Setup

**Edit `.env` file:**
```bash
# Add these lines to .env
NOTION_API_TOKEN=secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
NOTION_GUIDELINES_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Verify configuration:**
```bash
cat .env | grep NOTION
```

Expected output: Two lines with NOTION_API_TOKEN and NOTION_GUIDELINES_DATABASE_ID

## Test Scenarios

### Test Scenario 1: Verify Notion API Connection

**Acceptance Criteria:** AC-FEAT-002-001

**Purpose:** Validate Notion credentials and database access

**Steps:**
1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate  # macOS/Linux
   # or: venv\Scripts\activate  # Windows
   ```
   - **Expected:** Terminal prompt shows (venv) prefix

2. **Run connection test script:**
   ```bash
   python3 -c "from config.notion_config import NotionConfig; from notion_client import AsyncClient; import asyncio; config = NotionConfig(); client = AsyncClient(auth=config.api_token); print('Connection successful!')"
   ```
   - **Expected:** Output shows "Connection successful!" with no errors

3. **Verify database access:**
   ```bash
   python3 -c "from ingestion.notion_to_markdown import NotionToMarkdown; import asyncio; ntm = NotionToMarkdown(); asyncio.run(ntm.fetch_all_guidelines()); print('Database accessible')"
   ```
   - **Expected:** No 401 or 404 errors; script completes without crash

**✅ Pass Criteria:**
- No authentication errors (401)
- No "database not found" errors (404)
- Script completes without exceptions

**❌ Fail Scenarios:**
- If "401 Unauthorized": Check NOTION_API_TOKEN in .env is correct
- If "404 Not Found": Verify database ID and that database is shared with integration
- If "ModuleNotFoundError": Run `pip3 install -r requirements.txt`

---

### Test Scenario 2: Fetch Sample Pages

**Acceptance Criteria:** AC-FEAT-002-002, AC-FEAT-002-003, AC-FEAT-002-004

**Purpose:** Fetch 2-3 sample pages and inspect markdown output

**Steps:**
1. **Create output directory:**
   ```bash
   mkdir -p documents/notion_guidelines
   ```
   - **Expected:** Directory created (no error if already exists)

2. **Run fetch script (sample mode):**
   ```bash
   python3 -m ingestion.notion_to_markdown --sample 3
   ```
   - **Expected:** Script logs progress:
     ```
     Fetching sample of 3 pages...
     Page 1/3: Veiligheid op de Werkplek
     Page 2/3: Persoonlijke Beschermingsmiddelen
     Page 3/3: Noodprocedures
     Saved 3 markdown files to documents/notion_guidelines/
     ```

3. **List created files:**
   ```bash
   ls -lh documents/notion_guidelines/
   ```
   - **Expected:** 3 .md files with sanitized filenames

4. **Inspect first markdown file:**
   ```bash
   cat documents/notion_guidelines/veiligheid_op_de_werkplek.md
   ```
   - **Expected:** Readable markdown with:
     - Headings starting with # or ##
     - Paragraphs of Dutch text
     - Lists with - or 1. markers
     - No garbled characters (é, ë, ï should display correctly)

5. **Verify UTF-8 encoding:**
   ```bash
   file documents/notion_guidelines/*.md
   ```
   - **Expected:** All files show "UTF-8 Unicode text"

**✅ Pass Criteria:**
- 3 markdown files created
- Filenames are sanitized (lowercase, underscores, no special chars)
- Dutch characters display correctly
- Markdown formatting is valid (headings, lists, paragraphs)

**❌ Fail Scenarios:**
- If 0 files created: Check database has content and is shared
- If garbled characters: Check encoding (should be UTF-8)
- If markdown malformed: Review block conversion logic in code

---

### Test Scenario 3: Run Existing Ingestion Pipeline

**Acceptance Criteria:** AC-FEAT-002-005, AC-FEAT-002-301

**Purpose:** Verify existing pipeline processes Notion markdown without errors

**Steps:**
1. **Ensure sample files exist from Scenario 2:**
   ```bash
   ls documents/notion_guidelines/*.md | wc -l
   ```
   - **Expected:** Output shows "3" (or number of sample files)

2. **Run ingestion pipeline:**
   ```bash
   python3 -m ingestion.ingest documents/notion_guidelines
   ```
   - **Expected:** Script logs show:
     ```
     Loading documents from documents/notion_guidelines
     Found 3 markdown files
     Chunking documents...
     Generating embeddings...
     Storing in PostgreSQL...
     Ingestion complete: 3 documents, 45 chunks
     ```

3. **Verify database storage:**
   ```bash
   python3 -c "from agent.db_utils import initialize_database, db_pool; import asyncio; async def check(): await initialize_database(); async with db_pool.acquire() as conn: count = await conn.fetchval('SELECT COUNT(*) FROM documents WHERE source LIKE \"%notion_guidelines%\"'); print(f'Documents in DB: {count}'); asyncio.run(check())"
   ```
   - **Expected:** Output shows "Documents in DB: 3"

4. **Check chunks created:**
   ```bash
   python3 -c "from agent.db_utils import initialize_database, db_pool; import asyncio; async def check(): await initialize_database(); async with db_pool.acquire() as conn: count = await conn.fetchval('SELECT COUNT(*) FROM chunks WHERE document_id IN (SELECT id FROM documents WHERE source LIKE \"%notion_guidelines%\")'); print(f'Chunks in DB: {count}'); asyncio.run(check())"
   ```
   - **Expected:** Output shows "Chunks in DB: 45" (or similar count)

**✅ Pass Criteria:**
- Pipeline completes without errors
- Documents stored in PostgreSQL
- Chunks created with embeddings
- No encoding errors in pipeline logs

**❌ Fail Scenarios:**
- If "Connection refused": Start PostgreSQL (docker-compose up -d postgres)
- If "No such file": Verify documents directory path
- If encoding errors: Check markdown files are UTF-8

---

### Test Scenario 4: Validate Dutch Search

**Acceptance Criteria:** AC-FEAT-002-006

**Purpose:** Test search with Dutch queries returns relevant results

**Steps:**
1. **Ensure ingestion completed (Scenario 3):**
   - Check that documents and chunks exist in database

2. **Test search with Dutch query 1: "veiligheid"**
   ```bash
   python3 cli.py query "veiligheid werkplek"
   ```
   - **Expected:** Results returned with Dutch text containing "veiligheid" or "werkplek"
   - **Expected:** Similarity scores > 0.5 for relevant results

3. **Test search with Dutch query 2: "bescherming"**
   ```bash
   python3 cli.py query "persoonlijke beschermingsmiddelen PPE"
   ```
   - **Expected:** Results about personal protective equipment (PPE)

4. **Test search with Dutch query 3: "noodprocedures"**
   ```bash
   python3 cli.py query "noodprocedures evacuatie"
   ```
   - **Expected:** Results about emergency procedures

5. **Inspect result quality:**
   - Check that Dutch characters display correctly in results
   - Verify results are relevant to query
   - Confirm similarity scores are reasonable (0.5-0.9 range)

**✅ Pass Criteria:**
- All 3 Dutch queries return results
- Results contain expected Dutch keywords
- Dutch characters display without encoding issues
- Similarity scores indicate relevance (> 0.5)

**❌ Fail Scenarios:**
- If no results: Check embeddings were generated
- If garbled text: Check UTF-8 encoding throughout pipeline
- If irrelevant results: May indicate embedding quality issue (expected for small sample)

---

### Test Scenario 5: Full Ingestion (100 Guidelines)

**Acceptance Criteria:** AC-FEAT-002-002, AC-FEAT-002-201

**Purpose:** Fetch all ~100 guidelines and validate performance

**Steps:**
1. **Clear previous test data:**
   ```bash
   rm -rf documents/notion_guidelines/*
   ```
   - **Expected:** Directory emptied

2. **Run full fetch (time it):**
   ```bash
   time python3 -m ingestion.notion_to_markdown --all
   ```
   - **Expected:** Script logs:
     ```
     Fetching all pages from Notion database...
     Progress: 25/100 pages fetched...
     Progress: 50/100 pages fetched...
     Progress: 75/100 pages fetched...
     Progress: 100/100 pages fetched
     Fetch complete: 100 pages in 8m 23s
     Saved 100 markdown files to documents/notion_guidelines/
     ```
   - **Expected:** Total time < 10 minutes

3. **Verify file count:**
   ```bash
   ls documents/notion_guidelines/*.md | wc -l
   ```
   - **Expected:** Output shows "100" (or actual guideline count)

4. **Run full ingestion (time it):**
   ```bash
   time python3 -m ingestion.ingest documents/notion_guidelines
   ```
   - **Expected:** Script logs show all files processed
   - **Expected:** Total time < 20 minutes

5. **Verify total time:**
   - Add fetch time + ingest time
   - **Expected:** Total < 30 minutes

6. **Validate database counts:**
   ```bash
   python3 -c "from agent.db_utils import initialize_database, db_pool; import asyncio; async def check(): await initialize_database(); async with db_pool.acquire() as conn: doc_count = await conn.fetchval('SELECT COUNT(*) FROM documents WHERE source LIKE \"%notion_guidelines%\"'); chunk_count = await conn.fetchval('SELECT COUNT(*) FROM chunks WHERE document_id IN (SELECT id FROM documents WHERE source LIKE \"%notion_guidelines%\")'); print(f'Documents: {doc_count}, Chunks: {chunk_count}'); asyncio.run(check())"
   ```
   - **Expected:** Documents: 100, Chunks: 1500-2500 (depends on guideline size)

**✅ Pass Criteria:**
- All ~100 guidelines fetched
- No pagination errors
- Total ingestion time < 30 minutes
- All documents and chunks in database

**❌ Fail Scenarios:**
- If timeout: Check network connection to Notion
- If rate limit errors: Script should handle with retries (built into SDK)
- If missing pages: Check pagination logic

---

### Test Scenario 6: Markdown Quality Inspection

**Acceptance Criteria:** AC-FEAT-002-202

**Purpose:** Manually inspect markdown files for quality and completeness

**Steps:**
1. **Select 10 random markdown files:**
   ```bash
   ls documents/notion_guidelines/*.md | shuf -n 10
   ```
   - **Expected:** List of 10 random files

2. **For each file, inspect content:**
   ```bash
   cat documents/notion_guidelines/[filename].md
   ```

3. **Check the following:**
   - [ ] Headings use # or ## markers appropriately
   - [ ] Paragraphs are plain text (no HTML tags)
   - [ ] Lists use - or 1. formatting
   - [ ] Dutch special characters (é, ë, ï, ö, ü) display correctly
   - [ ] No Notion-specific syntax (no {{, [[, etc.)
   - [ ] Content is complete (no truncation or missing sections)

4. **Compare to original Notion page:**
   - Open same page in Notion web interface
   - Verify key sections are present in markdown
   - Check that no major content is missing

**✅ Pass Criteria:**
- 10/10 files have valid markdown formatting
- Dutch characters display correctly in all files
- Content matches original Notion pages (90%+ completeness)
- No malformed or corrupted files

**❌ Fail Scenarios:**
- If garbled characters: Check UTF-8 encoding
- If missing content: Review block conversion logic
- If HTML tags present: Fix block conversion to use markdown

---

## Visual & Data Quality Validation

### Overall Quality Check
- [ ] All markdown files are valid UTF-8
- [ ] Filenames follow sanitization rules (lowercase, underscores, no special chars)
- [ ] No duplicate filenames (unless expected from title collisions)
- [ ] File sizes reasonable (1-50 KB per guideline)
- [ ] No empty files (0 bytes)

### Dutch Content Validation
- [ ] Special characters preserved: é, ë, ï, ö, ü, à, è
- [ ] Common Dutch words display correctly: veiligheid, werkplek, bescherming, noodprocedure
- [ ] Markdown formatting doesn't break on Dutch text
- [ ] Search queries in Dutch return relevant results

### Performance Validation
- [ ] Fetch time < 10 minutes for 100 pages
- [ ] Conversion time negligible (< 1 second per page)
- [ ] Ingestion time < 20 minutes for 100 pages
- [ ] Total end-to-end time < 30 minutes

## Error Recovery Testing

### Test: Re-run Fetch Script

**Purpose:** Verify handling of duplicate pages

**Steps:**
1. Run fetch script twice without clearing directory
2. Check that existing files are overwritten (not duplicated)
3. Verify log message: "Overwriting existing file: [filename]"

**Expected:** Files are updated, no duplicates created

---

### Test: Handle Empty Notion Pages

**Purpose:** Verify graceful handling of pages with no content

**Steps:**
1. Create empty page in Notion database
2. Run fetch script
3. Check log for warning: "Page [title] has no content, skipping"

**Expected:** Script continues, no crash

---

### Test: Database Connection Failure

**Purpose:** Verify error handling when PostgreSQL is down

**Steps:**
1. Stop PostgreSQL: `docker-compose stop postgres`
2. Run ingestion pipeline
3. Check error message

**Expected:** Clear error message about database connection, script exits gracefully

---

## Bug Reporting

**If You Find a Bug, Report:**
1. **Title:** Brief description of issue (e.g., "Dutch characters garbled in markdown")
2. **Scenario:** Which test scenario (e.g., "Test Scenario 2: Fetch Sample Pages")
3. **Steps to Reproduce:**
   - Exact commands run
   - Configuration used (.env values if relevant)
4. **Expected Result:** What should have happened
5. **Actual Result:** What actually happened (include error messages)
6. **Files Affected:** Example markdown files or page IDs
7. **Environment:**
   - OS: macOS 14.6, Ubuntu 22.04, Windows 11, etc.
   - Python version: `python3 --version`
   - Notion API version: Check notion-client version in requirements.txt

## Test Completion Checklist

### All Scenarios Complete
- [ ] Test Scenario 1: Notion API Connection - PASS / FAIL
- [ ] Test Scenario 2: Fetch Sample Pages - PASS / FAIL
- [ ] Test Scenario 3: Existing Pipeline Integration - PASS / FAIL
- [ ] Test Scenario 4: Dutch Search Validation - PASS / FAIL
- [ ] Test Scenario 5: Full Ingestion (100 Guidelines) - PASS / FAIL
- [ ] Test Scenario 6: Markdown Quality Inspection - PASS / FAIL

### Additional Checks
- [ ] Error recovery tests complete
- [ ] Performance targets met (< 30 min total)
- [ ] Dutch content quality validated (10 random files inspected)

### Summary
- **Total Scenarios:** 6
- **Passed:** [Y]
- **Failed:** [Z]
- **Bugs Filed:** [Number and description]

**Overall Assessment:**
- [ ] ✅ Feature is ready for production use
- [ ] ⚠️ Feature has minor issues (specify below)
- [ ] ❌ Feature has blocking issues (specify below)

**Tester Sign-off:**
- **Name:** [Tester name]
- **Date:** [Testing completion date]
- **Notes:** [Any additional observations or recommendations]

---

**Next Steps:**
- If all tests pass: Feature approved for deployment
- If bugs found: Development team will fix and retest affected scenarios
- Update this document if feature changes significantly or new edge cases discovered
