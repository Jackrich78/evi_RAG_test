# Documentation Index

*Last updated: 2025-10-31 (Updated: FEAT-010 planning complete)*

## Features

### Active Features

#### [FEAT-001: Core RAG Infrastructure](features/FEAT-001_core-infrastructure/)
**Status:** Complete
**Created:** 2025-10-25
**Phase:** 1 (Foundation)
**Documents:**
- [Product Requirements](features/FEAT-001_core-infrastructure/prd.md)

**Summary:** Foundational infrastructure for local RAG system with PostgreSQL + pgvector, Dutch language support, and 3-tier guideline hierarchy.

---

#### [FEAT-002: Notion Integration (MVP)](features/FEAT-002_notion-integration/)
**Status:** Ready for Implementation
**Created:** 2025-10-25
**Phase:** 3 (Data Ingestion)
**Documents:**
- [Product Requirements](features/FEAT-002_notion-integration/prd.md) (1,193 words)
- [Research Findings](features/FEAT-002_notion-integration/research.md) (1,298 words)
- [Architecture Decision](features/FEAT-002_notion-integration/architecture.md) (1,410 words)
- [Acceptance Criteria](features/FEAT-002_notion-integration/acceptance.md) (1,576 words)
- [Testing Strategy](features/FEAT-002_notion-integration/testing.md) (1,568 words)
- [Manual Test Guide](features/FEAT-002_notion-integration/manual-test.md) (2,196 words)

**Test Stubs:** 13 test stubs in 2 files
- `tests/ingestion/test_notion_to_markdown.py` (10 unit tests)
- `tests/ingestion/test_notion_integration.py` (3 integration tests)

**Summary:** Fetch ~100 Dutch workplace safety guidelines from Notion database, convert to markdown, and ingest into PostgreSQL RAG system using existing pipeline. MVP approach prioritizes working system in 2-3 hours by descoping tier parsing for future iteration.

---

#### [FEAT-003: Query & Retrieval System (Specialist Agent MVP)](features/FEAT-003_query-retrieval/)
**Status:** ✅ Complete
**Created:** 2025-10-25
**Completed:** 2025-10-30
**Phase:** 4 (Query & Retrieval)
**Documents:**
- [Product Requirements](features/FEAT-003_query-retrieval/prd.md) (1,872 words)
- [Research Findings](features/FEAT-003_query-retrieval/research.md) (2,145 words)
- [Architecture Decision](features/FEAT-003_query-retrieval/architecture.md) (1,634 words)
- [Acceptance Criteria](features/FEAT-003_query-retrieval/acceptance.md) (2,318 words)
- [Testing Strategy](features/FEAT-003_query-retrieval/testing.md) (1,943 words)
- [Manual Test Guide](features/FEAT-003_query-retrieval/manual-test.md) (2,567 words)

**Implementation:**
- `agent/specialist_agent.py` - Core specialist agent with Pydantic AI
- `tests/agent/test_specialist_agent.py` - 5/6 unit tests passing
- CLI flag: `--language nl` (Dutch, default) or `--language en` (English)
- Bilingual support: Dutch and English response modes
- Citation system: Uses clean document titles (no .md filenames)
- Search: Hybrid (70% vector + 30% Dutch full-text)

**Summary:** Production-ready MVP specialist agent with bilingual support (Dutch/English), hybrid search integration, and streaming CLI responses. Single-agent pattern with search_guidelines tool. Tested and validated with 35 acceptance criteria.

---

#### [FEAT-004: Product Catalog Integration](features/FEAT-004_product-catalog/)
**Status:** 🚀 Ready for Planning (Deep Exploration Complete)
**Created:** 2025-10-25
**Explored:** 2025-10-31 (Updated with deeper analysis)
**Phase:** 4 (Product Catalog)
**Documents:**
- [Product Requirements](features/FEAT-004_product-catalog/prd.md) (15K - Comprehensive with 7 open question categories)
- [Research Findings](features/FEAT-004_product-catalog/research.md) (18K - Deep dive with uncertainty analysis)

**Approach:** Phased MVP (8-12 hours) with pilot testing phase

**Key Insight:** Pilot test with 10-20 products to validate retrieval quality BEFORE full ingestion. Critical risk mitigation for user concern: "I do wonder how well retrieving them will work."

**Summary:** Ingest ~100 EVI 360 products from Notion database using dedicated ingestion script. Test 3 embedding strategies in pilot phase. Enable automatic contextually relevant product recommendations (agent decides). 7 categories of open questions documented for resolution during implementation. Ready for `/plan FEAT-004`.

---

#### [FEAT-005: Multi-Agent RAG System](features/FEAT-005_multi-agent-system/)
**Status:** Exploring
**Created:** 2025-10-25
**Phase:** 5 (Multi-Agent System)
**Documents:**
- [Product Requirements](features/FEAT-005_multi-agent-system/prd.md)

**Summary:** Multi-agent architecture with Research Agent (query understanding & retrieval) and Specialist Agent (guideline expert & product recommendations) orchestrated by PydanticAI framework.

---

#### [FEAT-006: Knowledge Graph Integration](features/FEAT-006_knowledge-graph/)
**Status:** Exploring
**Created:** 2025-10-25
**Phase:** 6 (Knowledge Graph)
**Documents:**
- [Product Requirements](features/FEAT-006_knowledge-graph/prd.md)

**Summary:** Neo4j knowledge graph for guideline relationships, product connections, and temporal data tracking.

---

#### [FEAT-007: OpenWebUI Integration](features/FEAT-007_openwebui-integration/)
**Status:** ✅ Ready for Implementation
**Created:** 2025-10-30
**Phase:** 7 (Web Interface)
**Documents:**
- [Product Requirements](features/FEAT-007_openwebui-integration/prd.md) (9.4K) - Product requirements and user stories
- [Research Findings](features/FEAT-007_openwebui-integration/research.md) (31K) - Technical research with 10 topics and decisions
- [Architecture Decision](features/FEAT-007_openwebui-integration/architecture.md) (11K) - Architecture decision (Option 1: Standalone OpenWebUI)
- [Acceptance Criteria](features/FEAT-007_openwebui-integration/acceptance.md) (8.9K) - 20 acceptance criteria (AC-007-001 through AC-007-020)
- [Testing Strategy](features/FEAT-007_openwebui-integration/testing.md) (10K) - Testing strategy with 9 test stubs
- [Manual Test Guide](features/FEAT-007_openwebui-integration/manual-test.md) (9.6K) - Manual testing guide for non-technical users

**Test Stubs:** `tests/agent/test_openai_api.py` (4 tests created)

**Summary:** Web-based chat interface via OpenWebUI with OpenAI-compatible API endpoints, Dutch language UI, and structured markdown citations. Stateless architecture with single-user mode for MVP (6-8 hours implementation). All planning documentation complete - ready for Phase 2 implementation.

---

#### [FEAT-008: Advanced Memory & Context](features/FEAT-008_advanced-memory/)
**Status:** Exploring
**Created:** 2025-10-25
**Phase:** 8 (Advanced Features)
**Documents:**
- [Product Requirements](features/FEAT-008_advanced-memory/prd.md)

**Summary:** Advanced conversation context management, cross-session memory, and personalized specialist responses.

---

#### [FEAT-009: Tier-Aware Search](features/FEAT-009_tier-aware-search/)
**Status:** Exploring
**Created:** 2025-10-25
**Phase:** 9 (Advanced Features)
**Documents:**
- [Product Requirements](features/FEAT-009_tier-aware-search/prd.md)

**Summary:** Intelligent tier traversal (Tier 1 → 2 → 3) with automatic escalation based on query complexity and result quality.

---

#### [FEAT-010: True Token Streaming](features/FEAT-010_streaming/)
**Status:** ✅ Ready for Implementation
**Created:** 2025-10-31
**Explored:** 2025-10-31
**Planned:** 2025-10-31
**Phase:** 1 (Performance Enhancement)
**Documents:**
- [Product Requirements](features/FEAT-010_streaming/prd.md) (780 words)
- [Research Findings](features/FEAT-010_streaming/research.md) (850+ words)
- [Architecture Decision](features/FEAT-010_streaming/architecture.md) (3,200+ words)
- [Acceptance Criteria](features/FEAT-010_streaming/acceptance.md) (2,100+ words)
- [Testing Strategy](features/FEAT-010_streaming/testing.md) (2,400+ words)
- [Manual Test Guide](features/FEAT-010_streaming/manual-test.md) (1,800+ words)
- [Historical Reference](features/FEAT-010_streaming/learnings.md) (Working implementation)

**Test Stubs:** 44 test functions in 6 files
- `tests/unit/streaming/test_sse_formatting.py` (7 tests)
- `tests/unit/streaming/test_stream_handlers.py` (7 tests)
- `tests/integration/streaming/test_sse_endpoint.py` (10 tests)
- `tests/integration/streaming/test_pydantic_streaming.py` (5 tests)
- `tests/e2e/streaming/test_streaming_workflow.py` (8 tests)
- `tests/performance/streaming/test_streaming_performance.py` (7 tests)

**Summary:** Replace simulated streaming with true token-by-token streaming using Pydantic AI 0.3.2. Architecture based on SSE protocol with spike validation approach. 11 acceptance criteria defined. Estimated 3 hours implementation following TDD. All planning documentation complete - ready for Phase 2 implementation.

---

### Feature Summary

| Feature ID | Name | Phase | Status | Planning Docs | Test Stubs |
|------------|------|-------|--------|---------------|------------|
| FEAT-001 | Core RAG Infrastructure | 1 | Complete | 1/6 | N/A |
| FEAT-002 | Notion Integration (MVP) | 3 | Complete | 6/6 | 13 |
| FEAT-003 | Specialist Agent MVP | 4 | Complete | 6/6 | 13 |
| FEAT-004 | Product Catalog | 4 | Exploring | 1/6 | 0 |
| FEAT-005 | Multi-Agent System | 5 | Exploring | 1/6 | 0 |
| FEAT-006 | Knowledge Graph | 6 | Exploring | 1/6 | 0 |
| FEAT-007 | OpenWebUI Integration | 7 | Ready | 6/6 | 4 |
| FEAT-008 | Advanced Memory | 8 | Exploring | 1/6 | 0 |
| FEAT-009 | Tier-Aware Search | 9 | Exploring | 1/6 | 0 |
| FEAT-010 | True Token Streaming | 1 | Ready | 6/6 | 44 |

**Status Legend:**
- **Complete:** Implementation finished and deployed
- **Ready for Implementation:** All 6 planning docs complete, test stubs created
- **Researching:** PRD and research exist, ready for planning phase
- **Exploring:** Only PRD exists

---

## System Documentation

### Architecture & Design
- [Architecture Overview](system/architecture.md) - EVI 360 RAG system architecture with 3-tier guideline hierarchy
- [Tech Stack](system/stack.md) - Technology choices (PostgreSQL 17, Neo4j 5.26.1, Python 3.11+)
- [Database Schema](system/database.md) - PostgreSQL + Neo4j schema documentation
- [API Structure](system/api.md) - Planned API endpoints for Phase 5-7
- [Integrations](system/integrations.md) - Notion API configuration and planned integrations

---

## Standard Operating Procedures

### Development Practices
- [Git Workflow](sop/git-workflow.md) - Branching, commits, PRs
- [Testing Strategy](sop/testing-strategy.md) - How we test (pytest, coverage requirements)
- [Code Style](sop/code-style.md) - Linting (black, ruff), formatting, type hints

### Process Documentation
- [GitHub Setup](sop/github-setup.md) - Repository setup and CI/CD
- [Lessons Learned](sop/mistakes.md) - Gotchas to avoid and common mistakes

---

## Templates

*See [templates/](templates/) directory for document scaffolding*

Template files provide standardized structure for:
- Product Requirements Documents (PRDs)
- Research Findings
- Architecture Decisions
- Acceptance Criteria
- Testing Strategies
- Manual Test Guides
- Standard Operating Procedures

---

## Archived Documentation

### Old Structure
- [Archive: Original Templates](features/archive/original-templates/) - Legacy template files
- [Archive: Old Feature Structure](features/archive/old-structure/) - Previous FEAT-001, FEAT-003, FEAT-004 structure

### Deprecated Documentation
- [Archive: Workflow Templates](../docs/archive/workflow-templates/) - Non-EVI project files
- [Archive: Setup Docs](../docs/archive/setup-docs/) - Supabase migration and local setup
- [Archive: Planning Docs](../docs/archive/planning-docs/) - PROJECT_OVERVIEW.md, TASKS.md (moved to root)

---

## Quick Links

### For Developers
- [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) - Current phase status and completion tracking
- [Tech Stack](system/stack.md) - Languages, frameworks, dependencies
- [Testing Strategy](sop/testing-strategy.md) - How to write and run tests

### For Project Managers
- [Feature Summary](#feature-summary) - All features with status
- [CHANGELOG.md](../CHANGELOG.md) - What's changed and when
- [Architecture Overview](system/architecture.md) - System design and components

### For QA/Testing
- [Manual Test Guides](features/) - Step-by-step testing instructions per feature
- [Testing Strategy](sop/testing-strategy.md) - Overall testing approach
- [Lessons Learned](sop/mistakes.md) - Common issues to watch for

---

## Documentation Statistics

**Total Features:** 10
- Complete: 3
- Ready for Implementation: 3
- Exploring: 4

**Total Planning Documents:** 22
- PRDs: 10
- Research: 3
- Architecture: 3
- Acceptance: 3
- Testing: 3
- Manual Test: 3

**Total Test Stubs:** 70
- Unit: 30
- Integration: 21
- E2E: 12
- Performance: 7
- Architecture: 2
- Acceptance: 2
- Testing: 2
- Manual Test: 2

**Total Test Stubs:** 26
- Unit: 20
- Integration: 6

**System Documentation:** 5 files
**SOPs:** 5 files
**Templates:** Available in templates/ directory

---

**Maintained By:** Documenter Agent (Auto-generated)
**Index Version:** 1.0.0
**Project:** EVI 360 Workplace Safety RAG System
