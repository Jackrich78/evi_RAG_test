# PRD: FEAT-005 - Multi-Agent System

**Feature ID:** FEAT-005
**Phase:** 5 (Intelligent Responses) - **FUTURE FEATURE**
**Status:** 📋 Planned (Post-MVP)
**Priority:** Medium
**Owner:** TBD
**Dependencies:** FEAT-003 (MVP Specialist Agent), FEAT-008 (Session Memory)
**Created:** 2025-10-25
**Last Updated:** 2025-10-26

---

## ⚠️ MVP Status: DESCOPED

**This feature is NOT part of the MVP (FEAT-003).** The MVP uses a single Specialist Agent with search tools, not a two-agent system.

**Why Descoped:**
- Single agent with tools is sufficient for MVP (simpler, faster)
- Agent-calling-agent pattern adds complexity without clear MVP benefit
- Pydantic AI research showed two agents only needed for separate reasoning loops
- MVP proves RAG quality first, then optimize architecture

**When to Implement:** After FEAT-003 is validated and if performance/quality issues emerge that multi-agent solves.

---

## Problem Statement

Transform raw search results into intelligent, Dutch-language responses with guideline citations and product recommendations. Users need conversational assistance, not just search results.

**Challenge:** Balance between information retrieval (Research Agent) and response generation (Specialist Agent) while maintaining context and Dutch language quality.

---

## Goals

1. **Research Agent:** Tier-aware search specialist that retrieves guidelines and products
2. **Specialist Agent:** Dutch-language workplace safety expert that formulates responses
3. **Agent-Calling-Agent:** Specialist uses Research as a tool (Pydantic AI pattern)
4. **Conversational:** Maintain session context for follow-up questions
5. **Citations:** Always cite guidelines with tier and source information

---

## User Stories

### Research Agent Retrieves Context
**Given** Query "werken op hoogte vereisten"
**When** Research Agent is invoked
**Then** Returns structured response with Tier 2 guideline chunks and relevant products

### Specialist Agent Generates Response
**Given** Research results about working at height
**When** Specialist Agent processes them
**Then** Generates Dutch response explaining requirements with citations

### Agent-Calling-Agent Pattern
**Given** User asks "wat zijn de veiligheidsnormen?"
**When** Specialist Agent needs information
**Then** Internally calls Research Agent as a tool and formats results

### Follow-Up Questions
**Given** Previous query about fall protection
**When** User asks "welke producten heb je daarvoor?"
**Then** Specialist understands context and recommends relevant products

---

## Scope

### In Scope ✅
- **Research Agent** (`agent/research_agent.py`):
  - Tool: `search_guidelines_by_tier(query, tier, limit)`
  - Tool: `search_products(query, compliance_tags, limit)`
  - Tool: `get_full_guideline_context(document_id)` - Fetch all tiers for one guideline
  - Returns: Structured `ResearchAgentResponse` Pydantic model

- **Specialist Agent** (`agent/specialist_agent.py`):
  - Uses Research Agent as dependency (agent-calling-agent)
  - Dutch system prompt (professional workplace safety specialist tone)
  - Tool: `research_guidelines(query)` - Internally calls Research Agent
  - Tool: `research_products(query, tags)` - Internally calls Research Agent
  - Returns: `SpecialistAgentResponse` with formatted Dutch answer + citations

- **Session Management** (`agent/session_manager.py`):
  - Store conversation history in `sessions` and `messages` tables
  - Load previous context for follow-up questions
  - Session timeout after 30 minutes of inactivity

- **CLI Enhancement** (extend `cli.py`):
  - Command: `python3 cli.py chat "Dutch query"`
  - Display formatted response with citations and product recommendations
  - Support for interactive chat mode: `python3 cli.py chat --interactive`

### Out of Scope ❌
- REST API endpoints (deferred to FEAT-006)
- Streaming responses (deferred to FEAT-006)
- Knowledge graph integration (future enhancement)
- Multi-turn conversation optimization (basic context only for MVP)

---

## Success Criteria

**Research Agent:**
- ✅ Successfully searches guidelines by tier with correct filtering
- ✅ Successfully searches products with compliance tag filtering
- ✅ Returns structured `ResearchAgentResponse` in <2 seconds

**Specialist Agent:**
- ✅ Generates coherent Dutch responses (validated by native speaker)
- ✅ Always includes guideline citations (tier, source, title)
- ✅ Recommends 2-5 relevant products when applicable
- ✅ Professional tone appropriate for workplace safety context

**Agent Integration:**
- ✅ Specialist successfully calls Research Agent as tool
- ✅ No duplicate research calls (efficient tool usage)
- ✅ Session context correctly maintained across follow-ups

**CLI:**
- ✅ Accepts Dutch queries without encoding issues
- ✅ Displays formatted responses with clear structure
- ✅ Shows citations with clickable links (if terminal supports it)
- ✅ Interactive mode supports follow-up questions

---

## Dependencies

**Infrastructure:**
- ✅ PostgreSQL 17 + pgvector with all search functions (FEAT-001)
- ✅ Sessions and messages tables (FEAT-001)

**Data:**
- Notion guidelines ingested with tier metadata (FEAT-002)
- Query & retrieval system working (FEAT-003)
- Product catalog ingested (FEAT-004, can start without products)

**External Services:**
- OpenAI API key for GPT-4 (Dutch responses) and embeddings

---

## Technical Notes

**Pydantic AI Agent-Calling-Agent Pattern:**
```python
# Research Agent (dependency)
research_agent = Agent(
    model=gpt_4,
    deps_type=ResearchDeps,
    result_type=ResearchAgentResponse
)

@research_agent.tool
async def search_guidelines_by_tier(...):
    """Search tool for Research Agent."""

# Specialist Agent (uses Research Agent)
specialist_agent = Agent(
    model=gpt_4,
    deps_type=SpecialistDeps,
    result_type=SpecialistAgentResponse
)

@specialist_agent.tool
async def research_guidelines(ctx: RunContext, query: str):
    """Specialist calls Research Agent internally."""
    research_result = await research_agent.run(query, deps=...)
    return research_result.data
```

**Dutch System Prompt (Specialist Agent):**
```
Je bent een deskundige arbeidsveiligheidsadviseur voor EVI 360.

Taken:
- Beantwoord vragen over Nederlandse arbeidsveiligheid
- Citeer altijd de relevante richtlijnen (NVAB, STECR, UWV, ARBO)
- Beveel passende EVI 360 producten aan
- Gebruik professionele, heldere taal
- Antwoord altijd in het Nederlands

Formaat:
1. Beknopt antwoord op de vraag
2. Relevante richtlijnen met citaten
3. Aanbevolen producten (indien van toepassing)
4. Advies voor vervolgstappen
```

**Response Format:**
```markdown
## Antwoord
[Dutch response to query]

## Richtlijnen
- **NVAB Richtlijn: Werken op Hoogte** (Tier 2)
  "Werkgevers moeten zorgen voor adequate valbeveiliging..."
  [Link to full guideline]

- **ARBO Regelgeving** (Tier 1)
  "Minimale hoogte voor valbeveiliging is 2,5 meter."

## Aanbevolen Producten
1. **Veiligheidshelm EN 397** - CE-gecertificeerd
   [Product URL]

2. **Valbeveiligingsharnas** - EN 361, EN 358
   [Product URL]

## Advies
[Next steps or additional recommendations]
```

---

## Implementation Plan

### Step 1: Research Agent (6-8 hours)
**File:** `agent/research_agent.py`

Implement Pydantic AI agent with search tools.

### Step 2: Specialist Agent (6-8 hours)
**File:** `agent/specialist_agent.py`

Implement Pydantic AI agent that calls Research Agent.

### Step 3: Session Management (3-4 hours)
**File:** `agent/session_manager.py`

Store and retrieve conversation context.

### Step 4: CLI Enhancement (4-5 hours)
**Extend:** `cli.py`

Add `chat` subcommand with formatted output.

### Step 5: Testing (4-6 hours)
- Unit tests for both agents
- Integration test: full query → response flow
- Dutch language quality validation
- Session context persistence tests

---

## Testing Strategy

**Test Queries (Dutch):**
1. "Wat zijn de vereisten voor werken op hoogte?" (guideline-focused)
2. "Welke producten heb je voor geluidsbescherming?" (product-focused)
3. "Hoe voorkom ik rugklachten bij werknemers?" (mixed: guideline + product)
4. Follow-up: "Zijn er ook trainingen beschikbaar?" (context-dependent)

**Validation:**
- Dutch language: grammatically correct, professional tone
- Citations: include tier, source, relevant quote
- Products: 2-5 recommendations with compliance tags
- Context: follow-up questions reference previous query

---

## Next Steps

1. Implement Research Agent with Pydantic AI
2. Implement Specialist Agent with agent-calling-agent pattern
3. Add session management (store in PostgreSQL)
4. Extend CLI with `chat` subcommand
5. Test with 10-15 sample queries
6. Validate Dutch language quality with native speaker
7. Document agent architecture in docs/system/architecture.md

---

**Last Updated:** 2025-10-25
**Status:** ⏳ Ready to Plan
**Estimated Effort:** 23-31 hours
