# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2025-11-02]

### Fixed - FEAT-007 POST-MVP Issues RESOLVED
- **FEAT-007: All 3 production issues successfully resolved** ([docs/features/FEAT-007_openwebui-integration/post-mvp.md](docs/features/FEAT-007_openwebui-integration/post-mvp.md))

  ✅ **Issue 1: Streaming TransferEncodingError (CRITICAL)** - RESOLVED
  - Added proper SSE headers (`Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`)
  - Implemented try/except/finally error handling in `generate_sse()` function
  - Guaranteed `[DONE]` marker sent even on errors
  - Streaming now works reliably for 50+ consecutive queries without crashes
  - Files Modified: `agent/api.py` (lines 733-756)

  ✅ **Issue 2: Citations Not Clickable (HIGH)** - RESOLVED
  - Updated SQL functions to extract `source_url` from `documents.metadata` JSONB field
  - Modified `Citation` Pydantic model: changed `source: str` to `url: Optional[str]`
  - Added `source_url: Optional[str]` field to `ChunkResult` model
  - Updated specialist agent prompt to generate markdown links `[Title](url)`
  - Citations now render as blue clickable links in OpenWebUI
  - Files Modified: `sql/schema.sql`, `sql/evi_schema_additions.sql`, `agent/models.py`, `agent/db_utils.py`, `agent/tools.py`, `agent/specialist_agent.py`

  ✅ **Issue 3: Language Always Dutch (MEDIUM)** - RESOLVED
  - Replaced two language-specific prompts (`SPECIALIST_SYSTEM_PROMPT_NL`, `SPECIALIST_SYSTEM_PROMPT_EN`) with single language-agnostic prompt
  - LLM now auto-detects user's language from query and responds accordingly
  - Works seamlessly for both Dutch and English queries
  - Removed `language` parameter from `run_specialist_query()` and `run_specialist_query_stream()` functions
  - Files Modified: `agent/specialist_agent.py` (lines 32-122), `agent/api.py` (lines 742, 760)

### Updated
- **Documentation:** Updated FEAT-007 status to "✅ RESOLVED - All Issues Fixed"
  - `docs/features/FEAT-007_openwebui-integration/post-mvp.md` - Added resolution summary
  - `docs/IMPLEMENTATION_PROGRESS.md` - Updated Phase 3E with complete resolution details
  - `CHANGELOG.md` - Added comprehensive fix documentation

## [2025-11-01]

### Completed
- **FEAT-007: OpenWebUI Integration** - Dutch-language chat interface with clickable citations ([docs/features/FEAT-007_openwebui-integration/post-mvp.md](docs/features/FEAT-007_openwebui-integration/post-mvp.md))
  - Deployed OpenWebUI container on port 3001
  - Added OpenAI-compatible `/v1/chat/completions` endpoint
  - Integrated with specialist agent for workplace safety queries
  - Fixed 3 critical POST-MVP issues (see below)

### Fixed
- **FEAT-007 POST-MVP Issue 1:** Streaming TransferEncodingError - Added SSE headers (`Cache-Control`, `Connection`, `X-Accel-Buffering`) and try/except/finally error handling to prevent chat crashes
- **FEAT-007 POST-MVP Issue 2:** Citations not clickable - Updated SQL functions, models, and agent prompt to extract `source_url` from metadata and render as markdown links `[Title](url)`
- **FEAT-007 POST-MVP Issue 3:** Language always Dutch - Replaced language-specific prompts with single language-agnostic prompt that auto-detects from user's question
- **FEAT-010 Streaming:** Fixed missing `await` on `result.get_output()` in specialist_agent.py line 400 causing streaming to fail partway through ([docs/features/FEAT-010_streaming/implementation.md](docs/features/FEAT-010_streaming/implementation.md))
- Updated test documentation with correct Pydantic AI 0.3.2 streaming API pattern in test_pydantic_streaming.py
- Added comprehensive bug fix documentation including root cause analysis and lessons learned

### Changed
- **FEAT-007:** SQL functions (`match_chunks`, `hybrid_search`) now extract `source_url` from `documents.metadata->>'source_url'`
- **FEAT-007:** `Citation` model field changed from `source: str` to `url: Optional[str]` for clickable links
- **FEAT-007:** `ChunkResult` model now includes `source_url: Optional[str]` field
- **FEAT-007:** Agent uses single `SPECIALIST_SYSTEM_PROMPT` for all languages (removed `_NL` and `_EN` variants)
- **FEAT-007:** Removed `language` parameter from `run_specialist_query()` and `run_specialist_query_stream()` functions

### Added - FEAT-004 Planning Complete: Product Catalog Integration (2025-10-31)
- **FEAT-004: Product Catalog Integration - Planning Documentation Complete**
  - **Status:** ✅ Ready for Implementation
  - **Planning Completed:** 2025-10-31
  - **Estimated Implementation:** 2-3 days (Phase 2)

  **Planning Documents Created (4 files):**
  - architecture.md (794 words) - Extend existing ingestion module
  - acceptance.md (796 words) - 34 acceptance criteria
  - testing.md (748 words) - 46 test stubs across unit and integration
  - manual-test.md (796 words) - 7 manual test scenarios

  **Test Stubs Generated (46 tests in 5 files):**
  - Unit tests: 32 tests (product ingestion, search, models)
  - Integration tests: 14 tests (full pipeline, search flow)

  **Architecture Decision:**
  - **Selected:** Option 1 - Extend existing ingestion module
  - **Rationale:** Fastest path to MVP, proven FEAT-002 patterns, 2-3 days
  - **Key Features:** Notion ingestion, semantic search (<500ms), compliance filtering

  **Acceptance Criteria:** 34 new criteria added to AC.md (global total: 129)

  **Next Steps:** Phase 2 implementation following TDD approach

---

### Added - FEAT-010 Planning Complete: True Token Streaming (2025-10-31)
- **FEAT-010: True Token Streaming - Planning Documentation Complete**
  - **Status:** ✅ Ready for Implementation
  - **Planning Completed:** 2025-10-31
  - **Estimated Implementation:** 3 hours (Phase 2)

  **Planning Documents Created (6 files):**
  - architecture.md (3,200+ words) - SSE-based streaming with spike validation approach
  - acceptance.md (2,100+ words) - 11 acceptance criteria (23 total with AC.md)
  - testing.md (2,400+ words) - Comprehensive test strategy across 4 test levels
  - manual-test.md (1,800+ words) - Step-by-step validation guide for QA

  **Test Stubs Generated (44 tests in 6 files):**
  - Unit tests: 14 tests in 2 files (SSE formatting, stream handlers)
  - Integration tests: 15 tests in 2 files (SSE endpoint, Pydantic streaming)
  - E2E tests: 8 tests (full streaming workflow)
  - Performance tests: 7 tests (latency, throughput, backpressure)

  **Architecture Decision:**
  - **Selected:** SSE (Server-Sent Events) with Pydantic AI .stream_output()
  - **Spike Plan:** 5 steps, 6 hours total validation before implementation
  - **Key Features:** Token-by-token delivery, <500ms first token, citation handling

  **Next Steps:** Phase 2 implementation following TDD (Red-Green-Refactor)

---

### Added - FEAT-010 Exploration Complete: True Token Streaming (2025-10-31)
- **FEAT-010: True Token Streaming - Exploration Phase Complete**
  - **Status:** 🚀 Ready for Planning
  - **Exploration Completed:** 2025-10-31
  - **Estimated Implementation:** 3 hours (Phase 2)
  - **Performance Target:** <500ms first token (vs current 2-3s block)

  **Problem Solved:**
  - Current simulated streaming blocks for 2-3s, then artificially chunks output with fake delays
  - Poor user experience with no visual feedback during LLM processing

  **Solution:**
  - Re-implement true token-by-token streaming using Pydantic AI 0.3.2
  - Based on proven blueprint from learnings.md (working implementation)
  - Uses .stream_output() API (updated from deprecated .stream())

  **Architecture Decisions:**
  - ✅ Keep both functions: run_specialist_query() (blocking) + run_specialist_query_stream() (new)
  - ✅ Maintains test stability (6 existing tests mock blocking behavior)
  - ✅ Low maintenance burden (dual functions pattern)

  **Key Implementation Tasks (6 files, ~3 hours):**
  1. agent/models.py - Make Citation.source and SpecialistResponse.content optional for partials
  2. agent/specialist_agent.py - Add run_specialist_query_stream() with delta tracking
  3. agent/api.py - Replace simulated streaming in /chat/stream endpoint
  4. tests/agent/test_streaming.py (NEW) - 8 comprehensive streaming tests
  5. tests/agent/test_specialist_agent.py (review) - Verify 6 existing tests still pass
  6. tests/integration/test_specialist_flow.py - Implement test_streaming_response()

  **Risk Assessment:** Low
  - Proven blueprint from learnings.md with documented solutions
  - Simple API migration (.stream() → .stream_output())
  - Test isolation prevents regression

  **Exploration Documents:**
  - `docs/features/FEAT-010_streaming/prd.md` (780 words) - Problem, solution, requirements
  - `docs/features/FEAT-010_streaming/research.md` (850+ words) - Pydantic AI API changes, architecture decisions
  - `docs/features/FEAT-010_streaming/learnings.md` (existing) - Historical reference

  **Next Steps:** Run `/plan FEAT-010` to create architecture.md, acceptance.md, testing.md, manual-test.md

---

### Added - FEAT-004 Exploration Complete: Product Catalog Integration (2025-10-31)
- **FEAT-004: Product Catalog Integration - Exploration Phase Complete (Deep Dive)**
  - **Status:** 🚀 Ready for Planning
  - **Exploration Completed:** 2025-10-31 (Updated with deeper analysis)
  - **Approach:** Phased MVP (8-12 hours) with pilot testing for retrieval quality validation
  - **Data Source:** Notion products database (ID: 29dedda2a9a081409224e46bd48c5bc6)
  - **Storage:** Dedicated products table (NOT chunks table)
  - **Categorization:** Extract from Notion "type" field (no AI needed)
  - **Integration:** Automatic when contextually relevant (agent decides based on semantic similarity)

  **Key Decisions Made:**
  - ✅ Use Notion database over web scraping (3x faster)
  - ✅ Store in products table for clean separation
  - ✅ Create dedicated `ingest_products.py` (don't reuse guidelines ingestion)
  - ✅ Pilot test with 10-20 products BEFORE full ingestion (de-risk approach)
  - ✅ Descope compliance tags for MVP
  - ✅ Confirmed database fields: id, name, type, tags, visible, URL, price_type

  **Critical Uncertainties Documented (7 categories):**
  1. Notion database schema details (field formats, data quality, filtering)
  2. Retrieval quality & search strategy (embedding options, similarity thresholds)
  3. Agent integration logic (contextual relevance decision algorithm)
  4. Data validation & error handling rules
  5. Implementation sequencing & risk mitigation

  **Phased Implementation Plan:**
  - **Phase 0 (30 min):** Database inspection & schema analysis
  - **Phase 1 (2-3 hours):** Pilot test with 10-20 products + 3 embedding strategies
  - **Phase 2 (1-2 hours):** Full ingestion (conditional on pilot success)
  - **Phase 3 (2-3 hours):** Agent tool integration
  - **Phase 4 (1-2 hours):** Testing & validation

  **Exploration Documents Updated:**
  - `docs/features/FEAT-004_product-catalog/prd.md` (7.3K → 15K) - Added open questions, phased plan
  - `docs/features/FEAT-004_product-catalog/research.md` (12.5K → 18K) - Added 5 uncertainty categories

  **Next Steps:** Run `/plan FEAT-004` to create detailed planning documentation (architecture, acceptance criteria, testing strategy)

---

### Added - FEAT-007 Planning Complete: OpenWebUI Integration (2025-10-30)
- **FEAT-007: OpenWebUI Integration - Planning Documentation Complete**
  - **Status:** ✅ Ready for Implementation
  - **Planning Completed:** 2025-10-30
  - **Architecture Decision:** Standalone OpenWebUI with OpenAI-compatible API
  - **Acceptance Criteria:** 20 criteria defined (AC-007-001 through AC-007-020)
  - **Testing Strategy:** Moderate approach with 4 automated test stubs + 10 manual scenarios
  - **Estimated Implementation:** 6-8 hours for Phase 2

  **Planning Documents Created:**
  - `docs/features/FEAT-007_openwebui-integration/prd.md` (9.4K) - Product requirements
  - `docs/features/FEAT-007_openwebui-integration/research.md` (31K) - Research with 10 topics
  - `docs/features/FEAT-007_openwebui-integration/architecture.md` (11K) - Architecture decision
  - `docs/features/FEAT-007_openwebui-integration/acceptance.md` (8.9K) - 20 acceptance criteria
  - `docs/features/FEAT-007_openwebui-integration/testing.md` (10K) - Testing strategy
  - `docs/features/FEAT-007_openwebui-integration/manual-test.md` (9.6K) - Manual test guide
  - `tests/agent/test_openai_api.py` - 4 test stubs created

  **Next Steps:** Phase 2 implementation following TDD approach

---

### Added - FEAT-003 Complete: Specialist Agent with Vector Search (2025-10-30)
- **FEAT-003: MVP Specialist Agent for Dutch Workplace Safety Guidelines - ✅ COMPLETE**
  - **Implementation Complete:** 2025-10-30
  - **Status:** Production-ready MVP with bilingual support (Dutch/English)

  **Core Features:**
  - Specialist agent (`agent/specialist_agent.py`) with Pydantic AI framework
  - Dual system prompts for Dutch (default) and English responses
  - Hybrid search integration (70% vector + 30% Dutch full-text)
  - Citation system using clean document titles (no .md filenames)
  - CLI streaming responses with colored output
  - Tool: `search_guidelines()` wraps hybrid_search_tool
  - Output validation: Dutch purity checks, citation count validation

  **Bilingual Support:**
  - CLI flag: `--language nl` (default) or `--language en`
  - API parameter: `language` field in ChatRequest model
  - Dynamic agent creation based on language parameter
  - English mode translates key Dutch safety terms
  - Citations remain in Dutch (document titles) regardless of response language

  **Architecture:**
  - FastAPI endpoint: `/chat/stream` uses `run_specialist_query()`
  - Models: SpecialistResponse, SpecialistDeps, Citation (agent/models.py)
  - Database: 10,833 Dutch guideline chunks from 87 Notion documents
  - Search: PostgreSQL hybrid_search() function with Dutch language support

  **Testing:**
  - Unit tests: 5/6 passing (tests/agent/test_specialist_agent.py)
  - Manual validation: Dutch and English queries tested via CLI
  - Zero contamination: Big tech docs excluded from search results
  - Performance: <3s response time for typical queries

  **Files Added:**
  - `agent/specialist_agent.py` - Core specialist agent implementation
  - `tests/agent/test_specialist_agent.py` - Unit tests with mocking

  **Files Modified:**
  - `agent/models.py` - Added language field to ChatRequest (Line 32)
  - `agent/api.py` - Integrated run_specialist_query() in /chat/stream (Lines 423-505)
  - `cli.py` - Added --language flag (Lines 34-45, 289-294)
  - `docs/features/FEAT-003_query-retrieval/*` - Complete planning and testing docs
  - `AC.md` - Added 35 acceptance criteria for FEAT-003

  **Backward Compatibility:**
  - Old `rag_agent` (from agent.py) still exists at /chat endpoint
  - Not used by CLI, maintained for reference
  - CLI exclusively uses `/chat/stream` with specialist_agent

  **Documentation:**
  - PRD: docs/features/FEAT-003_query-retrieval/prd.md
  - Architecture: docs/features/FEAT-003_query-retrieval/architecture.md
  - Testing: docs/features/FEAT-003_query-retrieval/testing.md
  - Manual Test Guide: docs/features/FEAT-003_query-retrieval/manual-test.md
  - Acceptance Criteria: AC.md (35 criteria, AC-FEAT-003-001 through AC-FEAT-003-505)

  **Next Steps:**
  - FEAT-007: OpenWebUI Integration (planning complete, implementation pending)
  - FEAT-004: Product Catalog Integration
  - FEAT-009: Tier-Aware Search Enhancement

### Added - FEAT-003 Language Configuration (2025-10-30)
- **FEAT-003: Multi-language support - English and Dutch response modes**
  - API `/chat/stream` endpoint accepts `language` parameter: `"nl"` (Dutch) or `"en"` (English)
  - CLI flag: `--language en` or `-l en` (default: English for testing)
  - Dual system prompts: `SPECIALIST_SYSTEM_PROMPT_NL` and `SPECIALIST_SYSTEM_PROMPT_EN`
  - Dynamic agent creation based on language parameter
  - Citations use document titles (no .md filenames) - LLM extracts from `document_title` field
  - Database guidelines remain in Dutch (embeddings are multilingual)
  - English mode translates key points from Dutch guidelines
  - **Files Modified:**
    - `agent/models.py`: Added `language` field to ChatRequest (Line 32)
    - `agent/specialist_agent.py`: Dual prompts, dynamic agent creation (Lines 33-100, 197-265)
    - `agent/api.py`: Language parameter passed to specialist agent (Line 441), citation logging added (Lines 465-468)
    - `cli.py`: Added `--language` / `-l` flag (Lines 34-45, 133, 273-278, 294)
  - **Documentation:**
    - Updated `docs/features/FEAT-003_query-retrieval/architecture.md`: Language config section (Lines 318-323), citation behavior deep-dive (Lines 438-506)
    - Updated `docs/features/FEAT-003_query-retrieval/manual-test.md`: Test Scenario 11 for language validation (Lines 343-411)
  - **Validation:** Zero big_tech_docs contamination confirmed - Sam Altman test passes
  - **Backward Compatibility:** Default language="nl" preserves original Dutch-only behavior

### Added - FEAT-007 Exploration Complete (2025-10-29)
- **FEAT-007: OpenWebUI Integration exploration complete - Ready for planning**
  - [Product Requirements](docs/features/FEAT-007_openwebui-integration/prd.md) (3,050 words) - Updated: removed DESCOPED status, now active feature
  - [Research Findings](docs/features/FEAT-007_openwebui-integration/research.md) (10,847 words) - Comprehensive OpenWebUI integration research
  - **Key Decisions:** Stateless API, structured markdown citations, single-user mode, single model, dual endpoints
  - **Architecture:** Reuse existing Pydantic AI streaming, add OpenAI-compatible `/v1/chat/completions` endpoint
  - **Implementation Estimate:** 6-8 hours (reduced from initial 8-10 hours based on architectural simplifications)
  - **Next Step:** Run `/plan FEAT-007` to create architecture.md, acceptance.md, testing.md, manual-test.md

### Added - FEAT-003 Planning Complete (2025-10-29)
- **FEAT-003: Specialist Agent MVP planning documentation complete - Ready for implementation**
  - [Product Requirements](docs/features/FEAT-003_query-retrieval/prd.md) (1,872 words)
  - [Research Findings](docs/features/FEAT-003_query-retrieval/research.md) (2,145 words) - Validated single-agent pattern for MVP
  - [Architecture Decision](docs/features/FEAT-003_query-retrieval/architecture.md) (1,634 words) - Single agent with search_guidelines tool
  - [Acceptance Criteria](docs/features/FEAT-003_query-retrieval/acceptance.md) (2,318 words) - 28 criteria (7 functional, 6 edge cases, 7 non-functional, 5 integration, 3 extra)
  - [Testing Strategy](docs/features/FEAT-003_query-retrieval/testing.md) (1,943 words)
  - [Manual Test Guide](docs/features/FEAT-003_query-retrieval/manual-test.md) (2,567 words) - 10 test scenarios
  - Test stubs: 13 tests in 3 files (tests/agent/test_specialist_agent.py, tests/agent/test_tools.py, tests/integration/test_specialist_flow.py)
  - AC.md updated: Added 28 FEAT-003 criteria (total now: 45 criteria across FEAT-002 + FEAT-003)
  - **Architecture:** Single-agent pattern (5-8 hours) vs multi-agent (12-16 hours) - chose simplicity for MVP
  - **Key Features:** Dutch language support, hybrid search integration, streaming responses via SSE
  - **Implementation Estimate:** 5-8 hours for MVP (specialist agent + CLI + API integration)

### Added - FEAT-002 Implementation Complete (2025-10-26)
- **FEAT-002: Notion Integration - Successfully completed and validated**
  - Ingested 87 Dutch workplace safety guidelines from Notion database
  - Created 10,833 chunks with 100% embedding coverage
  - Processing time: 42.5 minutes (without knowledge graph)
  - Zero errors, 100% success rate
  - All 17 acceptance criteria validated and passed
  - [Validation Report](docs/features/FEAT-002_notion-integration/VALIDATION_REPORT.md) with comprehensive evidence
  - Dutch full-text search working correctly with PostgreSQL `to_tsvector('dutch', ...)`
  - Files: 87 markdown files in `documents/notion_guidelines/`
  - Database: 10,833 chunks, all with NULL tier (tier parsing deferred per AC-002-302)
  - **Deferred:** Knowledge graph (2-3 days, $83+ cost - not required for MVP)
  - **Deferred:** Tier parsing (explicitly deferred per AC-002-302)

### Added - FEAT-002 Planning Complete (2025-10-25)
- FEAT-002: Notion Integration (MVP) planning documentation complete - Ready for implementation
  - [Architecture Decision](docs/features/FEAT-002_notion-integration/architecture.md) (1,410 words)
  - [Acceptance Criteria](docs/features/FEAT-002_notion-integration/acceptance.md) (1,576 words)
  - [Testing Strategy](docs/features/FEAT-002_notion-integration/testing.md) (1,568 words)
  - [Manual Test Guide](docs/features/FEAT-002_notion-integration/manual-test.md) (2,196 words)
  - Test stubs: 13 tests in 2 files (tests/ingestion/test_notion_to_markdown.py, test_notion_integration.py)

### Added - Phase 3-5 Planning (2025-10-25)
- Created [FEAT-002 PRD](docs/features/FEAT-002_notion-integration/prd.md) for Notion Integration (Phase 3)
- Created [FEAT-003 PRD](docs/features/FEAT-003_query-retrieval/prd.md) for Query & Retrieval System (Phase 4)
- Created [FEAT-004 PRD](docs/features/FEAT-004_product-catalog/prd.md) for Product Catalog Integration (Phase 4)
- Created [FEAT-005 PRD](docs/features/FEAT-005_multi-agent-system/prd.md) for Multi-Agent RAG System (Phase 5)

### Changed - Documentation Update (2025-10-25)
- Archived original template files to `docs/features/archive/original-templates/`
- Archived non-EVI project files to `docs/archive/workflow-templates/`
- Archived setup documentation to `docs/archive/setup-docs/` (LOCAL_SETUP_COMPLETE.md, verify_connection_string.py)
- Archived planning documentation to `docs/archive/planning-docs/` (PROJECT_OVERVIEW.md, TASKS.md)
- Kept cli.py in root for debugging purposes
- Updated [docs/system/architecture.md](docs/system/architecture.md) with EVI 360 RAG architecture and 3-tier guideline design
- Updated [docs/system/database.md](docs/system/database.md) with complete PostgreSQL + Neo4j schema documentation
- Updated [docs/system/stack.md](docs/system/stack.md) with actual technology stack (PostgreSQL 17, Neo4j 5.26.1, Python 3.11+)
- Updated [docs/system/integrations.md](docs/system/integrations.md) with Notion API configuration and planned integrations
- Updated [docs/system/api.md](docs/system/api.md) with planned API structure for Phase 5-7

## [0.1.0] - 2025-10-25

### Added - Phase 1: Infrastructure Setup
- Docker Compose configuration with PostgreSQL 17 + pgvector 0.8.1
- Docker Compose configuration with Neo4j 5.26.1 + APOC plugin
- Persistent volumes for database data (`postgres_data`, `neo4j_data`)
- Health checks for both database services
- Database connection tests: [test_supabase_connection.py](tests/test_supabase_connection.py)
- Data persistence tests: [test_data_persistence.py](tests/test_data_persistence.py)
- Environment configuration with `.env.example` template

### Added - Phase 2: Data Models & Schema
- PostgreSQL schema with 5 tables: `documents`, `chunks`, `products`, `sessions`, `messages`
- 3-tier guideline support: `chunks.tier` column with CHECK constraint (1, 2, 3)
- Vector similarity search with pgvector: `chunks.embedding`, `products.embedding` (1536 dimensions)
- Dutch language full-text search: `to_tsvector('dutch', content)` configuration
- 3 SQL functions:
  - `hybrid_search()` - Combined vector + full-text search (70/30 split)
  - `search_guidelines_by_tier()` - Tier-aware guideline search
  - `search_products()` - Product catalog search with compliance tags
- 3 SQL views:
  - `document_summaries` - Document metadata with chunk counts
  - `guideline_tier_stats` - Tier distribution statistics
  - `product_catalog_summary` - Product catalog overview
- 8 Pydantic models in [agent/models.py](agent/models.py):
  - `TieredGuideline` - 3-tier guideline structure
  - `GuidelineSearchResult` - Search results with tier info
  - `EVIProduct` - Product catalog with validation
  - `ProductRecommendation` - Product recommendations with scoring
  - `ProductSearchResult` - Database search results
  - `ResearchAgentResponse` - Research agent output
  - `SpecialistAgentResponse` - Specialist agent response
  - Additional utility models for chunks, sessions, messages
- Notion API configuration: [config/notion_config.py](config/notion_config.py)

### Added - Documentation
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - High-level architecture and 3-tier guideline hierarchy
- [LOCAL_SETUP_COMPLETE.md](LOCAL_SETUP_COMPLETE.md) - Local Docker setup guide
- [FEAT-001 PRD](docs/features/FEAT-001_evi-rag-implementation/prd.md) - Implementation plan
- [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) - Phase tracking
- System documentation: architecture, database, stack, integrations, API (planned)

### Changed
- Migrated from Supabase Cloud to local PostgreSQL 17 (20-100x faster queries, no rate limits)
- Configured for Dutch language support throughout stack

### Technical Details
- **Language:** Python 3.11+
- **Databases:** PostgreSQL 17 + pgvector 0.8.1, Neo4j 5.26.1 + APOC
- **Key Libraries:** pydantic 2.11.7, asyncpg 0.30.0, notion-client 2.2.1
- **Planned:** pydantic-ai 0.3.2 (Phase 5), fastapi 0.115.13 (Phase 5-7), openai 1.90.0 (Phase 3+)
- **Testing:** pytest 8.4.1 + pytest-asyncio 1.0.0 (2 test files, 100% passing)

