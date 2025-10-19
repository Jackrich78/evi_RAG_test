# Original Project Files Archive

**Date**: October 19, 2025
**Reason for Archive**: Project template mismatch

This archive contains the original `PLANNING.md` and `TASK.md` files that described a different project than what is actually being built.

---

## Background

### Template Source

The EVI RAG project was initially based on the "Agentic RAG with Knowledge Graph" template from:
**https://github.com/coleam00/ottomator-agents/tree/main/agentic-rag-knowledge-graph**

This template was designed for:
- Analyzing big tech companies (Google, Microsoft, Meta, etc.)
- Tracking AI initiatives and partnerships
- General-purpose RAG for tech industry intelligence
- English language content

### Actual Project

**EVI 360 RAG System for Workplace Safety**

The project was adapted for a completely different purpose:
- Dutch-language workplace safety guidelines
- 3-tier guideline hierarchy (Summary → Key Facts → Details)
- Product catalog with compliance tags
- Multi-agent system (Research + Specialist agents)
- Notion integration for guideline database
- Product recommendations for safety equipment

---

## Files in This Archive

1. **ORIGINAL_PLANNING.md** (was `PLANNING.md`)
   - Describes architecture for "big tech companies and their AI initiatives"
   - Includes examples like "What are Google's main AI initiatives?"
   - Documents workflow for analyzing FAANG competitive strategies
   - **Does not match actual EVI 360 project**

2. **ORIGINAL_TASK.md** (was `TASK.md`)
   - Task list for generic agentic RAG system
   - Phases like "Process markdown files about tech companies"
   - No mention of 3-tier guidelines, Dutch language, or products
   - **Does not match actual EVI 360 tasks**

---

## Why These Files Were Archived

### The Mismatch

**What ORIGINAL_PLANNING.md described**:
```
"This system includes three main components:
1. Document Ingestion Pipeline: Processes markdown documents about tech companies
2. AI Agent Interface: Answers questions about big tech AI strategies
3. Streaming API: FastAPI backend for tech industry analysis"
```

**What EVI 360 actually is**:
```
"This system includes three main components:
1. Notion Integration: Fetches Dutch workplace safety guidelines with 3-tier structure
2. Multi-Agent System: Research Agent + Specialist Agent for safety consultations
3. Product Recommendations: Suggests safety equipment with compliance tags"
```

These are fundamentally different projects.

###Solution

Instead of deleting these valuable template files, we:
1. ✅ Archived them here to show project origins
2. ✅ Created new EVI 360-specific documentation
3. ✅ Preserved git history showing evolution

---

## Current Active Documentation

The EVI 360 project now has correct documentation:

**Active Project Files** (in project root):
- [README.md](../../README.md) - EVI 360 project overview
- [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md) - EVI 360 detailed architecture
- [TASKS.md](../../TASKS.md) - Points to Archon MCP for task tracking
- [CLAUDE.md](../../CLAUDE.md) - Updated with EVI 360 context
- [docs/IMPLEMENTATION_PROGRESS.md](../../docs/IMPLEMENTATION_PROGRESS.md) - EVI 360 progress tracking

---

## What Was Kept from Template

Even though the project focus changed, several architectural decisions from the template were kept:

### Retained Architecture
- ✅ PostgreSQL + pgvector for vector search
- ✅ Neo4j + Graphiti for knowledge graphs
- ✅ Pydantic AI for agent framework
- ✅ FastAPI for API layer
- ✅ Semantic chunking strategy
- ✅ Multi-agent system concept
- ✅ Streaming responses

### Adapted for EVI 360
- 🔄 Generic chunking → 3-tier hierarchical chunking
- 🔄 Markdown files → Notion API integration
- 🔄 English language → Dutch language support
- 🔄 Tech company data → Workplace safety guidelines
- 🔄 Single agent → Research Agent + Specialist Agent
- 🔄 General queries → Safety consultations + product recommendations

---

## Value of This Archive

### Why Keep These Files?

1. **Shows project origins**: Understanding where the architecture came from
2. **Template credit**: Acknowledges original template source
3. **Architecture decisions**: Explains why certain patterns exist
4. **Future reference**: May be useful for explaining design choices

### Historical Context

These files show:
- What the starting template looked like
- How significantly the project was adapted
- Why certain architectural decisions were made
- The evolution from generic RAG to specialized EVI 360 system

---

## Related Archives

**Migration Documentation**:
- [2025-10-19 Supabase Migration](../2025-10-19_supabase_migration/) - Infrastructure migration docs

---

## Credits

Original template: **Agentic RAG with Knowledge Graph**
- Author: Cole Medin (coleam00)
- Repository: https://github.com/coleam00/ottomator-agents
- Template: agentic-rag-knowledge-graph

Adapted for: **EVI 360 RAG System for Workplace Safety**
- Focus: Dutch workplace safety guidelines with 3-tier hierarchy
- Client: EVI 360 safety specialists
- Unique features: Tier-aware search, product recommendations, Dutch language

---

**Archive Purpose**: Preserve template source files while using correct EVI 360 documentation for active development.
