# Technology Stack - EVI 360 RAG

**Last Updated:** 2025-10-25
**Status:** Phase 1-2 Complete, Phase 3+ Planned

## Overview

The EVI 360 RAG system is built for workplace safety specialists with a focus on **Dutch language support**, **3-tier guideline hierarchy**, and **local-first infrastructure** for unlimited scale.

**Project Type:** RAG (Retrieval-Augmented Generation) System
**Phase:** Phase 1-2 Complete (Infrastructure + Data Models)

---

## Core Technologies

### Language

**Python 3.11+**
- **Version:** 3.11 or higher
- **Why:** Modern async support, type hints, excellent AI/ML ecosystem
- **Use Cases:** All application code (ingestion, agents, API, CLI)

---

## Database Layer ✅ COMPLETE (Phase 1-2)

### Primary Database

**PostgreSQL 17**
- **Version:** 17 (latest stable)
- **Why:** Mature, reliable, excellent extension ecosystem
- **Use Cases:** Relational data, full-text search (Dutch language), conversation history
- **ORM/Query Builder:** asyncpg 0.30.0 (direct async PostgreSQL driver)

**pgvector Extension**
- **Version:** 0.8.1
- **Why:** Native vector similarity search in PostgreSQL, no separate vector DB needed
- **Use Cases:** Guideline and product embeddings, semantic search
- **Performance:** IVFFLAT indexing for 10-100x speed improvement

### Graph Database

**Neo4j 5.26.1**
- **Version:** 5.26.1
- **Why:** Best-in-class graph database, excellent Cypher query language
- **Use Cases:** Knowledge graph (guideline relationships, product connections, concepts)
- **Plugin:** APOC (procedures unrestricted for advanced operations)
- **Driver:** neo4j 5.28.1 (Python driver)

### Caching

**Not yet implemented** (Phase 3+)
- **Planned:** In-memory caching for frequently accessed guidelines
- **Consideration:** Redis or Python cachetools

---

## Data & Validation ✅ COMPLETE (Phase 2)

### Data Models

**Pydantic 2.11.7**
- **Version:** 2.11.7
- **Why:** Modern data validation, type safety, excellent Python integration
- **Use Cases:** All data structures (8 custom models)

**Pydantic Models Implemented:**
1. `TieredGuideline` - 3-tier guideline structure
2. `GuidelineSearchResult` - Search results with tier info
3. `EVIProduct` - Product catalog with validation
4. `ProductRecommendation` - Product recommendations with scoring
5. `ProductSearchResult` - Database search results
6. `ResearchAgentResponse` - Research agent output (for Phase 5)
7. `SpecialistAgentResponse` - Specialist agent response (for Phase 5)
8. Additional utility models for chunks, sessions, messages

---

## Agent Framework (Phase 5 - Planned)

### Pydantic AI

**pydantic-ai 0.3.2**
- **Version:** 0.3.2
- **Why:** Type-safe agent framework, modern Python patterns, excellent documentation
- **Use Cases:** Multi-agent system (Research Agent + Intervention Specialist Agent)
- **Pattern:** Agent-calling-agent (Specialist uses Research as a tool)

**Related Packages:**
- `pydantic-ai-slim 0.3.2` - Core agent functionality
- `pydantic-graph 0.3.2` - Graph operations
- `pydantic-evals 0.3.2` - Agent evaluation

---

## API Framework (Phase 5-7 - Planned)

### FastAPI

**fastapi 0.115.13**
- **Version:** 0.115.13
- **Why:** Modern async Python framework, excellent type safety with Pydantic, streaming support
- **Use Cases:** REST API endpoints for agents
- **Server:** uvicorn 0.34.3

**API Type:** REST with streaming (SSE)
- **Endpoints (Planned):**
  - `POST /chat` - Main agent endpoint (Dutch queries)
  - `POST /research` - Direct Research Agent access
  - `POST /chat/stream` - Streaming responses via SSE

**Streaming Support:**
- `sse-starlette 2.3.6` - Server-Sent Events for real-time streaming
- `httpx-sse 0.4.0` - Client-side SSE support

---

## External Service Integrations

### Notion API ✅ CONFIGURATION COMPLETE

**notion-client 2.2.1**
- **Version:** 2.2.1
- **Why:** Official Notion Python client, complete API coverage
- **Use Cases:** Fetch ~100 Dutch safety guidelines with 3-tier structure
- **Configuration:** [`config/notion_config.py`](../../config/notion_config.py) (ready)
- **Status:** ✅ NotionConfig class implemented, environment variables configured

### OpenAI API (Phase 3-6 - Planned)

**openai 1.90.0**
- **Version:** 1.90.0
- **Why:** Best Dutch language support, excellent embedding quality
- **Use Cases:**
  - **Embeddings:** text-embedding-3-small (1536 dimensions)
  - **LLM:** GPT-4 for Dutch language agent responses
  - **Categorization:** AI-assisted product categorization

**Alternative LLMs (configured, not used yet):**
- `anthropic 0.54.0` - Claude for potential Dutch language tasks
- `groq 0.28.0` - Fast inference option
- `cohere 5.15.0` - Alternative embeddings/LLM
- `mistralai 1.8.2` - European-based LLM option

### Web Scraping (Phase 4 - Planned)

**beautifulsoup4 4.12.3**
- **Version:** 4.12.3
- **Why:** Simple, reliable HTML parsing
- **Use Cases:** Scrape ~100 products from EVI 360 website
- **HTTP Client:** httpx 0.28.1 (async capable)

---

## Testing ✅ COMPLETE (Phase 1-2)

### Test Framework

**pytest 8.4.1**
- **Version:** 8.4.1
- **Why:** Industry standard, excellent plugin ecosystem
- **Use Cases:** Unit tests, integration tests

**pytest-asyncio 1.0.0**
- **Version:** 1.0.0
- **Why:** Async test support for asyncpg, httpx, agents
- **Use Cases:** Test async database operations, API endpoints

**Test Suite (Current):**
- [`tests/test_supabase_connection.py`](../../tests/test_supabase_connection.py) - Database schema validation (✅ passing)
- [`tests/test_data_persistence.py`](../../tests/test_data_persistence.py) - Docker volume persistence (✅ passing)

**Test Utilities (Planned):**
- **Mocking:** pytest fixtures for database, Notion API, OpenAI API
- **Coverage:** Coverage reporting (future)

---

## Development Tools

### Package Manager

**pip (with requirements.txt)**
- **Version:** Latest with Python 3.11+
- **Lock File:** `requirements.txt` (95 dependencies)
- **Virtual Environment:** `venv/` (recommended)

### Code Quality

**Linting (Planned):**
- **Tool:** ruff or flake8
- **Config:** TBD

**Formatting (Planned):**
- **Tool:** black (Python standard)
- **Config:** Line length 88 (black default)

**Type Checking (In Use):**
- **Tool:** Python type hints with Pydantic validation
- **Strictness:** Enforced via Pydantic models

### Version Control

- **Git:** Latest
- **Branch Strategy:** Feature branches (see [git-workflow.md](../sop/git-workflow.md))
- **Commit Format:** Conventional commits (see [CLAUDE.md](../../CLAUDE.md))

---

## Deployment ✅ COMPLETE (Phase 1-2)

### Hosting

**Platform:** Local Docker Compose
- **Environments:** Local development only (production TBD)
- **Services:** PostgreSQL 17 + Neo4j 5.26.1 in containers

### Containerization

**Docker**
- **Version:** Latest
- **Compose:** docker-compose.yml
- **Registry:** N/A (local images only)
- **Containers:**
  - `evi_rag_postgres` - PostgreSQL 17 + pgvector 0.8.1
  - `evi_rag_neo4j` - Neo4j 5.26.1 + APOC

**Docker Configuration:**
- Persistent volumes: `postgres_data`, `neo4j_data`, `neo4j_logs`, `neo4j_import`, `neo4j_plugins`
- Health checks: Enabled for both services
- Networking: Bridge network `evi_rag_network`

**Deployment Process:**
```bash
# Start services
docker-compose up -d

# Verify health
docker-compose ps  # Both should show (healthy)

# Run tests
python3 tests/test_supabase_connection.py
python3 tests/test_data_persistence.py
```

---

## Key Libraries & Dependencies

### HTTP & Networking

- **httpx 0.28.1** - Async HTTP client (Notion, EVI 360 scraping, OpenAI API)
- **requests 2.32.4** - Sync HTTP client (fallback)
- **beautifulsoup4 4.12.3** - HTML parsing

### Data Processing

- **numpy 2.3.1** - Numerical operations (embeddings)
- **pydantic 2.11.7** - Data validation
- **python-dotenv 1.1.0** - Environment variable management

### Database Drivers

- **asyncpg 0.30.0** - PostgreSQL async driver
- **neo4j 5.28.1** - Neo4j Python driver

### Agent & LLM

- **pydantic-ai 0.3.2** - Agent framework (Phase 5)
- **openai 1.90.0** - OpenAI API (embeddings + LLM)
- **anthropic 0.54.0** - Claude API (alternative)

### Utilities

- **click 8.2.1** - CLI framework (for cli.py)
- **rich 14.0.0** - Terminal formatting and output
- **tqdm 4.67.1** - Progress bars (ingestion pipelines)
- **logfire-api 3.21.1** - Logging and observability

---

## Performance Considerations

### Database Performance

**Vector Search:**
- IVFFLAT indexing: 10-100x faster than exact search
- Trade-off: 95-98% recall for massive speed improvement
- Target: < 1000ms for Tier 2 queries

**Full-Text Search:**
- Dutch language configuration: `to_tsvector('dutch', content)`
- GIN indexes for fast lookups
- Target: < 500ms for Tier 1 queries

**Hybrid Search:**
- Default: 70% vector + 30% text (configurable)
- Optimized for Dutch safety terminology

### Local Development Benefits

**Performance vs. Supabase Cloud:**
- 20-100x faster queries (localhost vs network)
- No rate limits
- Unlimited storage (vs 500 MB free tier)
- Direct psql access for debugging

---

## Security

### Dependencies

- **Audit Tool:** pip-audit (planned)
- **Automation:** Dependabot (future)
- **Policy:** Update critical vulnerabilities within 1 week

### Secrets Management

- **Tool:** Environment variables via `.env` file
- **Storage:** Local `.env` file (`.gitignore`'d)
- **Production:** TBD (AWS Secrets Manager, Vault, etc.)

**Credentials in `.env`:**
- `DATABASE_URL` - PostgreSQL connection string
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` - Neo4j auth
- `NOTION_API_TOKEN`, `NOTION_GUIDELINES_DATABASE_ID` - Notion API
- `LLM_API_KEY`, `EMBEDDING_API_KEY` - OpenAI API keys

---

## Development Setup

### Prerequisites

```bash
# Python version
python3 --version  # 3.11 or higher

# Docker
docker --version  # Latest
docker-compose --version  # Latest
```

### Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd evi_rag_test

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 5. Start databases
docker-compose up -d

# 6. Verify setup
python3 tests/test_supabase_connection.py
```

---

## Upgrade Strategy

### Major Version Updates

- **Frequency:** Quarterly for non-critical, immediately for critical
- **Process:**
  1. Review changelog and breaking changes
  2. Update in virtual environment
  3. Run full test suite
  4. Update documentation
  5. Commit and test

### Security Patches

- **Frequency:** Immediately for critical, weekly for non-critical
- **Process:** `pip install --upgrade <package>`, run tests, commit

---

## Alternative Technologies Considered

| Technology | Considered For | Why Not Chosen |
|------------|----------------|----------------|
| Supabase Cloud | PostgreSQL hosting | Usage limits, slower, costs $300/year at scale |
| LangChain | Agent framework | More complex, less type-safe than Pydantic AI |
| Chroma/Pinecone | Vector database | pgvector sufficient, avoid separate service |
| Express.js | API framework | Python ecosystem preferred (Pydantic, asyncpg) |
| MongoDB | Document storage | PostgreSQL JSONB sufficient for metadata |

---

## Tech Stack Summary

**Infrastructure:**
- ✅ PostgreSQL 17 + pgvector 0.8.1 (vector search, Dutch full-text)
- ✅ Neo4j 5.26.1 + APOC (knowledge graph)
- ✅ Docker Compose (local deployment)

**Application:**
- ✅ Python 3.11+ (all code)
- ✅ Pydantic 2.11.7 (8 data models)
- ✅ asyncpg 0.30.0 (database driver)
- ⏳ Pydantic AI 0.3.2 (agents - Phase 5)
- ⏳ FastAPI 0.115.13 (API - Phase 5-7)

**Integrations:**
- ✅ notion-client 2.2.1 (configured, Phase 3)
- ⏳ OpenAI 1.90.0 (embeddings + LLM - Phase 3+)
- ⏳ beautifulsoup4 4.12.3 (scraping - Phase 4)

**Testing:**
- ✅ pytest 8.4.1 + pytest-asyncio 1.0.0
- ✅ 2 test files (100% passing)

---

**Note:** Update this document when:
- New technologies are adopted
- Versions are upgraded
- Tools are replaced
- Stack recommendations change

**See Also:**
- [architecture.md](architecture.md) - System architecture
- [database.md](database.md) - Database schema details
- [integrations.md](integrations.md) - External services
- [requirements.txt](../../requirements.txt) - Complete dependency list
