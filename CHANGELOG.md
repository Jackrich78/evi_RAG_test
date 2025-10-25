# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 3-5 Planning (2025-10-25)
- Created [FEAT-002 PRD](docs/features/FEAT-002_notion-integration/prd.md) for Notion Integration (Phase 3)
- Created [FEAT-003 PRD](docs/features/FEAT-003_product-ingestion/prd.md) for Product Ingestion (Phase 4)
- Created [FEAT-004 PRD](docs/features/FEAT-004_multi-agent-system/prd.md) for Multi-Agent System (Phase 5)

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

