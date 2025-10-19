# EVI 360 RAG System - Project Overview

**Vision**: Build an intelligent assistant for EVI 360 workplace safety specialists that provides tiered guideline access, product recommendations, and operates entirely in Dutch.

---

## 🎯 Project Goals

1. **Rapid Information Access**: 3-tier guideline hierarchy (Summary → Key Facts → Details)
2. **Product Integration**: Connect safety guidelines with relevant equipment
3. **Dutch Language First**: Native Dutch support for search and responses
4. **Conversation Context**: Multi-agent system maintains query state
5. **Notion Integration**: Live sync with EVI 360's guideline database
6. **Unlimited Scale**: Local PostgreSQL with no storage limits

---

## 🏗️ Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        User Interface                              │
│                    (CLI / API / Web - Future)                      │
└────────────────────────────────┬─────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Layer                                   │
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
│                     Storage Layer                                 │
│                                                                   │
│  ┌──────────────────────────┐    ┌────────────────────────────┐ │
│  │ PostgreSQL + pgvector    │    │   Neo4j + APOC            │ │
│  │                          │    │                            │ │
│  │ - Documents              │    │ - Guideline relationships │ │
│  │ - Chunks (with tier)     │    │ - Product connections     │ │
│  │ - Products               │    │ - Knowledge graph         │ │
│  │ - Sessions/Messages      │    │ - Temporal data           │ │
│  │ - Vector embeddings      │    │                            │ │
│  └──────────────────────────┘    └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                  ↑
┌─────────────────────────────────────────────────────────────────┐
│                    Ingestion Layer                                │
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

---

## 📊 3-Tier Guideline Hierarchy

### Design Rationale

Safety specialists need different levels of information detail:
- **Quick triage**: Is this guideline relevant? (Tier 1)
- **Most queries**: What are the key facts? (Tier 2)
- **Deep dive**: Give me everything (Tier 3)

### Tier Structure

**Tier 1: Summary** (1-2 sentences)
```
Example:
"Werken op hoogte vereist valbescherming vanaf 2.5 meter.
Veiligheidsvoorschriften EN 795 zijn verplicht."
```
- Single chunk, always retrieved together
- Provides quick context for relevance assessment
- ~50-100 words max

**Tier 2: Key Facts** (3-5 key points)
```
Example:
- Valbescherming verplicht vanaf 2.5m hoogte
- Valharnas EN 361 gecertificeerd vereist
- Ankerpunten moeten EN 795 norm hebben
- Inspectie elke 6 maanden verplicht
- Training medewerkers jaarlijks herhalen
```
- Semantically chunked for targeted retrieval
- Answers 80% of specialist queries
- ~200-500 words

**Tier 3: Full Details** (complete technical documentation)
```
Example:
[Full technical specifications, legal requirements,
step-by-step procedures, equipment details, inspection protocols,
training requirements, risk assessments, etc.]
```
- Retrieved only when explicitly needed
- Complete reference documentation
- ~1000-5000 words

### Database Storage

```sql
-- chunks table
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    tier INTEGER CHECK (tier IN (1, 2, 3)),  -- ← Tier marker
    content TEXT,
    embedding vector(1536),
    ...
);

-- Tier-aware search function
SELECT * FROM search_guidelines_by_tier(
    query_embedding,
    query_text,
    target_tiers := ARRAY[1, 2],  -- ← Filter by tier
    limit := 10
);
```

---

## 🤖 Multi-Agent System

### Agent Architecture

**Two specialized agents working together:**

1. **Research Agent** (Tool/Helper Agent)
   - Purpose: Retrieve and aggregate information
   - Tools: Vector search, graph traversal, product lookup
   - Output: Structured data for Specialist Agent

2. **Intervention Specialist Agent** (Primary Agent)
   - Purpose: Provide expert safety guidance
   - Tools: Research Agent (as a tool!)
   - Output: Dutch language responses + product recommendations

### Why This Design?

**Separation of concerns:**
- Research Agent = data retrieval expert
- Specialist Agent = domain expert communicator

**Benefits:**
- Research Agent can be called multiple times per query
- Specialist Agent maintains conversation context
- Clear responsibility boundaries
- Easy to test and debug each agent independently

### Agent Interaction Flow

```
User: "Wat zijn de vereisten voor werken op hoogte?"

Specialist Agent:
  1. Analyzes query intent
  2. Calls Research Agent(query="werken op hoogte", tiers=[1])
  3. Reviews Tier 1 results
  4. Decides: Need more detail
  5. Calls Research Agent(query="werken op hoogte", tiers=[2])
  6. Reviews Tier 2 results
  7. Calls Research Agent(query_products="valbescherming")
  8. Synthesizes all information
  9. Responds in Dutch with guideline summary + products

User receives:
  - Comprehensive answer
  - Relevant product recommendations
  - All in Dutch language
```

---

## 🗄️ Data Flow

### Guideline Ingestion (Notion → Database)

```
Notion Database
    ↓
Fetch all guidelines via Notion API
    ↓
Detect tier markers in content
(e.g., "## Samenvatting", "## Kerninformatie", "## Volledige Details")
    ↓
Split content by tier
    ↓
Apply chunking strategy per tier:
- Tier 1: Keep as single chunk
- Tier 2: Semantic chunking (3-5 chunks)
- Tier 3: Semantic chunking (10-20 chunks)
    ↓
Generate embeddings (text-embedding-3-small)
    ↓
Store in PostgreSQL with tier metadata
    ↓
Build knowledge graph in Neo4j
(relationships between guidelines, concepts, products)
```

### Product Ingestion (Website → Database)

```
EVI 360 Website
    ↓
Scrape product pages (BeautifulSoup4)
    ↓
Extract: name, description, URL, category
    ↓
AI-assisted categorization (GPT-4/Claude)
- Assign category/subcategory
- Generate compliance_tags array
    ↓
Generate embeddings
    ↓
Store in products table
    ↓
Link to guidelines in knowledge graph
```

### Query Processing (User → Response)

```
User query (Dutch)
    ↓
Specialist Agent receives query
    ↓
Calls Research Agent with tier strategy
    ↓
Research Agent:
  - Generates query embedding
  - Calls search_guidelines_by_tier(tiers=[1])
  - Calls search_products() if relevant
  - Calls Neo4j for relationships
    ↓
Returns structured results to Specialist
    ↓
Specialist Agent synthesizes:
  - Formulates Dutch language response
  - Includes relevant product recommendations
  - Maintains conversation context
    ↓
User receives comprehensive Dutch response
```

---

## 🌍 Dutch Language Support

### Full-Text Search

PostgreSQL configured with `dutch` language:
```sql
-- In hybrid_search() function
to_tsvector('dutch', content)  -- ← Dutch stemming & stop words
```

**Features:**
- Dutch stemming (werken → werk)
- Dutch stop words removed (de, het, een, etc.)
- Proper handling of Dutch characters (ë, ï, ü)

### Agent Responses

- System prompts configure Dutch output
- LLM generates responses in Dutch
- Product names may be in Dutch or English (as per catalog)

### Example Query Flow

```
User: "Wat zijn de vereisten voor persoonlijke beschermingsmiddelen?"

Database search: to_tsvector('dutch', 'persoonlijke beschermingsmiddelen')
→ Matches content with: bescherming, beschermd, pbm, etc.

Agent response (Dutch):
"Voor persoonlijke beschermingsmiddelen (PBM) gelden de volgende vereisten:
1. CE-certificering volgens EN-normen
2. Jaarlijkse inspectie verplicht
3. Training voor correct gebruik
..."
```

---

## 🔗 Technology Stack

### Core Infrastructure

- **PostgreSQL 17 + pgvector 0.8.1**: Vector similarity search
- **Neo4j 5.26.1 + APOC**: Knowledge graph with temporal support
- **Docker Compose**: Local deployment with persistent volumes

### Python Stack

- **Pydantic AI**: Agent framework
- **asyncpg**: Async PostgreSQL driver
- **notion-client**: Notion API integration
- **beautifulsoup4**: Web scraping
- **httpx**: Async HTTP client
- **FastAPI**: API layer (to be implemented)

### Data & Validation

- **Pydantic v2**: Data models with validation
- **8 custom models**: TieredGuideline, EVIProduct, SearchResults, etc.

---

## 📋 Current Implementation Status

**Phase 1-2**: ✅ Complete
- Infrastructure (PostgreSQL + Neo4j)
- Database schema with tier support
- 8 Pydantic models
- Notion configuration
- Test suite (100% passing)

**Phase 3**: ⏳ Next (Notion Integration)
- Notion API client
- Tier-aware chunking
- Guideline ingestion pipeline

**Phase 4-8**: 📝 Planned
- Product scraping
- Multi-agent system
- Dutch language polish
- CLI interface
- Comprehensive testing
- Documentation

See [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) for detailed tracking.

---

## 🎓 Key Design Decisions

### Why 3 Tiers?

**Alternative considered**: Single flat structure
**Decision**: Tiered hierarchy
**Rationale**:
- Safety specialists need quick triage (Tier 1)
- Most queries answered by key facts (Tier 2)
- Deep dives when needed (Tier 3)
- More efficient than always retrieving everything

### Why Local PostgreSQL?

**Alternative considered**: Supabase cloud
**Decision**: Local Docker
**Rationale**:
- No usage limits (was hitting 500 MB Supabase limit)
- 20-100x faster (localhost vs cloud)
- Unlimited storage for large knowledge base
- Complete control over configuration
- $300/year cost savings

### Why Multi-Agent (Research + Specialist)?

**Alternative considered**: Single agent with all tools
**Decision**: Two specialized agents
**Rationale**:
- Separation of concerns (retrieval vs communication)
- Research Agent can be called multiple times per query
- Clearer responsibility boundaries
- Easier testing and debugging
- Specialist maintains conversation context

### Why Notion Integration?

**Alternative considered**: Manual markdown files
**Decision**: Notion API sync
**Rationale**:
- EVI 360 already uses Notion for guidelines
- Live sync = always up-to-date content
- No manual export/import process
- Notion's structured content works well with tier detection

---

## 📊 Success Metrics

### Performance Targets

- Query latency: <  500ms for Tier 1 queries
- Query latency: < 1000ms for Tier 2 queries
- Query latency: < 2000ms for full Tier 3 queries
- Embedding generation: < 100ms per chunk
- Notion sync: < 5 minutes for full guideline database

### Accuracy Targets

- Tier classification: > 95% correct tier assignment
- Dutch search: > 90% relevant results in top 5
- Product recommendations: > 80% relevance per specialist feedback

### Scale Targets

- Guidelines: Support 1000+ guidelines with 3 tiers each
- Products: Support 500+ products with compliance tags
- Chunks: Handle 10,000+ chunks with embeddings
- Concurrent users: Support 10+ simultaneous sessions

---

## 🚀 Next Steps

See [README.md](README.md) and [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) for current status and next tasks.

---

**Document Status**: Living document, updated as architecture evolves.
**Last Updated**: October 19, 2025
