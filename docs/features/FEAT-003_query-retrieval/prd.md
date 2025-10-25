# PRD: FEAT-003 - Query & Retrieval System

**Feature ID:** FEAT-003
**Phase:** 3 (Search & Retrieval)
**Status:** ⏳ Planned
**Priority:** High
**Owner:** TBD

---

## Problem Statement

Enable Dutch-language queries against the ingested knowledge base with tier-aware hybrid search. Users need fast, relevant results that prioritize summaries (Tier 1) and key facts (Tier 2) before diving into full details (Tier 3).

**Challenge:** Balance speed vs. comprehensiveness. Quick queries should return Tier 1/2 results in <1 second. Deep dives should access Tier 3 when needed.

---

## Goals

1. **Dutch Query Support:** Accept queries in Dutch and match against Dutch full-text search
2. **Tier-Aware Search:** Prioritize Tier 1 → Tier 2 → Tier 3 based on query complexity
3. **Hybrid Search:** Combine vector similarity (semantic) + full-text (keyword matching)
4. **Fast Response:** Return Tier 1/2 results in <1 second
5. **CLI Interface:** Simple command-line tool for testing queries

---

## User Stories

### Quick Summary Search
**Given** I query "werken op hoogte vereisten"
**When** The system searches Tier 1 and Tier 2
**Then** I get 3-5 summary chunks in <1 second with Dutch content

### Deep Detail Search
**Given** I query "specifieke veiligheidsnormen voor valbeveiliging EN 361"
**When** The system detects complexity and searches all tiers
**Then** I get detailed Tier 3 chunks with technical specifications

### Dutch Language Matching
**Given** I use Dutch safety terminology (e.g., "persoonlijke beschermingsmiddelen")
**When** Full-text search processes the query
**Then** Dutch stemming and stop words are applied correctly

### Hybrid Search Quality
**Given** A query like "hoofdletsel preventie"
**When** Hybrid search combines vector + full-text
**Then** Results include both semantically similar ("hersenschudding") and exact matches ("hoofdletsel")

---

## Scope

### In Scope ✅
- **Search Tools** (`agent/search_tools.py`):
  - `search_tier_1()` - Search summaries only
  - `search_tier_2()` - Search key facts only
  - `search_tier_3()` - Search full details
  - `search_all_tiers()` - Search across all tiers with tier prioritization
  - All tools use `search_guidelines_by_tier()` SQL function

- **Query Processing** (`agent/query_processor.py`):
  - Detect query complexity (simple vs. detailed)
  - Generate query embedding (OpenAI text-embedding-3-small)
  - Select appropriate tier strategy

- **CLI Interface** (extend `cli.py`):
  - Command: `python3 cli.py search "Dutch query"`
  - Options: `--tier 1|2|3|all`, `--limit N`, `--method vector|hybrid`
  - Output: Display chunks with metadata (tier, source, similarity score)

- **Result Formatting**:
  - Show chunk content (truncated if long)
  - Display tier badge (Tier 1 / Tier 2 / Tier 3)
  - Show similarity score and document source
  - Highlight matched keywords (Dutch full-text)

### Out of Scope ❌
- Multi-agent response generation (deferred to FEAT-005)
- Streaming search results
- Search history or saved queries
- Advanced filters (date, source, compliance tags)
- Product search (deferred to FEAT-004)

---

## Success Criteria

**Search Performance:**
- ✅ Tier 1/2 search returns results in <1 second (95th percentile)
- ✅ All-tier search returns results in <3 seconds (95th percentile)
- ✅ Dutch full-text search correctly stems Dutch words (e.g., "werken" → "werk")

**Search Quality:**
- ✅ Top 5 results include at least 3 relevant chunks for test queries
- ✅ Hybrid search outperforms vector-only search by >15% (F1 score)
- ✅ Tier prioritization: Tier 1 chunks ranked higher than Tier 3 for same similarity score

**CLI Usability:**
- ✅ CLI accepts Dutch queries without encoding issues
- ✅ Output formatted clearly with chunk content, tier, and score
- ✅ `--tier` flag correctly filters results

---

## Dependencies

**Infrastructure:**
- ✅ PostgreSQL 17 + pgvector with `search_guidelines_by_tier()` function (FEAT-001)

**Data:**
- Notion guidelines ingested with tier metadata (FEAT-002)

**External Services:**
- OpenAI API key for query embeddings

---

## Technical Notes

**Hybrid Search Formula:**
```sql
combined_score = (vector_similarity * 0.7) + (text_rank * 0.3)
```

**Tier Prioritization:**
```sql
ORDER BY
  tier ASC,              -- Tier 1 first, then 2, then 3
  combined_score DESC    -- Within each tier, sort by relevance
```

**Dutch Full-Text Configuration:**
```sql
to_tsvector('dutch', content)
plainto_tsquery('dutch', query_text)
```

**Query Complexity Detection:**
```python
def detect_complexity(query: str) -> str:
    """Simple heuristic: length + specific keywords."""
    if len(query.split()) <= 5:
        return "simple"  # Search Tier 1+2
    elif any(word in query.lower() for word in ["specifiek", "technisch", "norm", "en ", "iso "]):
        return "detailed"  # Search all tiers
    else:
        return "moderate"  # Search Tier 2+3
```

---

## Implementation Plan

### Step 1: Search Tools (4-6 hours)
**File:** `agent/search_tools.py`

```python
async def search_tier(
    query: str,
    tier_filter: Optional[int] = None,
    limit: int = 10
) -> List[SearchResult]:
    """Search guidelines with tier filtering."""

    # Generate query embedding
    embedding = await embedder.embed_query(query)

    # Call SQL function
    results = await db.fetch(
        "SELECT * FROM search_guidelines_by_tier($1, $2, $3, $4)",
        embedding, query, tier_filter, limit
    )

    return [SearchResult(**row) for row in results]
```

### Step 2: Query Processor (2-3 hours)
**File:** `agent/query_processor.py`

Detect complexity and select tier strategy.

### Step 3: CLI Extension (3-4 hours)
**Extend:** `cli.py`

Add `search` subcommand with click framework.

### Step 4: Testing (3-4 hours)
- Unit tests for query complexity detection
- Integration tests with sample Dutch queries
- Benchmark search performance (Tier 1/2 vs. all tiers)

---

## Testing Strategy

**Test Queries (Dutch):**
1. "werken op hoogte" (simple, Tier 1+2)
2. "persoonlijke beschermingsmiddelen vereisten" (moderate, Tier 2+3)
3. "specifieke veiligheidsnormen EN 361 valbeveiliging" (detailed, all tiers)
4. "rugklachten preventie werkplek" (simple, Tier 1+2)
5. "geluidsniveau maximaal toegestaan ARBO" (detailed, all tiers)

**Validation:**
- For each query, verify:
  - Results are in Dutch
  - Tier filtering works correctly
  - Response time meets criteria
  - Top 5 results are relevant

---

## Next Steps

1. Implement search tools using existing SQL functions
2. Add query complexity detection logic
3. Extend CLI with `search` subcommand
4. Test with 10-20 sample Dutch queries
5. Benchmark performance (measure response times)
6. Validate Dutch full-text search accuracy

---

**Last Updated:** 2025-10-25
**Status:** ⏳ Ready to Plan
**Estimated Effort:** 12-17 hours
