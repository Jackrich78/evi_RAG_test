# EVI RAG System - Project Request Document

**Document Type:** Project Requirements & Planning Request
**Date:** 2025-10-19
**Status:** Initial Planning Phase
**Project Code:** EVI-RAG-001

---

## Executive Summary

Build a RAG (Retrieval-Augmented Generation) knowledge base system for workplace safety specialists at EVI 360 to:
- Search Dutch government safety guidelines
- Get regulatory compliance recommendations
- Receive EVI product suggestions aligned with safety regulations
- Understand connections between regulations and product recommendations

---

## Project Overview

### What We're Building

A multi-agent RAG system that helps workplace safety specialists find relevant Dutch government safety guidelines and recommend appropriate EVI products based on those guidelines.

### Core Use Case

**Example Query:**
> "My employee has hurt their back lifting boxes, what should I suggest?"

**Expected Flow:**
1. System searches Dutch safety guidelines about manual handling/lifting
2. Retrieves relevant regulatory requirements and best practices
3. Suggests EVI products that help comply with those guidelines
4. Explains the connection between regulations and recommendations

---

## Technical Foundation

### Base Repository

**Source:** `coleam00/ottomator-agents/agentic-rag-knowledge-graph`
**GitHub:** https://github.com/coleam00/ottomator-agents/tree/main/agentic-rag-knowledge-graph

**What it provides:**
- Pydantic AI agent framework
- PostgreSQL + PGVector for vector search
- Neo4j + Graphiti for knowledge graph
- Semantic chunking implementation
- FastAPI with streaming responses
- CLI interface
- Example: Tech company AI initiatives (to be adapted for safety guidelines)

**Status:** ✅ Cloned and available in this repository

---

## Data Sources

### 1. Dutch Safety Guidelines

**Source:** Notion database (already scraped)
**Volume:** ~100 guidelines
**Page Length:** 10-100 pages each

**Critical Structure - 3-Tier Hierarchy:**

Each guideline document has three levels of information:

- **Level 1:** High-level summary (lightweight, fast retrieval)
- **Level 2:** Detailed summary + key facts (medium detail)
- **Level 3:** Raw PDF content (comprehensive, specific queries)

**Example Document:** [big_tech_docs/example_evi_richtlijn_prikaccidenten.md](big_tech_docs/example_evi_richtlijn_prikaccidenten.md)

**Update Frequency:** Very infrequent (monthly manual re-ingestion is sufficient)

### 2. EVI Product Catalog

**Source:**
- EVI 360 website (source of truth)
- Notion database (backup)

**Volume:** ~100 products

**Current State:**
- ❌ Products are NOT currently categorized
- ❌ Products are NOT aligned to guidelines yet
- ✅ Website is source of truth

**Requirements:**
- Automated scraping preferred (products may change)
- Need to add categorization/metadata for better recall
- System must determine guideline-to-product alignment via RAG

**Example Product:** [big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md](big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md)

---

## Example User Queries

Real queries from EVI intervention specialists:

1. **Back Injury from Lifting:**
   > "Ik heb last van m'n onderrug, meestal nadat ik een paar dozen van 10 kilo heb verplaatst. Kan je een plan van aanpak schrijven op basis van STECR of NVAB richtlijnen om er voor te zorgen dat ik zo snel mogelijk weer kan re-integreren in mijn werk"

2. **Workplace Accident:**
   > "Guido heeft z'n vinger afgehakt in de werkplaats, daardoor kan hij niet meer in de houtzagerij werken. Welke interventies stel je voor?"

3. **Head Injury/Cognitive Impact:**
   > "M'n werknemer Patrick heeft z'n hoofd gestoten en weet niet meer wat hij als office manager moet doen. Wat adviseer jij?"

---

## Architecture Decisions

### Infrastructure

| Component | Technology | Deployment | Status |
|-----------|-----------|------------|---------|
| **Vector Database** | PostgreSQL + PGVector | Supabase (cloud) | ⏳ To be set up |
| **Knowledge Graph** | Neo4j + Graphiti | Docker (local dev) | ⏳ To be set up |
| **API Framework** | FastAPI | Docker | ✅ Available |
| **Agent Framework** | Pydantic AI | - | ✅ Available |
| **Interface (Now)** | CLI | - | ✅ Available |
| **Interface (Future)** | OpenWebUI | Docker | 📋 Planned |

### LLM & Embedding Configuration

**Embeddings:**
- **Model:** OpenAI `text-embedding-3-small` (1536 dimensions)
- **Future:** Consider Dutch-optimized models for improvement

**LLM:**
- **Provider:** OpenAI
- **Model:** GPT-4 (or latest available)
- **Future:** Open to switching providers

**Language Processing:**
- **Input:** Dutch (primary)
- **Output:** Dutch (all user-facing text)
- **Internal:** Can remain English where appropriate

### Multi-Agent Architecture

**Research Agent:**
- Searches guidelines and products
- Returns relevant data
- Handles RAG retrieval logic

**Intervention Specialist Agent:**
- Front-facing agent that interacts with users
- Asks clarifying questions
- Formats responses according to specialist prompt
- Leverages Research Agent for data retrieval

**Reference:** [agent/intervention_specialist_prompt.md](agent/intervention_specialist_prompt.md)

---

## Technical Requirements

### 1. Notion API Integration

**Status:** ⏳ Not yet configured

**Requirements:**
- Notion integration token available (can create new if needed)
- API setup needed as part of initial database configuration
- Must extract 3-tier structure from Notion pages
- Preserve formatting and hierarchy during ingestion

### 2. Database Schema Requirements

**Critical Considerations:**
- ✅ Exact schema must be clearly defined before implementation
- ✅ Metadata structure must support scalability
- ✅ Schema should be reusable template for different data types
- ✅ Must support 3-tier document hierarchy
- ✅ Must support product categorization/tagging

**New Tables Needed:**
```sql
-- Products table
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    compliance_tags TEXT[],
    embedding vector(1536),
    price DECIMAL(10,2),
    url TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);

-- Enhanced chunks to track tiers
ALTER TABLE chunks ADD COLUMN tier INTEGER CHECK (tier IN (1, 2, 3));
```

### 3. Product Scraping Pipeline

**Requirements:**
- Automated web scraping from EVI 360 website
- Scheduled updates (manual trigger for MVP)
- Categorization logic for products
- Embedding generation for product descriptions

### 4. Dutch Language Support

**Database Changes:**
```sql
-- Update PostgreSQL full-text search to Dutch
-- In hybrid_search function (lines 138, 145)
to_tsvector('dutch', c.content)  -- Changed from 'english'
plainto_tsquery('dutch', query_text)
```

**Agent Prompts:**
- System prompt: "Always respond in Dutch"
- All user-facing output in Dutch
- Formatting per intervention specialist prompt guidelines

---

## MVP Scope

### Phase 1 Deliverables

**In Scope:**
- ✅ Guideline ingestion from Notion (3-tier structure)
- ✅ Basic product matching using existing agent framework
- ✅ Dutch language support in database and responses
- ✅ PostgreSQL + PGVector on Supabase
- ✅ Neo4j in Docker (local)
- ✅ CLI interface for testing
- ✅ Manual re-ingestion workflow

**Out of Scope (Future Phases):**
- ❌ OpenWebUI integration
- ❌ Automated Notion sync
- ❌ Advanced product categorization
- ❌ Production deployment
- ❌ Multi-user authentication

---

## Data Flow Architecture

### Ingestion Pipeline

```
┌─────────────────────┐
│   Notion Database   │
│   ~100 Guidelines   │
│   (Dutch, 3-tier)   │
└──────────┬──────────┘
           │
           ▼
┌───────────────────────────────┐
│ ingestion/notion_client.py    │
│ - Fetch via Notion API        │
│ - Extract 3-tier structure    │
│ - Preserve formatting         │
└──────────┬────────────────────┘
           │
           ▼
┌───────────────────────────────┐
│ ingestion/tier_chunker.py     │
│ - Separate L1, L2, L3 content │
│ - Different strategies/tier   │
│ - Add tier metadata           │
└──────────┬────────────────────┘
           │
           ▼
┌───────────────────────────────┐
│ ingestion/embedder.py         │
│ - OpenAI embeddings           │
│ - Embed each tier separately  │
└──────────┬────────────────────┘
           │
           ▼
       ┌───┴───┐
       ▼       ▼
┌──────────┐ ┌─────────┐
│ Supabase │ │  Neo4j  │
│ PGVector │ │Graphiti │
│          │ │         │
│Guidelines│ │Guideline│
│Products  │ │Relations│
└──────────┘ └─────────┘
```

### Query Pipeline

```
┌────────────────────────┐
│ User Query (Dutch)     │
│ "Rugklachten tillen"   │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────────────┐
│ Intervention Specialist Agent  │
│ - Parse query                  │
│ - Ask clarifying questions     │
│ - Format response (Dutch)      │
└──────────┬─────────────────────┘
           │
           ▼
┌────────────────────────────────┐
│ Research Agent                 │
│ - Search L1/L2 guidelines      │
│ - If needed, search L3         │
│ - Find matching products       │
│ - Return structured data       │
└──────────┬─────────────────────┘
           │
       ┌───┴───┐
       ▼       ▼
┌──────────┐ ┌─────────┐
│ PGVector │ │  Neo4j  │
│ Search   │ │ Traverse│
└──────────┘ └─────────┘
```

---

## Critical Adaptations from Base Repository

### 1. Document Structure (Major Change)

**Current:** Flat markdown → semantic chunks
**Needed:** 3-tier hierarchy → tier-aware chunking

**Implementation:**
- Modify `ingestion/chunker.py` to recognize tier markers
- Create tier-specific chunking strategies
- Add `tier` column to `chunks` table
- Agent searches L1/L2 first, then L3 if needed

### 2. Notion Integration (New Component)

**Files to Create:**
- `ingestion/notion_client.py` - API wrapper
- `config/notion_config.py` - Authentication & settings

### 3. Product Catalog (New Component)

**Files to Create:**
- `ingestion/product_scraper.py` - Web scraping
- `agent/product_tools.py` - Product search tools
- SQL schema updates for `products` table

### 4. Dutch Language (Database & Agent)

**Database:**
- Update `sql/schema.sql` full-text search to `'dutch'`
- Test with Dutch text for proper tokenization

**Agent:**
- Update system prompts for Dutch output
- Use intervention specialist prompt template
- Ensure all user-facing text is Dutch

### 5. Multi-Agent System (Architecture)

**Current:** Single RAG agent
**Needed:** Research Agent + Intervention Specialist Agent

**Implementation:**
- Adapt `agent/agent.py` for Research Agent
- Create `agent/specialist_agent.py` for front-facing interactions
- Research Agent used as tool by Specialist Agent

---

## Setup Requirements

### Infrastructure Setup Needed

1. **Supabase Project:**
   - [ ] Create new Supabase project
   - [ ] Get connection string
   - [ ] Run SQL schema migrations
   - [ ] Enable PGVector extension
   - [ ] Configure Dutch full-text search

2. **Neo4j Docker:**
   - [ ] Docker Compose configuration
   - [ ] Local Neo4j instance
   - [ ] Graphiti setup

3. **Notion API:**
   - [ ] Create/configure integration token
   - [ ] Set up database access permissions
   - [ ] Test API connection

4. **Environment Variables:**
   ```bash
   # Supabase
   DATABASE_URL=postgresql://...

   # Neo4j (local)
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password

   # OpenAI
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-...
   LLM_CHOICE=gpt-4
   EMBEDDING_PROVIDER=openai
   EMBEDDING_API_KEY=sk-...
   EMBEDDING_MODEL=text-embedding-3-small

   # Notion
   NOTION_API_TOKEN=secret_...
   NOTION_DATABASE_ID=...

   # Application
   APP_ENV=development
   LOG_LEVEL=INFO
   APP_PORT=8058
   ```

---

## Documentation Requirements

### Archon Knowledge Base

Documentation being added to Archon for reference during implementation:

1. **Pydantic AI** - Agent framework patterns
   - URL: https://ai.pydantic.dev/

2. **PGVector** - Vector similarity search
   - URL: https://github.com/pgvector/pgvector

3. **Supabase PGVector** - Supabase-specific setup
   - URL: https://supabase.com/docs/guides/database/extensions/pgvector

4. **Neo4j + Graphiti** - Knowledge graph
   - Graphiti: https://github.com/getzep/graphiti
   - Neo4j: https://neo4j.com/docs/python-manual/current/

5. **FastAPI** - API framework
   - URL: https://fastapi.tiangolo.com/

6. **Notion API** - Database queries and page retrieval
   - URL: https://developers.notion.com/reference/intro

**Status:** ⏳ In progress

---

## Success Criteria

### MVP Success Metrics

- [ ] Ingest all ~100 Dutch guidelines from Notion with 3-tier structure preserved
- [ ] Ingest ~100 EVI products from website
- [ ] Research Agent can search guidelines by injury/risk type
- [ ] Research Agent can recommend relevant EVI products
- [ ] Intervention Specialist Agent formats responses in Dutch per prompt template
- [ ] CLI interface works for testing queries
- [ ] Response time < 5 seconds for typical query
- [ ] Relevant guidelines returned for sample queries (80%+ accuracy)
- [ ] Relevant products suggested based on guidelines

### Example Query Tests

All three example queries should return:
1. Relevant Dutch safety guidelines (NVAB, STECR, etc.)
2. Specific compliance requirements
3. 2-5 relevant EVI products with reasoning
4. Formatted response in Dutch per specialist prompt

---

## Timeline & Phases

### Phase 1: MVP (Current Focus)

**Goal:** Working RAG system with guidelines and basic product matching

**Deliverables:**
- Supabase database configured
- Neo4j running in Docker
- Notion ingestion pipeline
- Product scraping pipeline
- Research Agent with search tools
- Intervention Specialist Agent
- CLI interface
- Manual re-ingestion workflow

### Phase 2: Enhancement (Future)

**Potential Features:**
- OpenWebUI integration
- Automated Notion sync
- Advanced product categorization
- Performance optimization
- Multi-user support
- Production deployment

---

## Open Questions & Decisions Needed

### Schema & Metadata Design

**Critical:** Need to finalize exact schema and metadata structure before implementation

**Questions:**
- [ ] What specific metadata fields for guidelines? (source, date, category, etc.)
- [ ] What product categories to use? (manual definition or AI-generated?)
- [ ] How to tag guideline-product relationships?
- [ ] What indexes needed for optimal performance?

### Product Categorization

**Question:** How should products be categorized?

**Options:**
1. Manual categorization by domain expert
2. AI-generated categories from product descriptions
3. Hybrid: AI suggestions + manual review

**Decision:** TBD

### Tier Search Strategy

**Question:** How should the agent decide when to search each tier?

**Options:**
1. Always search L1/L2 first, L3 only if insufficient results
2. Use query complexity to determine tier (simple → L1, complex → L3)
3. Search all tiers, rank by relevance + tier weight

**Decision:** TBD

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| 3-tier structure not well-defined in Notion | High | Review sample documents, clarify structure with data owner |
| Dutch language processing less accurate | Medium | Use OpenAI models (good Dutch support), test thoroughly |
| Product scraping breaks with website changes | Medium | Version control scraping logic, implement error handling |
| Supabase free tier limits | Medium | Monitor usage, plan for upgrade if needed |
| Knowledge graph building too slow | Low | Can skip graph for MVP (already supported in code) |

### Data Quality Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Inconsistent Notion formatting | High | Develop robust parsing with error handling |
| Products lack sufficient detail | Medium | Enhance descriptions or add manual metadata |
| Guidelines outdated | Medium | Track ingestion dates, implement review workflow |

---

## Next Steps

### Immediate Actions

1. **Review & Validate:** Review this document with stakeholders
2. **Finalize Schema:** Define exact database schema and metadata structure
3. **Setup Infrastructure:**
   - Create Supabase project
   - Configure Neo4j Docker
   - Setup Notion API access
4. **Create Archon Project:** Set up project tracking in Archon MCP
5. **Generate Detailed PRP:** Create comprehensive implementation plan
6. **Begin Implementation:** Start with infrastructure setup

### Questions for Clarification

Before proceeding, please confirm:

1. **Notion Structure:** Can you share the exact structure of a Notion page showing the 3-tier format?
2. **Product Fields:** What information is available for each product on the website?
3. **Schema Preferences:** Any specific requirements for database schema design?
4. **Priority:** Any specific components that should be prioritized?

---

## References

- **Base Repository:** [coleam00/ottomator-agents](https://github.com/coleam00/ottomator-agents/tree/main/agentic-rag-knowledge-graph)
- **Intervention Specialist Prompt:** [agent/intervention_specialist_prompt.md](agent/intervention_specialist_prompt.md)
- **Example Guideline:** [big_tech_docs/example_evi_richtlijn_prikaccidenten.md](big_tech_docs/example_evi_richtlijn_prikaccidenten.md)
- **Example Product:** [big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md](big_tech_docs/example_evi360_product_bedrijfsfysiotherapie.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Next Review:** After stakeholder feedback
