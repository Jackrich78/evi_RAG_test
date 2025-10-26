# PRD: FEAT-009 - Tier-Aware Search Strategy

**Feature ID:** FEAT-009
**Phase:** 9 (Optimization) - **FUTURE FEATURE**
**Status:** 📋 Planned (Post-MVP)
**Priority:** Low
**Owner:** TBD
**Dependencies:** FEAT-003 (MVP must prove tiers are needed)
**Created:** 2025-10-26
**Last Updated:** 2025-10-26

---

## ⚠️ MVP Status: DESCOPED - Tier Column Unused

**This feature is NOT part of the MVP (FEAT-003).** All 10,833 chunks have `tier = NULL`. MVP searches all content without tier filtering.

**Why Descoped:**
- Tier column exists but was never populated during FEAT-002 ingestion
- MVP must first prove whether tier-aware search improves quality
- Adding tier logic increases complexity without validated benefit
- Simple vector/hybrid search may be sufficient

**Current State:**
- `chunks.tier` column: Exists, all NULL
- `search_guidelines_by_tier()` SQL function: Exists but unused
- Hybrid search: Returns all chunks regardless of tier
- Specialist agent: No tier strategy

**When to Implement:** After FEAT-003 MVP testing reveals that:
1. Responses are too verbose (need Tier 1/2 summaries first)
2. Users want progressive disclosure (summary → details)
3. Response time is slow (tier filtering could improve performance)

---

## Problem Statement

Dutch workplace safety guidelines have a natural 3-tier hierarchy:
- **Tier 1: Samenvatting** (Summary) - 1-2 sentence overviews
- **Tier 2: Kernfacten** (Key Facts) - 3-5 essential points
- **Tier 3: Details** (Full Content) - Complete technical documentation

**Hypothesis:** Tier-aware search could improve response quality by:
1. **Faster answers**: Tier 1/2 returns quicker than full-text search
2. **Progressive disclosure**: Show summary first, details on request
3. **Better UX**: "Quick answer" vs "Deep dive" search modes

**Challenge:** Unknown if tiers actually improve quality. MVP must validate this hypothesis before investing in tier population and search logic.

---

## Goals

1. **Populate Tier Column**: Re-process 10,833 chunks to detect tier from content/metadata
2. **Tier-Aware Search**: Enable `search_guidelines_by_tier()` SQL function
3. **Query Complexity Detection**: Auto-select tier strategy based on query
4. **Progressive Disclosure**: "Quick summary" button shows Tier 1/2, "Full details" shows all tiers
5. **Performance Optimization**: Tier 1/2 search <1 second (faster than all-tier search)

---

## User Stories

### Story 1: Quick Summary Search

**As a** specialist who needs a quick answer
**I want** to search only Tier 1 and Tier 2 content
**So that** I get a fast response without unnecessary details

**Acceptance Criteria:**
- [ ] Query: "Wat zijn de vereisten voor werken op hoogte?" (simple query)
- [ ] System detects query complexity = simple
- [ ] Search only Tier 1 + Tier 2 chunks
- [ ] Response time <1 second
- [ ] Response is concise (2-3 sentences + key facts)

### Story 2: Detailed Technical Search

**As a** specialist researching specific standards
**I want** to search all tiers including detailed technical content
**So that** I get comprehensive information

**Acceptance Criteria:**
- [ ] Query: "Welke specifieke EN normen gelden voor valbeveiliging EN 361?" (complex query)
- [ ] System detects query complexity = detailed
- [ ] Search all tiers (1, 2, 3)
- [ ] Response includes technical specifications
- [ ] Response cites Tier 3 chunks with standards

### Story 3: Progressive Disclosure

**As a** specialist who wants control over detail level
**I want** buttons for "Quick answer" and "Full details"
**So that** I can choose the appropriate level of information

**Acceptance Criteria:**
- [ ] UI shows two buttons: "Snel antwoord" and "Volledig antwoord"
- [ ] "Snel antwoord": Searches Tier 1+2, fast response
- [ ] "Volledig antwoord": Searches all tiers, comprehensive response
- [ ] User can switch between modes mid-conversation

---

## Scope

### In Scope ✅

**Tier Population:**
- Re-process 10,833 chunks to detect tier
- Strategy 1: Detect from chunk metadata (if Notion export had tier markers)
- Strategy 2: Use chunk_index as proxy (first chunks = summary, later = details)
- Strategy 3: GPT-4 classification (expensive: $50+ for full dataset)
- Update `chunks.tier` column (1, 2, or 3)

**Query Complexity Detection:**
- Heuristic: Query length + specific keywords
- Simple (Tier 1+2): ≤5 words, no technical terms
- Detailed (All tiers): >5 words, mentions "specifiek", "technisch", "norm", "EN", "ISO"
- Moderate (Tier 2+3): Everything else

**Tier-Aware Search Function:**
- Use existing `search_guidelines_by_tier()` SQL function
- Modify `hybrid_search_tool` to accept `tier_filter` parameter
- Specialist agent calls with appropriate tier based on query

**Performance Optimization:**
- Tier 1+2 search uses smaller index (fewer chunks)
- Should be 30-50% faster than all-tier search
- Measure and document performance gains

### Out of Scope ❌

**Not included in v1:**
- User-configurable tier preferences
- Tier learning (ML to predict optimal tier for user)
- Tier visualization in UI (showing which tier chunks came from)
- Cross-tier summarization (combining Tier 1 + Tier 3 into new summary)

---

## Architecture

```
User Query: "werken op hoogte"
    ↓
Query Complexity Detector
    ├─ Simple → tier_filter=[1, 2]
    ├─ Moderate → tier_filter=[2, 3]
    └─ Detailed → tier_filter=None (all)
    ↓
hybrid_search_tool(query, tier_filter)
    ↓
PostgreSQL: search_guidelines_by_tier()
    ↓
Returns filtered chunks
    ↓
Specialist Agent synthesizes response
```

---

## Technical Notes

### Tier Population Strategies

**Strategy 1: Metadata-Based (If Available)**
```python
# Check if Notion export included tier markers
chunk_metadata = {
    "notion_block_type": "callout",  # Tier 1 = callout blocks?
    "heading_level": 2,               # Tier 2 = H2 headings?
    "content_type": "paragraph"       # Tier 3 = regular paragraphs?
}
```

**Strategy 2: Chunk Index Heuristic**
```python
# First 1-2 chunks = Tier 1 (summary)
# Next 3-5 chunks = Tier 2 (key facts)
# Remaining chunks = Tier 3 (details)

for doc in documents:
    chunks = get_chunks(doc.id, order_by="chunk_index")
    for i, chunk in enumerate(chunks):
        if i < 2:
            chunk.tier = 1
        elif i < 7:
            chunk.tier = 2
        else:
            chunk.tier = 3
```

**Strategy 3: GPT-4 Classification (Expensive)**
```python
async def classify_tier(content: str) -> int:
    """Classify chunk tier using GPT-4."""
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": "Classify this Dutch safety guideline chunk as:\n1 = Summary (1-2 sentences)\n2 = Key Facts (3-5 points)\n3 = Detailed Content\nRespond with only the number."
        }, {
            "role": "user",
            "content": content[:500]  # First 500 chars
        }]
    )
    return int(response.choices[0].message.content)
```

### Query Complexity Detection

```python
def detect_query_complexity(query: str) -> str:
    """
    Detect query complexity to determine tier strategy.

    Returns: "simple", "moderate", or "detailed"
    """
    query_lower = query.lower()
    word_count = len(query.split())

    # Detailed indicators
    detailed_keywords = ["specifiek", "technisch", "norm", "en ", "iso ", "ce "]
    if any(kw in query_lower for kw in detailed_keywords):
        return "detailed"

    # Simple indicators
    if word_count <= 5:
        return "simple"

    # Default to moderate
    return "moderate"


def get_tier_filter(complexity: str) -> Optional[List[int]]:
    """
    Map complexity to tier filter.

    Returns: [1, 2] for simple, [2, 3] for moderate, None for detailed (all tiers)
    """
    if complexity == "simple":
        return [1, 2]
    elif complexity == "moderate":
        return [2, 3]
    else:
        return None  # Search all tiers
```

---

## Implementation Plan

### Phase 1: Tier Population (4-6 hours)

**Option A: Chunk Index Heuristic (Fast)**
```bash
# Run SQL script to update tiers
PGPASSWORD=postgres psql -h localhost -U postgres -d evi_rag << EOF
WITH ranked_chunks AS (
  SELECT id, document_id, chunk_index,
    ROW_NUMBER() OVER (PARTITION BY document_id ORDER BY chunk_index) as rank,
    COUNT(*) OVER (PARTITION BY document_id) as total_chunks
  FROM chunks
)
UPDATE chunks c
SET tier = CASE
  WHEN rc.rank <= 2 THEN 1
  WHEN rc.rank <= 7 THEN 2
  ELSE 3
END
FROM ranked_chunks rc
WHERE c.id = rc.id;
EOF
```

**Option B: GPT-4 Classification (Slow, Expensive)**
```python
# Run classification script
python3 scripts/classify_tiers.py
# Processes 10,833 chunks at ~$0.005 each = ~$50 total
# Takes 6-8 hours with rate limiting
```

**Validation:**
```sql
-- Check tier distribution
SELECT tier, COUNT(*) FROM chunks GROUP BY tier;
-- Expected: Tier 1 (~15%), Tier 2 (~35%), Tier 3 (~50%)
```

### Phase 2: Modify Search Tools (2 hours)

**File: `agent/tools.py` (MODIFY)**

Update `hybrid_search_tool`:
```python
async def hybrid_search_tool(input_data: HybridSearchInput, tier_filter: Optional[List[int]] = None):
    """
    Hybrid search with optional tier filtering.

    Args:
        input_data: Search parameters
        tier_filter: List of tiers to search (e.g., [1, 2]) or None for all
    """
    # Generate embedding
    embedding = await generate_embedding(input_data.query)

    # Call database with tier filter
    results = await hybrid_search(
        embedding=embedding,
        query_text=input_data.query,
        limit=input_data.limit,
        text_weight=input_data.text_weight,
        tier_filter=tier_filter  # NEW parameter
    )

    return results
```

**File: `agent/db_utils.py` (MODIFY)**

Update `hybrid_search` function signature to accept tier_filter, pass to SQL function.

### Phase 3: Add Complexity Detection (1 hour)

**File: `agent/specialist_agent.py` (MODIFY)**

Update `search_guidelines` tool:
```python
@specialist_agent.tool
async def search_guidelines(ctx, query: str, limit: int = 10):
    """Search with automatic tier selection."""

    # Detect query complexity
    complexity = detect_query_complexity(query)

    # Map to tier filter
    tier_filter = get_tier_filter(complexity)

    logger.info(f"Query complexity: {complexity}, tier_filter: {tier_filter}")

    # Call hybrid search with tier filter
    results = await hybrid_search_tool(
        HybridSearchInput(query=query, limit=limit),
        tier_filter=tier_filter
    )

    return results
```

### Phase 4: Testing & Validation (2-3 hours)

**Test Queries:**
1. "werken op hoogte" (simple → Tier 1+2)
2. "specifieke EN 361 normen valbeveiliging" (detailed → All tiers)
3. "rugklachten preventie" (moderate → Tier 2+3)

**Validation:**
- Measure response time (Tier 1+2 vs All)
- Check result relevance (are Tier 1/2 sufficient for simple queries?)
- Validate tier distribution in results

---

## Success Criteria

**Tier Population:**
- ✅ All 10,833 chunks have tier assigned (1, 2, or 3)
- ✅ Tier distribution is reasonable (~15% Tier 1, ~35% Tier 2, ~50% Tier 3)
- ✅ Spot-check 20 random chunks: tier assignment makes sense

**Performance:**
- ✅ Tier 1+2 search is 30-50% faster than all-tier search
- ✅ Simple queries return <1 second (95th percentile)
- ✅ Detailed queries maintain <3 second target

**Quality:**
- ✅ Tier 1+2 results are sufficient for 80% of simple queries
- ✅ No loss in relevance for complex queries (all-tier search)
- ✅ Users prefer tier-aware search in A/B testing (if applicable)

---

## Dependencies

### Infrastructure
- ✅ `chunks.tier` column exists (currently NULL)
- ✅ `search_guidelines_by_tier()` SQL function exists
- ⏳ Tier population (must be done first)

### Research
- ⏳ FEAT-003 MVP testing must show tiers are beneficial
- ⏳ Validate that tier filtering doesn't harm result quality

---

## References

**Code:**
- SQL function: `sql/evi_schema_additions.sql` (`search_guidelines_by_tier`)
- Hybrid search: `agent/tools.py` (needs tier_filter parameter)
- Database utils: `agent/db_utils.py` (needs tier_filter parameter)

**Documentation:**
- FEAT-002: Notion Integration (tier column created but not populated)
- FEAT-003: MVP Specialist Agent (current stateless implementation)

---

**Last Updated:** 2025-10-26
**Status:** 📋 Planned (Post-MVP)
**Estimated Effort:** 8-12 hours (tier population + search modifications + testing)
**Risk Level:** Medium (tier population strategy uncertain, quality impact unknown)
**Decision Point:** Only implement if FEAT-003 MVP testing shows clear need for tier filtering
