# PRD: FEAT-004 - Multi-Agent System

**Feature ID:** FEAT-004
**Phase:** 5 (Multi-Agent System)
**Status:** Planned
**Priority:** High
**Owner:** TBD

## Overview

Implement the core multi-agent system using Pydantic AI 0.3.2 with an agent-calling-agent pattern. The system consists of two agents: (1) **Research Agent** - performs tier-aware hybrid search across guidelines and products, and (2) **Intervention Specialist Agent** - generates Dutch-language responses by calling the Research Agent as a tool. Include a basic CLI for testing agent interactions before API development.

## Scope

**In Scope:**
- **Research Agent** (`agent/research_agent.py`):
  - Tool: Tier-aware guideline search using `search_guidelines_by_tier()` SQL function
  - Tool: Product search using `search_products()` SQL function
  - Returns: Structured `ResearchAgentResponse` with guideline chunks, products, citations
  - Default tier: 2 (Key Facts) unless explicitly requested
  - Hybrid search: 70% vector similarity + 30% full-text (Dutch language)
- **Intervention Specialist Agent** (`agent/specialist_agent.py`):
  - Uses Research Agent as a tool (agent-calling-agent pattern)
  - Generates Dutch-language responses based on research results
  - Returns: `SpecialistAgentResponse` with formatted answer, citations, product recommendations
  - Dutch system prompt: Professional workplace safety specialist tone
- **CLI** (`cli.py`):
  - Command: `python3 cli.py chat "Wat zijn de vereisten voor werken op hoogte?"`
  - Display: Dutch response, guideline citations (with tier), product recommendations
  - Session management: Basic in-memory session (no persistence for MVP)
- Pydantic models already implemented in `agent/models.py` (✅ ready)

**Out of Scope:**
- REST API endpoints (deferred to FEAT-005)
- Streaming responses (deferred to FEAT-006)
- Advanced session persistence (Phase 7)
- Knowledge graph integration (future phase)

## Success Criteria

- ✅ Research Agent successfully searches guidelines by tier (Tier 1, 2, 3, or all)
- ✅ Research Agent successfully searches products and returns relevant recommendations
- ✅ Specialist Agent generates coherent Dutch-language responses using research results
- ✅ CLI accepts Dutch queries and displays formatted responses
- ✅ Test suite validates:
  - Research Agent tier filtering (Tier 1 returns summaries, Tier 2 returns key facts, etc.)
  - Research Agent product search accuracy (top 5 products relevant to query)
  - Specialist Agent response quality (Dutch grammar, citations included, professional tone)
  - Agent-calling-agent pattern works correctly (Specialist calls Research as tool)
- ✅ End-to-end CLI test: Query → Research → Specialist Response → Display in < 3 seconds (Tier 2)

## Dependencies

- **Infrastructure:** PostgreSQL 17 + pgvector with all tables, functions, views (FEAT-001 ✅)
- **Data:** Notion guidelines ingested (FEAT-002)
- **Data:** Product catalog ingested (FEAT-003)
- **External Services:** OpenAI API key for GPT-4 (Dutch responses) and embeddings (query encoding)

## Technical Notes

- **Pydantic AI Pattern:** Define agents as Pydantic AI Agent classes with type-safe tools
- **Agent-Calling-Agent:** Specialist Agent's tools include `research_guidelines()` and `research_products()` which internally call Research Agent
- **Dutch Language:** Ensure GPT-4 system prompt explicitly requests Dutch responses
- **Error Handling:** Gracefully handle cases where no guidelines/products found (inform user)
- **CLI Framework:** Use `click 8.2.1` for CLI argument parsing and `rich 14.0.0` for formatted output

## Next Steps

1. Implement Research Agent with tier-aware search tools
2. Implement Specialist Agent with Research Agent as dependency
3. Create CLI interface with click + rich
4. Write comprehensive tests for both agents
5. Test end-to-end with sample Dutch queries (e.g., "werken op hoogte", "persoonlijke beschermingsmiddelen")
6. Validate Dutch language response quality (grammar, tone, completeness)
7. Document agent architecture and usage in docs/system/architecture.md
