# External Service Integrations - EVI 360 RAG

**Last Updated:** 2025-10-25
**Status:** Phase 1-2 Complete (Notion configured), Phase 3+ Planned

## Overview

The EVI 360 RAG system integrates with external services for guideline ingestion, embeddings, and LLM responses. All integrations prioritize **Dutch language support** for workplace safety specialists.

---

## Notion API ✅ CONFIGURATION COMPLETE (Phase 3 - Ready)

**Purpose:** Fetch ~100 Dutch safety guidelines with 3-tier structure from EVI 360's Notion database

**Provider:** Notion Labs Inc.
**Documentation:** https://developers.notion.com/

**Library:** notion-client 2.2.1 (official Python client)

**Configuration:** [`config/notion_config.py`](../../config/notion_config.py) ✅ Implemented

**Environment Variables:**
```bash
NOTION_API_TOKEN=secret_...
NOTION_GUIDELINES_DATABASE_ID=...
```

**Status:** ✅ Ready for Phase 3 implementation

**Tier Detection:** Parses Notion headings (## Samenvatting, ## Kerninformatie, ## Volledige Details)

**Rate Limiting:** 3 requests/second (Notion API limit)

---

## OpenAI API (Phase 3-6 - Planned)

**Purpose:** Generate embeddings for semantic search and Dutch language LLM responses

**Provider:** OpenAI
**Documentation:** https://platform.openai.com/docs

**Library:** openai 1.90.0

**Environment Variables:**
```bash
LLM_API_KEY=sk-...
EMBEDDING_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4
```

**Use Cases:**
1. **Embeddings** (Phase 3): text-embedding-3-small (1536 dims) for guideline chunks and products
2. **LLM Responses** (Phase 5-6): GPT-4 for Dutch language Specialist Agent
3. **Categorization** (Phase 4): AI-assisted product categorization

**Dutch Support:** Excellent (native language model)

---

## EVI 360 Website (Phase 4 - Planned)

**Purpose:** Scrape ~100 product listings for catalog

**Technology:** beautifulsoup4 4.12.3 + httpx 0.28.1

**Target:** https://evi360.nl/producten (or provided URL)

**Rate Limiting:** 0.5 req/sec (self-imposed, respect robots.txt)

**Data Extraction:** Product name, description (Dutch), URL, category

**Fallback:** Manual CSV upload if scraping infeasible

---

## Internal Services

### PostgreSQL Database

**Driver:** asyncpg 0.30.0

**Connection:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/evi_rag
```

**See:** [database.md](database.md) for schema details

### Neo4j Graph Database

**Driver:** neo4j 5.28.1

**Connection:**
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

**See:** [database.md](database.md) for graph schema

---

## Security

**API Keys:** Stored in `.env` file (`.gitignore`'d)
**Production:** Use secrets management service (AWS Secrets Manager, Vault)
**HTTPS:** All external APIs over HTTPS
**Rate Limiting:** Implemented with exponential backoff

---

**Note:** Update this document when:
- New external services are integrated
- API endpoints or authentication methods change
- Rate limits are updated

**See Also:**
- [architecture.md](architecture.md) - System architecture
- [stack.md](stack.md) - Technology stack
- [database.md](database.md) - Internal data storage
- [`config/notion_config.py`](../../config/notion_config.py) - Notion configuration
