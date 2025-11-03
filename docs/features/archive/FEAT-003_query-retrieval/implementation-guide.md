# Implementation Guide: FEAT-003 - Specialist Agent with Vector Search

**Feature ID:** FEAT-003
**Last Updated:** 2025-10-26
**Estimated Effort:** 5-8 hours (coding + testing)

---

## Overview

This guide provides step-by-step instructions for implementing the EVI 360 Specialist Agent MVP. By following this guide, you will:

1. Create the Specialist Agent with Dutch system prompt
2. Integrate it with the existing API server
3. Test the complete flow from CLI → API → Agent → Database
4. Validate Dutch response quality and citation accuracy

**Prerequisites:**
- Read [prd.md](./prd.md) and [architecture.md](./architecture.md) first
- PostgreSQL container running with 10,833 chunks ingested
- OpenAI API key configured in `.env`
- Python 3.11+ with all dependencies installed

---

## Phase 1: Create Specialist Agent (2-3 hours)

### Step 1.1: Create Specialist Prompt File

**File:** `agent/specialist_prompt.py` (NEW)

**Purpose:** Simplified Dutch system prompt for guidelines-only MVP (no products, no tiers).

**Action:** Create new file with the following content:

```python
"""
System prompt for Dutch Intervention Specialist Agent.
Simplified from intervention_specialist_prompt.md v2.5 for guidelines-only MVP.

Changes from full prompt:
- Removed product recommendation protocol
- Removed tier-aware search strategy
- Removed kb_reference_protocol (portal.evi360.nl integration)
- Simplified to focus on guideline search and Dutch synthesis
- Kept citation requirements and formatting standards
"""

SPECIALIST_SYSTEM_PROMPT = """Je bent een deskundige arbeidsveiligheidsadviseur voor EVI 360.

Je taak is om Nederlandse arbeidsveiligheidsspecialisten te ondersteunen door
snel relevante informatie uit de kennisbank te halen en heldere, bruikbare
aanbevelingen te geven.

**Gedragsregels:**
1. **Zoek eerst**: Gebruik altijd de search_guidelines tool voordat je antwoordt
2. **Nederlands**: Antwoord altijd in het Nederlands, tenzij expliciet om Engels gevraagd wordt
3. **Citeer bronnen**: Vermeld altijd de richtlijnen die je gebruikt (titel + bron)
4. **Wees specifiek**: Geef concrete veiligheidsvereisten, geen vage adviezen
5. **Geen producten**: Focus alleen op richtlijnen (productaanbevelingen komen later)
6. **Geen tiers**: Zoek door alle richtlijnen heen (tier-filtering komt later)

**Antwoordstructuur:**
1. **Kort antwoord** op de vraag (2-3 zinnen)
2. **Relevante richtlijnen** met citaten:
   - Titel van de richtlijn (bijv. "NVAB Richtlijn: Werken op Hoogte")
   - Bron (NVAB, STECR, UWV, Arboportaal)
   - Relevante quote of samenvatting uit de gevonden chunk
3. **Praktisch advies** (indien van toepassing en gebaseerd op de richtlijnen)

**Belangrijk:**
- Als de kennisbank onvoldoende informatie heeft, zeg dat eerlijk
- Geef geen medisch of juridisch advies, verwijs naar bedrijfsarts/jurist
- Bij onduidelijke vragen, vraag om verduidelijking
- Gebruik informele taal ("je"/"jij", niet "u")
- Citeer minimaal 2 relevante richtlijnen als die beschikbaar zijn

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

**Tool Usage:**
- Je hebt toegang tot de tool `search_guidelines(query, limit)`
- Gebruik deze tool voor ELKE vraag om relevante chunks op te halen
- De tool gebruikt hybrid search (vector + Dutch full-text)
- Standaard limit is 10 chunks, pas aan als meer context nodig is
"""
```

**Validation:**
- [ ] File saved at `agent/specialist_prompt.py`
- [ ] Prompt is in Dutch
- [ ] Prompt explicitly mentions search_guidelines tool
- [ ] Prompt includes example output format

---

### Step 1.2: Create Specialist Agent File

**File:** `agent/specialist_agent.py` (NEW)

**Purpose:** Pydantic AI agent that wraps search tools and synthesizes Dutch responses.

**Action:** Create new file with the following content:

```python
"""
Specialist Agent for EVI 360 workplace safety guidelines.

This agent provides Dutch language synthesis of workplace safety guidelines
with proper citations. It uses hybrid search (vector + Dutch full-text) to
retrieve relevant chunks and formats responses according to the specialist
system prompt.

Architecture:
- Model: GPT-4 (from .env LLM_API_KEY)
- Tools: search_guidelines (wraps hybrid_search_tool)
- Result: SpecialistResponse (content + citations + metadata)
- Dependencies: SpecialistDeps (session_id, user_id)

Usage:
    from agent.specialist_agent import specialist_agent, SpecialistDeps

    deps = SpecialistDeps(session_id="123", user_id="user1")
    result = await specialist_agent.run("Wat zijn de vereisten voor werken op hoogte?", deps=deps)

    print(result.data.content)  # Dutch response
    print(result.data.citations)  # List of guideline citations
"""

import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext

from .providers import get_llm_model
from .tools import hybrid_search_tool, HybridSearchInput
from .specialist_prompt import SPECIALIST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


# Pydantic Models

class Citation(BaseModel):
    """Citation for a guideline source."""
    title: str = Field(..., description="Title of the guideline document")
    source: str = Field(..., description="Source organization (NVAB, STECR, UWV, Arboportaal)")
    quote: str = Field(default="", description="Relevant quote from the guideline")


class SpecialistResponse(BaseModel):
    """Structured response from the specialist agent."""
    content: str = Field(..., description="Dutch language response with citations")
    citations: List[Citation] = Field(default_factory=list, description="List of guideline citations")
    search_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about search (chunks_retrieved, search_time, etc.)"
    )


class SpecialistDeps(BaseModel):
    """Dependencies injected into the specialist agent."""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(default="cli_user", description="User identifier")


# Initialize Specialist Agent

specialist_agent = Agent(
    model=get_llm_model(),  # GPT-4 from .env
    deps_type=SpecialistDeps,
    result_type=SpecialistResponse,
    system_prompt=SPECIALIST_SYSTEM_PROMPT
)


# Agent Tools

@specialist_agent.tool
async def search_guidelines(
    ctx: RunContext[SpecialistDeps],
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search Dutch safety guidelines using hybrid search.

    This tool combines vector similarity (semantic) with Dutch full-text
    search to find relevant guideline chunks. It should be called for every
    user query to retrieve context before generating a response.

    The tool uses the hybrid_search SQL function which:
    - Generates embeddings via OpenAI (text-embedding-3-small)
    - Performs vector similarity search (cosine distance)
    - Performs Dutch full-text search (to_tsvector('dutch', ...))
    - Ranks results by combined score (70% vector, 30% text)

    Args:
        ctx: Agent context (contains session_id, user_id)
        query: Search query in Dutch (e.g., "werken op hoogte")
        limit: Maximum number of chunks to return (default: 10, max: 50)

    Returns:
        List of dictionaries, each containing:
        - content: Full text of the guideline chunk
        - score: Combined relevance score (0.0-1.0)
        - document_title: Title of the source guideline document
        - document_source: Source organization (NVAB, STECR, etc.)
        - chunk_id: UUID of the chunk (for debugging)

    Example:
        results = await search_guidelines(ctx, "valbeveiliging", limit=10)
        # Returns top 10 chunks about fall protection
    """
    logger.info(
        f"[Session {ctx.deps.session_id}] Searching guidelines: query='{query}', limit={limit}"
    )

    try:
        # Call hybrid search tool
        search_results = await hybrid_search_tool(
            HybridSearchInput(
                query=query,
                limit=limit,
                text_weight=0.3  # 70% vector, 30% Dutch full-text
            )
        )

        # Format results for agent
        formatted_results = [
            {
                "content": r.content,
                "score": r.score,
                "document_title": r.document_title,
                "document_source": r.document_source,
                "chunk_id": str(r.chunk_id),
                "metadata": r.metadata  # Contains additional info (page numbers, etc.)
            }
            for r in search_results
        ]

        logger.info(
            f"[Session {ctx.deps.session_id}] Retrieved {len(formatted_results)} chunks "
            f"(top score: {formatted_results[0]['score']:.3f if formatted_results else 0})"
        )

        return formatted_results

    except Exception as e:
        logger.error(
            f"[Session {ctx.deps.session_id}] Search failed: {e}",
            exc_info=True
        )
        # Return empty list so agent can respond with "no results found"
        return []


# Utility Functions

async def run_specialist_query(query: str, session_id: str, user_id: str = "cli_user") -> SpecialistResponse:
    """
    Convenience function to run a single query through the specialist agent.

    Args:
        query: Dutch language query
        session_id: Session identifier
        user_id: User identifier (default: "cli_user")

    Returns:
        SpecialistResponse with content, citations, and metadata

    Example:
        response = await run_specialist_query(
            "Wat zijn de vereisten voor werken op hoogte?",
            session_id="test-123"
        )
        print(response.content)
    """
    deps = SpecialistDeps(session_id=session_id, user_id=user_id)

    result = await specialist_agent.run(query, deps=deps)

    return result.data


async def run_specialist_query_stream(query: str, session_id: str, user_id: str = "cli_user"):
    """
    Stream specialist agent responses token-by-token.

    Args:
        query: Dutch language query
        session_id: Session identifier
        user_id: User identifier

    Yields:
        Response chunks as they are generated

    Example:
        async with run_specialist_query_stream("werken op hoogte", "test") as stream:
            async for chunk in stream:
                print(chunk, end="", flush=True)
    """
    deps = SpecialistDeps(session_id=session_id, user_id=user_id)

    async with specialist_agent.run_stream(query, deps=deps) as result:
        yield result
```

**Validation:**
- [ ] File saved at `agent/specialist_agent.py`
- [ ] Imports are correct (pydantic_ai, tools, providers)
- [ ] Tool decorator uses `@specialist_agent.tool`
- [ ] search_guidelines tool wraps hybrid_search_tool
- [ ] SpecialistResponse includes content, citations, metadata
- [ ] Logging statements use session_id for traceability

---

### Step 1.3: Test Specialist Agent in Isolation

**Purpose:** Verify agent works before integrating with API.

**File:** `tests/agent/test_specialist_agent.py` (NEW)

**Action:** Create test file:

```python
"""
Unit tests for specialist agent.

Run with: pytest tests/agent/test_specialist_agent.py -v
"""

import pytest
import asyncio
from agent.specialist_agent import specialist_agent, SpecialistDeps, run_specialist_query


@pytest.mark.asyncio
async def test_specialist_agent_basic():
    """Test basic agent query with Dutch response."""
    deps = SpecialistDeps(session_id="test-001", user_id="test_user")

    result = await specialist_agent.run(
        "Wat zijn de vereisten voor werken op hoogte?",
        deps=deps
    )

    # Validate response structure
    assert result.data.content, "Response should have content"
    assert isinstance(result.data.content, str), "Content should be string"
    assert len(result.data.content) > 50, "Content should be substantial"

    # Validate Dutch output (basic check)
    content_lower = result.data.content.lower()
    dutch_keywords = ["werken", "hoogte", "veiligheid", "richtlijn", "werkgever"]
    assert any(keyword in content_lower for keyword in dutch_keywords), \
        "Response should contain Dutch keywords"

    # Validate citations (should have at least 1)
    assert len(result.data.citations) >= 1, "Should have at least 1 citation"

    # Validate citation structure
    if result.data.citations:
        first_citation = result.data.citations[0]
        assert first_citation.title, "Citation should have title"
        assert first_citation.source, "Citation should have source"


@pytest.mark.asyncio
async def test_specialist_agent_citations():
    """Test that agent provides proper guideline citations."""
    deps = SpecialistDeps(session_id="test-002")

    result = await specialist_agent.run(
        "Hoe voorkom ik rugklachten bij werknemers?",
        deps=deps
    )

    # Validate citations
    assert len(result.data.citations) >= 2, "Should cite multiple guidelines"

    # Check citation sources are valid
    valid_sources = ["NVAB", "STECR", "UWV", "Arboportaal", "ARBO"]
    for citation in result.data.citations:
        assert any(source in citation.source for source in valid_sources), \
            f"Citation source '{citation.source}' should be from known sources"


@pytest.mark.asyncio
async def test_specialist_agent_search_metadata():
    """Test that search metadata is populated."""
    deps = SpecialistDeps(session_id="test-003")

    result = await specialist_agent.run(
        "geluidsniveau werkplek",
        deps=deps
    )

    # Validate metadata exists
    assert result.data.search_metadata, "Should have search metadata"

    # Metadata should be a dict
    assert isinstance(result.data.search_metadata, dict), \
        "Metadata should be dictionary"


@pytest.mark.asyncio
async def test_run_specialist_query_convenience():
    """Test convenience function for single query."""
    response = await run_specialist_query(
        query="veiligheid werkplek",
        session_id="test-004",
        user_id="test_user"
    )

    assert response.content, "Convenience function should return content"
    assert isinstance(response.citations, list), "Should have citations list"


@pytest.mark.asyncio
async def test_specialist_agent_no_english():
    """Test that responses are NOT in English."""
    deps = SpecialistDeps(session_id="test-005")

    result = await specialist_agent.run(
        "werken op hoogte vereisten",
        deps=deps
    )

    content_lower = result.data.content.lower()

    # Should NOT contain English words (basic check)
    english_words = ["safety", "requirements", "height", "employer", "employee"]
    english_found = [word for word in english_words if word in content_lower]

    assert not english_found, \
        f"Response should not contain English words: {english_found}"


@pytest.mark.asyncio
async def test_specialist_agent_empty_query():
    """Test agent handles empty/nonsense query gracefully."""
    deps = SpecialistDeps(session_id="test-006")

    result = await specialist_agent.run(
        "xyzabc123 qwerty",  # Nonsense query
        deps=deps
    )

    # Agent should respond (even if no results)
    assert result.data.content, "Agent should respond even with no results"

    # Response should acknowledge lack of results
    content_lower = result.data.content.lower()
    acknowledgments = ["geen", "niet gevonden", "onvoldoende", "kan niet"]
    assert any(ack in content_lower for ack in acknowledgments), \
        "Agent should acknowledge when no results found"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
```

**Run Tests:**
```bash
# Activate venv
source venv_linux/bin/activate

# Ensure database is running
docker-compose ps  # Should show postgres as healthy

# Run tests
pytest tests/agent/test_specialist_agent.py -v
```

**Expected Output:**
```
tests/agent/test_specialist_agent.py::test_specialist_agent_basic PASSED
tests/agent/test_specialist_agent.py::test_specialist_agent_citations PASSED
tests/agent/test_specialist_agent.py::test_specialist_agent_search_metadata PASSED
tests/agent/test_specialist_agent.py::test_run_specialist_query_convenience PASSED
tests/agent/test_specialist_agent.py::test_specialist_agent_no_english PASSED
tests/agent/test_specialist_agent.py::test_specialist_agent_empty_query PASSED

============================== 6 passed in 45.23s ===============================
```

**Validation:**
- [ ] All 6 tests pass
- [ ] Responses are in Dutch
- [ ] Citations include NVAB/STECR/UWV/Arboportaal
- [ ] No crashes or exceptions

---

## Phase 2: Integrate with API Server (1 hour)

### Step 2.1: Modify API Server to Use Specialist Agent

**File:** `agent/api.py` (MODIFY)

**Changes Required:**

**Change 1: Update Imports (Line ~21)**

Replace:
```python
from .agent import rag_agent, AgentDependencies
```

With:
```python
# OLD: from .agent import rag_agent, AgentDependencies
from .specialist_agent import specialist_agent, SpecialistDeps, SpecialistResponse
```

**Change 2: Update Chat Endpoint (Line ~220-300, exact location varies)**

Find the `/chat/stream` endpoint function. It currently uses `rag_agent`.

Replace the agent initialization and streaming logic with:

```python
@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    """
    Streaming chat endpoint using specialist agent.

    Accepts Dutch language queries and streams back Dutch responses
    with guideline citations.
    """
    try:
        # Generate session ID if not provided (stateless for MVP)
        session_id = request.session_id or str(uuid.uuid4())

        # Initialize specialist agent dependencies
        deps = SpecialistDeps(
            session_id=session_id,
            user_id=request.user_id or "cli_user"
        )

        logger.info(
            f"[Session {session_id}] Chat request: {request.message[:100]}..."
        )

        async def generate_stream():
            """Generator for SSE streaming."""
            try:
                # Send session ID first
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

                # Run specialist agent with streaming
                async with specialist_agent.run_stream(
                    request.message,
                    deps=deps
                ) as result:
                    # Stream response tokens
                    async for chunk in result.stream():
                        yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

                    # Get final result with citations
                    final_result = await result.get_data()

                    # Send citations
                    if final_result.citations:
                        yield f"data: {json.dumps({
                            'type': 'citations',
                            'citations': [c.dict() for c in final_result.citations]
                        })}\n\n"

                    # Send metadata
                    if final_result.search_metadata:
                        yield f"data: {json.dumps({
                            'type': 'metadata',
                            'metadata': final_result.search_metadata
                        })}\n\n"

                    # Send end marker
                    yield f"data: {json.dumps({'type': 'end'})}\n\n"

            except Exception as e:
                logger.error(f"[Session {session_id}] Stream error: {e}", exc_info=True)
                yield f"data: {json.dumps({
                    'type': 'error',
                    'content': f'Er is een fout opgetreden: {str(e)}'
                })}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Change 3: Update Health Check (Optional, Line ~150-180)**

Find the `/health` endpoint. Optionally update it to skip graph check:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        db_healthy = await test_connection()

        # Skip graph check for MVP (Neo4j is empty)
        # graph_healthy = await test_graph_connection()
        graph_healthy = True  # Assume healthy for MVP

        status = "healthy" if (db_healthy and graph_healthy) else "degraded"

        return {
            "status": status,
            "database": "healthy" if db_healthy else "unhealthy",
            "graph": "skipped_for_mvp",  # Neo4j not used yet
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

**Validation:**
- [ ] Imports changed to specialist_agent
- [ ] Chat endpoint uses SpecialistDeps
- [ ] Stream properly yields SSE format
- [ ] Citations are sent after content
- [ ] Health check updated (or left as-is if graph check doesn't fail)

---

### Step 2.2: Start API Server and Test

**Start API Server:**
```bash
# Activate venv
source venv_linux/bin/activate

# Ensure .env has APP_PORT=8058
grep APP_PORT .env  # Should show: APP_PORT=8058

# Start server
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/Users/builder/dev/evi_rag_test']
INFO:     Uvicorn running on http://0.0.0.0:8058 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Starting up agentic RAG API...
INFO:     Database initialized
INFO:     Graph database initialized  # Or skipped
INFO:     Agentic RAG API startup complete
INFO:     Application startup complete.
```

**Test Health Endpoint:**
```bash
curl http://localhost:8058/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "graph": "skipped_for_mvp",
  "timestamp": "2025-10-26T18:30:45.123456"
}
```

**Validation:**
- [ ] API starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] Database shows as healthy
- [ ] No import errors or missing modules

---

## Phase 3: Test Complete Flow (2-3 hours)

### Step 3.1: Test CLI Connection

**Start CLI (in new terminal):**
```bash
# Activate venv
source venv_linux/bin/activate

# Run CLI
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

Ready to chat! Ask me about tech companies and AI initiatives.

You:
```

**Note:** The "tech companies" message is from the old prompt. After typing a query, you should get Dutch safety responses (not tech responses).

**Validation:**
- [ ] CLI connects without errors
- [ ] Health check passes (green checkmark)
- [ ] Prompt appears and accepts input

---

### Step 3.2: Run Test Queries

**Test Query 1: Basic Safety Question**

```
You: Wat zijn de vereisten voor werken op hoogte?
```

**Expected Response Structure:**
```
🤖 Assistant:
Voor werken op hoogte gelden strikte veiligheidseisen. Vanaf 2,5 meter hoogte
is valbeveiliging verplicht volgens de Arbowet. [... more Dutch text ...]

Relevante richtlijnen:

• NVAB Richtlijn: Werken op Hoogte (NVAB)
  [Quote from guideline]

• Arbowet Artikel 3 (Arboportaal)
  [Quote from guideline]

────────────────────────────────────────────────────────────
```

**Validation Checklist:**
- [ ] Response is in Dutch (no English)
- [ ] Response cites ≥2 guidelines
- [ ] Citations include title and source
- [ ] Response is actionable (specific requirements)
- [ ] No errors or crashes
- [ ] Response time <3 seconds

**Test Query 2: Employee Health**

```
You: Hoe voorkom ik rugklachten bij werknemers?
```

**Validate:**
- [ ] Dutch response
- [ ] Citations about ergonomics, lifting, workplace setup
- [ ] Practical advice included

**Test Query 3: Workplace Noise**

```
You: Welke maatregelen zijn nodig voor lawaai op de werkplek?
```

**Validate:**
- [ ] Response mentions decibel limits or hearing protection
- [ ] Cites ARBO or NVAB guidelines
- [ ] Specific measures (not vague)

**Test Query 4: Employer Duty of Care**

```
You: Wat is de zorgplicht van de werkgever?
```

**Validate:**
- [ ] Response cites Arbowet
- [ ] Explains legal obligations
- [ ] Dutch terminology correct

**Test Query 5: Nonsense Query (Edge Case)**

```
You: xyzabc qwerty foobar
```

**Validate:**
- [ ] Agent responds gracefully
- [ ] No crash or error
- [ ] Message indicates no relevant guidelines found

**Run All 10 Test Queries:**

Copy these queries one by one into the CLI:

1. "Wat zijn de vereisten voor werken op hoogte?"
2. "Hoe voorkom ik rugklachten bij werknemers?"
3. "Welke maatregelen zijn nodig voor lawaai op de werkplek?"
4. "Wat is de zorgplicht van de werkgever?"
5. "Hoe moet ik omgaan met een arbeidsongeval?"
6. "Wat zegt de Arbowet over werkdruk?"
7. "Wat zijn de regels voor nachtwerk?"
8. "Welke EN normen gelden voor valbescherming?"
9. "Wat is de maximale blootstelling aan geluid?"
10. "Hoe begeleidt ik een zieke werknemer?"

**For Each Query, Record:**
- Response time (use CLI timer or watch)
- Dutch quality (grammatically correct? native-level?)
- Citation count (0, 1, 2, 3+)
- Relevance (on-topic? actionable?)
- Errors (any crashes or encoding issues?)

**Success Criteria:**
- ✅ 8/10 queries have ≥2 citations
- ✅ 8/10 queries have response time <3 seconds
- ✅ 10/10 queries return valid Dutch (no English or gibberish)
- ✅ 8/10 queries are relevant and actionable
- ✅ 0/10 queries crash or cause errors

---

### Step 3.3: Validate Search Quality

**Purpose:** Check that hybrid search is returning relevant chunks.

**Method:** Add debug logging to see search results.

**Option 1: Check API Logs**

When you run a query in the CLI, watch the API server terminal. You should see:

```
INFO: [Session abc-123] Searching guidelines: query='werken op hoogte', limit=10
INFO: [Session abc-123] Retrieved 10 chunks (top score: 0.847)
```

**Option 2: Add Temporary Debug Endpoint**

Add to `agent/api.py`:

```python
@app.post("/debug/search")
async def debug_search(request: dict):
    """
    Debug endpoint to see raw search results.

    Body: {"query": "Dutch query", "limit": 10}
    """
    from agent.tools import hybrid_search_tool, HybridSearchInput

    results = await hybrid_search_tool(
        HybridSearchInput(
            query=request["query"],
            limit=request.get("limit", 10)
        )
    )

    return {
        "query": request["query"],
        "results_count": len(results),
        "results": [
            {
                "content_preview": r.content[:200],
                "score": r.score,
                "title": r.document_title,
                "source": r.document_source
            }
            for r in results
        ]
    }
```

**Test Debug Endpoint:**
```bash
curl -X POST http://localhost:8058/debug/search \
  -H "Content-Type: application/json" \
  -d '{"query": "werken op hoogte", "limit": 5}'
```

**Validation:**
- [ ] Top 5 results have scores >0.6 (reasonable relevance)
- [ ] Results are about the query topic
- [ ] No duplicate chunks
- [ ] Document titles make sense (NVAB, ARBO, etc.)

---

## Phase 4: Final Validation (1 hour)

### Step 4.1: Dutch Quality Check

**Method:** Have a native Dutch speaker review 3-5 responses.

**Checklist:**
- [ ] Grammar is correct
- [ ] Terminology is appropriate for workplace safety
- [ ] Informal "je/jij" is used (not formal "u")
- [ ] No awkward machine translation phrases

**If no native speaker available:**
- Use GPT-4 to validate: "Is this grammatically correct Dutch?"
- Check for common errors: missing articles, wrong verb conjugations

---

### Step 4.2: Citation Quality Check

**For 5 random queries:**

1. Note the citations provided by the agent
2. Check if citation titles match actual documents in database:

```sql
-- Connect to database
PGPASSWORD=postgres psql -h localhost -U postgres -d evi_rag

-- Check if cited documents exist
SELECT title, source FROM documents WHERE title ILIKE '%werken op hoogte%';
```

3. Validate that quotes come from actual chunk content:

```sql
-- Check if quote appears in chunks
SELECT d.title, c.content
FROM chunks c
JOIN documents d ON c.document_id = d.id
WHERE c.content ILIKE '%valbeveiliging boven 2,5 meter%';
```

**Validation:**
- [ ] All cited titles exist in database
- [ ] Quotes are accurate (not hallucinated)
- [ ] Sources are correctly attributed

---

### Step 4.3: Performance Benchmarking

**Run 10 queries and measure time:**

```bash
# Simple timing script
for query in "werken op hoogte" "rugklachten preventie" "lawaai werkplek"; do
  echo "Query: $query"
  time curl -X POST http://localhost:8058/chat/stream \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"$query\"}" \
    > /dev/null 2>&1
done
```

**Or use CLI with manual timing:**
- Start stopwatch when pressing Enter
- Stop when response completes

**Record Times:**
| Query | Time (seconds) |
|-------|----------------|
| Query 1 | 2.3s |
| Query 2 | 1.8s |
| Query 3 | 2.7s |
| ... | ... |

**Validation:**
- [ ] 95th percentile <3 seconds
- [ ] No queries >5 seconds
- [ ] Average time ~2 seconds

---

### Step 4.4: Error Handling Test

**Test Error Scenarios:**

**1. Database Down:**
```bash
# Stop PostgreSQL
docker-compose stop postgres

# Try query in CLI
You: test query
# Should get error message (not crash)

# Restart database
docker-compose start postgres
```

**Validate:** Agent returns friendly error in Dutch, CLI doesn't crash

**2. Invalid API Key:**
```bash
# Temporarily set wrong key in .env
LLM_API_KEY=invalid_key

# Restart API server
# Try query

# Restore correct key
```

**Validate:** Error is logged, user gets "service unavailable" message

**3. Network Timeout:**
```bash
# Simulate slow OpenAI by adding sleep in tools.py (temporary)
# In generate_embedding function:
import time
time.sleep(10)  # Force timeout

# Try query
```

**Validate:** Request times out gracefully, doesn't hang forever

---

## Phase 5: Documentation Updates (30 minutes)

### Step 5.1: Update README.md

**Add API Startup Section:**

```markdown
## Running the MVP

### Start the API Server

```bash
# 1. Ensure Docker containers are running
docker-compose ps  # Should show postgres as healthy

# 2. Activate virtual environment
source venv_linux/bin/activate

# 3. Start API server on port 8058
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload

# Expected output:
# INFO: Uvicorn running on http://0.0.0.0:8058
# INFO: Database initialized
# INFO: Application startup complete
```

### Use the CLI

```bash
# In a new terminal:
source venv_linux/bin/activate
python3 cli.py

# Ask questions in Dutch:
You: Wat zijn de vereisten voor werken op hoogte?
```

### Test Queries

Try these 10 Dutch queries to validate the system:
1. "Wat zijn de vereisten voor werken op hoogte?"
2. "Hoe voorkom ik rugklachten bij werknemers?"
3. "Welke maatregelen zijn nodig voor lawaai op de werkplek?"
... (list all 10)
```

---

### Step 5.2: Document Known Issues

**Create:** `docs/features/FEAT-003_query-retrieval/known-issues.md`

```markdown
# Known Issues: FEAT-003 MVP

## Current Limitations

### 1. Tier Column Unused
- **Issue:** All 10,833 chunks have `tier = NULL`
- **Impact:** No tier-aware search (returns all tiers mixed)
- **Workaround:** None for MVP
- **Fix:** FEAT-009 will populate and use tier column

### 2. No Session Memory
- **Issue:** Each query is stateless
- **Impact:** Agent doesn't remember previous queries in same session
- **Workaround:** User must repeat context
- **Fix:** FEAT-008 will add session memory

### 3. Graph Search Disabled
- **Issue:** Neo4j is empty, graph tools not used
- **Impact:** No relationship queries
- **Workaround:** Use vector/hybrid search only
- **Fix:** FEAT-006 will populate graph

### 4. No Product Recommendations
- **Issue:** Products table is empty
- **Impact:** Agent can't recommend safety equipment
- **Workaround:** Focus on guidelines only
- **Fix:** FEAT-004 will add product catalog

### 5. CLI Shows "Tech Companies" Welcome Message
- **Issue:** Hardcoded message in cli.py (line 206)
- **Impact:** Confusing welcome message
- **Workaround:** Ignore message, system works correctly
- **Fix:** Update cli.py welcome message to match specialist domain

## Performance Notes

- First query after API startup is slower (~5s) due to model loading
- Subsequent queries are ~2s
- Embedding API calls add ~300ms latency

## Debugging Tips

- Check API logs: `tail -f logs/api.log` (if logging to file)
- Test search directly: `curl -X POST http://localhost:8058/debug/search`
- Verify database: `PGPASSWORD=postgres psql -h localhost -U postgres -d evi_rag -c "SELECT COUNT(*) FROM chunks;"`
```

---

## Troubleshooting Guide

### Problem: API Won't Start

**Symptoms:**
```
ImportError: cannot import name 'specialist_agent' from 'agent.specialist_agent'
```

**Solution:**
- Verify `agent/specialist_agent.py` exists
- Check for syntax errors: `python3 -m py_compile agent/specialist_agent.py`
- Ensure all imports are correct

---

### Problem: "No module named 'pydantic_ai'"

**Symptoms:**
```
ModuleNotFoundError: No module named 'pydantic_ai'
```

**Solution:**
```bash
pip install pydantic-ai
# or
pip install -r requirements.txt
```

---

### Problem: CLI Shows English Responses

**Symptoms:** Agent responds in English about tech companies

**Solution:**
- Verify `agent/api.py` imports `specialist_agent` (not `rag_agent`)
- Restart API server after making changes
- Check API logs for import errors

---

### Problem: No Citations in Response

**Symptoms:** Agent responds but doesn't cite guidelines

**Solution:**
- Check if search_guidelines tool is being called (check API logs)
- Verify database has data: `SELECT COUNT(*) FROM chunks;` (should be 10,833)
- Test search directly: Use `/debug/search` endpoint
- Check system prompt includes citation instructions

---

### Problem: Search Returns No Results

**Symptoms:** Agent says "Geen relevante richtlijnen gevonden"

**Solution:**
- Verify embeddings exist: `SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL;`
- Check OpenAI API key: `echo $LLM_API_KEY` or check `.env`
- Test embedding generation separately
- Check Dutch full-text search config: `SELECT to_tsvector('dutch', 'werken op hoogte');`

---

### Problem: Slow Response Time (>5 seconds)

**Symptoms:** Queries take too long

**Solution:**
- Check database connection pool: Should have 5-20 connections
- Verify pgvector index exists: `\d chunks` (should show ivfflat index on embedding)
- Monitor OpenAI API latency (separate issue)
- Consider increasing `lists` parameter in pgvector index

---

## Next Steps After Implementation

### 1. Manual Testing Checklist

Complete all 10 test queries and record:
- [ ] Response time for each
- [ ] Citation count for each
- [ ] Dutch quality (grammatically correct?)
- [ ] Relevance score (1-5, where 5 = perfect answer)

### 2. Code Review Checklist

- [ ] All new files follow PEP8 style
- [ ] Docstrings are complete and accurate
- [ ] Type hints are present
- [ ] Error handling is robust
- [ ] Logging statements are informative

### 3. Documentation Checklist

- [ ] README updated with API startup instructions
- [ ] Known issues documented
- [ ] Test results recorded
- [ ] Implementation notes added to IMPLEMENTATION_PROGRESS.md

### 4. Handoff

- [ ] Record demo video of CLI interaction (optional)
- [ ] Share test results with team
- [ ] Document any deviations from plan
- [ ] List any technical debt or future improvements

---

## Success Criteria Final Checklist

### Functional Requirements
- [ ] Specialist agent responds to Dutch queries
- [ ] Responses include ≥2 guideline citations
- [ ] Citations include title and source
- [ ] Responses are in grammatically correct Dutch
- [ ] No English responses (except if user explicitly requests)

### Performance Requirements
- [ ] 95th percentile response time <3 seconds
- [ ] API startup time <10 seconds
- [ ] No crashes during 10-query test session

### Quality Requirements
- [ ] 8/10 test queries return relevant answers
- [ ] Top 5 search results include ≥3 relevant chunks
- [ ] No duplicate chunks in top 10 results

### Technical Requirements
- [ ] 90% code reuse (existing tools, db_utils, API, CLI)
- [ ] Only 2 new files (specialist_agent.py, specialist_prompt.py)
- [ ] 1 modified file (agent/api.py)
- [ ] All tests pass (6/6 unit tests)

---

**Estimated Total Time:** 5-8 hours
- Phase 1 (Agent Creation): 2-3 hours
- Phase 2 (API Integration): 1 hour
- Phase 3 (Testing): 2-3 hours
- Phase 4 (Validation): 1 hour
- Phase 5 (Documentation): 30 minutes

**Confidence Level:** High (90% of code already exists and tested)

**Risk Areas:**
- Dutch quality validation (requires native speaker or thorough GPT-4 review)
- OpenAI API reliability (external dependency)
- First-time streaming implementation (may need debugging)

---

**Last Updated:** 2025-10-26
**Status:** Ready for Implementation
**Next Document:** Review stub PRDs for future features (FEAT-007, FEAT-008, FEAT-009)
