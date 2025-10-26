# PRD: FEAT-006 - Knowledge Graph Enhancement

**Feature ID:** FEAT-006
**Phase:** 6 (Optimization & Knowledge Graph) - **FUTURE FEATURE**
**Status:** 📋 Planned (Deferred from FEAT-002)
**Priority:** Low (Future Enhancement)
**Owner:** TBD
**Dependencies:** FEAT-003 (MVP must validate that graph is needed)
**Created:** 2025-10-25
**Last Updated:** 2025-10-26

---

## ⚠️ MVP Status: DESCOPED - Neo4j Empty, Graph Search Disabled

**This feature is NOT part of the MVP (FEAT-003).** The MVP uses vector/hybrid search only. Neo4j container runs but database is empty.

**Why Descoped:**
- Graph population is expensive: 52-78 hours, $83+ cost for 87 documents
- Vector + Dutch full-text search may be sufficient (needs validation)
- MVP must prove whether graph adds value before investing time/money
- Graph tools exist in code but are disabled/ignored for MVP

**Current State:**
- Neo4j container: Running but empty
- Graph tools: `graph_search_tool`, `get_entity_relationships_tool` exist but unused
- Graphiti integration: Configured but not populated

**When to Implement:** After FEAT-003 MVP proves current search is insufficient (e.g., poor relationship queries, missing context).

---

## Problem Statement

While the current RAG system (FEAT-002) successfully retrieves Dutch workplace safety guidelines using vector + full-text search, a knowledge graph could potentially improve retrieval quality by capturing relationships between guidelines, topics, and entities.

**Challenge:** Knowledge graph building is expensive and time-consuming. Initial testing showed:
- Time: 52-78 hours for 87 documents (20-30 seconds per episode)
- Cost: $83+ for full dataset (LLM calls for entity extraction)
- Not required for MVP (0 of 17 FEAT-002 acceptance criteria mentioned KG)

**This feature is deferred until we validate whether knowledge graph actually improves retrieval quality over the current vector + full-text approach.**

---

## Background: Why This Was Deferred

**From FEAT-002 Knowledge Graph Exploration:**

### Test Results (5-File Subset)
- Processing time: ~83 minutes (27% complete)
- Cost: $4.77
- Nodes created: 806+
- Projected for 87 files: 52-78 hours, $83+ cost

### Why So Slow
- LLM API call per episode (~20-30 seconds each)
- Entity extraction using `gpt-4.1-mini`
- Embedding generation for each episode
- Neo4j graph operations
- Rate limiting delays

### Decision Rationale
- **FEAT-002 Acceptance Criteria:** 17 total, 0 mention knowledge graph
- **PRD Out of Scope:** Knowledge graph explicitly listed
- **AC-002-302:** Tier parsing deferred (tier column NULL for all chunks)
- **MVP Focus:** Get working search first, optimize later

**See:** `docs/features/FEAT-002_notion-integration/exploration/README.md` for detailed analysis

---

## Goals (When Implemented)

1. **Improve Retrieval Quality:** Use graph relationships to find relevant guidelines that vector search might miss
2. **Entity Linking:** Connect entities (conditions, regulations, organizations) across guidelines
3. **Relationship Discovery:** Surface connections between related safety topics
4. **Smart Navigation:** Enable "related guidelines" recommendations based on graph structure
5. **Validation:** A/B test to prove KG improves retrieval quality vs current approach

---

## User Stories (When Implemented)

### Discover Related Guidelines via Graph
**Given** I'm viewing a guideline about "pregnancy at work"
**When** I request related guidelines
**Then** The system uses graph relationships to suggest guidelines about "workplace adjustments", "risk assessment", "legal requirements"

### Entity-Based Search
**Given** I search for "NVAB" (Dutch occupational health organization)
**When** The system processes my query
**Then** All guidelines with NVAB entity references are retrieved, even if NVAB isn't in the text

### Cross-Reference Detection
**Given** Two guidelines reference the same regulation (e.g., "Arbowet artikel 3.5")
**When** Building the knowledge graph
**Then** A relationship edge is created between these guidelines

---

## Questions to Answer Before Implementation

### 1. Does Knowledge Graph Actually Improve Retrieval?
**Method:** A/B testing with sample queries
- Test 50 Dutch queries with and without KG
- Measure relevance, precision, recall
- Compare results with current vector + full-text approach

**Success Criteria:** KG must show >10% improvement in retrieval quality to justify cost/complexity

### 2. What's the Update Frequency?
- Daily updates: 42 minutes (current pipeline) vs 52-78 hours (with KG) = impractical
- Monthly updates: 52-78 hours one-time cost = more acceptable
- Incremental updates: Only process changed/new documents = investigate

### 3. Can We Optimize Performance?
**Potential Optimizations:**
1. **Parallel Processing:** 3-5x faster (process multiple episodes simultaneously)
2. **Faster LLM:** Switch to `gpt-3.5-turbo` for entity extraction (2x faster, lower quality)
3. **Batch Operations:** 1.5-2x faster (create multiple episodes per Graphiti call)
4. **Cached Entity Extraction:** Reuse entities across similar guidelines
5. **Pattern Matching:** Use regex for common entities instead of LLM (10x+ faster)

**Target:** Reduce 52-78 hours to <5 hours through optimizations

### 4. What's the Cost Model?
- One-time build: $83+ acceptable?
- Ongoing maintenance: $5-10/month for updates?
- Alternative models: Smaller LLM, cached results, pattern-based extraction?

---

## Technical Approach (When Implemented)

### Architecture

```
documents/notion_guidelines/*.md (87 files)
    ↓
ingestion/ingest.py (without --fast flag)
    ↓
Graph Builder (Graphiti + Neo4j)
    ↓
    ├─→ Entity Extraction (LLM: extract people, orgs, regulations)
    ├─→ Relationship Detection (LLM: find connections between entities)
    ├─→ Episode Creation (Graphiti: create nodes and edges)
    └─→ Neo4j Storage (graph database)
    ↓
Hybrid Retrieval (vector + full-text + graph)
```

### Components

**Already Exists:**
- `agent/graph_utils.py` - Graph initialization and search
- `ingestion/graph_builder.py` - Graphiti integration
- Neo4j 5.26.1 container in Docker Compose
- Graphiti client configured

**Needs Implementation:**
1. **Optimized Entity Extraction** - Faster, cheaper entity extraction
2. **Incremental Updates** - Only process new/changed documents
3. **Graph-Aware Retrieval** - Combine graph relationships with vector search
4. **A/B Testing Framework** - Compare retrieval with/without graph

### Data Flow

**Current (FEAT-002):**
```
Markdown → Chunks → Embeddings → PostgreSQL → Search Results
```

**With Knowledge Graph (FEAT-006):**
```
Markdown → Chunks → Embeddings → PostgreSQL ┐
                                              ├→ Combined Results
Markdown → Episodes → Entities → Neo4j ──────┘
```

---

## Success Criteria (When Implemented)

### Functional Requirements
- ✅ Knowledge graph builds successfully for all 87 guidelines
- ✅ Entities extracted for people, organizations, regulations, topics
- ✅ Relationships detected between related guidelines
- ✅ Graph-aware search returns relevant results
- ✅ "Related guidelines" feature working

### Performance Requirements
- ✅ Build time < 5 hours (with optimizations)
- ✅ Update time < 1 hour for incremental changes
- ✅ Search latency < 2 seconds (including graph queries)

### Quality Requirements
- ✅ A/B testing shows >10% improvement in retrieval quality
- ✅ Entity extraction accuracy >85%
- ✅ Relationship detection accuracy >80%

### Cost Requirements
- ✅ One-time build cost < $50
- ✅ Monthly maintenance cost < $10

---

## Out of Scope (Phase 6)

### Not Included in Initial Implementation
- ❌ Real-time graph updates (will use batch processing)
- ❌ Graph visualization UI (future FEAT-007)
- ❌ Complex reasoning over graph (future enhancement)
- ❌ Multi-hop relationship queries (start with single-hop)

---

## Dependencies

**Prerequisites:**
- ✅ FEAT-002 complete (87 guidelines ingested)
- ✅ Neo4j container running
- ✅ Graphiti client configured
- ⏳ A/B testing framework (need to build)
- ⏳ Performance optimizations (need to implement)

**Blocked By:**
- None (can start when prioritized)

**Blocks:**
- FEAT-007: Graph Visualization (if implemented)

---

## Timeline (When Prioritized)

**Estimated Effort:** 24-32 hours (including optimizations and A/B testing)

**Phase 1: Validation (8 hours)**
- Research optimization strategies
- Implement A/B testing framework
- Run retrieval quality tests
- **Decision point:** Proceed only if KG shows >10% improvement

**Phase 2: Optimization (12 hours)**
- Implement parallel processing
- Optimize entity extraction (caching, patterns)
- Implement incremental updates
- Reduce build time to <5 hours

**Phase 3: Integration (8 hours)**
- Implement graph-aware retrieval
- Add "related guidelines" feature
- Update search tools to use graph
- Validate performance and quality

**Phase 4: Documentation (4 hours)**
- Update architecture docs
- Document optimization strategies
- Create maintenance guide

---

## Risks & Mitigation

### Risk 1: Knowledge Graph Doesn't Improve Retrieval
- **Impact:** High (wasted effort)
- **Likelihood:** Medium (unproven benefit)
- **Mitigation:** A/B testing BEFORE full implementation (Phase 1)

### Risk 2: Performance Optimizations Insufficient
- **Impact:** Medium (still too slow for practical use)
- **Likelihood:** Low (multiple optimization strategies available)
- **Mitigation:** Test optimizations on subset before full build

### Risk 3: Cost Still Too High
- **Impact:** Medium (budget constraints)
- **Likelihood:** Low (can reduce via optimizations)
- **Mitigation:** Use cheaper LLM, cached extraction, pattern matching

### Risk 4: Maintenance Burden
- **Impact:** Medium (ongoing time/cost)
- **Likelihood:** Medium (87 guidelines may update frequently)
- **Mitigation:** Implement incremental updates, automated monitoring

---

## References

- **FEAT-002 Exploration:** `docs/features/FEAT-002_notion-integration/exploration/README.md`
- **Knowledge Graph Analysis:** `docs/features/FEAT-002_notion-integration/exploration/KNOWLEDGE_GRAPH_ANALYSIS.md`
- **Graph Utils:** `agent/graph_utils.py`
- **Graph Builder:** `ingestion/graph_builder.py`
- **Graphiti Docs:** https://github.com/getzep/graphiti
- **Neo4j Docs:** https://neo4j.com/docs/

---

## Open Questions

1. **Retrieval Quality:** Does KG actually improve results? (A/B test needed)
2. **Update Frequency:** How often do guidelines change? (Ask EVI 360 team)
3. **Entity Types:** What entities matter most? (regulations, conditions, organizations, products?)
4. **Relationship Types:** What relationships to capture? (references, related_to, requires, supersedes?)
5. **Cost Budget:** What's acceptable one-time and ongoing cost?

---

## Recommendation

**Status:** ⏸️ **DEFER** until:
1. FEAT-003 (Query & Retrieval) complete
2. FEAT-004 (Product Catalog) complete
3. FEAT-005 (Multi-Agent System) complete
4. We have baseline retrieval quality metrics
5. We can justify >10% improvement via A/B testing

**Rationale:**
- Current vector + full-text search meets FEAT-002 requirements
- Focus on delivering user-facing features first (search, products, agents)
- Revisit when we have baseline metrics and can prove KG value

**Decision Point:** Review in Phase 5 after Multi-Agent System is complete.

---

**Next Steps:**
1. Complete FEAT-003, FEAT-004, FEAT-005 first
2. Establish baseline retrieval quality metrics
3. Design A/B testing framework
4. Run retrieval quality experiments
5. Only proceed with FEAT-006 if experiments show >10% improvement

---

**Status:** 📋 Planned - Awaiting prioritization
**Created:** 2025-10-26
**Target:** Phase 6 (post-FEAT-005)
