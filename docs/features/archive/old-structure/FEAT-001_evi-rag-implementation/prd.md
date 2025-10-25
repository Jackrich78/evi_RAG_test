# Implementation Plan: EVI RAG System for Workplace Safety

## Overview

Build a Dutch-language RAG (Retrieval-Augmented Generation) knowledge base system for EVI 360 workplace safety specialists. The system will help search Dutch government safety guidelines, provide regulatory compliance recommendations, and suggest appropriate EVI products based on regulatory alignment.

**Base:** Adapting existing `agentic-rag-knowledge-graph` repository
**Target Users:** EVI 360 intervention specialists
**Primary Language:** Dutch (input and output)
**Deployment:** Local development initially, production-ready architecture

---

## Requirements Summary

### Core Functionality
- Search ~100 Dutch safety guidelines with 3-tier hierarchy (high-level → detailed → raw PDF)
- Recommend EVI 360 products aligned with safety regulations
- Explain connections between regulations and product recommendations
- Handle real Dutch workplace safety queries from intervention specialists
- Multi-agent architecture: Research Agent + Intervention Specialist Agent

### Data Sources
- **Guidelines:** ~100 Dutch safety documents (already scraped in Notion, 10-100 pages each)
- **Products:** ~100 EVI 360 products (scrape from website, currently uncategorized)
- **Update Frequency:** Infrequent (manual monthly re-ingestion acceptable for MVP)

### Technical Requirements
- PostgreSQL + PGVector on Supabase (vector search)
- Neo4j + Graphiti (knowledge graph) in Docker
- Notion API integration for guideline ingestion
- Dutch language support in database and LLM outputs
- OpenAI embeddings (text-embedding-3-small, 1536 dimensions)
- CLI interface for MVP testing

---

## Research Findings

### Best Practices from Knowledge Base

**Pydantic AI Multi-Agent Patterns:**
- Use separate Agent instances for specialized tasks
- Share dependencies via `deps_type` dataclass pattern
- Agents can call other agents as tools using `RunContext`
- System prompts control tool selection behavior

**3-Tier Document Retrieval Strategy:**
- Store tiers as separate chunks with tier metadata
- Search L1/L2 first for general queries, fall back to L3 for specific details
- Use metadata filtering to restrict searches by tier
- Enables faster responses for high-level queries while maintaining detail access

**Notion API Integration:**
- Use `notion-client` Python library (official)
- Notion databases require database_id + integration token
- Pages have block children retrieved via recursive API calls
- Extract markdown-like structure from Notion blocks

**Dutch Language Support:**
- PostgreSQL full-text search: `to_tsvector('dutch', content)`
- OpenAI models have good Dutch language support
- System prompts should explicitly request Dutch output
- Metadata and internal processing can remain English

### Reference Implementations

**From Existing Codebase:**
- `agent/agent.py` - Pydantic AI agent with tool registration pattern
- `agent/tools.py` - Tool implementation with Pydantic input validation
- `agent/prompts.py` - System prompt configuration
- `ingestion/chunker.py` - Semantic chunking with LLM
- `ingestion/embedder.py` - Batch embedding generation
- `sql/schema.sql` - PostgreSQL + PGVector schema

**From Archon Knowledge Base:**
- FastAPI dependency injection patterns
- Pydantic AI agent configuration examples
- PGVector hybrid search strategies

### Technology Decisions

| Technology | Choice | Rationale |
|------------|--------|-----------|
| **Vector DB** | Supabase (PostgreSQL + PGVector) | Managed service, scalable, familiar SQL interface |
| **Knowledge Graph** | Neo4j + Graphiti | Already implemented in base repo, temporal support |
| **Agent Framework** | Pydantic AI | Type-safe, modern Python patterns, excellent docs |
| **Embeddings** | OpenAI text-embedding-3-small | Good Dutch support, 1536 dims, cost-effective |
| **LLM** | OpenAI GPT-4 | Best Dutch language performance available |
| **API Framework** | FastAPI | Already in base repo, streaming support, async |
| **Notion Client** | notion-client (official) | Well-maintained, complete API coverage |
| **Web Scraping** | BeautifulSoup + httpx | Lightweight, async-capable |

---

## Implementation Tasks

### Phase 1: Infrastructure Setup

#### 1.1 Supabase Database Configuration
**Description:** Create and configure Supabase project with PGVector and Dutch language support
**Files to modify/create:**
- `sql/schema.sql` - Update hybrid_search function for Dutch (lines 138, 145)
- `sql/evi_schema_additions.sql` - Create products table and tier column
- `.env` - Add Supabase connection string

**Dependencies:** None
**Estimated effort:** 2 hours

**Tasks:**
- Create new Supabase project via web console
- Enable PGVector extension
- Run base schema.sql
- Add products table schema
- Add `tier INTEGER CHECK (tier IN (1, 2, 3))` to chunks table
- Update full-text search to Dutch language
- Test connection with Python asyncpg

#### 1.2 Neo4j Docker Setup
**Description:** Configure Neo4j in Docker for local development
**Files to modify/create:**
- `docker-compose.yml` - Neo4j service definition
- `.env` - Add Neo4j credentials

**Dependencies:** None
**Estimated effort:** 1 hour

**Tasks:**
- Create docker-compose.yml with Neo4j 5.x
- Set memory and performance settings
- Configure ports (7474 web, 7687 bolt)
- Test connection with neo4j Python driver

#### 1.3 Notion API Configuration
**Description:** Set up Notion integration for guidelines access
**Files to modify/create:**
- `.env` - Add NOTION_API_TOKEN and NOTION_DATABASE_ID
- `config/notion_config.py` - NEW: Notion settings dataclass

**Dependencies:** None
**Estimated effort:** 30 minutes

**Tasks:**
- Create Notion integration at notion.so/my-integrations
- Share guidelines database with integration
- Copy database ID from Notion URL
- Test API access with simple query

---

### Phase 2: Data Models & Schema

#### 2.1 Database Schema Extensions
**Description:** Extend PostgreSQL schema for EVI-specific needs
**Files to modify/create:**
- `sql/evi_schema_additions.sql` - NEW: Products table, tier support

**Dependencies:** Phase 1.1
**Estimated effort:** 2 hours

**SQL to implement:**
```sql
-- Add tier support to chunks
ALTER TABLE chunks ADD COLUMN tier INTEGER CHECK (tier IN (1, 2, 3));
CREATE INDEX idx_chunks_tier ON chunks (tier);

-- Create products table
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id TEXT UNIQUE, -- EVI360 product ID
    name TEXT NOT NULL,
    name_nl TEXT, -- Dutch name if different
    description TEXT,
    description_nl TEXT, -- Dutch description
    category TEXT,
    compliance_tags TEXT[], -- Array of related guideline types
    embedding vector(1536),
    url TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_compliance_tags ON products USING GIN (compliance_tags);

-- Update hybrid_search for Dutch
-- Lines 138 and 145 in schema.sql
-- Change: to_tsvector('english', ...) → to_tsvector('dutch', ...)
-- Change: plainto_tsquery('english', ...) → plainto_tsquery('dutch', ...)

-- Create product search function
CREATE OR REPLACE FUNCTION search_products(
    query_embedding vector(1536),
    match_count INT DEFAULT 10,
    category_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    product_id TEXT,
    name TEXT,
    description TEXT,
    category TEXT,
    similarity FLOAT,
    url TEXT,
    compliance_tags TEXT[]
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.product_id,
        COALESCE(p.name_nl, p.name) AS name,
        COALESCE(p.description_nl, p.description) AS description,
        p.category,
        1 - (p.embedding <=> query_embedding) AS similarity,
        p.url,
        p.compliance_tags
    FROM products p
    WHERE p.embedding IS NOT NULL
        AND (category_filter IS NULL OR p.category = category_filter)
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

#### 2.2 Pydantic Models for EVI Data
**Description:** Create data models for guidelines, products, and tiers
**Files to modify/create:**
- `agent/models.py` - Add EVI-specific models

**Dependencies:** None
**Estimated effort:** 1 hour

**Models to add:**
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class TieredGuideline(BaseModel):
    """Dutch safety guideline with 3-tier structure."""
    id: str
    title: str
    source: str  # NVAB, STECR, UWV, etc.
    tier1_summary: str  # High-level overview
    tier2_details: str  # Detailed summary + key facts
    tier3_content: str  # Raw PDF content
    process_date: Optional[str] = None
    staging_uuid: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

class EVIProduct(BaseModel):
    """EVI 360 product/service."""
    product_id: str
    name: str
    name_nl: Optional[str] = None
    description: str
    description_nl: Optional[str] = None
    category: str
    url: str
    compliance_tags: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

class GuidelineSearchResult(BaseModel):
    """Search result from guideline database."""
    guideline_id: str
    title: str
    content: str
    tier: Literal[1, 2, 3]
    source: str
    similarity_score: float
    chunk_id: str

class ProductRecommendation(BaseModel):
    """Product recommendation with reasoning."""
    product: EVIProduct
    relevance_score: float
    reasoning: str  # Why this product matches the need
    guideline_alignment: List[str]  # Which guidelines support this
```

---

### Phase 3: Notion Integration & Guideline Ingestion

#### 3.1 Notion Client Wrapper
**Description:** Create Notion API client for fetching guidelines
**Files to modify/create:**
- `ingestion/notion_client.py` - NEW: Notion API wrapper
- `requirements.txt` - Add notion-client

**Dependencies:** Phase 1.3
**Estimated effort:** 3 hours

**Key functions:**
```python
async def fetch_all_guidelines(database_id: str) -> List[Dict]:
    """Fetch all pages from Notion guidelines database."""

async def extract_tiered_content(page_id: str) -> TieredGuideline:
    """Extract 3-tier structure from Notion page."""

async def notion_blocks_to_markdown(blocks: List[Dict]) -> str:
    """Convert Notion blocks to markdown."""
```

#### 3.2 Tier-Aware Chunking Strategy
**Description:** Modify chunker to handle 3-tier document structure
**Files to modify/create:**
- `ingestion/tier_chunker.py` - NEW: Tier-aware chunking
- `ingestion/chunker.py` - Refactor to support tier metadata

**Dependencies:** Phase 2.2, Phase 3.1
**Estimated effort:** 4 hours

**Implementation approach:**
- Detect tier markers in Notion export (H2 "### Summary", "### Key Data", "### Raw PDF")
- Chunk each tier separately with tier-specific strategies
  - Tier 1: Keep as single chunk (high-level summary)
  - Tier 2: Chunk by key fact sections
  - Tier 3: Standard semantic chunking
- Add `{"tier": 1|2|3}` to chunk metadata
- Maintain document_id linkage across all tiers

#### 3.3 Guideline Ingestion Pipeline
**Description:** End-to-end pipeline from Notion to PostgreSQL/Neo4j
**Files to modify/create:**
- `ingestion/ingest_guidelines.py` - NEW: Guideline-specific ingestion

**Dependencies:** Phase 3.1, Phase 3.2
**Estimated effort:** 3 hours

**Pipeline steps:**
1. Fetch all guideline pages from Notion
2. Extract 3-tier structure for each
3. Tier-aware chunking
4. Generate embeddings for all chunks
5. Insert into PostgreSQL with tier metadata
6. Build knowledge graph relationships
7. Progress tracking and error handling

---

### Phase 4: Product Scraping & Catalog

#### 4.1 EVI 360 Website Scraper
**Description:** Scrape product catalog from EVI360 website
**Files to modify/create:**
- `ingestion/product_scraper.py` - NEW: Web scraping for products
- `requirements.txt` - Add beautifulsoup4

**Dependencies:** Phase 2.2
**Estimated effort:** 4 hours

**Scraping strategy:**
- Use httpx for async requests
- BeautifulSoup for HTML parsing
- Extract: product name, description, URL, category hints
- Handle pagination if needed
- Respect robots.txt and rate limiting
- Store raw HTML for re-parsing if needed

#### 4.2 Product Categorization Logic
**Description:** AI-assisted product categorization for better recall
**Files to modify/create:**
- `ingestion/product_categorizer.py` - NEW: LLM-based categorization

**Dependencies:** Phase 4.1
**Estimated effort:** 3 hours

**Approach:**
- Use LLM to analyze product descriptions
- Generate categories: Physical Therapy, Occupational Health, Legal, Training, etc.
- Generate compliance_tags based on safety domain keywords
- Manual review workflow for corrections

#### 4.3 Product Ingestion Pipeline
**Description:** Ingest products into PostgreSQL with embeddings
**Files to modify/create:**
- `ingestion/ingest_products.py` - NEW: Product ingestion pipeline

**Dependencies:** Phase 4.2
**Estimated effort:** 2 hours

**Pipeline steps:**
1. Scrape products from website
2. Categorize with LLM
3. Generate embeddings for descriptions
4. Insert into products table
5. Update compliance_tags based on content analysis

---

### Phase 5: Multi-Agent System

#### 5.1 Research Agent Implementation
**Description:** Create specialized agent for searching guidelines and products
**Files to modify/create:**
- `agent/research_agent.py` - NEW: Research-focused agent
- `agent/research_tools.py` - NEW: Tools for guideline/product search

**Dependencies:** Phase 2.2, Phase 3.3, Phase 4.3
**Estimated effort:** 5 hours

**Tools to implement:**
```python
@research_agent.tool
async def search_guidelines_by_tier(
    query: str,
    tier: int = 2,
    limit: int = 5
) -> List[GuidelineSearchResult]:
    """Search guidelines at specific tier level."""

@research_agent.tool
async def search_related_products(
    guideline_ids: List[str],
    query: str,
    limit: int = 5
) -> List[ProductRecommendation]:
    """Find products aligned with specific guidelines."""

@research_agent.tool
async def get_guideline_full_context(
    guideline_id: str
) -> TieredGuideline:
    """Retrieve all tiers for a specific guideline."""
```

**Agent configuration:**
- System prompt: Act as research assistant for workplace safety
- Always search tier 1-2 first
- Fall back to tier 3 only if needed
- Return structured data, not prose

#### 5.2 Intervention Specialist Agent
**Description:** User-facing agent that formats responses per specialist prompt
**Files to modify/create:**
- `agent/specialist_agent.py` - NEW: Front-facing specialist agent
- `agent/specialist_tools.py` - NEW: Tools wrapping research agent

**Dependencies:** Phase 5.1
**Estimated effort:** 5 hours

**Implementation:**
- Load system prompt from `agent/intervention_specialist_prompt.md`
- Use Research Agent as a tool (agent calling agent pattern)
- Format responses in Dutch per prompt template
- Handle clarifying questions
- Generate structured recommendations with:
  - Relevant guidelines (NVAB, STECR, etc.)
  - Compliance requirements
  - 2-5 EVI product recommendations
  - Reasoning linking guidelines to products

#### 5.3 Agent Integration & Testing
**Description:** Wire up multi-agent system and test flows
**Files to modify/create:**
- `agent/agent.py` - Refactor to support both agents
- `agent/api.py` - Update endpoints for specialist agent

**Dependencies:** Phase 5.2
**Estimated effort:** 3 hours

**Integration points:**
- Specialist agent uses Research agent via tool calls
- Share database connections via dependency injection
- Session management for conversation context
- Streaming responses for real-time feedback

---

### Phase 6: Dutch Language Support

#### 6.1 Database Dutch Language Updates
**Description:** Update PostgreSQL full-text search for Dutch
**Files to modify/create:**
- `sql/schema.sql` - Update lines 138, 145

**Dependencies:** Phase 1.1
**Estimated effort:** 30 minutes

**Changes:**
```sql
-- Line 138
to_tsvector('dutch', c.content)  -- was 'english'

-- Line 145
plainto_tsquery('dutch', query_text)  -- was 'english'
```

#### 6.2 Agent Prompts in Dutch
**Description:** Ensure all user-facing output is Dutch
**Files to modify/create:**
- `agent/specialist_agent.py` - Dutch system prompt
- `agent/prompts.py` - Add Dutch prompt constants

**Dependencies:** Phase 5.2
**Estimated effort:** 1 hour

**System prompt additions:**
- "Antwoord altijd in het Nederlands" (Always respond in Dutch)
- Use intervention_specialist_prompt.md as base
- Ensure all error messages and status updates in Dutch

#### 6.3 Test Dutch Language Accuracy
**Description:** Validate Dutch output quality with sample queries
**Files to modify/create:**
- `tests/test_dutch_language.py` - NEW: Dutch language tests

**Dependencies:** Phase 6.2
**Estimated effort:** 2 hours

**Test cases:**
- Sample queries from requirements doc
- Verify Dutch grammar and terminology
- Check guideline citations in Dutch
- Validate product names preserved correctly

---

### Phase 7: CLI & Testing Interface

#### 7.1 Update CLI for Specialist Agent
**Description:** Modify CLI to use specialist agent endpoint
**Files to modify/create:**
- `cli.py` - Update for specialist agent interaction

**Dependencies:** Phase 5.3
**Estimated effort:** 2 hours

**Changes:**
- Add Dutch language prompts
- Display guideline citations clearly
- Show product recommendations with URLs
- Tool usage visibility for debugging

#### 7.2 Manual Testing Workflow
**Description:** Create test script with sample queries
**Files to modify/create:**
- `tests/manual_test_queries.py` - NEW: Interactive test script

**Dependencies:** Phase 7.1
**Estimated effort:** 2 hours

**Test queries (from requirements):**
1. "Ik heb last van m'n onderrug..." (Back pain from lifting)
2. "Guido heeft z'n vinger afgehakt..." (Workplace accident)
3. "M'n werknemer Patrick heeft z'n hoofd gestoten..." (Head injury)

**Validation criteria:**
- Relevant guidelines returned (NVAB, STECR, etc.)
- Specific compliance requirements mentioned
- 2-5 relevant EVI products suggested
- Dutch language throughout
- Response time < 10 seconds

---

### Phase 8: Documentation & Deployment Prep

#### 8.1 Update README
**Description:** Document EVI-specific setup and usage
**Files to modify/create:**
- `README.md` - Add EVI RAG setup section

**Dependencies:** Phase 7.2
**Estimated effort:** 2 hours

**Sections to add:**
- EVI RAG System overview
- Notion integration setup
- Guideline ingestion instructions
- Product scraping workflow
- Sample queries and expected outputs
- Troubleshooting common issues

#### 8.2 Environment Configuration Template
**Description:** Provide .env.example with all required variables
**Files to modify/create:**
- `.env.example` - Add EVI-specific variables

**Dependencies:** All phases
**Estimated effort:** 30 minutes

**Variables to add:**
```bash
# Notion Integration
NOTION_API_TOKEN=secret_...
NOTION_GUIDELINES_DATABASE_ID=...

# Supabase
DATABASE_URL=postgresql://...

# Neo4j (Docker local)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# OpenAI
LLM_API_KEY=sk-...
EMBEDDING_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small

# Language
OUTPUT_LANGUAGE=nl  # Dutch
```

#### 8.3 Create Migration Scripts
**Description:** Scripts for initial data population
**Files to modify/create:**
- `scripts/initial_setup.sh` - Setup automation
- `scripts/reingest_all.py` - Re-ingestion workflow

**Dependencies:** All ingestion phases
**Estimated effort:** 2 hours

**Scripts:**
- Run Supabase schema migrations
- Start Neo4j Docker container
- Ingest all guidelines from Notion
- Scrape and ingest products
- Verify data counts and indexes

---

## Codebase Integration Points

### Files to Modify

#### Core Schema
- **`sql/schema.sql`** (lines 138, 145)
  - Change `'english'` to `'dutch'` for full-text search

#### Agent System
- **`agent/agent.py`**
  - Add research_agent and specialist_agent instances
  - Configure Dutch language support

- **`agent/api.py`**
  - Update `/chat` endpoint to use specialist_agent
  - Add `/research` endpoint for direct research agent access

- **`agent/prompts.py`**
  - Add SPECIALIST_SYSTEM_PROMPT from intervention_specialist_prompt.md
  - Add RESEARCH_SYSTEM_PROMPT

- **`agent/models.py`**
  - Add TieredGuideline, EVIProduct, GuidelineSearchResult, ProductRecommendation

#### Ingestion
- **`ingestion/chunker.py`**
  - Extend ChunkingConfig with tier_aware option
  - Add tier parameter to DocumentChunk

- **`requirements.txt`**
  - Add: `notion-client`, `beautifulsoup4`, `lxml`

#### Configuration
- **`.env.example`**
  - Add Notion and EVI-specific variables

- **`README.md`**
  - Add EVI RAG section

### New Files to Create

#### Configuration
- `config/notion_config.py` - Notion settings dataclass

#### Ingestion Pipeline
- `ingestion/notion_client.py` - Notion API wrapper
- `ingestion/tier_chunker.py` - Tier-aware chunking logic
- `ingestion/product_scraper.py` - EVI360 website scraper
- `ingestion/product_categorizer.py` - LLM-based categorization
- `ingestion/ingest_guidelines.py` - Guideline ingestion pipeline
- `ingestion/ingest_products.py` - Product ingestion pipeline

#### Agent System
- `agent/research_agent.py` - Research agent implementation
- `agent/research_tools.py` - Research agent tools
- `agent/specialist_agent.py` - Intervention specialist agent
- `agent/specialist_tools.py` - Specialist agent tools (wraps research agent)

#### Database
- `sql/evi_schema_additions.sql` - Products table and tier support

#### Testing & Scripts
- `tests/test_dutch_language.py` - Dutch language validation
- `tests/manual_test_queries.py` - Interactive testing script
- `scripts/initial_setup.sh` - Automated setup
- `scripts/reingest_all.py` - Re-ingestion automation

### Existing Patterns to Follow

**Dependency Injection (from agent/agent.py):**
```python
@dataclass
class AgentDependencies:
    session_id: str
    user_id: Optional[str] = None
    search_preferences: Dict[str, Any] = None
```

**Tool Registration (from agent/agent.py):**
```python
@rag_agent.tool
async def tool_name(
    ctx: RunContext[AgentDependencies],
    param: str
) -> ReturnType:
    """Docstring explains tool purpose."""
    # Tool implementation
```

**Async Database Operations (from agent/db_utils.py pattern):**
```python
async with get_db_pool() as pool:
    async with pool.acquire() as conn:
        result = await conn.fetch(query, *args)
```

**Semantic Chunking (from ingestion/chunker.py):**
```python
chunker = SemanticChunker(config)
chunks = await chunker.chunk_document(
    content, title, source, metadata
)
```

**Embedding Generation (from ingestion/embedder.py pattern):**
```python
embeddings = await generate_embeddings_batch(
    texts, model="text-embedding-3-small"
)
```

---

## Technical Design

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User (via CLI)                          │
│                    Dutch Queries                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Server                            │
│  ┌────────────────────────────────────────────────┐        │
│  │   Intervention Specialist Agent                │        │
│  │   (User-Facing, Dutch Output)                  │        │
│  │   - Clarifying questions                       │        │
│  │   - Response formatting                        │        │
│  │   - Guideline citations                        │        │
│  │   - Product recommendations                    │        │
│  └────────────┬───────────────────────────────────┘        │
│               │                                             │
│               │ (calls as tool)                             │
│               ▼                                             │
│  ┌────────────────────────────────────────────────┐        │
│  │   Research Agent                               │        │
│  │   (Data Retrieval, Structured Output)          │        │
│  │   Tools:                                       │        │
│  │   - search_guidelines_by_tier()                │        │
│  │   - search_related_products()                  │        │
│  │   - get_guideline_full_context()               │        │
│  └────────────┬───────────────────────────────────┘        │
└───────────────┼─────────────────────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌─────────────┐
│  Supabase    │  │   Neo4j     │
│  PostgreSQL  │  │  Graphiti   │
│  + PGVector  │  │   (Docker)  │
│              │  │             │
│ ┌──────────┐ │  │ ┌─────────┐ │
│ │Guidelines│ │  │ │Guideline│ │
│ │(3 tiers) │ │  │ │Relations│ │
│ │          │ │  │ │         │ │
│ │Products  │ │  │ │Product  │ │
│ │          │ │  │ │Links    │ │
│ └──────────┘ │  │ └─────────┘ │
└──────────────┘  └─────────────┘
        ▲                ▲
        │                │
        └────────────────┘
                │
     ┌──────────┴──────────┐
     │                     │
     ▼                     ▼
┌─────────────┐   ┌────────────────┐
│   Notion    │   │  EVI360.nl     │
│  Guidelines │   │  Products      │
│  Database   │   │  Website       │
└─────────────┘   └────────────────┘
```

### Data Flow

#### Ingestion Pipeline

```
Notion Database              EVI360 Website
(Guidelines)                 (Products)
     │                            │
     │ fetch_all_guidelines()     │ scrape_products()
     ▼                            ▼
notion_client.py            product_scraper.py
     │                            │
     │ extract_tiered_content()   │ categorize_product()
     ▼                            ▼
tier_chunker.py             product_categorizer.py
     │                            │
     │ semantic chunking          │ embedding generation
     ▼                            ▼
embedder.py                 embedder.py
     │                            │
     ├─────────┬──────────────────┤
     │         │                  │
     ▼         ▼                  ▼
Supabase    Neo4j            Supabase
(chunks     (graph)          (products
+ tiers)                     + embeddings)
```

#### Query Pipeline

```
User Query (Dutch)
"Rugklachten door tillen"
     │
     ▼
Intervention Specialist Agent
     │
     │ Analyze query, determine need
     │ May ask clarifying question
     │
     ▼
Research Agent (called as tool)
     │
     ├──── search_guidelines_by_tier(query, tier=2)
     │          │
     │          ▼
     │     Supabase: Vector search on tier 2 chunks
     │          │
     │          └──── Returns: NVAB guideline on manual handling
     │
     ├──── get_guideline_full_context(guideline_id)
     │          │
     │          └──── Fetches all 3 tiers for context
     │
     └──── search_related_products(guideline_ids, query)
                │
                ▼
           Supabase: Vector search on products
           Filter by compliance_tags
                │
                └──── Returns: Ergonomics training,
                              Bedrijfsfysiotherapie
     │
     ▼
Research Agent returns structured data
     │
     ▼
Intervention Specialist Agent
     │
     │ Format response in Dutch
     │ Structure recommendations:
     │   - Relevant NVAB guideline (Tier 2 summary)
     │   - Compliance requirement: "Werkgever moet ergonomische training bieden"
     │   - Product 1: Ergonomie training (with URL)
     │   - Product 2: Bedrijfsfysiotherapie (with URL)
     │   - Reasoning linking guideline to products
     │
     ▼
Dutch Response to User
```

### API Endpoints

#### Primary Endpoint
**POST `/chat`**
- Input: `{"message": "Dutch query", "session_id": "uuid"}`
- Output: Dutch-formatted response with guidelines & products
- Agent: Intervention Specialist Agent

#### Research Endpoint (for debugging)
**POST `/research`**
- Input: `{"query": "search term", "tier": 2}`
- Output: Raw guideline/product search results
- Agent: Research Agent

#### Streaming Endpoint
**POST `/chat/stream`**
- Same as `/chat` but with SSE streaming
- Allows real-time response generation

---

## Dependencies and Libraries

### New Dependencies to Add

```txt
# Notion API
notion-client==2.2.1

# Web Scraping
beautifulsoup4==4.12.3
lxml==5.1.0

# Already included (verify versions)
pydantic-ai>=0.0.14
asyncpg>=0.29.0
fastapi>=0.109.0
httpx>=0.26.0
```

### Update requirements.txt

```bash
# Add to requirements.txt
notion-client==2.2.1
beautifulsoup4==4.12.3
lxml==5.1.0
```

---

## Testing Strategy

### Unit Tests

**New test files:**
- `tests/ingestion/test_notion_client.py` - Notion API mocking
- `tests/ingestion/test_tier_chunker.py` - Tier extraction logic
- `tests/ingestion/test_product_scraper.py` - Scraping logic
- `tests/agent/test_research_agent.py` - Research agent tools
- `tests/agent/test_specialist_agent.py` - Specialist agent formatting
- `tests/test_dutch_language.py` - Dutch output validation

**Testing approach:**
- Mock Notion API responses with example guideline pages
- Mock product website HTML
- Mock database connections (existing pattern from tests/conftest.py)
- Mock LLM calls for deterministic testing

### Integration Tests

**Test scenarios:**
1. **End-to-end guideline ingestion:** Notion → PostgreSQL → Neo4j
2. **End-to-end product ingestion:** Website → PostgreSQL
3. **Multi-agent query flow:** User query → Specialist → Research → Response
4. **Tier search strategy:** Verify L1/L2 searched before L3

### Manual Testing (MVP)

**Test cases from requirements:**

1. **Back injury from lifting:**
   ```
   Query: "Ik heb last van m'n onderrug, meestal nadat ik een paar dozen
          van 10 kilo heb verplaatst. Kan je een plan van aanpak schrijven
          op basis van STECR of NVAB richtlijnen..."

   Expected:
   - NVAB/STECR guideline on manual handling
   - Compliance requirements (ergonomic training, workstation adjustments)
   - Products: Bedrijfsfysiotherapie, Ergonomie training
   - Response in Dutch
   - Response time < 10 seconds
   ```

2. **Workplace accident (finger injury):**
   ```
   Query: "Guido heeft z'n vinger afgehakt in de werkplaats, daardoor kan
          hij niet meer in de houtzagerij werken. Welke interventies stel
          je voor?"

   Expected:
   - NVAB guideline on workplace accidents/reintegration
   - Compliance requirements (accident reporting, safety measures)
   - Products: Arbeidsdeskundige, Re-integratie coaching
   - Response in Dutch
   ```

3. **Head injury with cognitive impact:**
   ```
   Query: "M'n werknemer Patrick heeft z'n hoofd gestoten en weet niet
          meer wat hij als office manager moet doen. Wat adviseer jij?"

   Expected:
   - NVAB guideline on neurological injury/cognitive assessment
   - Compliance requirements (medical evaluation, work modifications)
   - Products: Neuropsychologisch onderzoek, Arbeidsdeskundige
   - Response in Dutch
   ```

### Edge Cases to Test

- Query with no matching guidelines → Graceful response
- Query matching multiple unrelated guidelines → Prioritization logic
- Product catalog empty → Explain no products available
- Dutch query with English terms → Handle mixed language
- Very specific tier 3 query → Verify tier 3 search triggered

---

## Success Criteria

### MVP Success Metrics

- [ ] Ingest all ~100 Dutch guidelines from Notion with 3-tier structure preserved
- [ ] Ingest ~100 EVI products from website with categories
- [ ] Research Agent can search guidelines by tier (tier 1/2 first, tier 3 fallback)
- [ ] Research Agent can recommend products aligned with guidelines
- [ ] Intervention Specialist Agent formats responses in Dutch per prompt template
- [ ] CLI interface works for testing queries
- [ ] All 3 sample queries return relevant results:
  - Relevant Dutch guidelines (NVAB, STECR, etc.)
  - Specific compliance requirements
  - 2-5 relevant EVI products with URLs
  - Dutch language throughout
- [ ] Response time < 10 seconds for typical query
- [ ] Guideline-to-product reasoning is clear and logical

### Quality Metrics

- [ ] Dutch language accuracy verified by native speaker
- [ ] Product URLs are valid and correct
- [ ] Guideline citations are accurate (correct source, title)
- [ ] No hallucinated guidelines or products
- [ ] Tier search strategy works (L1/L2 before L3)

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| 3-tier structure not well-defined in Notion | High | Medium | Review example docs, create extraction heuristics, manual validation |
| Notion API rate limits during ingestion | Medium | Low | Implement exponential backoff, batch requests, cache pages |
| Dutch language processing less accurate | Medium | Low | Use OpenAI models (good Dutch support), validate with test queries |
| Product scraping breaks with website changes | Medium | Medium | Version scraping logic, implement error handling, manual fallback |
| Supabase free tier limits exceeded | Low | Low | Monitor usage, optimize queries, plan upgrade path |
| Knowledge graph building too slow | Low | Low | Can skip graph for MVP (vector search sufficient), add later |
| Agent calling agent pattern complexity | Medium | Medium | Thorough testing, clear interface contracts, fallback to direct tools |

### Data Quality Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Inconsistent Notion formatting | High | High | Robust parsing with fallbacks, manual cleanup script, validation tests |
| Products lack sufficient detail for embeddings | Medium | Medium | Enhance descriptions manually, use meta descriptions, contact EVI360 |
| Guidelines outdated or incorrect | High | Low | Track ingestion dates, implement review workflow, version control |
| Product-to-guideline alignment weak | Medium | Medium | Improve categorization, add manual tagging, refine compliance_tags logic |
| Missing Dutch translations for products | Low | Medium | Keep original names, translate descriptions only, ask EVI360 for translations |

### Process Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Scope creep beyond MVP | Medium | High | Strict MVP scope, defer OpenWebUI and automation to Phase 2 |
| Insufficient test data | Medium | Medium | Create synthetic test cases, manual test queries, user feedback loop |
| Dependencies on external services | Medium | Low | Use stable API versions, implement retry logic, have backup plans |

---

## Open Questions & Decisions Needed

### Schema & Metadata Design

**Questions:**
1. What specific metadata fields for guidelines beyond tier/source/title?
   - **Proposed:** `{tier, source, process_date, staging_uuid, category, keywords}`
   - **Decision needed:** Confirm with data owner

2. What product categories to use?
   - **Options:**
     - A) Manual expert categorization
     - B) LLM-generated from descriptions
     - C) Hybrid (LLM suggests, expert reviews)
   - **Recommendation:** Start with B (LLM), refine with C (expert review)
   - **Decision needed:** Confirm approach

3. How to tag guideline-product relationships?
   - **Proposed:** `compliance_tags` array on products (e.g., ["manual_handling", "ergonomics", "reintegration"])
   - **Decision needed:** Validate tag taxonomy

4. What indexes needed for optimal performance?
   - **Proposed:**
     - IVFFLAT on embeddings (both chunks and products)
     - GIN on compliance_tags
     - BTREE on tier
     - GIN on metadata JSONB
   - **Decision needed:** Performance testing after initial load

### Product Categorization

**Question:** How should products be categorized?

**Options:**
1. Manual categorization by domain expert (high accuracy, slow)
2. AI-generated categories from product descriptions (fast, needs review)
3. Hybrid: AI suggestions + manual review (balanced)

**Recommendation:** Option 3 (Hybrid)
- Use GPT-4 to analyze product descriptions
- Generate suggested categories and compliance_tags
- Human expert reviews and corrects
- Iterate on prompt engineering for better accuracy

**Decision needed:** Confirm approach and allocate expert time

### Tier Search Strategy

**Question:** How should the agent decide when to search each tier?

**Options:**
1. Always search L1/L2 first, L3 only if insufficient results
2. Use query complexity to determine tier (simple → L1, complex → L3)
3. Search all tiers, rank by relevance + tier weight

**Recommendation:** Option 1 with fallback
- Default: Search tier 2 (detailed summaries)
- If < 3 results with good scores: Search tier 1 + tier 3
- Agent can explicitly request tier 3 via tool parameter
- Benefits: Fast responses, access to detail when needed

**Decision needed:** Validate with sample queries

**Implementation:**
```python
async def search_guidelines_by_tier(
    query: str,
    tier: int = 2,  # Default to tier 2
    fallback: bool = True,  # Auto-fallback to other tiers
    limit: int = 5
) -> List[GuidelineSearchResult]:
    """Search with tier preference and optional fallback."""
```

### Notion Structure Validation

**Question:** Can you share the exact structure of a Notion page showing the 3-tier format?

**Action needed:** Review `big_tech_docs/example_evi_richtlijn_prikaccidenten.md` to confirm:
- Tier 1: "## Summary" section (line 5)
- Tier 2: "### Summary" + "### Key Data and Insights" (lines 5-44)
- Tier 3: "### Raw PDF" (lines 54-83)

**Note:** Example shows clear markdown structure - can extract by H2/H3 headers

### Product Website Structure

**Question:** What information is available for each product on the website?

**Action needed:** Inspect EVI360.nl product pages to determine:
- HTML structure and selectors
- Available fields (name, description, category, price, etc.)
- Pagination or listing format
- Any structured data (JSON-LD, microdata)

**Example from requirements:** `big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md` shows:
- Product name: "Bedrijfsfysiotherapie"
- Description: Multi-paragraph Dutch text
- Section headers: Beschrijving, Werkwijze, Resultaat, Maatwerk
- No explicit category or compliance tags (need to infer)

---

## Next Steps

### Immediate Actions (Before Implementation)

1. **✅ Review this PRP with stakeholders**
   - Validate approach and scope
   - Confirm MVP boundaries
   - Get approval on technology choices

2. **Validate Notion Structure**
   - Connect to Notion API with test token
   - Fetch 1-2 sample guideline pages
   - Verify 3-tier extraction logic works
   - Document any deviations from assumptions

3. **Inspect Product Website**
   - Visit EVI360.nl product pages
   - Document HTML structure
   - Test scraping approach with 1-2 products
   - Verify URL patterns

4. **Finalize Database Schema**
   - Review proposed products table schema
   - Confirm compliance_tags taxonomy
   - Decide on additional metadata fields
   - Get approval from data owner

5. **Setup Infrastructure**
   - Create Supabase project
   - Run base schema + EVI additions
   - Start Neo4j Docker container
   - Verify database connections

6. **Begin Phase 1 Implementation**
   - Follow task sequence in Implementation Tasks section
   - Use TodoWrite tool to track progress
   - Update TASK.md after each completed phase

### Implementation Order

**Week 1: Infrastructure & Schema**
- Phases 1, 2 (Infrastructure Setup, Data Models & Schema)
- Deliverable: Databases configured, schemas deployed

**Week 2: Ingestion Pipelines**
- Phases 3, 4 (Notion Integration, Product Scraping)
- Deliverable: Can ingest guidelines and products

**Week 3: Multi-Agent System**
- Phase 5 (Multi-Agent System)
- Deliverable: Research + Specialist agents working

**Week 4: Polish & Testing**
- Phases 6, 7, 8 (Dutch Language, CLI, Documentation)
- Deliverable: Fully functional MVP ready for user testing

### Success Validation

After implementation:
1. Run all 3 sample queries from requirements
2. Validate Dutch output with native speaker
3. Check guideline citations for accuracy
4. Verify product URLs are correct
5. Measure response times
6. Document any issues or refinements needed

---

## References

### Base Repository
- **GitHub:** https://github.com/coleam00/ottomator-agents/tree/main/agentic-rag-knowledge-graph
- **Local:** `/Users/builder/dev/evi_rag_test/`

### Requirements & Examples
- **Requirements:** [PRPs/requests/evi_rag_system_request.md](PRPs/requests/evi_rag_system_request.md)
- **Intervention Specialist Prompt:** [agent/intervention_specialist_prompt.md](agent/intervention_specialist_prompt.md)
- **Example Guideline:** [big_tech_docs/example_evi_richtlijn_prikaccidenten.md](big_tech_docs/example_evi_richtlijn_prikaccidenten.md)
- **Example Product:** [big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md](big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md)

### Documentation (Archon Knowledge Base)
- **Pydantic AI:** c0e629a894699314 (ai.pydantic.dev)
- **FastAPI:** c889b62860c33a44 (fastapi.tiangolo.com)
- **PGVector:** c5f2c6c39c63757b (github.com/pgvector/pgvector)
- **Supabase:** 9c5f534e51ee9237 (supabase.com/docs)
- **Neo4j:** d3a9cedab9c9e2ec (neo4j.com/docs/python-manual)

### Key Implementation Files (Base Repo)
- `agent/agent.py` - Pydantic AI agent pattern
- `agent/tools.py` - Tool implementation examples
- `agent/prompts.py` - System prompt configuration
- `ingestion/chunker.py` - Semantic chunking
- `ingestion/embedder.py` - Embedding generation
- `sql/schema.sql` - PostgreSQL + PGVector schema

---

**Document Version:** 1.0
**Created:** 2025-10-19
**Status:** Ready for Review
**Next Step:** Stakeholder review and approval

---

*This plan is ready for execution. Use `/execute-plan PRPs/evi_rag_implementation_plan.md` to begin implementation with full Archon task management integration.*
