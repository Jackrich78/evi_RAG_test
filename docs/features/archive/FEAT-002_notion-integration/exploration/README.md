# FEAT-002 Exploration: Knowledge Graph

**Status:** Deferred to Phase 6
**Decision Date:** 2025-10-26
**Reason:** Too slow and expensive for MVP

---

## What Was Explored

This directory contains exploration work for integrating a knowledge graph (Neo4j + Graphiti) with the Notion ingestion pipeline.

### Files

- **KNOWLEDGE_GRAPH_ANALYSIS.md** - Performance analysis showing 2-3 day processing time and $83+ cost
- **test_knowledge_graph.py** - Test script for validating knowledge graph search functionality
- **test_subset.py** - Script for testing KG on subset of 5 files
- **monitor_progress.py** - Python monitoring script for ingestion progress
- **simple_monitor.sh** - Shell script for monitoring ingestion
- **cleanup_all.sh** - Cleanup script for test data

---

## Test Results

**5-File Test:**
- Processing time: ~83 minutes (27% complete)
- Cost: $4.77
- Nodes created: 806+
- **Projected for 87 files:** 52-78 hours, $83+ cost

**Why So Slow:**
- LLM API call per episode (~20-30 seconds each)
- Entity extraction using `gpt-4.1-mini`
- Embedding generation for each episode
- Neo4j graph operations
- Rate limiting delays

---

## Decision: Defer to Phase 6

**FEAT-002 Acceptance Criteria (AC.md):**
- 17 total criteria defined
- **0 criteria mention knowledge graph**
- AC-002-302 explicitly states: "tier column is NULL for all Notion-sourced chunks (tier parsing deferred)"

**PRD Out of Scope:**
- Knowledge graph relationships (deferred to future phase)

**What Was Actually Required:**
1. ✅ Fetch guidelines from Notion
2. ✅ Convert to markdown
3. ✅ Ingest using existing pipeline
4. ✅ Dutch full-text search working
5. ✅ Store chunks with NULL tier (defer tier parsing)

**Actual FEAT-002 Results (without KG):**
- Processing time: 42.5 minutes
- Cost: Minimal (embedding generation only)
- Documents: 87/87 (100%)
- Chunks: 10,833 (100% embedded)
- Errors: 0
- Dutch search: ✅ Working

---

## Future Enhancement: Phase 6

When we revisit knowledge graph integration:

### Optimization Strategies

1. **Parallel Processing** - Process multiple episodes simultaneously (3-5x faster)
2. **Faster LLM** - Switch to `gpt-3.5-turbo` for entity extraction (2x faster, lower quality)
3. **Batch Operations** - Create multiple episodes per Graphiti call (1.5-2x faster)
4. **Incremental Updates** - Only process new/changed documents
5. **Simpler Entity Extraction** - Use pattern matching instead of LLM for common entities

### Questions to Answer First

1. Does knowledge graph improve retrieval quality? (A/B testing needed)
2. What's the update frequency? (Daily vs monthly affects acceptable ingestion time)
3. Is 2-3 days one-time cost acceptable? (vs fast incremental updates)
4. Can we use cached entity extraction? (reuse entities across similar guidelines)

---

## Lessons Learned

1. **Always check acceptance criteria** - Knowledge graph wasn't required for FEAT-002 sign-off
2. **MVP first, optimize later** - Get core functionality working before adding complex features
3. **Cost/time projections are critical** - Test on subset, extrapolate before full run
4. **Document deferral decisions** - Clear explanation prevents confusion later

---

**Next Steps:** Proceed with FEAT-003 (Query & Retrieval) using vector + full-text search without knowledge graph.
