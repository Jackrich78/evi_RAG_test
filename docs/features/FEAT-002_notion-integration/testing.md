# Testing Strategy: Notion Integration

**Feature ID:** FEAT-002
**Created:** 2025-10-25
**Test Coverage Goal:** 80%

## Test Strategy Overview

This feature follows a pragmatic testing approach: comprehensive unit tests for the Notion fetcher logic, focused integration tests for the end-to-end flow, and structured manual testing to validate Dutch content quality. The existing ingestion pipeline is already tested, so we focus testing efforts on the new Notion fetch and conversion layer.

**Testing Levels:**
- ✅ Unit Tests: Notion API interaction, block-to-markdown conversion, file I/O
- ✅ Integration Tests: Full fetch → save → ingest flow with sample pages
- ✅ Manual Tests: Dutch content validation, markdown inspection, search quality

## Unit Tests

### Test Files to Create

#### `tests/ingestion/test_notion_to_markdown.py`

**Purpose:** Test individual functions for fetching pages and converting blocks to markdown

**Test Stubs:**
1. **Test: API Client Initialization** (References AC-FEAT-002-001)
   - **Given:** Valid Notion API token and database ID in config
   - **When:** NotionToMarkdown class is instantiated
   - **Then:** Notion client is initialized without errors
   - **Mocks:** Mock notion_client.AsyncClient

2. **Test: Fetch Single Page Success** (References AC-FEAT-002-002)
   - **Given:** Mock Notion API returns single page response
   - **When:** fetch_page() is called with valid page_id
   - **Then:** Page metadata (title, ID) is returned correctly
   - **Mocks:** Mock notion.databases.query()

3. **Test: Fetch All Pages with Pagination** (References AC-FEAT-002-002)
   - **Given:** Mock Notion API returns paginated response (has_more=True, next_cursor)
   - **When:** fetch_all_guidelines() is called
   - **Then:** All pages across multiple requests are collected
   - **Mocks:** Mock notion.databases.query() with pagination

4. **Test: Convert Heading Block to Markdown** (References AC-FEAT-002-003)
   - **Given:** Notion block of type heading_2 with Dutch text
   - **When:** block_to_markdown() processes the block
   - **Then:** Returns "## [Dutch text]" with proper formatting
   - **Mocks:** None (pure function)

5. **Test: Convert Paragraph Block to Markdown** (References AC-FEAT-002-003)
   - **Given:** Notion block of type paragraph with Dutch text
   - **When:** block_to_markdown() processes the block
   - **Then:** Returns plain text with Dutch characters preserved
   - **Mocks:** None (pure function)

6. **Test: Convert List Blocks to Markdown** (References AC-FEAT-002-003)
   - **Given:** Notion blocks of type bulleted_list_item and numbered_list_item
   - **When:** blocks_to_markdown() processes the blocks
   - **Then:** Returns "- Item" for bulleted, "1. Item" for numbered
   - **Mocks:** None (pure function)

7. **Test: Handle Unknown Block Type** (References AC-FEAT-002-102)
   - **Given:** Notion block with unknown or unsupported type
   - **When:** block_to_markdown() processes the block
   - **Then:** Returns empty string or placeholder, logs warning
   - **Mocks:** None (pure function)

8. **Test: Dutch Character Preservation** (References AC-FEAT-002-003, AC-FEAT-002-202)
   - **Given:** Notion block with Dutch special characters (é, ë, ï, ö, ü)
   - **When:** blocks_to_markdown() processes the block
   - **Then:** All special characters preserved in output
   - **Mocks:** None (pure function)

9. **Test: Sanitize Filename** (References AC-FEAT-002-402)
   - **Given:** Page title with spaces, special chars, and Unicode
   - **When:** sanitize_filename() is called
   - **Then:** Returns lowercase, underscores, no special chars, max 100 chars
   - **Mocks:** None (pure function)

10. **Test: Save Markdown File** (References AC-FEAT-002-004)
    - **Given:** Markdown content and sanitized filename
    - **When:** save_markdown_file() is called
    - **Then:** File created in documents/notion_guidelines/ with UTF-8 encoding
    - **Mocks:** Mock file system operations (pathlib.Path)

---

### Unit Test Coverage Goals

- **Functions:** All public functions in notion_to_markdown.py tested
- **Branches:** All conditional branches (if/else) covered
- **Edge Cases:** Empty content, malformed blocks, Unicode edge cases
- **Error Handling:** API errors, file write errors, encoding errors

**Target Coverage:** 85% line coverage for notion_to_markdown.py

## Integration Tests

### Test Files to Create

#### `tests/ingestion/test_notion_integration.py`

**Purpose:** Test full end-to-end flow from Notion API to PostgreSQL storage

**Test Stubs:**
1. **Test: Full Fetch and Save Workflow** (References AC-FEAT-002-001 through AC-FEAT-002-004)
   - **Components:** NotionToMarkdown → File System → Ingestion Pipeline
   - **Setup:** Mock Notion API with 3 sample pages, temporary documents directory
   - **Scenario:** Fetch pages → convert to markdown → save files → verify files exist
   - **Assertions:** 3 markdown files created, content matches expected format, filenames sanitized

2. **Test: Ingestion Pipeline Compatibility** (References AC-FEAT-002-005, AC-FEAT-002-301)
   - **Components:** Markdown Files → DocumentIngestionPipeline → PostgreSQL
   - **Setup:** Pre-created markdown files in temp directory, test database
   - **Scenario:** Run ingestion pipeline on Notion markdown files
   - **Assertions:** Chunks created in DB, embeddings generated, no pipeline errors

3. **Test: End-to-End with Dutch Content** (References AC-FEAT-002-006)
   - **Components:** Full stack (fetch → convert → ingest → search)
   - **Setup:** Mock Notion API with Dutch guideline, test database
   - **Scenario:** Fetch Dutch page → ingest → search with Dutch query
   - **Assertions:** Search returns relevant chunks, Dutch characters preserved, similarity > 0.5

---

### Integration Test Scope

**Internal Integrations:**
- NotionToMarkdown → File System: Markdown file creation and UTF-8 encoding
- Markdown Files → DocumentIngestionPipeline: Existing pipeline processes Notion markdown

**External Integrations:**
- Notion API (mocked): Fetch pages and blocks via notion-client SDK
- PostgreSQL (real test DB): Store chunks and verify storage

**Mock Strategy:**
- **Fully Mocked:** Notion API (use recorded responses for deterministic tests)
- **Real:** File system (use temporary directories), PostgreSQL (test database)

## Manual Testing

### Test Scenarios

*See `manual-test.md` for detailed step-by-step instructions.*

**Quick Reference:**
1. **API Connection Test:** Verify Notion credentials and database access
2. **Sample Page Fetch:** Fetch 2-3 pages, inspect markdown output for quality
3. **Full Ingestion:** Fetch all ~100 guidelines, run pipeline, validate count
4. **Dutch Search Validation:** Test search with Dutch queries (veiligheid, werkplek, bescherming)
5. **Markdown Quality Check:** Manually inspect 10 random markdown files for formatting and completeness

**Manual Test Focus:**
- **Visual Verification:** Markdown formatting (headings, lists, paragraphs)
- **Data Quality:** Dutch content preserved without encoding issues
- **Search Quality:** Relevant results returned for Dutch queries
- **Error Handling:** Graceful handling of API errors, missing pages, etc.

## Test Data Requirements

### Fixtures & Seed Data

**Unit Test Fixtures:**
```python
# Sample Notion API responses for mocking
MOCK_PAGE_RESPONSE = {
    "id": "test-page-id-123",
    "properties": {
        "title": {"title": [{"text": {"content": "Veiligheid op de Werkplek"}}]}
    }
}

MOCK_BLOCKS_RESPONSE = {
    "results": [
        {"type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "Samenvatting"}}]}},
        {"type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Dit is een test."}}]}}
    ]
}

MOCK_PAGINATED_RESPONSE = {
    "results": [...],  # 100 mock pages
    "has_more": True,
    "next_cursor": "cursor-token-abc"
}
```

**Integration Test Data:**
- Sample markdown files: 3 pre-created files with Dutch content
- Test database: Empty PostgreSQL instance for ingestion testing
- Notion API mocks: Recorded responses from real Notion API (sanitized)

**Manual Test Data:**
- Real Notion database: EVI 360's actual guidelines database (user provides credentials)
- Test queries: List of 10 Dutch search terms (veiligheid, werkplek, PPE, etc.)

## Mocking Strategy

### What to Mock

**Always Mock:**
- Notion API calls (to avoid rate limits and enable deterministic tests)
- External network requests (notion-client SDK calls)

**Sometimes Mock:**
- File system operations (mock for unit tests, real temp dirs for integration)
- Database operations (mock for unit tests, real test DB for integration)

**Never Mock:**
- Core conversion logic (block_to_markdown, sanitize_filename)
- Existing ingestion pipeline (test real integration)

### Mocking Approach

**Framework:** pytest with unittest.mock

**Mock Examples:**
```python
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_fetch_all_guidelines():
    with patch('notion_client.AsyncClient') as mock_client:
        mock_client.return_value.databases.query = AsyncMock(
            return_value=MOCK_PAGINATED_RESPONSE
        )

        fetcher = NotionToMarkdown(config)
        pages = await fetcher.fetch_all_guidelines()

        assert len(pages) == 100
        mock_client.return_value.databases.query.assert_called()
```

## Test Execution

### Running Tests Locally

**Activate Virtual Environment:**
```bash
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

**Unit Tests:**
```bash
python3 -m pytest tests/ingestion/test_notion_to_markdown.py -v --cov=ingestion.notion_to_markdown
```

**Integration Tests:**
```bash
python3 -m pytest tests/ingestion/test_notion_integration.py -v
```

**All Tests:**
```bash
python3 -m pytest tests/ingestion/ -v --cov=ingestion
```

### CI/CD Integration (Phase 2)

**Pipeline Stages:**
1. Unit tests (run on every commit)
2. Integration tests (run on every commit)
3. Coverage report generation (enforce 80% threshold)
4. Manual test checklist (run before merge)

**Failure Handling:**
- Failing tests block merge to main branch
- Coverage drops below 80% block merge
- Manual test failures require investigation

## Coverage Goals

### Coverage Targets

| Test Level | Target Coverage | Minimum Acceptable |
|------------|----------------|-------------------|
| Unit | 85% | 75% |
| Integration | N/A (flow-based) | 3 critical workflows |

### Critical Paths

**Must Have 100% Coverage:**
- Notion API authentication and error handling
- Block-to-markdown conversion for Dutch content
- File sanitization and UTF-8 encoding

**Can Have Lower Coverage:**
- Logging and telemetry code
- Edge case block types (embeds, images, tables)
- Retry logic (tested in integration)

## Performance Testing

**Requirement:** Complete ingestion within 30 minutes for 100 guidelines (AC-FEAT-002-201)

**Test Approach:**
- **Tool:** Python time module, manual timing
- **Scenarios:**
  1. **Fetch Time:** Measure time to fetch all 100 pages from Notion API
  2. **Conversion Time:** Measure time to convert blocks to markdown for all pages
  3. **Ingestion Time:** Measure existing pipeline time for 100 markdown files

**Acceptance:**
- Fetch: < 10 minutes
- Convert: < 5 minutes
- Ingest: < 15 minutes
- **Total:** < 30 minutes

## Test Stub Generation (Phase 1)

*These test files will be created with TODO stubs during planning:*

```
tests/ingestion/
├── test_notion_to_markdown.py (10 unit test stubs)
└── test_notion_integration.py (3 integration test stubs)
```

**Total Test Stubs:** 13 test functions with TODO comments

## Out of Scope

*What we're explicitly NOT testing in this phase:*

- Tier parsing logic (deferred to future phase)
- Webhook-based sync (not implemented in MVP)
- Incremental update detection (not implemented)
- Notion API rate limit exhaustion (handled by SDK)
- Cross-browser testing (no UI component)

---

**Next Steps:**
1. Planner will generate test stub files based on this strategy
2. Phase 2: Implementer will make stubs functional
3. Phase 2: Tester will execute and validate
