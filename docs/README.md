# Documentation Index

*Last updated: 2025-11-03*

## Overview

This documentation index provides a comprehensive map of all project documentation, organized by category and feature status.

---

## Features

### Completed Features

#### [FEAT-002: Notion Integration](features/FEAT-002_notion-integration/)
**Status:** Implemented and Validated
**Completed:** 2025-10-29
**Documents:**
- [Product Requirements](features/FEAT-002_notion-integration/prd.md)
- [Research Findings](features/FEAT-002_notion-integration/research.md)
- [Architecture Decision](features/FEAT-002_notion-integration/architecture.md)
- [Acceptance Criteria](features/FEAT-002_notion-integration/acceptance.md)
- [Testing Strategy](features/FEAT-002_notion-integration/testing.md)
- [Manual Test Guide](features/FEAT-002_notion-integration/manual-test.md)
- [Completion Summary](features/FEAT-002_notion-integration/COMPLETION_SUMMARY.md)
- [Validation Report](features/FEAT-002_notion-integration/VALIDATION_REPORT.md)

#### [FEAT-003: Query and Retrieval System](features/FEAT-003_query-retrieval/)
**Status:** Implemented
**Completed:** 2025-10-30
**Documents:**
- [Product Requirements](features/FEAT-003_query-retrieval/prd.md)
- [Research Findings](features/FEAT-003_query-retrieval/research.md)
- [Architecture Decision](features/FEAT-003_query-retrieval/architecture.md)
- [Acceptance Criteria](features/FEAT-003_query-retrieval/acceptance.md)
- [Testing Strategy](features/FEAT-003_query-retrieval/testing.md)
- [Manual Test Guide](features/FEAT-003_query-retrieval/manual-test.md)
- [Implementation Guide](features/FEAT-003_query-retrieval/implementation-guide.md)
- [Testing Guide](features/FEAT-003_query-retrieval/TESTING_GUIDE.md)

#### [FEAT-007: OpenWebUI Integration](features/FEAT-007_openwebui-integration/) ⭐ NEW
**Status:** Implemented with POST-MVP Fixes
**Completed:** 2025-11-01
**Documents:**
- [Product Requirements](features/FEAT-007_openwebui-integration/prd.md)
- [Research Findings](features/FEAT-007_openwebui-integration/research.md)
- [Architecture Decision](features/FEAT-007_openwebui-integration/architecture.md)
- [Acceptance Criteria](features/FEAT-007_openwebui-integration/acceptance.md)
- [Testing Strategy](features/FEAT-007_openwebui-integration/testing.md)
- [Manual Test Guide](features/FEAT-007_openwebui-integration/manual-test.md)
- [Post-MVP Fixes](features/FEAT-007_openwebui-integration/post-mvp.md) - **Critical bug fixes**

**Recent Changes:**
- Fixed streaming TransferEncodingError with SSE headers and error handling
- Implemented clickable citation URLs with markdown link formatting
- Added language auto-detection (English/Dutch) with single prompt
- All three POST-MVP issues resolved and tested

### In Progress

#### [FEAT-010: SSE Streaming](features/FEAT-010_streaming/) ⭐ RECENTLY UPDATED
**Status:** Implemented - Bug Fix Applied
**Updated:** 2025-11-01
**Documents:**
- [Product Requirements](features/FEAT-010_streaming/prd.md)
- [Research Findings](features/FEAT-010_streaming/research.md)
- [Architecture Decision](features/FEAT-010_streaming/architecture.md)
- [Acceptance Criteria](features/FEAT-010_streaming/acceptance.md)
- [Testing Strategy](features/FEAT-010_streaming/testing.md)
- [Manual Test Guide](features/FEAT-010_streaming/manual-test.md)
- [Implementation Guide](features/FEAT-010_streaming/implementation.md) - **Updated with bug fix**
- [Learnings](features/FEAT-010_streaming/learnings.md)
- [Planning Complete](features/FEAT-010_streaming/planning_complete.md)

**Recent Changes:**
- Fixed missing `await` on `result.get_output()` in `specialist_agent.py` line 400
- Updated test documentation with correct Pydantic AI streaming pattern
- Streaming now fully functional and tested

### Ready for Implementation

#### [FEAT-004: Product Catalog with Interventie Wijzer Integration](features/FEAT-004_product-catalog/) ⭐ MERGED FEAT-011
**Status:** Planning Complete - Ready for Build
**Updated:** 2025-11-03 (Merged FEAT-011 scope)
**Scope:** Portal scraping + CSV problem mappings + hybrid search
**Dependencies:** FEAT-002 ✅, FEAT-003 ✅
**Blocks:** FEAT-012
**Estimated:** 14 hours
**Documents:**
- [Product Requirements v3](features/FEAT-004_product-catalog/prd.md) - **Merged FEAT-011**
- [Research Findings](features/FEAT-004_product-catalog/research.md)
- [Archived v1 Planning](features/FEAT-004_product-catalog/archive/) - Original broad-scope docs
- [Interventie Wijzer Data](features/FEAT-004_product-catalog/Interventiewijzer.md) - 5-step methodology
- [Intervention Matrix CSV](features/FEAT-004_product-catalog/Intervention_matrix.csv) - 33 problem-intervention mappings

**Recent Changes:**
- ✅ **MERGED FEAT-011** into FEAT-004 (scope consolidation)
- Changed from Notion to portal.evi360.nl web scraping (Crawl4AI)
- Integrated interventie wijzer CSV (33 problem-product mappings)
- Fuzzy matching CSV→portal products (≥0.9 threshold)
- Hybrid search: 70% vector + 30% Dutch text
- Embedding: 1 product = 1 embedding (NO chunking)

**What It Does:**
- Scrape ~60 products from portal.evi360.nl
- Parse Intervention_matrix.csv for problem mappings
- Enrich metadata with problem_mappings
- Generate embeddings (description + problems)
- Enable hybrid search for agent recommendations

#### [FEAT-012: Two-Stage Search Protocol & Product-Guideline Linking](features/FEAT-012_two-stage-search/) ⭐ NEW
**Status:** Planning Complete - Blocked by FEAT-004
**Created:** 2025-11-03
**Scope:** Stage 1 candidate generation + Stage 2 LLM ranking + product-guideline linking
**Dependencies:** FEAT-004 (blocking)
**Estimated:** 20 hours
**Documents:**
- [Product Requirements](features/FEAT-012_two-stage-search/prd.md)

**What It Does:**
- Stage 1: Fast vector search (50 candidates, <100ms)
- Stage 2: LLM contextual ranking with weighted scoring (impact 0.4, fit 0.3, guidelines 0.2, feasibility 0.1)
- Apply interventie wijzer 5-step methodology in LLM prompt
- Link products to relevant Dutch guidelines (citations)
- Display product URLs in recommendations
- Improve search relevance from ~85% to ~90%

#### [FEAT-008: Advanced Memory - Stateless Multi-Turn Conversations](features/FEAT-008_advanced-memory/) ✅
**Status:** Implemented
**Completed:** 2025-11-03
**Pattern:** Pure Stateless (OpenWebUI sends full history)
**Documents:**
- [Product Requirements v2](features/FEAT-008_advanced-memory/prd-v2.md)
- [Architecture Decision v2](features/FEAT-008_advanced-memory/architecture-v2.md) - Stateless message conversion
- [Acceptance Criteria v2](features/FEAT-008_advanced-memory/acceptance-v2.md) - 20 criteria (6 functional + 9 edge cases + 5 non-functional)
- [Testing Strategy v2](features/FEAT-008_advanced-memory/testing-v2.md)
- [Manual Test Guide v2](features/FEAT-008_advanced-memory/manual-test-v2.md)
- [Planning Summary](features/FEAT-008_advanced-memory/planning-summary.md)
- [OpenWebUI Session Research](features/FEAT-008_advanced-memory/openwebui-session-findings.md) - 4 hours of investigation

**Key Implementation:**
- `convert_openai_to_pydantic_history()` function (82 lines with docstring)
- Zero database queries for session management
- Sub-5ms conversion latency
- Horizontally scalable (no server-side state)
- OpenWebUI native integration via `/v1/chat/completions` endpoint

**Archive Reference:**
- [v1 Incorrect Assumptions (archived)](features/archive/FEAT-008_incorrect_assumptions/) - Original database-backed approach based on incorrect assumptions about OpenWebUI behavior

### Exploring (PRD Only)

#### [FEAT-001: Core Infrastructure](features/FEAT-001_core-infrastructure/)
**Status:** Exploring
- [Product Requirements](features/FEAT-001_core-infrastructure/prd.md)

#### [FEAT-005: Multi-Agent System](features/FEAT-005_multi-agent-system/)
**Status:** Exploring
- [Product Requirements](features/FEAT-005_multi-agent-system/prd.md)

#### [FEAT-006: Knowledge Graph](features/FEAT-006_knowledge-graph/)
**Status:** Exploring
- [Product Requirements](features/FEAT-006_knowledge-graph/prd.md)

#### [FEAT-008: Advanced Memory](features/FEAT-008_advanced-memory/)
**Status:** Exploring
- [Product Requirements](features/FEAT-008_advanced-memory/prd.md)

#### [FEAT-009: Tier-Aware Search](features/FEAT-009_tier-aware-search/)
**Status:** Exploring
- [Product Requirements](features/FEAT-009_tier-aware-search/prd.md)

---

## System Documentation

Technical architecture and integration documentation:

- [Architecture Overview](system/architecture.md) - System design and component interactions
- [Technology Stack](system/stack.md) - Technologies, frameworks, and tools
- [Database Design](system/database.md) - Schema, models, and data flow
- [API Documentation](system/api.md) - Endpoints, request/response formats
- [Integrations](system/integrations.md) - External services and MCP servers

---

## Standard Operating Procedures

Development standards and workflows:

- [Git Workflow](sop/git-workflow.md) - Branching, commits, PRs
- [Testing Strategy](sop/testing-strategy.md) - How we test (pytest, coverage)
- [Code Style](sop/code-style.md) - Linting (black, ruff), formatting, type hints
- [GitHub Setup](sop/github-setup.md) - Repository setup and CI/CD
- [Lessons Learned](sop/mistakes.md) - Gotchas to avoid
- [SOP Template](sop/sop-template.md) - Standard operating procedure template

---

## Templates

Document scaffolding for consistent planning:

- [PRD Template](templates/prd-template.md) - Product requirements structure
- [Research Template](templates/research-template.md) - Research documentation format
- [Architecture Template](templates/architecture-template.md) - Architecture decision records
- [Acceptance Template](templates/acceptance-template.md) - Acceptance criteria format
- [Testing Template](templates/testing-template.md) - Test strategy structure
- [Manual Test Template](templates/manual-test-template.md) - Manual testing guide format

---

## Archive

Historical documentation and deprecated content:

- [Original Templates](features/archive/original-templates/) - Pre-workflow templates
- [Old Feature Structure](features/archive/old-structure/) - Legacy feature docs
- [Planning Documents](archive/planning-docs/) - Initial project planning
- [Setup Documentation](archive/setup-docs/) - Historical setup guides
- [Workflow Templates](archive/workflow-templates/) - Legacy workflow docs

---

## Implementation Progress

Current development status: [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md)

---

## Quick Links

- **Project Root:** [README.md](../README.md)
- **Configuration:** [CLAUDE.md](../CLAUDE.md) - AI assistant configuration
- **Acceptance Criteria:** [AC.md](../AC.md) - Global acceptance criteria
- **Changelog:** [CHANGELOG.md](../CHANGELOG.md) - Project changelog

---

## Documentation Statistics

**Total Features:** 10
- Completed: 2
- In Progress: 1
- Ready for Build: 2
- Exploring: 5

**Total Documents:** 77 markdown files
- Feature Documentation: 65 files
- System Documentation: 5 files
- SOPs: 6 files
- Templates: 6 files

**Last Documentation Update:** 2025-11-01 by Documenter Agent

---

*This index is auto-generated by the Documenter agent. Do not edit manually.*
