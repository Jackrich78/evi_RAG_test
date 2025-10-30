# Global Acceptance Criteria

This file tracks all acceptance criteria across all features in the project. Each criterion has a unique ID in the format `AC-FEAT-XXX-###`.

**Purpose:** Global registry of acceptance criteria for traceability and testing alignment.

**Last Updated:** 2025-10-30

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

## FEAT-003: Specialist Agent with Vector Search (MVP) - ✅ COMPLETE (2025-10-30)

### Core Functionality

### Functional Criteria

- **AC-FEAT-003-001:** Given CLI is connected to API server, when user enters Dutch query with special characters (ë, ï, ü), then query is accepted without UTF-8 encoding errors and processed correctly
- **AC-FEAT-003-002:** Given specialist agent receives Dutch query, when agent generates response, then response is in grammatically correct Dutch (native speaker quality) with no English words mixed in
- **AC-FEAT-003-003:** Given agent searches guidelines and finds relevant chunks, when agent synthesizes response, then response includes ≥2 distinct guideline citations with title and source
- **AC-FEAT-003-004:** Given user queries "valbeveiliging" (fall protection), when hybrid search executes, then results include semantically similar terms ("veiligheid hoogte", "valbescherming") with top 5 results including ≥3 relevant chunks
- **AC-FEAT-003-005:** Given agent cites guidelines in response, when citations are formatted, then each citation shows title (e.g., "NVAB Richtlijn: Werken op Hoogte") and source (NVAB, STECR, UWV, Arboportaal)
- **AC-FEAT-003-006:** Given API server is running on port 8058, when CLI starts and checks health endpoint, then connection established and health check passes in <2 seconds
- **AC-FEAT-003-007:** Given 100 test queries submitted, when measuring end-to-end response time, then 95th percentile is <3 seconds

### Edge Cases & Error Handling

- **AC-FEAT-003-101:** Given user enters empty string or whitespace, when query is processed, then agent responds with helpful Dutch message ("Ik heb geen vraag ontvangen") without crashing
- **AC-FEAT-003-102:** Given user enters nonsense query "xyzabc qwerty foobar", when search returns no relevant results, then agent acknowledges gracefully ("Geen relevante richtlijnen gevonden") without hallucination
- **AC-FEAT-003-103:** Given database connection cannot be established, when search tool attempts query, then graceful Dutch error message shown ("Kan momenteel niet zoeken in de kennisbank") and CLI doesn't crash
- **AC-FEAT-003-104:** Given OpenAI API call fails with 401 Unauthorized, when agent attempts to generate response, then clear error message logged ("Service tijdelijk niet beschikbaar") and user notified
- **AC-FEAT-003-105:** Given search returns 0 results, when agent synthesizes response, then agent acknowledges lack of information honestly ("Geen relevante richtlijnen gevonden voor deze vraag")
- **AC-FEAT-003-106:** Given OpenAI API takes >60 seconds to respond, when timeout threshold exceeded, then request is cancelled and user notified ("Verzoek duurde te lang, probeer opnieuw")

### Non-Functional Requirements

- **AC-FEAT-003-201:** Given 100 sequential queries, when measuring response times, then no significant degradation from query 1 to 100 and memory usage remains stable
- **AC-FEAT-003-202:** Given 5 concurrent users submitting queries, when each query completes, then all queries complete successfully in <5s with no connection pool exhaustion errors
- **AC-FEAT-003-203:** Given 10 responses reviewed by native Dutch speaker, when rating for grammar and naturalness, then 9/10 rated "good" or "excellent" with no English words (except proper nouns like NVAB)
- **AC-FEAT-003-204:** Given responses generated, when checking language purity, then response content is 100% Dutch with only exceptions being proper nouns and acronyms (NVAB, STECR, PBM, CE, EN standards)
- **AC-FEAT-003-205:** Given API server starts from `uvicorn` command, when measuring startup time, then "Application startup complete" message appears within 10 seconds
- **AC-FEAT-003-206:** Given MVP runs locally without authentication, when API endpoints receive requests, then all requests accepted with no auth middleware (localhost-only, .env in .gitignore, production security documented)
- **AC-FEAT-003-207:** Given database queries are executed, when code review of db_utils.py performed, then all queries use parameterized format ($1, $2 placeholders) with no string concatenation

### Language Support (Added 2025-10-30)

- **AC-FEAT-003-301:** Given CLI started with `--language en` flag, when Dutch query is submitted, then response is in English with key Dutch safety terms translated
- **AC-FEAT-003-302:** Given CLI started with `--language nl` flag (or default), when query is submitted, then response is in Dutch
- **AC-FEAT-003-303:** Given agent receives language parameter, when generating response, then appropriate system prompt loaded (SPECIALIST_SYSTEM_PROMPT_NL or SPECIALIST_SYSTEM_PROMPT_EN)
- **AC-FEAT-003-304:** Given English mode is used, when citations are generated, then document titles remain in Dutch but explanatory text is in English

### Citation Quality (Added 2025-10-30)

- **AC-FEAT-003-401:** Given search results contain document_title field, when agent formats citations, then citation.title uses document_title value (not document_source filename)
- **AC-FEAT-003-402:** Given LLM generates citations, when extracting from search results, then citation.source field also uses document_title (as per prompt instructions)
- **AC-FEAT-003-403:** Given citations are displayed in CLI, when formatted output shown, then no .md file extensions appear in citation titles (clean document names only)

### Integration Requirements

- **AC-FEAT-003-501:** Given API running on port 8058, when CLI makes POST request to /chat/stream, then streaming response received and displayed correctly with SSE format
- **AC-FEAT-003-502:** Given API receives chat request, when API calls specialist_agent.run_stream(), then agent executes and returns structured SpecialistResponse
- **AC-FEAT-003-503:** Given agent calls search_guidelines tool, when tool executes hybrid_search, then relevant chunks returned from PostgreSQL via db_utils.hybrid_search()
- **AC-FEAT-003-504:** Given agent generates response, when API streams via SSE, then CLI displays tokens incrementally as they arrive (not buffered)
- **AC-FEAT-003-505:** Given existing tools.py, db_utils.py, api.py, when implementing specialist agent, then reuse hybrid_search_tool and database utilities with 90%+ code reuse rate

---

**Total Acceptance Criteria:** 17 (FEAT-002) + 35 (FEAT-003) = 52
