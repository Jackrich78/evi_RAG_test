# Acceptance Criteria: Notion Integration

**Feature ID:** FEAT-002
**Created:** 2025-10-25
**Status:** Draft

## Overview

This feature is complete when:
- All ~100 Dutch workplace safety guidelines are fetched from Notion database
- Markdown files are saved to `documents/notion_guidelines/` with proper formatting
- Existing ingestion pipeline successfully processes all guidelines into PostgreSQL
- Search queries in Dutch return relevant guideline chunks

## Functional Acceptance Criteria

### AC-FEAT-002-001: Notion API Authentication

**Given** Notion API token and database ID are configured in `.env`
**When** The fetch script initializes the Notion client
**Then** Authentication succeeds without 401 errors and database access is verified

**Validation:**
- [ ] Script logs "Notion client initialized successfully"
- [ ] No authentication errors in console output
- [ ] Database query returns at least 1 page

**Priority:** Must Have

---

### AC-FEAT-002-002: Fetch All Guidelines

**Given** Notion database contains ~100 workplace safety guideline pages
**When** The fetch script runs `fetch_all_guidelines()`
**Then** All pages are retrieved using pagination without skipping any pages

**Validation:**
- [ ] Script logs total page count matching Notion database count
- [ ] Pagination handles has_more correctly
- [ ] No pages skipped due to pagination errors

**Priority:** Must Have

---

### AC-FEAT-002-003: Block-to-Markdown Conversion

**Given** A Notion page with Dutch content (headings, paragraphs, lists)
**When** The conversion function processes the page blocks
**Then** Markdown file contains proper formatting with Dutch characters preserved

**Validation:**
- [ ] Heading blocks converted to # or ## markers
- [ ] Paragraph blocks converted to plain text
- [ ] List items converted to - or 1. format
- [ ] Dutch special characters (é, ë, ï) display correctly
- [ ] Complex blocks (images, embeds) are handled gracefully (skipped or placeholder)

**Priority:** Must Have

---

### AC-FEAT-002-004: Save Markdown Files

**Given** Markdown content generated from Notion page
**When** The script saves the file to disk
**Then** File is created in `documents/notion_guidelines/` with sanitized filename

**Validation:**
- [ ] Directory `documents/notion_guidelines/` is created if not exists
- [ ] Filename is sanitized (spaces → underscores, special chars removed)
- [ ] File extension is .md
- [ ] File content is UTF-8 encoded markdown

**Priority:** Must Have

---

### AC-FEAT-002-005: Existing Pipeline Integration

**Given** Markdown files exist in `documents/notion_guidelines/`
**When** User runs `python3 -m ingestion.ingest documents/notion_guidelines`
**Then** Existing pipeline processes files without modification or errors

**Validation:**
- [ ] Chunker successfully splits markdown into chunks
- [ ] Embedder generates vectors for all chunks
- [ ] Chunks stored in PostgreSQL documents and chunks tables
- [ ] No pipeline errors related to Notion markdown format

**Priority:** Must Have

---

### AC-FEAT-002-006: Dutch Content Search

**Given** Guidelines are ingested into PostgreSQL
**When** User searches with Dutch query (e.g., "veiligheid", "werkplek", "bescherming")
**Then** Relevant guideline chunks are returned with high similarity scores

**Validation:**
- [ ] Search query in Dutch returns results
- [ ] Results contain expected Dutch keywords
- [ ] Similarity scores are > 0.5 for relevant results
- [ ] No encoding errors in returned content

**Priority:** Must Have

---

## Edge Cases & Error Handling

### AC-FEAT-002-101: Rate Limit Handling

**Scenario:** Notion API returns 429 rate limit error during fetch

**Given** Fetch script is making requests to Notion API
**When** Rate limit is exceeded (3 req/sec)
**Then** Script retries with exponential backoff without crashing

**Validation:**
- [ ] notion-client SDK handles rate limiting automatically
- [ ] Script logs rate limit warnings but continues
- [ ] All pages eventually fetched despite rate limits

**Priority:** Should Have

---

### AC-FEAT-002-102: Invalid Page Content

**Scenario:** Notion page has empty content or malformed blocks

**Given** A Notion page with no content blocks
**When** Conversion function processes the page
**Then** Empty page is skipped gracefully with warning log

**Validation:**
- [ ] Script logs "Warning: Page X has no content, skipping"
- [ ] No crash or exception thrown
- [ ] Other pages continue processing

**Priority:** Should Have

---

### AC-FEAT-002-103: File Write Errors

**Scenario:** Unable to write markdown file (permissions, disk full)

**Given** Script attempts to save markdown file
**When** File write fails due to permissions or disk space
**Then** Clear error message is logged with failed page title

**Validation:**
- [ ] Script catches IOError or OSError
- [ ] Error message includes page title and reason
- [ ] Script continues with remaining pages

**Priority:** Should Have

---

### AC-FEAT-002-104: Database Connection Failure

**Scenario:** PostgreSQL connection fails during ingestion

**Given** Ingestion pipeline attempts to connect to database
**When** Connection fails (wrong credentials, DB down)
**Then** Clear error message shown with troubleshooting steps

**Validation:**
- [ ] Connection error caught and logged
- [ ] Error message includes database host and connection status
- [ ] Script exits gracefully without data corruption

**Priority:** Must Have

---

### AC-FEAT-002-105: Duplicate Page Handling

**Scenario:** Same guideline page fetched multiple times (re-run script)

**Given** Markdown file already exists in `documents/notion_guidelines/`
**When** Fetch script encounters same page again
**Then** Existing file is overwritten (latest version wins)

**Validation:**
- [ ] Duplicate page overwrites existing file
- [ ] Log message: "Overwriting existing file: {filename}"
- [ ] No duplicate chunks created in database (handled by ingestion pipeline)

**Priority:** Should Have

---

## Non-Functional Requirements

### AC-FEAT-002-201: Performance

**Requirement:** Complete end-to-end ingestion within 30 minutes for 100 guidelines

**Criteria:**
- **Fetch Time:** < 10 minutes to fetch all pages from Notion
- **Conversion Time:** < 5 minutes to convert blocks to markdown
- **Ingestion Time:** < 15 minutes for chunking, embedding, and storage

**Validation:**
- [ ] Script logs timestamps for each phase
- [ ] Total execution time measured and logged
- [ ] Performance meets targets on standard hardware

---

### AC-FEAT-002-202: Data Quality

**Requirement:** No data loss during conversion and ingestion

**Criteria:**
- **Content Completeness:** All Dutch text from Notion preserved in markdown
- **Encoding Integrity:** No garbled characters or encoding issues
- **Structural Integrity:** Headings, lists, paragraphs maintain logical structure

**Validation:**
- [ ] Manual inspection of 10 random markdown files shows complete content
- [ ] Dutch special characters render correctly
- [ ] Heading hierarchy preserved (H1, H2, H3)

---

### AC-FEAT-002-203: Logging & Observability

**Requirement:** Clear logging for debugging and monitoring

**Criteria:**
- **Progress Tracking:** Log each page fetched with title and status
- **Error Reporting:** All errors logged with context (page ID, error type)
- **Summary Statistics:** Log final counts (pages fetched, files saved, chunks created)

**Validation:**
- [ ] Console output shows progress bar or page-by-page status
- [ ] Errors are distinguishable from warnings
- [ ] Final summary includes all relevant metrics

---

## Integration Requirements

### AC-FEAT-002-301: Existing Pipeline Compatibility

**Requirement:** No breaking changes to existing `ingestion/ingest.py` pipeline

**Given** Existing pipeline code is unchanged
**When** Notion markdown files are processed
**Then** Pipeline operates identically to processing other markdown files

**Validation:**
- [ ] No code modifications to ingestion/ingest.py
- [ ] No new dependencies added to ingestion pipeline
- [ ] Existing tests for pipeline still pass

---

### AC-FEAT-002-302: Database Schema Compatibility

**Requirement:** Store chunks with tier=NULL (tier parsing deferred)

**Given** Chunks are stored in PostgreSQL
**When** Querying chunks table
**Then** tier column is NULL for all Notion-sourced chunks

**Validation:**
- [ ] SQL query: `SELECT COUNT(*) FROM chunks WHERE tier IS NULL` returns expected count
- [ ] Chunks have proper document_id foreign key
- [ ] Embeddings generated and stored for all chunks

---

## Data Requirements

### AC-FEAT-002-401: Configuration Validation

**Requirement:** Validate required environment variables before execution

**Criteria:**
- **NOTION_API_TOKEN:** Must be non-empty 50+ character string
- **NOTION_GUIDELINES_DATABASE_ID:** Must be 32-character hex string
- **Database credentials:** PostgreSQL connection string valid

**Validation:**
- [ ] Script checks for required env vars at startup
- [ ] Clear error message if any variable missing or malformed
- [ ] Validation runs before making any API calls

---

### AC-FEAT-002-402: Output File Structure

**Requirement:** Markdown files follow consistent naming convention

**Criteria:**
- **Filename format:** `{sanitized_page_title}.md`
- **Sanitization rules:** Lowercase, spaces → underscores, remove special chars
- **Character limit:** Max 100 chars for filename (truncate if needed)
- **Uniqueness:** Append numeric suffix if title collision (e.g., `guideline_1.md`, `guideline_2.md`)

**Validation:**
- [ ] All filenames are valid on Windows, macOS, Linux
- [ ] No filename collisions or overwrites (except intentional re-runs)
- [ ] Filenames are human-readable and descriptive

---

## Acceptance Checklist

### Development Complete
- [ ] All functional criteria met (AC-FEAT-002-001 through AC-FEAT-002-006)
- [ ] All edge cases handled (AC-FEAT-002-101 through AC-FEAT-002-105)
- [ ] Non-functional requirements met (AC-FEAT-002-201 through AC-FEAT-002-203)
- [ ] Integration requirements met (AC-FEAT-002-301 through AC-FEAT-002-302)
- [ ] Data requirements met (AC-FEAT-002-401 through AC-FEAT-002-402)

### Testing Complete
- [ ] Unit tests written and passing (notion_to_markdown.py functions)
- [ ] Integration test written and passing (full fetch + ingest flow)
- [ ] Manual testing completed per manual-test.md
- [ ] Sample markdown files inspected for quality
- [ ] Search validation with Dutch queries successful

### Documentation Complete
- [ ] Code documented (docstrings for all functions)
- [ ] Usage instructions in README.md
- [ ] Configuration guide for .env variables
- [ ] Troubleshooting section for common errors

### Deployment Ready
- [ ] Code reviewed and approved
- [ ] Unit and integration tests passing
- [ ] `documents/notion_guidelines/` directory documented
- [ ] Cleanup procedure documented for re-runs

---

**Appended to `/AC.md`:** No (will append after document complete)
**Next Steps:** Proceed to testing strategy and test stub generation
