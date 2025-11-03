# PRD: FEAT-001 - Core RAG Infrastructure

**Feature ID:** FEAT-001
**Phase:** 1 (Foundation)
**Status:** ✅ Complete
**Priority:** Critical
**Owner:** System

---

## Problem Statement

Build foundational infrastructure for a local RAG (Retrieval-Augmented Generation) knowledge base system. The system must support Dutch workplace safety guidelines with a 3-tier hierarchy, enable unlimited local storage without cloud costs, and provide flexible data ingestion from multiple sources (Notion, PDFs, documents).

**Key Requirements:**
- Local PostgreSQL database with vector search (no cloud dependencies)
- Dutch language full-text search support
- 3-tier guideline hierarchy (Summary → Key Facts → Details)
- Flexible schema for varied data sources
- Robust ingestion pipeline that can be reused

---

## Goals

1. **Infrastructure:** Local PostgreSQL 17 + pgvector 0.8.1 running in Docker
2. **Schema:** Database tables supporting tiered guidelines, products, sessions, messages
3. **Search:** Dutch language hybrid search (vector + full-text)
4. **Pipeline:** Reusable ingestion code (chunking, embedding, storage)
5. **Models:** Type-safe Pydantic data models for all entities

---

## User Stories

### Infrastructure Setup
**Given** I need a local knowledge base with no usage limits
**When** I run `docker-compose up -d`
**Then** PostgreSQL and Neo4j containers start with persistent data volumes

### Schema Deployment
**Given** I need to store tiered guidelines and products
**When** I deploy the SQL schema
**Then** Tables are created with tier columns, Dutch search, and embedding indexes

### Data Persistence
**Given** I store documents and embeddings in PostgreSQL
**When** I restart Docker containers
**Then** All data persists across restarts (verified by tests)

---

## Scope

### In Scope ✅
- ✅ PostgreSQL 17 + pgvector 0.8.1 in Docker with persistent volumes
- ✅ Neo4j 5.26.1 + APOC plugin in Docker (for future knowledge graph)
- ✅ Database schema: `documents`, `chunks` (with tier), `products`, `sessions`, `messages`
- ✅ SQL functions: `hybrid_search()`, `search_guidelines_by_tier()`, `search_products()`
- ✅ Dutch language configuration in full-text search
- ✅ Pydantic models: 8 data models with validation
- ✅ Ingestion pipeline: `chunker.py`, `embedder.py`, `ingest.py`
- ✅ NotionConfig class for API integration
- ✅ Test utilities: connection tests, data persistence tests
- ✅ Docker health checks and automatic restart policies

### Out of Scope ❌
- API endpoints (deferred to FEAT-004)
- Multi-agent system (deferred to FEAT-005)
- Product ingestion (deferred to FEAT-003)
- Knowledge graph building (future enhancement)

---

## Success Criteria

**Infrastructure:**
- ✅ PostgreSQL and Neo4j containers healthy and accessible
- ✅ Data persists across container restarts (100% verified)
- ✅ Connection tests passing (100%)

**Schema:**
- ✅ All 5 tables created with correct types
- ✅ Tier column in chunks table with CHECK constraint (1, 2, 3)
- ✅ Products table with embeddings and compliance_tags array
- ✅ Dutch language full-text search configured

**Search Functions:**
- ✅ `hybrid_search()` uses Dutch language (`'dutch'` not `'english'`)
- ✅ `search_guidelines_by_tier()` supports tier filtering
- ✅ `search_products()` supports compliance tag filtering

**Pipeline:**
- ✅ Chunker can do semantic or simple chunking
- ✅ Embedder generates 1536-dim vectors with OpenAI
- ✅ Ingest pipeline orchestrates: chunk → embed → store → graph

**Models:**
- ✅ 8 Pydantic models created with field validation
- ✅ Models support Dutch content (TieredGuideline, EVIProduct, etc.)

---

## Dependencies

**External Services:**
- Docker and Docker Compose installed
- OpenAI API key for embeddings (configured in `.env`)

**Libraries:**
- PostgreSQL with pgvector extension
- Python 3.11+ with asyncpg, pydantic, httpx

---

## Technical Notes

**Database Connection:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/evi_rag
```

**Key Files:**
- `docker-compose.yml` - PostgreSQL + Neo4j services
- `sql/schema.sql` - Base schema
- `sql/evi_schema_additions.sql` - EVI-specific extensions (tiers, products, Dutch)
- `agent/models.py` - 8 Pydantic models
- `ingestion/ingest.py` - Main ingestion orchestrator
- `ingestion/chunker.py` - Semantic chunking logic
- `ingestion/embedder.py` - OpenAI embedding generation
- `config/notion_config.py` - Notion API configuration

**Schema Highlights:**
- `chunks.tier` INTEGER CHECK (tier IN (1, 2, 3)) - Tier filtering
- `products.compliance_tags` TEXT[] - Array of safety standards
- `to_tsvector('dutch', content)` - Dutch full-text search

**Tests:**
- `tests/test_supabase_connection.py` - Database validation (100% passing)
- `tests/test_data_persistence.py` - Data persistence verification

---

## Implementation Status

**Phase 1: Infrastructure ✅ Complete**
- Docker Compose configured
- PostgreSQL + pgvector running locally
- Neo4j + APOC configured
- Persistent volumes verified

**Phase 2: Schema ✅ Complete**
- Base schema deployed
- EVI extensions added (tier column, products table, Dutch search)
- All indexes created
- Views created (guideline_tier_stats, product_catalog_summary)

**Phase 3: Models & Pipeline ✅ Complete**
- 8 Pydantic models implemented
- Chunker supports semantic + simple modes
- Embedder supports batch processing with retry logic
- Ingest pipeline orchestrates full flow

---

## Next Steps

With infrastructure complete, proceed to:
1. **FEAT-002:** Notion Integration (fetch guidelines from Notion DB)
2. **FEAT-003:** Query & Retrieval (search Dutch guidelines)
3. **FEAT-004:** Multi-Agent System (Research + Specialist agents)
4. **FEAT-005:** Multi-Format Support (PDFs, Word docs)

---

**Last Updated:** 2025-10-25
**Status:** ✅ Complete and Ready for Use
