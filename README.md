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
   # Check database connection
   PGPASSWORD=postgres psql -h localhost -U postgres -d evi_rag \
     -c "SELECT COUNT(*) FROM chunks;"
   # Should return: 10833

   # Test Dutch full-text search
   PGPASSWORD=postgres psql -h localhost -U postgres -d evi_rag \
     -c "SELECT COUNT(*) FROM chunks WHERE to_tsvector('dutch', content) @@ plainto_tsquery('dutch', 'werken hoogte');"
   # Should return: >0 (matches found)
   ```

---

## 🌐 Using OpenWebUI (Web Interface)

**OpenWebUI is the primary interface for the EVI 360 Specialist Agent** - it provides a ChatGPT-like web interface with conversation history, streaming responses, and clickable citations.

### Quick Start: OpenWebUI

**Prerequisites:** Initial setup complete (see [Installation](#installation) above)

#### 1. Start All Services

```bash
# Start Docker containers (PostgreSQL, Neo4j, OpenWebUI)
docker-compose up -d

# Verify all containers are healthy (should take 10-30 seconds)
docker-compose ps
# Expected: postgres (healthy), neo4j (healthy), openwebui (Up)
```

#### 2. Activate Python Environment

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

#### 3. Start the API Server

```bash
# Start FastAPI server on port 8058 (OpenWebUI expects it here)
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8058 (Press CTRL+C to quit)
INFO:     Started server process [12346]
INFO:     Application startup complete.
INFO:     Database initialized
INFO:     Agentic RAG API startup complete
```

#### 4. Open OpenWebUI

Open your web browser and navigate to:
```
http://localhost:3001
```

**You should see the "EVI 360 Specialist" chat interface.**

#### 5. Start Chatting

The system supports both **Dutch** and **English** queries automatically:

**Dutch Examples:**
- "Wat zijn de vereisten voor werken op hoogte?"
- "Hoe voorkom ik rugklachten bij werknemers?"
- "Welke maatregelen zijn nodig voor lawaai op de werkplek?"

**English Examples:**
- "What are the requirements for working at height?"
- "How do I prevent back injuries in employees?"
- "What measures are needed for workplace noise?"

**Features:**
- ✅ Real-time streaming responses
- ✅ Clickable citations (when guidelines have URLs)
- ✅ Automatic language detection (Dutch/English)
- ✅ Conversation history saved in OpenWebUI
- ✅ Markdown formatting with blockquotes for sources

### Shutdown

```bash
# Stop API server (in terminal where uvicorn is running)
Ctrl+C

# Stop Docker containers (keeps all data)
docker-compose down

# OR: Keep containers running in background (no action needed)
# Data persists in Docker volumes either way
```

**Note:** Docker volumes persist your data even when containers are stopped. To completely remove data, use `docker-compose down -v` (⚠️ WARNING: deletes everything).

### Troubleshooting

**Problem:** OpenWebUI shows "Connection Error" or "API not responding"

**Solution:**
1. Verify API server is running: `curl http://localhost:8058/health`
2. Check Docker containers: `docker-compose ps` (all should be healthy/Up)
3. Check API logs in terminal where uvicorn is running

**Problem:** Citations are not clickable

**Solution:**
- This is expected if documents don't have `source_url` in their metadata
- Re-ingest documents with URLs to enable clickable citations
- See [Notion Integration docs](docs/features/FEAT-002_notion-integration/) for ingestion

**Problem:** Port 3001 already in use

**Solution:**
- Change OpenWebUI port in `docker-compose.yml`: `"3002:8080"` instead of `"3001:8080"`
- Restart: `docker-compose down && docker-compose up -d`
- Access at new port: http://localhost:3002

---

## 🎨 Customizing the Agent Prompt

The agent's behavior is controlled by a system prompt that defines its personality, response format, and citation requirements.

### Prompt Location

**File:** `agent/specialist_agent.py`
**Variable:** `SPECIALIST_SYSTEM_PROMPT` (lines 34-89)

### How to Modify

1. **Open the file:**
   ```bash
   # With your preferred editor
   nano agent/specialist_agent.py
   # or
   code agent/specialist_agent.py
   ```

2. **Find the prompt:**
   ```python
   # Look for this line (around line 34)
   SPECIALIST_SYSTEM_PROMPT = """You are a workplace safety specialist for EVI 360.
   ```

3. **Edit the prompt:** Modify the text within the triple quotes to change:
   - Agent personality ("informal, friendly tone" → "professional, formal tone")
   - Response structure (add/remove sections)
   - Citation requirements (minimum sources, formatting)
   - Language instructions (Dutch/English behavior)

4. **Restart the API server:**
   ```bash
   # Stop current server (Ctrl+C)
   # Start again (changes auto-reload with --reload flag)
   python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload
   ```

   **Note:** With `--reload` flag, you can edit the prompt and it will auto-reload. Just save the file and the next query will use the new prompt.

### Example Modifications

**Change tone to formal:**
```python
# Find this line:
- Use informal, friendly tone

# Change to:
- Use professional, formal tone appropriate for safety compliance
```

**Require more citations:**
```python
# Find this line:
- Always cite at least 2 sources (NVAB, STECR, UWV, Arboportaal, ARBO)

# Change to:
- Always cite at least 3-4 sources (NVAB, STECR, UWV, Arboportaal, ARBO)
```

**Add a disclaimer:**
```python
# At the end of the prompt, before the closing triple quotes:
**Disclaimer:** Always consult a certified safety professional for workplace-specific advice.
"""
```

---

## 🖥️ Running the MVP (CLI Alternative)

### Start the API Server

```bash
# Ensure Docker containers are running
docker-compose ps  # Should show: postgres (healthy), neo4j (healthy)

# Activate virtual environment
source venv_linux/bin/activate  # Linux/Mac

# Start API server on port 8058 (configured in .env)
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8058 (Press CTRL+C to quit)
INFO:     Will watch for changes in these directories: ['/Users/builder/dev/evi_rag_test']
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Application startup complete.
INFO:     Database initialized
INFO:     Agentic RAG API startup complete
```

### Use the CLI

```bash
# In a new terminal, activate venv
source venv_linux/bin/activate

# Run CLI (connects to API on localhost:8058)
python3 cli.py
```

**Expected Output:**
```
============================================================
🤖 Agentic RAG with Knowledge Graph CLI
============================================================
Connected to: http://localhost:8058
Type 'exit', 'quit', or Ctrl+C to exit
Type 'help' for commands
============================================================

✓ API is healthy

Ready to chat! Ask questions in Dutch about workplace safety.

You:
```

### Test with Dutch Queries

Try these Dutch workplace safety questions:

```
You: Wat zijn de vereisten voor werken op hoogte?
# Expected: Dutch response with citations to NVAB/ARBO guidelines

You: Hoe voorkom ik rugklachten bij werknemers?
# Expected: Ergonomics and lifting guidelines with sources

You: Welke maatregelen zijn nodig voor lawaai op de werkplek?
# Expected: Noise regulations and hearing protection recommendations
```

### Check Health Status

```bash
# Test API health
curl http://localhost:8058/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "healthy",
#   "graph": "skipped_for_mvp",
#   "timestamp": "2025-10-26T18:30:45.123456"
# }
```

---

## 📊 Current Status

**Phase 1**: ✅ Complete (Core Infrastructure)
**Phase 2**: ✅ Complete (Notion Integration)
**Phase 3A**: ✅ Complete (Specialist Agent MVP)
**Phase 3E**: ✅ Complete (OpenWebUI Integration)

**Overall Progress:** 67% (4 of 9 phases complete)

See [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) for detailed progress tracking.

### What's Complete ✅

**Infrastructure**:
- ✅ PostgreSQL 17 + pgvector 0.8.1 (local, unlimited storage)
- ✅ Neo4j 5.26.1 (empty, for future knowledge graph)
- ✅ Docker Compose configuration with health checks
- ✅ FastAPI server with OpenAI-compatible API
- ✅ OpenWebUI web interface (port 3001)
- ✅ CLI client with streaming support
- ✅ Search tools (vector, hybrid) implemented

**Data**:
- ✅ 87 Dutch workplace safety guidelines ingested
- ✅ 10,833 chunks with embeddings generated
- ✅ Dutch full-text search enabled and tested

**Database Schema**:
- ✅ 5 tables: documents, chunks (with tier column), products, sessions, messages
- ✅ SQL functions: hybrid_search (Dutch), match_chunks, search_guidelines_by_tier
- ✅ Indexes: ivfflat on embeddings, GIN on metadata

**Agent & API**:
- ✅ Specialist Agent with language auto-detection (Dutch/English)
- ✅ Pydantic AI framework with tools and validators
- ✅ OpenAI-compatible `/v1/chat/completions` endpoint
- ✅ Streaming responses with Server-Sent Events (SSE)
- ✅ Clickable citations with source URLs
- ✅ Search tools (`agent/tools.py`) with hybrid search
- ✅ Database utils (`agent/db_utils.py`) with connection pooling
- ✅ 8 Pydantic models with validation

### What's Next ⏳

**Ready for Implementation:**

**Phase 3B: Product Catalog** ([FEAT-004](docs/features/FEAT-004_product-catalog/prd.md))
- Scrape ~100 EVI 360 products from website
- AI-assisted categorization with compliance tags
- Product recommendation integration with specialist agent

**Future Phases:**
- **Phase 3C:** Multi-Agent System (if performance issues emerge)
- **Phase 3D:** Knowledge Graph Enhancement (if relationship queries needed)
- **Phase 3F:** Advanced Memory & Session Management
- **Phase 3G:** Tier-Aware Search Strategy

---

## 🛠️ Tech Stack

### Core Technologies

- **Database**: PostgreSQL 17 + pgvector 0.8.1
- **Graph DB**: Neo4j 5.26.1 + APOC
- **Agent Framework**: Pydantic AI
- **API**: FastAPI with OpenAI-compatible endpoints
- **Web Interface**: OpenWebUI (ChatGPT-like UI)
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
