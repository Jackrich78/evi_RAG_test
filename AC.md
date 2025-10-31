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

## FEAT-007: OpenWebUI Integration

### Functional Criteria

#### Story 1: Chat Interface for Guideline Queries

- **AC-007-001:** Given I am logged into the OpenWebUI chat interface, when I type "Wat zijn de richtlijnen voor werken op hoogte?" (What are guidelines for working at height?), then the system returns tier 1 summary guidelines for working at height in Dutch, and the response appears within 2 seconds, and the formatting is readable with proper line breaks and structure

- **AC-007-002:** Given I have received a tier 1 summary response, when I ask a follow-up question "Geef me meer details" (Give me more details), then the system retrieves tier 2 key facts for the same guideline topic, and maintains context from the previous query, and provides clear navigation hints for accessing tier 3 if available

- **AC-007-003:** Given I am viewing guideline information, when I ask "Welke producten raad je aan voor deze situatie?" (Which products do you recommend for this situation?), then the system returns relevant products from the catalog with compliance tags, and includes product names, descriptions, and safety certifications, and links products to specific guideline requirements

#### Story 2: Multi-Turn Conversation Support

- **AC-007-004:** Given I have asked 3 questions about ladder safety in a conversation, when I ask "Wat zijn de verschillen met steigers?" (What are the differences with scaffolding?), then the system understands I'm comparing ladder vs. scaffolding safety, and maintains the conversation history visible in the UI, and provides contextually relevant comparisons

- **AC-007-005:** Given I am in a conversation about fall protection, when I ask an unrelated question "Wat zijn de regels voor gehoorbescherming?" (What are the rules for hearing protection?), then the system detects the topic change, and starts a new context for hearing protection guidelines, and does not confuse previous fall protection context with new topic

- **AC-007-006:** Given I am logged into the system, when I close the browser and return later, then I can see my previous conversation history, and I can continue previous conversations from where I left off, and conversation history is scoped to my user account only

#### Story 3: Secure User Authentication

- **AC-007-007:** Given I navigate to the OpenWebUI interface, when I attempt to access the chat without logging in, then I am redirected to a login page, and I cannot send queries until authenticated, and I see clear instructions for obtaining access credentials

- **AC-007-008:** Given I have successfully logged in, when my session expires after 2 hours of inactivity, then I am prompted to re-authenticate, and my conversation history is preserved after re-login, and I can resume my previous session state

- **AC-007-009:** Given two users are logged in simultaneously, when both users send queries at the same time, then each user's conversation remains isolated, and no cross-contamination of responses occurs, and each user sees only their own chat history

#### Story 4: Docker Deployment

- **AC-007-010:** Given I have the project repository cloned, when I run `docker-compose up` in the project root, then all services start successfully (OpenWebUI, FastAPI, PostgreSQL), and OpenWebUI is accessible at http://localhost:3000, and FastAPI is accessible at http://localhost:8000, and health checks pass for all containers within 30 seconds

- **AC-007-011:** Given I need to configure API keys and database credentials, when I create a `.env` file with required variables, then all services read configuration from environment variables, and sensitive values are not hardcoded in Docker images, and the system provides clear error messages for missing variables

- **AC-007-012:** Given the system is running with active conversations, when I restart the Docker containers, then conversation history is preserved in PostgreSQL, and users can resume their sessions after restart, and no data loss occurs during normal restarts

### Edge Cases & Error Scenarios

- **AC-007-013:** Given I am in the chat interface, when I submit an empty message or only whitespace, then the system prompts me to enter a valid question, and does not make unnecessary API calls, and provides example queries to guide me

- **AC-007-014:** Given I query for a guideline that doesn't exist in the database, when I ask "Wat zijn de regels voor ruimtereizen?" (What are the rules for space travel?), then the system responds with "Geen richtlijnen gevonden" (No guidelines found), and suggests related topics or broader search terms, and logs the query for potential content gap analysis

- **AC-007-015:** Given the FastAPI backend is down or unreachable, when I send a query in the chat interface, then I receive an error message "Backend service tijdelijk niet beschikbaar" (Backend service temporarily unavailable), and the system retries the request automatically (max 3 attempts), and provides an estimated time for resolution if available

- **AC-007-016:** Given 10 users are sending queries simultaneously, when all queries are submitted within the same second, then all users receive responses within 3 seconds (P95), and no requests timeout or fail due to concurrency, and response accuracy is not degraded under load

### Non-Functional Requirements

- **AC-007-017:** Given all safety guidelines are in Dutch, when I query in Dutch using natural language, then the LLM correctly interprets Dutch queries, and responses maintain proper Dutch grammar and terminology, and technical safety terms are not mistranslated

- **AC-007-018:** Given I send a guideline query, when the system processes the request, then tier 1 responses return in <2 seconds (P95), and tier 2/3 responses return in <3 seconds (P95), and product recommendation queries return in <2.5 seconds (P95)

- **AC-007-019:** Given I access OpenWebUI from a mobile device, when I use the chat interface on a screen <768px width, then the UI is fully responsive and usable, and all features work on touch interfaces, and text is readable without horizontal scrolling

- **AC-007-020:** Given I am a user with accessibility needs, when I use screen reader software with OpenWebUI, then all chat messages are announced clearly, and keyboard navigation works for all features, and color contrast meets WCAG 2.1 AA standards

---

## FEAT-010: True Token Streaming

### Functional Requirements

#### User Story 1: Real-time Token Display

- **AC-FEAT-010-001:** Given a user submits a query to the specialist agent, when the LLM begins generating a response, then the first token must appear in the UI within 500ms
- **AC-FEAT-010-002:** Given the LLM is generating a response, when tokens are being produced, then tokens must appear continuously without buffering delays between chunks
- **AC-FEAT-010-003:** Given a streaming response is in progress, when the user views the chat interface, then a visual indicator (cursor/animation) must show that streaming is active

#### User Story 2: Citation Integration

- **AC-FEAT-010-004:** Given the LLM response includes citation markers `[1]`, `[2]`, etc., when tokens stream to the frontend, then citation markers must render correctly without breaking across chunk boundaries
- **AC-FEAT-010-005:** Given a citation marker appears in the streaming text, when the marker is rendered, then the citation panel must update in real-time to show the referenced source
- **AC-FEAT-010-006:** Given the streaming response is complete, when the user clicks a citation marker, then the citation panel must scroll to and highlight the correct source

#### User Story 3: Bilingual Support

- **AC-FEAT-010-007:** Given the user asks a question in Dutch, when the agent responds in Dutch, then tokens must stream correctly with proper UTF-8 encoding for Dutch characters (ë, ö, etc.)
- **AC-FEAT-010-008:** Given the user asks a question in English, when the agent responds in English, then tokens must stream correctly with same performance as Dutch responses

#### User Story 4: Error Handling

- **AC-FEAT-010-009:** Given a streaming response is in progress, when the network connection is interrupted, then the UI must display an error message and allow retry without losing accumulated text
- **AC-FEAT-010-010:** Given the LLM takes longer than 60 seconds to complete, when the timeout threshold is reached, then the stream must close gracefully with a timeout error message
- **AC-FEAT-010-011:** Given the backend encounters an error during streaming, when the error occurs, then the frontend must receive an error event and display a user-friendly message

### Non-Functional Requirements

#### Performance

- **AC-FEAT-010-012:** Given a typical query (50-100 tokens), when measured across 100 requests, then 95th percentile time-to-first-token must be under 500ms
- **AC-FEAT-010-013:** Given a query that generates 2000+ tokens, when streaming the response, then the stream must remain stable without stuttering or freezing
- **AC-FEAT-010-014:** Given 10 users simultaneously streaming queries, when all streams are active, then each stream must maintain <500ms first-token latency and smooth delivery

#### Reliability

- **AC-FEAT-010-015:** Given 50 consecutive streaming queries, when all queries complete, then no memory leaks must be detectable (backend or frontend)
- **AC-FEAT-010-016:** Given a user navigates away during streaming, when the browser closes the connection, then the backend must detect disconnection and clean up resources within 5 seconds

#### Security

- **AC-FEAT-010-017:** Given an unauthenticated user attempts to access the streaming endpoint, when the connection is attempted, then the request must be rejected with 401 Unauthorized
- **AC-FEAT-010-018:** Given a user makes more than 20 streaming requests in 1 minute, when the rate limit is exceeded, then subsequent requests must be rejected with 429 Too Many Requests

#### Compatibility

- **AC-FEAT-010-019:** Given the supported browsers (Chrome, Firefox, Safari, Edge), when accessing the streaming interface, then streaming must work consistently across all supported browsers
- **AC-FEAT-010-020:** Given a user accesses the system on a mobile device, when streaming a response, then the streaming UI must be responsive and performant on mobile networks

### Edge Cases

- **AC-FEAT-010-021:** Given the LLM generates an empty response, when the stream completes, then the UI must display a message indicating no content was generated
- **AC-FEAT-010-022:** Given a user submits a new query before the previous stream completes, when the new query is submitted, then the previous stream must be cancelled and the new stream must start immediately
- **AC-FEAT-010-023:** Given a response contains special characters (emoji, mathematical symbols, etc.), when streaming the response, then all special characters must render correctly without encoding issues

---

**Total Acceptance Criteria:** 17 (FEAT-002) + 35 (FEAT-003) + 20 (FEAT-007) + 23 (FEAT-010) = 95
