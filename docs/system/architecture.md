# System Architecture - EVI 360 RAG

**Last Updated:** 2025-10-25
**Status:** Phase 1-2 Complete, Phase 3+ In Planning

## Overview

The EVI 360 RAG system is an intelligent assistant for workplace safety specialists that provides **tiered guideline access** (Summary → Key Facts → Details), **product recommendations**, and operates entirely in **Dutch language**.

This document describes the architecture as implemented in **Phases 1-2** (Infrastructure + Data Models), with planned components for **Phases 3-8** clearly marked.

## Architecture Goals

- **Rapid Information Access**: 3-tier guideline hierarchy enables quick triage or deep dives as needed
- **Dutch Language First**: Native Dutch support for full-text search and agent responses
- **Unlimited Scale**: Local PostgreSQL eliminates cloud storage limits for large knowledge bases
- **Conversation Context**: Multi-agent system (planned Phase 5) maintains query state across interactions
- **Product Integration**: Connect safety guidelines with relevant EVI 360 equipment and services
- **Maintainability**: Separation of concerns across ingestion, storage, and agent layers

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        User Interface                              │
│                    (CLI / API / Web - Future)                      │
└────────────────────────────────┬─────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Layer (Phase 5 - Planned)               │
│                                                                   │
│  ┌──────────────────────┐      ┌───────────────────────────┐  │
│  │ Intervention         │      │   Research Agent          │  │
│  │ Specialist Agent     │◄─────│   (Tool for Specialist)   │  │
│  │                      │      │                           │  │
│  │ - Dutch responses    │      │ - Tier traversal (1→2→3)  │  │
│  │ - Product recs       │      │ - Vector search           │  │
│  │ - Context management │      │ - Graph queries           │  │
│  └──────────────────────┘      │ - Product lookup          │  │
│                                  └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│              Storage Layer (Phase 1-2 ✅ COMPLETE)               │
│                                                                   │
│  ┌──────────────────────────┐    ┌────────────────────────────┐ │
│  │ PostgreSQL 17            │    │   Neo4j 5.26.1            │ │
│  │ + pgvector 0.8.1         │    │   + APOC                  │ │
│  │ (Docker)                 │    │   (Docker)                │ │
│  │                          │    │                            │ │
│  │ - documents              │    │ - Guideline relationships │ │
│  │ - chunks (with tier)     │    │ - Product connections     │ │
│  │ - products               │    │ - Knowledge graph         │ │
│  │ - sessions/messages      │    │ - Temporal data           │ │
│  │ - Vector embeddings      │    │                            │ │
│  │ - Dutch full-text search │    │                            │ │
│  └──────────────────────────┘    └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  ↑
┌─────────────────────────────────────────────────────────────────┐
│            Ingestion Layer (Phase 3-4 - Planned)                 │
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────────────────┐ │
│  │ Notion Ingestion │         │   Product Scraping           │ │
│  │                  │         │                               │ │
│  │ - Fetch guidelines│        │ - Scrape EVI 360 site        │ │
│  │ - Detect tiers   │         │ - AI categorization          │ │
│  │ - Chunk by tier  │         │ - Compliance tag generation  │ │
│  │ - Generate embeds│         │ - Embed products             │ │
│  └──────────────────┘         └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                ↑                             ↑
            Notion API                  EVI 360 Website
```

## Components

### Component 1: Storage Layer ✅ COMPLETE (Phase 1-2)

**Purpose:** Persistent storage for guidelines, products, embeddings, and knowledge graph

**Responsibilities:**
- Store guideline chunks with tier metadata (1, 2, or 3)
- Vector similarity search for Dutch language content
- Store product catalog with compliance tags
- Maintain conversation history (sessions/messages)
- Knowledge graph for guideline and product relationships
- Dutch full-text search via PostgreSQL

**Technology:**
- PostgreSQL 17 + pgvector 0.8.1 (vector similarity search)
- Neo4j 5.26.1 + APOC plugin (knowledge graph)
- Docker Compose (containerization)
- Persistent Docker volumes (data retention)

**Location:**
- Schema: [`sql/schema.sql`](../../sql/schema.sql), [`sql/evi_schema_additions.sql`](../../sql/evi_schema_additions.sql)
- Configuration: [`docker-compose.yml`](../../docker-compose.yml)
- Data Models: [`agent/models.py`](../../agent/models.py)

**Implementation Status:**
- ✅ 5 tables: documents, chunks (with tier), products, sessions, messages
- ✅ 3 SQL functions: hybrid_search (Dutch), search_guidelines_by_tier, search_products
- ✅ 3 views: document_summaries, guideline_tier_stats, product_catalog_summary
- ✅ Dutch language configuration (`to_tsvector('dutch', content)`)
- ✅ Persistent volumes tested and working
- ✅ Health checks configured

### Component 2: Data Models ✅ COMPLETE (Phase 2)

**Purpose:** Type-safe data validation and structure for all system entities

**Responsibilities:**
- Validate guideline data with 3-tier structure
- Validate product data with compliance tags
- Define search result structures
- Define agent response formats
- Ensure data integrity across system

**Technology:**
- Pydantic v2 with field validation
- Type hints for all models
- Custom validators for EVI-specific rules

**Location:** [`agent/models.py`](../../agent/models.py)

**Models Implemented:**
1. `TieredGuideline` - 3-tier guideline structure
2. `GuidelineSearchResult` - Search results with tier info
3. `EVIProduct` - Product catalog with validation
4. `ProductRecommendation` - Product recommendations with scoring
5. `ProductSearchResult` - Database search results
6. `ResearchAgentResponse` - Research agent output (for Phase 5)
7. `SpecialistAgentResponse` - Specialist agent response (for Phase 5)
8. Additional utility models for chunks, sessions, messages

### Component 3: Ingestion Layer (Phase 3-4 - PLANNED)

**Purpose:** Extract guidelines from Notion and products from website, process into searchable chunks

**Responsibilities:**
- Fetch all guidelines from Notion database via API
- Detect tier markers in Notion content (## Samenvatting, ## Kerninformatie, ## Volledige Details)
- Apply tier-specific chunking strategies
- Generate embeddings for all chunks (OpenAI text-embedding-3-small)
- Scrape EVI 360 website for product catalog
- AI-assisted product categorization and compliance tag generation
- Store processed data in PostgreSQL + Neo4j

**Technology (Planned):**
- notion-client 2.2.1 (Notion API)
- BeautifulSoup4 4.12.3 (web scraping)
- asyncpg (database operations)
- OpenAI API (embeddings + categorization)

**Location (Planned):**
- `ingestion/notion_client.py` - Notion API wrapper
- `ingestion/tier_chunker.py` - Tier-aware chunking
- `ingestion/product_scraper.py` - EVI 360 website scraper
- `ingestion/product_categorizer.py` - AI categorization
- `ingestion/ingest_guidelines.py` - Guideline pipeline
- `ingestion/ingest_products.py` - Product pipeline

**Configuration (Complete):**
- ✅ [`config/notion_config.py`](../../config/notion_config.py) - NotionConfig dataclass ready
- ✅ Environment variables in `.env.example`

### Component 4: Multi-Agent System (Phase 5 - PLANNED)

**Purpose:** Provide intelligent Dutch-language responses with guideline citations and product recommendations

**Responsibilities:**
- **Research Agent**: Tier-aware guideline search, product lookup, graph traversal
- **Intervention Specialist Agent**: Dutch language synthesis, conversation context, user-facing responses
- Coordinate tier search strategy (start with Tier 1-2, escalate to Tier 3 if needed)
- Format responses with guideline citations and product recommendations
- Maintain conversation history across sessions

**Technology (Planned):**
- Pydantic AI (agent framework)
- Agent-calling-agent pattern (Specialist uses Research as tool)
- Streaming responses via FastAPI
- Dutch language system prompts

**Location (Planned):**
- `agent/research_agent.py` - Research agent implementation
- `agent/research_tools.py` - Vector search, graph queries
- `agent/specialist_agent.py` - Intervention specialist
- `agent/specialist_tools.py` - Wraps research agent

**Design Pattern:**
```python
# Specialist Agent calls Research Agent as a tool
@specialist_agent.tool
async def research_guidelines(query: str, tier: int = 2) -> ResearchAgentResponse:
    return await research_agent.run(query, tier=tier)
```

### Component 5: User Interface (Phase 7-8 - PLANNED)

**Purpose:** Provide access to the RAG system for EVI 360 specialists

**Responsibilities:**
- Accept Dutch language queries from users
- Stream agent responses in real-time
- Display guideline citations and product recommendations
- Maintain conversation context across queries

**Technology (Planned):**
- CLI: Python CLI tool for MVP testing
- API: FastAPI with streaming endpoints
- Future: Web UI (OpenWebUI integration)

**Location (Planned):**
- `cli.py` - Command-line interface
- `agent/api.py` - FastAPI endpoints
- Endpoints: `/chat`, `/research`, `/chat/stream`

## Data Flow

### 1. Guideline Ingestion Flow (Phase 3 - Planned)

```
Notion Database (~100 Dutch safety guidelines)
    ↓
[Fetch via Notion API using notion-client]
    ↓
[Detect tier markers in content]
(## Samenvatting → Tier 1, ## Kerninformatie → Tier 2, ## Volledige Details → Tier 3)
    ↓
[Apply tier-specific chunking]
- Tier 1: Single chunk (50-100 words)
- Tier 2: Semantic chunking (200-500 words per chunk)
- Tier 3: Semantic chunking (1000-5000 words per chunk)
    ↓
[Generate embeddings via OpenAI text-embedding-3-small]
    ↓
[Store in PostgreSQL]
- chunks table with tier metadata
- documents table with source info
    ↓
[Build knowledge graph in Neo4j]
- Guideline relationships
- Concept links
```

### 2. Product Ingestion Flow (Phase 4 - Planned)

```
EVI 360 Website (~100 products)
    ↓
[Scrape product pages with BeautifulSoup4]
    ↓
[Extract: name, description, URL, category hints]
    ↓
[AI-assisted categorization with GPT-4/Claude]
- Assign category/subcategory
- Generate compliance_tags array (e.g., ["EN_397", "CE_certified"])
    ↓
[Generate embeddings for product descriptions]
    ↓
[Store in PostgreSQL products table]
    ↓
[Link to guidelines in Neo4j knowledge graph]
```

### 3. Query Processing Flow (Phase 5-7 - Planned)

```
User Query in Dutch: "Wat zijn de vereisten voor werken op hoogte?"
    ↓
[Intervention Specialist Agent receives query]
    ↓
[Analyzes query intent and decides on tier strategy]
    ↓
[Calls Research Agent as a tool]
    ↓
Research Agent Processing:
  1. Generate query embedding
  2. Call search_guidelines_by_tier(tiers=[1]) for quick summary
  3. Review results - if insufficient detail:
  4. Call search_guidelines_by_tier(tiers=[2]) for key facts
  5. Call search_products(query="valbescherming", compliance_tags=["EN_795"])
  6. Query Neo4j for related guidelines and products
    ↓
[Returns structured data to Specialist Agent]
    ↓
Specialist Agent Synthesis:
  1. Formulate Dutch language response
  2. Include guideline summary (with tier info)
  3. Add relevant product recommendations with URLs
  4. Explain connections between guidelines and products
  5. Store conversation in sessions/messages tables
    ↓
[Stream response to user via FastAPI or CLI]
    ↓
User receives:
- Comprehensive Dutch answer
- Guideline citations (NVAB, STECR, UWV, etc.)
- 2-5 relevant EVI 360 products with reasoning
```

## Integration Points

### External Services

**Notion API** (Phase 3 - Configuration Complete)
- **Purpose:** Sync ~100 Dutch safety guidelines with 3-tier structure
- **Documentation:** https://developers.notion.com/
- **Configuration:** [`config/notion_config.py`](../../config/notion_config.py)
- **Status:** ✅ NotionConfig class ready, environment variables configured
- **Credentials:** `.env` file (`NOTION_API_TOKEN`, `NOTION_GUIDELINES_DATABASE_ID`)

**OpenAI API** (Phase 3-6 - Planned)
- **Purpose:** Generate embeddings (text-embedding-3-small) and LLM responses (GPT-4 for Dutch)
- **Documentation:** https://platform.openai.com/docs
- **Configuration:** `.env` file (`LLM_API_KEY`, `EMBEDDING_API_KEY`)
- **Use Cases:** Embeddings for vector search, AI categorization of products, Dutch language agent responses

**EVI 360 Website** (Phase 4 - Planned)
- **Purpose:** Scrape ~100 product listings for catalog
- **Technology:** BeautifulSoup4 + httpx (async HTTP)
- **Configuration:** Respect robots.txt, rate limiting

### Internal APIs

**PostgreSQL Database Connection**
- **Driver:** asyncpg (async PostgreSQL driver)
- **Connection String:** `postgresql://postgres:postgres@localhost:5432/evi_rag`
- **Shared via:** Connection pooling in `agent/db_utils.py` (existing pattern)

**Neo4j Graph Database**
- **Driver:** neo4j Python driver
- **Connection:** `bolt://localhost:7687`
- **Credentials:** neo4j/password123 (development)

## 3-Tier Guideline Design

This architecture's most distinctive feature is the **3-tier guideline hierarchy**:

**Tier 1: Summary (50-100 words)**
- Purpose: Quick relevance check
- Storage: Single chunk per guideline
- Retrieval: Always fetched for initial context

**Tier 2: Key Facts (200-500 words)**
- Purpose: Answers 80% of specialist queries
- Storage: 3-5 semantic chunks per guideline
- Retrieval: Default tier for most searches

**Tier 3: Full Details (1000-5000 words)**
- Purpose: Deep dive technical documentation
- Storage: 10-20 semantic chunks per guideline
- Retrieval: Only when explicitly needed or Tier 2 insufficient

**Database Implementation:**
```sql
-- chunks table stores tier metadata
tier INTEGER CHECK (tier IN (1, 2, 3))

-- Tier-aware search function
search_guidelines_by_tier(
    query_embedding vector(1536),
    query_text TEXT,
    target_tiers INTEGER[], -- e.g., ARRAY[1, 2]
    limit INTEGER
)
```

**Search Strategy (Phase 5):**
1. Start with Tier 1 (quick context)
2. Search Tier 2 for details (most queries stop here)
3. Escalate to Tier 3 only if needed
4. Agent decides based on query complexity and initial results

## Dutch Language Support

**Full-Text Search:**
- PostgreSQL configured with `dutch` language
- Function: `to_tsvector('dutch', content)`
- Features: Dutch stemming (werken → werk), stop words removed (de, het, een)

**Agent Responses (Planned Phase 6):**
- System prompts: "Antwoord altijd in het Nederlands"
- LLM: OpenAI GPT-4 (excellent Dutch support)
- Output: All user-facing text in Dutch

**Example:**
```
User: "Wat zijn de vereisten voor persoonlijke beschermingsmiddelen?"
Database: to_tsvector('dutch', 'persoonlijke beschermingsmiddelen')
→ Matches: bescherming, beschermd, pbm, etc.
Agent: "Voor persoonlijke beschermingsmiddelen (PBM) gelden..."
```

## Deployment

**Current Environment (Phase 1-2):**
- **Local Development:** Docker Compose on localhost
- **Services:** PostgreSQL + Neo4j containers
- **Data Persistence:** Docker volumes (postgres_data, neo4j_data)
- **Status:** ✅ Fully operational, health checks passing

**Deployment Process:**
```bash
# Start services
docker-compose up -d

# Verify health
docker-compose ps  # Both services should show (healthy)

# Run tests
python3 tests/test_supabase_connection.py
python3 tests/test_data_persistence.py
```

**Future Environments (Planned):**
- **Staging:** Cloud deployment (Phase 8)
- **Production:** TBD based on EVI 360 infrastructure

## Performance Targets

**Query Latency (Phase 5-7):**
- Tier 1 queries: < 500ms
- Tier 2 queries: < 1000ms
- Tier 3 queries: < 2000ms

**Scale Targets:**
- Guidelines: 1000+ with 3 tiers each
- Products: 500+ with compliance tags
- Chunks: 10,000+ with embeddings
- Concurrent users: 10+ simultaneous sessions

**Current Performance (Phase 1-2):**
- Local PostgreSQL: ~20-100x faster than Supabase cloud
- No usage limits (unlimited storage, queries, embeddings)

## Technology Stack

See [stack.md](stack.md) for detailed technology choices, versions, and rationale.

## Architecture Decisions

**Key Decisions:**

1. **3-Tier Hierarchy** (vs. flat structure)
   - Rationale: Enables quick triage and efficient retrieval
   - Impact: More complex chunking but better UX

2. **Local PostgreSQL** (vs. Supabase cloud)
   - Rationale: No usage limits, 20-100x faster, $300/year savings
   - Impact: Self-hosted infrastructure, Docker dependency

3. **Multi-Agent System** (vs. single agent)
   - Rationale: Separation of concerns (retrieval vs. communication)
   - Impact: Research Agent can be called multiple times per query

4. **Notion Integration** (vs. manual markdown)
   - Rationale: EVI 360 already uses Notion, live sync
   - Impact: API dependency, but eliminates manual export/import

See [FEAT-001 PRD](../features/FEAT-001_evi-rag-implementation/prd.md) for complete implementation plan.

## Evolution

**Phase 1-2 (October 2025):** ✅ COMPLETE
- PostgreSQL + Neo4j infrastructure
- Database schema with tier support
- 8 Pydantic models
- Notion configuration
- Test suite (100% passing)

**Phase 3 (Next):** Notion Integration
- Notion API client
- Tier-aware chunking
- Guideline ingestion pipeline

**Phase 4-8 (Planned):**
- Product scraping and categorization
- Multi-agent system (Research + Specialist)
- Dutch language polish
- CLI and API interfaces
- Comprehensive testing
- Production deployment

---

**Last Updated:** 2025-10-25
**Status:** Living document, updated as architecture evolves

**See Also:**
- [database.md](database.md) - Database schema details
- [stack.md](stack.md) - Technology stack
- [integrations.md](integrations.md) - External service integrations
- [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md) - High-level architecture overview
