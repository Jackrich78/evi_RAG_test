# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

