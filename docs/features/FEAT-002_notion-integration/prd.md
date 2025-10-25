# PRD: FEAT-002 - Notion Integration

**Feature ID:** FEAT-002
**Phase:** 3 (Guideline Ingestion)
**Status:** Planned
**Priority:** High
**Owner:** TBD

## Overview

Implement automated ingestion of ~100 Dutch workplace safety guidelines from EVI 360's Notion database. The system must parse the 3-tier guideline structure (Summary, Key Facts, Full Details), intelligently chunk content by tier, generate embeddings using OpenAI's text-embedding-3-small model, and store structured data in PostgreSQL with tier metadata.

## Scope

**In Scope:**
- Fetch all guideline pages from Notion database using notion-client 2.2.1
- Detect 3-tier structure by parsing Dutch headings (## Samenvatting, ## Kerninformatie, ## Volledige Details)
- Chunk content with tier-specific strategies:
  - Tier 1: Single chunk per guideline (50-100 words)
  - Tier 2: 3-5 semantic chunks (200-500 words total)
  - Tier 3: 10-20 semantic chunks (1000-5000 words total)
- Generate 1536-dimensional embeddings for each chunk
- Store in PostgreSQL tables: `documents`, `chunks` with tier column populated
- Rate limiting (3 req/sec for Notion API)
- Error handling and retry logic

**Out of Scope:**
- Manual guideline editing or validation
- Automatic guideline updates (one-time ingestion for MVP)
- Knowledge graph creation (deferred to future phase)

## Success Criteria

- ✅ All ~100 guidelines successfully ingested from Notion
- ✅ Tier detection accuracy: 100% (validated by spot checks)
- ✅ Chunk counts per tier match expected ranges (Tier 1: 1 chunk, Tier 2: 3-5, Tier 3: 10-20)
- ✅ Embeddings generated for all chunks (no nulls in `chunks.embedding`)
- ✅ Test suite validates: Notion API connection, tier parsing, chunking logic, database insertion
- ✅ Ingestion pipeline completes in < 30 minutes for 100 guidelines

## Dependencies

- **Infrastructure:** PostgreSQL 17 + pgvector (FEAT-001 ✅)
- **External Services:** Notion API token + database ID configured (✅ ready)
- **External Services:** OpenAI API key for embeddings (pending configuration)

## Technical Notes

- Use `config/notion_config.py` NotionConfig class (already implemented)
- Dutch language support: Ensure chunking preserves Dutch sentence boundaries
- Embedding model: text-embedding-3-small (1536 dims, excellent Dutch support)
- Store original Notion URLs in `documents.source_url` for traceability

## Next Steps

1. Configure OpenAI API credentials in `.env`
2. Implement Notion fetcher (`ingestion/notion_fetcher.py`)
3. Implement tier-aware chunking logic (`ingestion/chunker.py`)
4. Implement embedding generation (`ingestion/embedder.py`)
5. Write tests for each component
6. Run end-to-end ingestion and validate results
