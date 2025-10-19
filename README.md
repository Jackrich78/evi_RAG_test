# EVI 360 RAG System - Workplace Safety Intelligence

**Dutch-language RAG system for workplace safety specialists powered by 3-tier guideline hierarchy and product recommendations.**

---

## 🎯 Overview

EVI 360 RAG is an intelligent assistant system designed specifically for EVI 360 workplace safety specialists. It combines:

- **3-Tier Guideline Hierarchy**: Quick summaries → Key facts → Full technical details
- **Product Catalog Integration**: Safety equipment recommendations with compliance tags
- **Dutch Language Support**: Native Dutch full-text search and responses
- **Multi-Agent Architecture**: Research Agent + Intervention Specialist Agent
- **Notion Integration**: Live sync with guideline database
- **Knowledge Graph**: Relationships between guidelines, products, and safety concepts

---

## 🏗️ Architecture

### 3-Tier Guideline System

**Tier 1: Summary** (1-2 sentences)
- Quick overview for rapid triage
- Always retrieved as a single chunk

**Tier 2: Key Facts** (3-5 key points)
- Essential information for most queries
- Semantically chunked for targeted retrieval

**Tier 3: Full Details** (complete technical documentation)
- Comprehensive information for deep dives
- Retrieved only when explicitly needed

### Multi-Agent System

```
User Query → Research Agent → [Vector Search + Graph Traversal + Product Lookup]
                    ↓
         Intervention Specialist Agent → Dutch Response + Product Recommendations
```

**Research Agent**:
- Traverses tiers 1 → 2 → 3 as needed
- Searches product catalog with compliance filtering
- Retrieves knowledge graph relationships

**Intervention Specialist Agent**:
- Uses Research Agent as a tool
- Formulates Dutch language responses
- Provides contextual product recommendations
- Maintains conversation history

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Notion account with API access
- LLM API key (OpenAI, Ollama, or compatible)

### Installation

1. **Clone and enter directory**
   ```bash
   cd evi_rag_test
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start infrastructure services**
   ```bash
   docker-compose up -d

   # Verify services are healthy
   docker-compose ps
   # Both postgres and neo4j should show (healthy)
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # - NOTION_API_TOKEN
   # - NOTION_GUIDELINES_DATABASE_ID
   # - LLM_API_KEY
   ```

6. **Verify setup**
   ```bash
   python3 tests/test_supabase_connection.py
   # Should see all ✅ checks passing
   ```

---

## 📊 Current Status

**Phase 1-2**: ✅ Complete (Infrastructure + Data Models)
**Phase 3**: ⏳ Next (Notion Integration - 3 tasks)

See [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) for detailed progress tracking.

### What's Complete ✅

**Infrastructure**:
- ✅ PostgreSQL 17 + pgvector 0.8.1 (local, unlimited storage)
- ✅ Neo4j 5.26.1 with APOC plugin
- ✅ Docker Compose configuration with health checks
- ✅ Data persistence verified across container restarts

**Database Schema**:
- ✅ 5 tables: documents, chunks (with tier), products, sessions, messages
- ✅ 3 views: document_summaries, guideline_tier_stats, product_catalog_summary
- ✅ 3 functions: hybrid_search (Dutch), search_guidelines_by_tier, search_products
- ✅ Dutch language full-text search configured

**Data Models**:
- ✅ 8 Pydantic models with validation (TieredGuideline, EVIProduct, etc.)
- ✅ NotionConfig class for API integration
- ✅ Type-safe models for all data structures

**Testing**:
- ✅ Database connection validation (100% passing)
- ✅ Data persistence verification (100% passing)

### What's Next ⏳

**Phase 3: Notion Integration** (3 tasks):
1. Create Notion API client wrapper
2. Implement tier-aware chunking strategy
3. Build guideline ingestion pipeline

---

## 🛠️ Tech Stack

### Core Technologies

- **Database**: PostgreSQL 17 + pgvector 0.8.1
- **Graph DB**: Neo4j 5.26.1 + APOC
- **Agent Framework**: Pydantic AI
- **API**: FastAPI (to be implemented)
- **Language**: Python 3.11+

### Key Libraries

- **asyncpg**: Async PostgreSQL driver
- **httpx**: Async HTTP client
- **pydantic**: Data validation
- **notion-client**: Notion API integration
- **beautifulsoup4**: Web scraping for products
- **pytest**: Testing framework

---

## 📚 Documentation

### Active Documentation

- **[LOCAL_SETUP_COMPLETE.md](LOCAL_SETUP_COMPLETE.md)** - Complete setup guide with troubleshooting
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Detailed EVI 360 architecture
- **[CLAUDE.md](CLAUDE.md)** - AI assistant development instructions
- **[TASKS.md](TASKS.md)** - Task management (points to Archon MCP)
- **[docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md)** - Comprehensive progress tracking

### Historical Archives

- **[archive/2025-10-19_supabase_migration/](archive/2025-10-19_supabase_migration/)** - Migration documentation
- **[archive/2025-10-19_original_project_files/](archive/2025-10-19_original_project_files/)** - Template source files

---

## 🎓 Key Features

### Tier-Aware Search

```python
# Search with tier filtering
results = search_guidelines_by_tier(
    query_embedding=embedding,
    query_text="werken op hoogte",  # Dutch: "working at height"
    target_tiers=[1, 2],  # Summary + Key Facts
    limit=10
)
```

### Product Recommendations

```python
# Search products with compliance filtering
products = search_products(
    query_embedding=embedding,
    query_text="veiligheidshelm",  # Dutch: "safety helmet"
    compliance_tags=["EN_397", "CE_certified"],
    limit=5
)
```

### Dutch Language Support

- Full-text search configured for Dutch (`dutch` language in PostgreSQL)
- Stemming and stop word handling for Dutch
- Agent responses in Dutch

---

## 🗄️ Database Schema

### Tables

1. **documents** - Source document metadata
2. **chunks** - Text chunks with `tier` (1, 2, or 3)
3. **products** - EVI 360 products with `compliance_tags` array
4. **sessions** - Conversation sessions
5. **messages** - Chat message history

### Functions

- `hybrid_search()` - Combined vector + full-text search (Dutch)
- `search_guidelines_by_tier()` - Tier-aware guideline search
- `search_products()` - Product search with compliance filtering

See [sql/evi_schema_additions.sql](sql/evi_schema_additions.sql) for complete schema.

---

## 🧪 Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Database connection validation
python3 tests/test_supabase_connection.py

# Data persistence verification
python3 tests/test_data_persistence.py
```

All tests should show ✅ passing with detailed output.

---

## 🔧 Common Operations

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres
docker-compose logs -f neo4j

# Stop services (keeps data!)
docker-compose down
```

### Database Access

```bash
# Interactive SQL
docker exec -it evi_rag_postgres psql -U postgres -d evi_rag

# Quick query
docker exec evi_rag_postgres psql -U postgres -d evi_rag -c "SELECT COUNT(*) FROM chunks;"

# Backup database
docker exec evi_rag_postgres pg_dump -U postgres evi_rag > backup_$(date +%Y%m%d).sql
```

---

## 🎯 Project Goals

1. **Rapid Information Access**: 3-tier system allows quick triage or deep dives as needed
2. **Product Integration**: Connect guidelines with relevant safety equipment
3. **Dutch Language First**: Native Dutch support throughout the system
4. **Conversation Context**: Multi-agent system maintains query context
5. **Notion Integration**: Live sync with EVI 360's guideline database
6. **Unlimited Scale**: Local PostgreSQL = no storage limits

---

## 🚦 Next Steps

Ready to continue development? Here's what's next:

1. **Phase 3: Notion Integration** (3 tasks)
   - Build Notion API client
   - Implement tier-aware chunking
   - Create guideline ingestion pipeline

2. **Phase 4: Product Scraping** (3 tasks)
   - Scrape EVI 360 website
   - AI-assisted categorization
   - Product ingestion pipeline

3. **Phase 5: Multi-Agent System** (6 tasks)
   - Build Research Agent
   - Build Specialist Agent
   - Wire up orchestration

See [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) for complete phase breakdown.

---

## 📝 Development Guidelines

- Follow patterns in [CLAUDE.md](CLAUDE.md)
- Use Archon MCP for task tracking (see [TASKS.md](TASKS.md))
- Keep files under 500 lines
- Write unit tests for all new features
- Update [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) as you go

---

## 🤝 Contributing

This is an EVI 360-specific system. Development follows:
- Python style: PEP8 with type hints
- Documentation: Google-style docstrings
- Testing: pytest with comprehensive coverage
- Task tracking: Archon MCP (project ID: `c5b0366e-d3a8-45cc-8044-997366030473`)

---

## 📖 Credits

**Template Source**: Agentic RAG with Knowledge Graph by Cole Medin (coleam00)
- Repository: https://github.com/coleam00/ottomator-agents
- Template: agentic-rag-knowledge-graph

**Adapted for**: EVI 360 Workplace Safety RAG System
- Focus: Dutch workplace safety guidelines with 3-tier hierarchy
- Client: EVI 360 safety specialists
- Unique features: Tier-aware search, product recommendations, Notion integration

---

**Project Status**: Phase 1-2 Complete | Ready for Phase 3 | Infrastructure Solid | Tests Passing ✅
