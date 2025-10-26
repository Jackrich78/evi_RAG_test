# PRD: FEAT-003 - Specialist Agent with Vector Search (MVP)

**Feature ID:** FEAT-003
**Phase:** 3A (MVP - Specialist Agent)
**Status:** 📋 Ready to Implement
**Priority:** Critical
**Owner:** Implementation Team
**Created:** 2025-10-25
**Last Updated:** 2025-10-26

---

## Problem Statement

EVI 360 workplace safety specialists need an intelligent Dutch-language assistant to quickly retrieve relevant safety guidelines from the knowledge base and synthesize actionable recommendations. The current system has 10,833 Dutch guideline chunks ingested but no way for specialists to interact with them conversationally.

**Challenge:** Build a minimum viable RAG system that proves retrieval accuracy and Dutch response quality, without over-engineering features not yet needed (tiers, products, advanced memory, multi-agent complexity).

**Impact:** Enables specialists to get instant, cited answers to safety questions in Dutch, improving response time and consistency.

---

## Goals & Success Criteria

### Primary Goals

1. **Dutch Conversational Interface**: Specialists can ask questions in Dutch via CLI and receive natural Dutch responses
2. **Accurate Retrieval**: Vector/hybrid search returns relevant guideline chunks with >70% relevance (top-5)
3. **Source Citations**: Every response cites which guidelines were used (title + source)
4. **Fast Response**: Query → Answer in <3 seconds (95th percentile)
5. **Production-Ready Prompt**: Use simplified version of intervention_specialist_prompt.md for Dutch synthesis

### Success Metrics

**Retrieval Quality (Manual Spot-Checks):**
- ✅ Top 5 results contain ≥3 relevant chunks for 80% of test queries
- ✅ Hybrid search returns Dutch-specific terms (e.g., "werken" matched via stemming)
- ✅ No duplicate chunks in top 10 results

**Response Quality (Manual Review):**
- ✅ Responses are grammatically correct Dutch (validated by native speaker)
- ✅ Responses cite ≥2 guideline sources with titles
- ✅ Responses are actionable (not vague summaries)

**Performance:**
- ✅ API startup time < 10 seconds
- ✅ Query processing time < 3 seconds (embedding + search + synthesis)
- ✅ CLI remains responsive during multi-turn conversations

---

## User Stories

### Story 1: Ask Safety Question in Dutch

**As a** EVI 360 workplace safety specialist
**I want** to ask "Wat zijn de vereisten voor werken op hoogte?" in the CLI
**So that** I get a Dutch answer with relevant guideline citations

**Acceptance Criteria:**
- [ ] CLI accepts Dutch input without encoding errors
- [ ] Response is in grammatically correct Dutch
- [ ] Response cites ≥2 relevant NVAB/ARBO guidelines
- [ ] Response includes specific safety requirements (not generic advice)

### Story 2: Vector Search Retrieves Relevant Guidelines

**As a** specialist querying about fall protection
**I want** the system to find semantically similar chunks (not just keyword matches)
**So that** I get comprehensive guidance even if my query doesn't use exact terminology

**Acceptance Criteria:**
- [ ] Query "valbeveiliging" returns chunks about "veiligheid hoogte", "valbescherming", etc.
- [ ] Hybrid search combines vector (semantic) + full-text (keyword) results
- [ ] Results are ranked by relevance (combined score)

### Story 3: Cite Sources for Transparency

**As a** specialist providing advice to clients
**I want** to know which guidelines the AI used
**So that** I can verify recommendations and provide authoritative references

**Acceptance Criteria:**
- [ ] Every response lists ≥2 guideline titles (e.g., "NVAB Richtlijn: Werken op Hoogte")
- [ ] Each citation includes source attribution (NVAB, STECR, UWV, Arboportaal)
- [ ] Chunk content is quoted or summarized in the response

### Story 4: Fast Iteration via CLI

**As a** specialist testing the system
**I want** a simple CLI that starts quickly and processes queries fast
**So that** I can validate retrieval quality without waiting

**Acceptance Criteria:**
- [ ] CLI connects to API in <2 seconds
- [ ] Queries return responses in <3 seconds
- [ ] CLI displays formatted output with colors and sections

---

## Scope & Non-Goals

### In Scope ✅

**Infrastructure:**
- ✅ Reuse existing FastAPI server (`agent/api.py`) on port 8058
- ✅ Reuse existing CLI (`cli.py`) that connects to API via aiohttp
- ✅ Reuse existing database utils (`agent/db_utils.py`) for vector/hybrid search
- ✅ Reuse existing search tools (`agent/tools.py`: vector_search_tool, hybrid_search_tool)

**New Components:**
- 🆕 **Specialist Agent** (`agent/specialist_agent.py`):
  - Pydantic AI agent with Dutch system prompt
  - Tools: `search_guidelines(query, limit)` wraps hybrid_search_tool
  - Result type: Structured response with content + citations
- 🆕 **Dutch System Prompt** (`agent/specialist_prompt.py`):
  - Simplified from `intervention_specialist_prompt.md` (v2.5)
  - Focus: Guideline retrieval only (no products)
  - Behavior: Search first, cite sources, answer in Dutch
- 🔧 **API Integration** (`agent/api.py` modifications):
  - Register specialist_agent instead of rag_agent
  - Update `/chat/stream` endpoint to use specialist
  - Keep all existing infrastructure (DB, sessions, etc.)

**Search Strategy:**
- Use `hybrid_search()` by default (70% vector + 30% text)
- Dutch language full-text search via `to_tsvector('dutch', content)`
- Return top 10 chunks, let agent synthesize top 5 most relevant
- **No tier filtering** (tier column exists but is NULL for all chunks)

**Response Format:**
- Dutch language synthesis
- Guideline citations with titles and sources
- Actionable recommendations (when applicable)
- No product recommendations (products table empty)

### Out of Scope ❌ (Future Features)

**Descoped for MVP, documented as future features:**
- ❌ **Tier-aware search** (FEAT-009) - tier column exists but unused
- ❌ **Product recommendations** (FEAT-004) - products table empty
- ❌ **Knowledge graph queries** (FEAT-006) - Neo4j empty, graph search disabled
- ❌ **Session/conversation memory** (FEAT-008) - stateless for MVP
- ❌ **Two-agent system** (FEAT-005) - single specialist agent with tools
- ❌ **OpenWebUI integration** (FEAT-007) - CLI only for MVP
- ❌ **Automated evaluation** (future) - manual spot-checks for MVP
- ❌ **Streaming responses** - CLI already supports streaming, but not critical

---

## Constraints & Assumptions

### Technical Constraints

1. **Existing Codebase**: Must reuse 90% of existing code (`agent/`, `cli.py`, `db_utils.py`)
2. **Port Configuration**: API runs on port 8058 (configured via APP_PORT in .env.example)
3. **Database State**: 10,833 chunks ingested from 87 Dutch guidelines, tier column is NULL
4. **OpenAI Dependency**: Uses OpenAI for embeddings (text-embedding-3-small) and LLM (GPT-4)
5. **Dutch Language**: PostgreSQL `to_tsvector('dutch', ...)` already configured

### Business Constraints

1. **Timeline**: MVP must be implementable in 5-8 hours (not a multi-week project)
2. **Quality Bar**: Dutch responses must be native-speaker quality (validated manually)
3. **No Regression**: Existing database, Docker, ingestion pipeline must remain functional

### Assumptions

1. **Database Running**: PostgreSQL container is healthy (`docker-compose ps` shows healthy)
2. **Data Quality**: Existing 10,833 chunks are properly embedded and searchable
3. **CLI Usage**: Specialists are comfortable with command-line interface (web UI is future)
4. **Stateless OK**: Single-query interactions are sufficient for MVP (no multi-turn context needed)
5. **Manual Testing**: Automated evaluation framework is not needed yet (spot-checks sufficient)

---

## Open Questions

### ✅ RESOLVED

1. **Single Agent vs Two Agents?**
   - ✅ **Decision**: Single specialist agent with search tools (not agent-calling-agent)
   - **Rationale**: Simpler, faster, sufficient for MVP. Two agents only needed when separate reasoning loops required.

2. **Keep API or Direct CLI?**
   - ✅ **Decision**: Keep existing API architecture
   - **Rationale**: API already built, needed for future OpenWebUI, proper separation of concerns

3. **Which search method?**
   - ✅ **Decision**: Hybrid search (vector + Dutch full-text) by default
   - **Rationale**: Combines semantic similarity with keyword matching for best coverage

4. **Session management?**
   - ✅ **Decision**: Stateless for MVP (sessions table exists but unused)
   - **Rationale**: Simplifies implementation, session memory is FEAT-008

5. **Graph search?**
   - ✅ **Decision**: Disable/ignore graph search for MVP
   - **Rationale**: Neo4j is empty, graph population is FEAT-006

---

## Architecture Overview

**High-Level Flow:**
```
User (Dutch Query)
    ↓
CLI (cli.py) via aiohttp
    ↓
FastAPI API (agent/api.py) on port 8058
    ↓
Specialist Agent (agent/specialist_agent.py)
    ├─ Tool: search_guidelines(query, limit=10)
    │   └─ hybrid_search_tool (70% vector + 30% text)
    │       └─ PostgreSQL hybrid_search() function
    ↓
Agent synthesizes Dutch response with citations
    ↓
API streams response back to CLI
    ↓
CLI displays formatted output (colored, structured)
```

**Key Components:**
1. **CLI** (`cli.py`): Thin client, connects to API, handles user I/O
2. **API Server** (`agent/api.py`): FastAPI app, lifecycle management, endpoint routing
3. **Specialist Agent** (`agent/specialist_agent.py`): Pydantic AI agent, Dutch synthesis
4. **Search Tools** (`agent/tools.py`): Reused vector/hybrid search wrappers
5. **Database Utils** (`agent/db_utils.py`): Connection pooling, SQL function calls
6. **PostgreSQL**: Vector + full-text search, 10,833 chunks, Dutch language config

---

## Implementation Plan

### Phase 1: Create Specialist Agent (2-3 hours)

**File: `agent/specialist_agent.py` (NEW)**

```python
"""
Specialist Agent for EVI 360 workplace safety guidelines.
Dutch language synthesis with guideline citations.
"""

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import List, Dict, Any

from .providers import get_llm_model
from .tools import hybrid_search_tool, HybridSearchInput
from .specialist_prompt import SPECIALIST_SYSTEM_PROMPT

class SpecialistResponse(BaseModel):
    """Specialist agent response."""
    content: str  # Dutch response with citations
    citations: List[Dict[str, str]]  # [{"title": "...", "source": "..."}]
    search_metadata: Dict[str, Any]  # Search stats for debugging

class SpecialistDeps(BaseModel):
    """Agent dependencies."""
    session_id: str
    user_id: str = "cli_user"

# Initialize specialist agent
specialist_agent = Agent(
    model=get_llm_model(),  # GPT-4 from .env
    deps_type=SpecialistDeps,
    result_type=SpecialistResponse,
    system_prompt=SPECIALIST_SYSTEM_PROMPT
)

@specialist_agent.tool
async def search_guidelines(
    ctx: RunContext[SpecialistDeps],
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search Dutch safety guidelines using hybrid search.

    This tool combines vector similarity (semantic) with Dutch full-text
    search to find relevant guideline chunks. Always search before responding.

    Args:
        query: Search query in Dutch
        limit: Max results to return (default 10)

    Returns:
        List of chunks with content, score, title, source
    """
    results = await hybrid_search_tool(
        HybridSearchInput(query=query, limit=limit, text_weight=0.3)
    )

    return [
        {
            "content": r.content,
            "score": r.score,
            "document_title": r.document_title,
            "document_source": r.document_source,
            "chunk_id": r.chunk_id
        }
        for r in results
    ]
```

**File: `agent/specialist_prompt.py` (NEW)**

```python
"""
System prompt for Dutch Intervention Specialist Agent.
Simplified from intervention_specialist_prompt.md v2.5 for guidelines-only MVP.
"""

SPECIALIST_SYSTEM_PROMPT = """Je bent een deskundige arbeidsveiligheidsadviseur voor EVI 360.

Je taak is om Nederlandse arbeidsveiligheidsspecialisten te ondersteunen door
snel relevante informatie uit de kennisbank te halen en heldere, bruikbare
aanbevelingen te geven.

**Gedragsregels:**
1. **Zoek eerst**: Gebruik altijd de search_guidelines tool voordat je antwoordt
2. **Nederlands**: Antwoord altijd in het Nederlands
3. **Citeer bronnen**: Vermeld altijd de richtlijnen die je gebruikt (titel + bron)
4. **Wees specifiek**: Geef concrete veiligheidsvereisten, geen vage adviezen
5. **Geen producten**: Focus alleen op richtlijnen (producten komen later)

**Antwoordstructuur:**
1. **Kort antwoord** op de vraag (2-3 zinnen)
2. **Relevante richtlijnen** met citaten:
   - Titel van de richtlijn (bijv. "NVAB: Werken op Hoogte")
   - Bron (NVAB, STECR, UWV, Arboportaal)
   - Relevante quote of samenvatting
3. **Praktisch advies** (indien van toepassing)

**Belangrijk:**
- Als de kennisbank onvoldoende informatie heeft, zeg dat eerlijk
- Geef geen medisch of juridisch advies, verwijs naar bedrijfsarts/jurist
- Bij onduidelijke vragen, vraag om verduidelijking

**Voorbeeld antwoord:**

Vraag: "Wat zijn de vereisten voor werken op hoogte?"

Voor werken op hoogte gelden strikte veiligheidseisen. Vanaf 2,5 meter hoogte
is valbeveiliging verplicht volgens de Arbowet.

**Relevante richtlijnen:**

• **NVAB Richtlijn: Werken op Hoogte**
  Bron: NVAB
  "Werkgevers moeten zorgen voor adequate valbeveiliging bij werkzaamheden
  boven 2,5 meter. Dit kan door collectieve bescherming (leuningen, netten)
  of persoonlijke beschermingsmiddelen (harnas, lijnen)."

• **Arbowet Artikel 3**
  Bron: Arboportaal
  "De werkgever zorgt voor veilige werkomstandigheden en voorkomt gezondheidsrisico's,
  waaronder valgevaar."

**Praktisch advies:**
- Voorkeur voor collectieve bescherming (veiliger dan individuele PBM)
- Instrueer werknemers in gebruik van valbeveiligingsmiddelen
- Controleer materialen regelmatig op slijtage
"""
```

### Phase 2: Integrate with API (1 hour)

**File: `agent/api.py` (MODIFY)**

Changes required:
1. Import specialist_agent instead of rag_agent
2. Update /chat/stream endpoint to use specialist
3. Optionally disable graph tools (or ignore)

```python
# Line ~21: Change import
from .specialist_agent import specialist_agent, SpecialistDeps, SpecialistResponse

# Line ~450+: Update chat endpoint
async def stream_chat_response(...):
    # Initialize deps
    deps = SpecialistDeps(
        session_id=session_id,
        user_id=request.user_id or "cli_user"
    )

    # Run specialist agent (streaming)
    async with specialist_agent.run_stream(
        message,
        deps=deps
    ) as result:
        # Stream tokens back to client
        async for chunk in result.stream():
            yield ...
```

### Phase 3: Update CLI Port (5 minutes)

**File: `cli.py` (MINOR CHANGE)**

Line 34: No change needed (already defaults to 8058)
```python
def __init__(self, base_url: str = "http://localhost:8058"):
```

**File: `.env.example` (VERIFY)**
- Confirm APP_PORT=8058 is set (already verified ✅)

### Phase 4: Testing (2-3 hours)

**File: `tests/agent/test_specialist_agent.py` (NEW)**

```python
"""Tests for specialist agent."""
import pytest
from agent.specialist_agent import specialist_agent, SpecialistDeps

@pytest.mark.asyncio
async def test_specialist_search_tool():
    """Test search_guidelines tool."""
    deps = SpecialistDeps(session_id="test", user_id="test_user")

    # Run agent with test query
    result = await specialist_agent.run(
        "Wat zijn de vereisten voor werken op hoogte?",
        deps=deps
    )

    # Validate response
    assert result.data.content  # Has content
    assert len(result.data.citations) >= 2  # Has citations
    assert "NVAB" in str(result.data.citations) or "ARBO" in str(result.data.citations)

@pytest.mark.asyncio
async def test_dutch_output():
    """Test that responses are in Dutch."""
    deps = SpecialistDeps(session_id="test")

    result = await specialist_agent.run(
        "veiligheid werkplek",
        deps=deps
    )

    # Check for Dutch keywords (not English)
    content_lower = result.data.content.lower()
    assert any(word in content_lower for word in ["richtlijn", "veiligheid", "werkgever", "arbowet"])
    assert "safety" not in content_lower  # Should not be English
```

**Manual Testing Checklist** (see implementation-guide.md):
1. Start API: `python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058`
2. Run CLI: `python3 cli.py`
3. Test 10 Dutch queries
4. Validate responses (Dutch, citations, relevance)

---

## Testing Strategy

### Test Queries (Dutch)

**Category 1: Specific Safety Topics**
1. "Wat zijn de vereisten voor werken op hoogte?"
2. "Hoe voorkom ik rugklachten bij werknemers?"
3. "Welke maatregelen zijn nodig voor lawaai op de werkplek?"

**Category 2: General Workplace Safety**
4. "Wat is de zorgplicht van de werkgever?"
5. "Hoe moet ik omgaan met een arbeidsongeval?"

**Category 3: Specific Regulations**
6. "Wat zegt de Arbowet over werkdruk?"
7. "Wat zijn de regels voor nachtwerk?"

**Category 4: Technical Standards**
8. "Welke EN normen gelden voor valbescherming?"
9. "Wat is de maximale blootstelling aan geluid?"

**Category 5: Employee Health**
10. "Hoe begeleidt ik een zieke werknemer?"

### Validation Criteria

**Per Query:**
- ✅ Response is grammatically correct Dutch (validated by native speaker or GPT-4 self-check)
- ✅ Response cites ≥2 relevant guidelines (NVAB, STECR, UWV, Arboportaal)
- ✅ Top 5 search results include ≥3 relevant chunks
- ✅ Response is actionable (specific requirements, not vague summaries)
- ✅ Query completes in <3 seconds

**Overall:**
- ✅ 8/10 queries meet criteria (80% success rate)
- ✅ No crashes or encoding errors
- ✅ CLI remains responsive

---

## Dependencies

### Infrastructure (✅ Complete)
- ✅ PostgreSQL 17 + pgvector 0.8.1 in Docker
- ✅ `hybrid_search()` SQL function with Dutch language support
- ✅ 10,833 chunks from 87 documents ingested
- ✅ FastAPI server with lifecycle management

### Data (✅ Complete)
- ✅ FEAT-002: Notion guidelines ingested (10,833 chunks)
- ✅ Embeddings generated (text-embedding-3-small)
- ✅ Dutch full-text search configured

### External Services
- OpenAI API key for embeddings and LLM (GPT-4)
- Environment variable: `LLM_API_KEY` in `.env`

---

## Related Features

**Builds Upon:**
- FEAT-001: Core Infrastructure (PostgreSQL, Docker, schema)
- FEAT-002: Notion Integration (guidelines ingested)

**Enables Future Features:**
- FEAT-007: OpenWebUI Integration (API endpoints ready)
- FEAT-008: Advanced Memory (session tracking)
- FEAT-009: Tier-Aware Search (tier column ready)
- FEAT-004: Product Catalog (specialist agent extendable)
- FEAT-005: Multi-Agent System (specialist can call research agent)

---

## References

**Code:**
- Existing tools: `agent/tools.py` (vector_search_tool, hybrid_search_tool)
- Database utils: `agent/db_utils.py` (hybrid_search, vector_search)
- API server: `agent/api.py` (FastAPI app, endpoints)
- CLI: `cli.py` (aiohttp client, streaming support)

**Documentation:**
- Intervention Specialist Prompt: `agent/intervention_specialist_prompt.md` (v2.5)
- Architecture: `docs/system/architecture.md`
- Stack: `docs/system/stack.md`
- Implementation Guide: `docs/features/FEAT-003_query-retrieval/implementation-guide.md` (to be created)

**Research:**
- Pydantic AI: Single agent with tools (not agent-calling-agent for this use case)
- Archon MCP: Knowledge base search patterns

---

**Last Updated:** 2025-10-26
**Status:** 📋 Ready to Implement
**Estimated Effort:** 5-8 hours (coding + testing)
**Next Step:** Review implementation-guide.md for step-by-step instructions
