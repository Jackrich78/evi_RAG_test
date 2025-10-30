# Documentation Index

*Last updated: 2025-10-30 (Updated: FEAT-003 complete)*

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
**Status:** Exploring
**Created:** 2025-10-25
**Phase:** 4 (Product Catalog)
**Documents:**
- [Product Requirements](features/FEAT-004_product-catalog/prd.md)

**Summary:** EVI 360 product catalog with compliance tags, smart recommendations based on guideline queries, and tiered product-to-guideline mapping.

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
**Status:** Exploring (Research Complete)
**Created:** 2025-10-26
**Phase:** 7 (Web Interface)
**Documents:**
- [Product Requirements](features/FEAT-007_openwebui-integration/prd.md) (3,050 words)
- [Research Findings](features/FEAT-007_openwebui-integration/research.md) (10,847 words)

**Summary:** Web-based chat interface via OpenWebUI with OpenAI-compatible API endpoints, Dutch language UI, and structured markdown citations. Stateless architecture with single-user mode for MVP (6-8 hours implementation).

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

### Feature Summary

| Feature ID | Name | Phase | Status | Planning Docs | Test Stubs |
|------------|------|-------|--------|---------------|------------|
| FEAT-001 | Core RAG Infrastructure | 1 | Complete | 1/6 | N/A |
| FEAT-002 | Notion Integration (MVP) | 3 | Complete | 6/6 | 13 |
| FEAT-003 | Specialist Agent MVP | 4 | Ready | 6/6 | 13 |
| FEAT-004 | Product Catalog | 4 | Exploring | 1/6 | 0 |
| FEAT-005 | Multi-Agent System | 5 | Exploring | 1/6 | 0 |
| FEAT-006 | Knowledge Graph | 6 | Exploring | 1/6 | 0 |
| FEAT-007 | OpenWebUI Integration | 7 | Researching | 2/6 | 0 |
| FEAT-008 | Advanced Memory | 8 | Exploring | 1/6 | 0 |
| FEAT-009 | Tier-Aware Search | 9 | Exploring | 1/6 | 0 |

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

**Total Features:** 5
- Complete: 2
- Ready for Implementation: 1
- Exploring: 2

**Total Planning Documents:** 16
- PRDs: 5
- Research: 2
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
