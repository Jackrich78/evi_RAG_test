# Global Acceptance Criteria

This file tracks all acceptance criteria across all features in the project. Each criterion has a unique ID in the format `AC-FEAT-XXX-###`.

**Purpose:** Global registry of acceptance criteria for traceability and testing alignment.

**Last Updated:** 2025-10-25

---

## FEAT-002: Notion Integration

### Functional Criteria

- **AC-FEAT-002-001:** Given Notion API token and database ID are configured in `.env`, when the fetch script initializes the Notion client, then authentication succeeds without 401 errors and database access is verified
- **AC-FEAT-002-002:** Given Notion database contains ~100 workplace safety guideline pages, when the fetch script runs `fetch_all_guidelines()`, then all pages are retrieved using pagination without skipping any pages
- **AC-FEAT-002-003:** Given a Notion page with Dutch content (headings, paragraphs, lists), when the conversion function processes the page blocks, then markdown file contains proper formatting with Dutch characters preserved
- **AC-FEAT-002-004:** Given markdown content generated from Notion page, when the script saves the file to disk, then file is created in `documents/notion_guidelines/` with sanitized filename
- **AC-FEAT-002-005:** Given markdown files exist in `documents/notion_guidelines/`, when user runs `python3 -m ingestion.ingest documents/notion_guidelines`, then existing pipeline processes files without modification or errors
- **AC-FEAT-002-006:** Given guidelines are ingested into PostgreSQL, when user searches with Dutch query (e.g., "veiligheid", "werkplek", "bescherming"), then relevant guideline chunks are returned with high similarity scores

### Edge Cases & Error Handling

- **AC-FEAT-002-101:** Given fetch script is making requests to Notion API, when rate limit is exceeded (3 req/sec), then script retries with exponential backoff without crashing
- **AC-FEAT-002-102:** Given a Notion page with no content blocks, when conversion function processes the page, then empty page is skipped gracefully with warning log
- **AC-FEAT-002-103:** Given script attempts to save markdown file, when file write fails due to permissions or disk space, then clear error message is logged with failed page title
- **AC-FEAT-002-104:** Given ingestion pipeline attempts to connect to database, when connection fails (wrong credentials, DB down), then clear error message shown with troubleshooting steps
- **AC-FEAT-002-105:** Given markdown file already exists in `documents/notion_guidelines/`, when fetch script encounters same page again, then existing file is overwritten (latest version wins)

### Non-Functional Requirements

- **AC-FEAT-002-201:** Complete end-to-end ingestion within 30 minutes for 100 guidelines (Fetch: <10 min, Conversion: <5 min, Ingestion: <15 min)
- **AC-FEAT-002-202:** All Dutch text from Notion preserved in markdown with no garbled characters or encoding issues; headings, lists, paragraphs maintain logical structure
- **AC-FEAT-002-203:** Clear logging for debugging - log each page fetched with title/status, all errors with context, final summary with counts (pages fetched, files saved, chunks created)

### Integration Requirements

- **AC-FEAT-002-301:** Given existing pipeline code is unchanged, when Notion markdown files are processed, then pipeline operates identically to processing other markdown files
- **AC-FEAT-002-302:** Given chunks are stored in PostgreSQL, when querying chunks table, then tier column is NULL for all Notion-sourced chunks (tier parsing deferred)

### Data Requirements

- **AC-FEAT-002-401:** Validate required environment variables before execution - NOTION_API_TOKEN (50+ chars), NOTION_GUIDELINES_DATABASE_ID (32-char hex), PostgreSQL credentials valid
- **AC-FEAT-002-402:** Markdown files follow consistent naming - format: `{sanitized_page_title}.md`, sanitization: lowercase, spaces → underscores, remove special chars, max 100 chars, append numeric suffix if collision

---

**Total Acceptance Criteria:** 17 (FEAT-002)
