# PRD: FEAT-012 - Two-Stage Search Protocol & Product-Guideline Linking

**Feature ID:** FEAT-012
**Feature Name:** Two-Stage Search Protocol & Product-Guideline Linking
**Status:** Planned
**Priority:** High
**Created:** 2025-11-03
**Dependencies:**
- FEAT-004 (Product Catalog Core) - **BLOCKING**
- FEAT-011 (Interventie Wijzer) - **HIGHLY RECOMMENDED** for optimal quality

---

## Executive Summary

Implement a sophisticated two-stage search protocol that combines fast vector retrieval (Stage 1) with LLM-powered contextual ranking (Stage 2) to deliver highly relevant product recommendations. Additionally, link products to relevant Dutch workplace safety guidelines at search time, providing comprehensive recommendations with citations and URLs.

**Value Proposition:** Transforms basic similarity search into intelligent, context-aware recommendations that match the quality of expert human intervention specialists.

---

## Background & Context

### Current State (FEAT-004 + FEAT-011)

**FEAT-004 provides:**
- Basic vector similarity search
- Product ingestion from Notion + web scraping
- Simple agent tool returning top N products

**FEAT-011 provides (if complete):**
- Interventie wijzer enrichment (33 problem-intervention mappings from CSV)
- Methodology framework (5-step decision process from Interventiewijzer.md)
- Query expansion with wijzer keywords (Probleem → Soort interventie)
- Product metadata enrichment (interventie_keywords, probleem_keywords)
- Metadata boosting in search

**Current Limitation:**
- Pure similarity ranking doesn't consider:
  - **Impact on attendance/functioning** (most critical factor)
  - **Fit with role/sector/constraints** (context-specific)
  - **Alignment with Dutch guidelines** (regulatory compliance)
  - **Feasibility & time-to-benefit** (practical considerations)
- No linking between products and relevant guidelines
- No product URLs displayed in recommendations

---

### The Two-Stage Protocol (from Original System Prompt)

The original `intervention_specialist_prompt.md` describes a sophisticated retrieval system:

**Stage 1: Candidate Generation**
- Fast vector search to retrieve top N candidates (N=50)
- Wide net with low similarity threshold
- Optional interventie wijzer boosting if <3 results

**Stage 2: Canonicalization & Ranking**
- LLM evaluates candidates with contextual understanding
- Applies weighted scoring formula:
  - **Impact on attendance/functioning:** 0.4 weight
  - **Fit with role/sector & constraints:** 0.3 weight
  - **Alignment with Dutch guidelines:** 0.2 weight
  - **Feasibility & time-to-benefit:** 0.1 weight
- Returns top K final results (K=3-5)

**Product-Guideline Linking:**
- Products displayed with "Ondersteunende Nederlandse Richtlijnen" section
- Cites 1-2 relevant guideline titles (NVAB, UWV, STECR, Arbowet)
- Product URLs shown in "Details & Boekingsinformatie" line

---

### Why Two-Stage vs Single-Stage?

**Single-Stage (FEAT-004):**
```
Query → Vector Search → Top 3 Products
Latency: ~100ms
Quality: ~70% relevance (similarity only)
```

**Two-Stage (FEAT-012):**
```
Query → Stage 1: Top 50 Candidates (~100ms)
     → Stage 2: LLM Ranking (~1.5s)
     → Top 3-5 Products
Latency: ~1.6s
Quality: ~90% relevance (contextual + similarity)
```

**Trade-off:** 15x slower but 20-30% higher quality recommendations

---

## Goals & Success Metrics

### Goals

1. **Intelligent Ranking:** Product recommendations reflect expert judgment (impact, fit, guidelines, feasibility)
2. **Guideline Integration:** Products linked to relevant Dutch workplace safety guidelines
3. **URL Display:** Product URLs from FEAT-004 web scraping shown in responses
4. **Performance:** Total search latency <2.5s (acceptable for assistant UX)
5. **Edge Case Handling:** Gracefully handle <3 candidates, 0 results, duplicate products

### Success Metrics

| Metric | Baseline (FEAT-004+011) | Target (FEAT-012) | Measurement Method |
|--------|-------------------------|-------------------|-------------------|
| **Recommendation Relevance** | ~85% (with FEAT-011) | ≥90% | Human evaluation on 30 test queries |
| **Guideline Citation Rate** | 0% (no linking) | ≥80% of products | % products with ≥1 guideline cited |
| **URL Display Rate** | 0% (not shown) | 100% | All products include working URL |
| **Stage 1 Latency** | N/A | <100ms | 95th percentile |
| **Stage 2 Latency** | N/A | <2s | 95th percentile |
| **Total Latency** | ~100ms (FEAT-004) | <2.5s | End-to-end search time |
| **Expert Satisfaction** | Baseline | +40% | EVI specialist survey (1-5 scale) |

### Non-Goals (Out of Scope)

- ❌ Real-time guideline updates (use existing chunks from FEAT-002)
- ❌ Explainable AI (why this ranking?) - LLM black box acceptable for MVP
- ❌ User feedback loop (thumbs up/down) - deferred to future
- ❌ A/B testing different scoring weights - use fixed 0.4/0.3/0.2/0.1 for MVP
- ❌ Multi-modal search (images, videos) - text only

---

## User Stories & Use Cases

### User Story 1: Context-Aware Product Ranking

**As an** EVI intervention specialist
**I want** products ranked by their actual impact on the employee's situation
**So that** I recommend the most effective intervention, not just the most similar

**Example:**
- Query: "Werknemer met burn-out klachten, 3 maanden verzuim, kantoorfunctie"
- **Without FEAT-012:** Returns "Burn-out preventie workshop" (high similarity but preventive, not suitable for 3 months verzuim)
- **With FEAT-012:** Returns "Herstelcoaching" (ranked #1 due to high impact on existing burn-out, fit for office role, aligns with NVAB guidelines)

**Acceptance Criteria:**
- Products ranked by contextual appropriateness, not just keyword similarity
- Impact on attendance weighs heavily (0.4) in ranking
- Role/sector fit considered (0.3) in ranking

---

### User Story 2: Guideline-Backed Recommendations

**As an** EVI specialist
**I want** products linked to relevant Dutch workplace safety guidelines
**So that** I can explain recommendations with regulatory backing

**Example:**
- Product: "Herstelcoaching"
- **Without FEAT-012:** No guidelines shown
- **With FEAT-012:** Shows "Ondersteunende Nederlandse Richtlijnen: Wet verbetering poortwachter, NVAB Richtlijn Overspanning en burn-out"

**Acceptance Criteria:**
- ≥80% of products include 1-2 relevant guideline citations
- Guidelines matched from existing `chunks` table (FEAT-002 data)
- Guideline titles formatted clearly (source + title)

---

### User Story 3: One-Click Product Access

**As an** EVI specialist
**I want** direct URLs to product pages on portal.evi360.nl
**So that** I can immediately book or learn more without manual searching

**Example:**
- Product: "Bedrijfsfysiotherapie"
- **Without FEAT-012:** No URL shown
- **With FEAT-012:** Shows "[https://portal.evi360.nl/products/12]"

**Acceptance Criteria:**
- 100% of products display working URLs (from FEAT-004 scraping)
- URLs formatted consistently (markdown link)
- Broken URLs logged and reported

---

## Technical Architecture

### Stage 1: Candidate Generation (Vector Search)

**Purpose:** Fast retrieval of potentially relevant products

**Implementation:**
```python
async def stage1_candidate_generation(
    query: str,
    limit: int = 50,
    similarity_threshold: float = 0.5
) -> List[ProductSearchResult]:
    """
    Stage 1: Cast wide net with vector similarity search.

    Args:
        query: User query (Dutch language)
        limit: Max candidates to retrieve (default 50)
        similarity_threshold: Min similarity score (default 0.5)

    Returns:
        List of product search results with similarity scores
    """
    # Generate embedding for query
    query_embedding = await generate_embedding(query)

    # Call PostgreSQL search_products() function
    results = await db.execute(
        "SELECT * FROM search_products($1, $2, $3, $4)",
        query_embedding,
        query,
        limit,
        similarity_threshold
    )

    return [ProductSearchResult.from_db_row(row) for row in results]
```

**Performance Target:** <100ms (95th percentile)

**Optimization:**
- Use pgvector IVFFLAT index (already exists from FEAT-004)
- Limit=50 keeps search fast while providing LLM enough options
- Low threshold (0.5) allows borderline matches through to Stage 2

---

### Stage 2: LLM Contextual Ranking

**Purpose:** Evaluate candidates with human-like judgment

**Implementation:**
```python
async def stage2_llm_ranking(
    query: str,
    candidates: List[ProductSearchResult],
    query_context: Dict[str, Any],
    top_k: int = 3
) -> List[ProductRecommendation]:
    """
    Stage 2: LLM evaluates candidates and ranks by contextual appropriateness.

    Args:
        query: Original user query
        candidates: Products from Stage 1
        query_context: Extracted context (role, sector, severity, duration)
        top_k: Number of final recommendations (default 3)

    Returns:
        List of product recommendations with reasoning and guideline links
    """
    # Build LLM prompt with ranking instructions
    prompt = f"""
Je bent een EVI 360 interventie specialist. Beoordeel deze producten voor de volgende situatie:

**Situatie:** {query}
**Context:**
- Rol: {query_context.get('role', 'Onbekend')}
- Sector: {query_context.get('sector', 'Onbekend')}
- Ernst: {query_context.get('severity', 'Matig')}
- Duur: {query_context.get('duration', 'Onbekend')}

**Kandidaat Producten:**
{format_candidates_for_llm(candidates)}

**Rankingscriteria (gewogen):**
1. Impact op aanwezigheid/functioneren (40%)
   - Hoe effectief lost dit product het probleem op?
   - Vermindert het verzuim of verbetert het werkprestaties?

2. Fit met rol/sector & beperkingen (30%)
   - Past dit bij het werktype (fysiek/mentaal/management)?
   - Is dit haalbaar binnen de organisatiecontext?

3. Aansluiting bij Nederlandse richtlijnen (20%)
   - Voldoet dit aan Arbowet/NVAB/UWV richtlijnen?
   - Is dit best practice volgens guidelines?

4. Haalbaarheid & time-to-benefit (10%)
   - Hoe snel kan dit ingezet worden?
   - Wat is de tijdsinvestering voor werknemer/werkgever?

**Interventie Wijzer Methodology (indien FEAT-011 compleet):**
Pas de 5-stappen interventiewijzer toe bij je beoordeling:

Stap 1 - Aanleiding: Is er sprake van (dreigend) langdurig verzuim?
Stap 2 - Situatieschets: Is het beeld van functiebelasting en belastbaarheid compleet?
Stap 3 - Indicatie: Welke interventie bekort verzuim het meest (gebruik interventiematrix)?
Stap 4 - Evidence-based: Is de gekozen interventie evidence-based en relevant voor re-integratie?
Stap 5 - Organiseer: Producten via portal.evi360.nl

**Interventiematrix Context:**
{format_interventie_wijzer_context(query)}
# Returns: Matching entries from 33-entry CSV
# Example: "burn-out" → "Multidisciplinaire burnout aanpak" (Category: Verbetering belastbaarheid)

**Output Format (JSON):**
{{
  "recommendations": [
    {{
      "product_id": "<uuid>",
      "rank": 1,
      "relevance_score": 0.95,
      "reasoning": "Kort (1-2 zinnen) waarom dit product #1 is",
      "impact_score": 0.9,
      "fit_score": 0.85,
      "guideline_alignment_score": 0.8,
      "feasibility_score": 0.9,
      "relevant_guidelines": ["NVAB Richtlijn Overspanning en burn-out", "Wet verbetering poortwachter"]
    }},
    ...
  ]
}}

Geef exact {top_k} aanbevelingen, gerangschikt van meest naar minst geschikt.
"""

    # Call LLM (GPT-4 or Claude for Dutch language quality)
    llm_response = await llm_client.complete(prompt, response_format="json")

    # Parse JSON and create ProductRecommendation objects
    recommendations = []
    for rec in llm_response['recommendations']:
        product = find_product_by_id(candidates, rec['product_id'])
        recommendations.append(ProductRecommendation(
            product=product,
            relevance_score=rec['relevance_score'],
            reasoning=rec['reasoning'],
            guideline_citations=rec['relevant_guidelines']
        ))

    return recommendations
```

**Performance Target:** <2s (95th percentile)

**Optimization:**
- Use streaming LLM response (start rendering while LLM generates)
- Cache common query patterns (optional, Phase 2)
- Use smaller model for simpler queries (optional, Phase 2)

---

### Product-Guideline Linking Logic

**Purpose:** Link products to relevant guidelines from `chunks` table

**Implementation:**
```python
async def link_products_to_guidelines(
    products: List[ProductRecommendation],
    query: str
) -> List[ProductRecommendation]:
    """
    For each product, find 1-2 relevant guidelines from chunks table.

    Matching Strategy:
    1. Semantic similarity (product description ↔ guideline summary)
    2. Category matching (product.category ↔ guideline topic)
    3. Keyword overlap (product interventie_keywords ↔ guideline content)

    Args:
        products: List of products to link
        query: Original user query (provides context)

    Returns:
        Products with guideline_citations populated
    """
    for product in products:
        # Option A: Semantic similarity (recommended)
        # Embed product description, search chunks table for top 2 matches
        product_embedding = await generate_embedding(
            f"{product.name} {product.description}"
        )
        guideline_results = await db.search_guidelines(
            embedding=product_embedding,
            query=product.name,
            limit=5
        )

        # Filter to guidelines with high relevance (>0.7 similarity)
        relevant_guidelines = [
            g for g in guideline_results
            if g.similarity_score > 0.7
        ][:2]  # Top 2 only

        product.guideline_citations = [
            f"{g.document_source} - {g.document_title}"
            for g in relevant_guidelines
        ]

    return products
```

**Alternative (Simpler):** Let LLM handle guideline linking in Stage 2
- LLM has context of both products and guidelines (via RAG context)
- LLM can use domain knowledge to link appropriately
- **Advantage:** No separate linking logic needed
- **Disadvantage:** Relies on LLM retrieval, may miss some guidelines

**Recommendation:** Let LLM handle linking in Stage 2 prompt (simpler for MVP)

---

### Canonicalization & Deduplication

**Purpose:** Handle duplicate products with different variants

**Implementation:**
```python
def canonicalize_products(
    candidates: List[ProductSearchResult]
) -> List[ProductSearchResult]:
    """
    Deduplicate and normalize product candidates.

    Rules:
    1. Deduplicate by product_id (exact matches)
    2. Normalize product names (lowercase, trim)
    3. Merge similar products (fuzzy match ≥0.9)
    4. Keep highest similarity score for duplicates

    Args:
        candidates: Raw candidates from Stage 1

    Returns:
        Deduplicated and normalized candidates
    """
    seen_ids = set()
    canonical = []

    for product in candidates:
        if product.id in seen_ids:
            continue  # Skip exact duplicate

        # Check for fuzzy duplicates (name similarity ≥0.9)
        is_duplicate = False
        for canon in canonical:
            if fuzzy_match(product.name, canon.name) >= 0.9:
                # Merge: keep product with higher similarity
                if product.similarity_score > canon.similarity_score:
                    canonical.remove(canon)
                    canonical.append(product)
                is_duplicate = True
                break

        if not is_duplicate:
            canonical.append(product)
            seen_ids.add(product.id)

    return canonical
```

**When to Run:** After Stage 1, before Stage 2
- Reduces LLM input size (fewer duplicates)
- Improves ranking quality (LLM sees distinct options)

---

### Edge Case Handling

#### Edge Case 1: < 3 Candidates from Stage 1

**Scenario:** Query very specific or niche, Stage 1 returns 0-2 products

**Handling:**
```python
if len(candidates) < 3:
    # Expand search with interventie wijzer boosting (FEAT-011)
    if interventie_wijzer_available:
        wijzer_keywords = match_query_to_wijzer(query)
        expanded_query = f"{query} {' '.join(wijzer_keywords)}"
        candidates = await stage1_candidate_generation(
            expanded_query,
            limit=50,
            similarity_threshold=0.3  # Lower threshold
        )

    # If still < 3, return what we have with note
    if len(candidates) < 3:
        return {
            "products": candidates,
            "note": "Minder dan 3 relevante opties gevonden in product catalogus. Overweeg bredere zoektermen of neem contact op met EVI specialist."
        }
```

#### Edge Case 2: 0 Candidates

**Scenario:** No products match query at all

**Handling:**
```python
if len(candidates) == 0:
    return {
        "products": [],
        "message": "Geen producten gevonden voor deze zoekopdracht. Neem contact op met een EVI specialist voor maatwerk advies.",
        "fallback_guidelines": await search_guidelines_only(query)  # Show guidelines without products
    }
```

#### Edge Case 3: Broken Product URLs

**Scenario:** URL from FEAT-004 scraping is outdated or broken

**Handling:**
```python
async def validate_product_url(url: str) -> bool:
    """
    Check if product URL is accessible (HTTP 200).
    """
    try:
        response = await httpx.head(url, follow_redirects=True, timeout=2.0)
        return response.status_code == 200
    except:
        return False

# In response formatting:
for product in recommendations:
    if not await validate_product_url(product.url):
        product.url = "https://portal.evi360.nl/products"  # Fallback to catalog homepage
        product.url_note = "(Directe link niet beschikbaar, zie algemene catalogus)"
```

---

## Implementation Plan

### Phase 1: Stage 1 Candidate Generation (2 hours)

**Tasks:**
1. Create `agent/search_stages.py` module
2. Implement `stage1_candidate_generation()` function
3. Test: Query returns 50 candidates in <100ms
4. Add canonicalization logic
5. Test: Duplicates removed correctly

**Deliverables:**
- `agent/search_stages.py::stage1_candidate_generation()`
- `agent/search_stages.py::canonicalize_products()`

---

### Phase 2: Stage 2 LLM Ranking (4 hours)

**Tasks:**
1. Design LLM ranking prompt with weighted criteria
2. Implement `stage2_llm_ranking()` function
3. Parse JSON response from LLM
4. Handle LLM errors/timeouts gracefully
5. Test: 10 queries, verify rankings make sense

**Deliverables:**
- `agent/search_stages.py::stage2_llm_ranking()`
- `agent/prompts.py::RANKING_PROMPT_TEMPLATE`

---

### Phase 3: Product-Guideline Linking (3 hours)

**Tasks:**
1. Implement guideline linking in LLM prompt (recommended)
   - OR implement `link_products_to_guidelines()` separately
2. Test: Products show 1-2 relevant guidelines
3. Validate guideline citations (check they exist in chunks table)
4. Handle products with no guideline matches

**Deliverables:**
- Updated `stage2_llm_ranking()` prompt with guideline instructions
- OR `agent/search_stages.py::link_products_to_guidelines()`

---

### Phase 4: URL Display & Validation (2 hours)

**Tasks:**
1. Ensure all products include `url` field (from FEAT-004)
2. Add URL validation logic (HTTP HEAD check)
3. Format URLs in response (markdown link)
4. Handle broken URLs with fallback
5. Test: All products display working URLs

**Deliverables:**
- `agent/search_stages.py::validate_product_url()`
- Updated response formatting

---

### Phase 5: Two-Stage Integration (3 hours)

**Tasks:**
1. Update `agent/tools.py::search_products_tool()`
2. Replace single-stage search with two-stage protocol
3. Add performance logging (Stage 1 latency, Stage 2 latency, total)
4. Test: End-to-end search completes in <2.5s
5. Compare results: FEAT-004+011 vs FEAT-012

**Deliverables:**
- Updated `search_products_tool()` in `agent/tools.py`
- Performance metrics logged

---

### Phase 6: Edge Case Handling (2 hours)

**Tasks:**
1. Implement < 3 candidates handling (interventie wijzer boosting)
2. Implement 0 candidates handling (fallback message)
3. Implement broken URL handling (validation + fallback)
4. Test: All edge cases covered
5. Document edge case behavior

**Deliverables:**
- Edge case logic in `agent/search_stages.py`
- Test suite for edge cases

---

### Phase 7: Testing & Validation (4 hours)

**Tasks:**
1. Create test suite in `tests/integration/test_two_stage_search.py`
2. Test: Stage 1 performance (<100ms)
3. Test: Stage 2 performance (<2s)
4. Test: Total latency (<2.5s)
5. Human evaluation: 30 test queries, compare FEAT-004+011 vs FEAT-012
6. Document results in validation report

**Deliverables:**
- Test suite (20+ tests)
- Performance benchmarks
- Validation report with metrics

---

## User Experience

### Example: Full Two-Stage Search Flow

**Query:** "Werknemer met burn-out klachten, 6 maanden verzuim, management functie"

---

**Stage 1: Candidate Generation (80ms)**
- Query embedding generated
- PostgreSQL vector search returns 50 candidates:
  1. Herstelcoaching (0.89 similarity)
  2. Burn-out preventie workshop (0.87)
  3. Psychologische ondersteuning (0.85)
  4. Executive coaching (0.82)
  5. Bedrijfsmaatschappelijk werk (0.80)
  ... 45 more ...
- Canonicalize: Remove 5 duplicates → 45 unique candidates

---

**Stage 2: LLM Ranking (1.4s)**

LLM analyzes context:
- **Duration:** 6 maanden (chronic) → Needs intensive intervention
- **Role:** Management → High responsibility, leadership component relevant
- **Severity:** Burn-out (high) → Immediate action required

LLM ranks candidates:
1. **Herstelcoaching** (0.95 relevance)
   - **Impact:** 0.95 (proven effective for burn-out recovery)
   - **Fit:** 0.90 (suitable for management, flexible scheduling)
   - **Guidelines:** 0.85 (NVAB Overspanning en burn-out, Wet verbetering poortwachter)
   - **Feasibility:** 0.90 (6-9 months trajectory matches duration)
   - **Reasoning:** "Meest effectief voor langdurig burn-out verzuim bij management. Gestructureerde aanpak met focus op veerkracht en inzetbaarheid."
   - **Guideline Citations:** ["NVAB Richtlijn Overspanning en burn-out", "Wet verbetering poortwachter"]

2. **Executive Coaching** (0.88 relevance)
   - **Impact:** 0.85 (helps with leadership challenges post-recovery)
   - **Fit:** 0.95 (specifically for management roles)
   - **Guidelines:** 0.70 (general Arbowet compliance)
   - **Feasibility:** 0.85 (shorter trajectory, 3-6 months)
   - **Reasoning:** "Ondersteunt leiderschapsontwikkeling en werkhervatting voor management. Combineert goed met herstelcoaching."
   - **Guideline Citations:** ["Arbowet artikel 3"]

3. **Psychologische Ondersteuning** (0.85 relevance)
   - **Impact:** 0.90 (addresses mental health root causes)
   - **Fit:** 0.75 (not management-specific)
   - **Guidelines:** 0.85 (NVAB, GGZ standaard)
   - **Feasibility:** 0.80 (variable duration)
   - **Reasoning:** "Voor diepergaande psychologische begeleiding indien herstelcoaching onvoldoende is."
   - **Guideline Citations:** ["NVAB Richtlijn Psychische problemen", "GGZ standaard Arbeid als medicijn"]

---

**Final Response to User (Dutch):**

```
Werknemergerichte Interventies voor [Naam]:

### 1. Herstelcoaching

Deze EVI 360 dienst biedt een traject van 6–9 maanden (minimaal 20 sessies) geleid door een arbeidsdeskundige, beginnend met een gedetailleerde intakevragenlijst en uitmondend in een op maat gemaakt inzetbaarheidsplan.

* Voordelen voor [Naam]
Gestructureerde ondersteuning om veerkracht opnieuw op te bouwen, specifiek gericht op burn-out herstel en geleidelijke werkhervatting in management functie.

* Voordelen voor [Bedrijf]
Bevordert stabiele productiviteit, vermindert verzuimrisico en faciliteert duurzame re-integratie van leidinggevende.

* Ondersteunende Nederlandse Richtlijnen
NVAB Richtlijn Overspanning en burn-out, Wet verbetering poortwachter

* Details & Boekingsinformatie
[https://portal.evi360.nl/products/15]

### 2. Executive Coaching

Deze EVI 360 dienst richt zich op leiderschapsontwikkeling en werkhervatting voor management, met focus op strategisch denken en teamleiderschap.

* Voordelen voor [Naam]
Ondersteunt leiderschapsontwikkeling tijdens en na herstel, helpt met werkdruk management en delegeren.

* Voordelen voor [Bedrijf]
Versterkt leiderschapskwaliteiten en zorgt voor soepele overgang terug naar volledige managementverantwoordelijkheden.

* Ondersteunende Nederlandse Richtlijnen
Arbowet artikel 3 (zorgplicht werkgever)

* Details & Boekingsinformatie
[https://portal.evi360.nl/products/28]

### 3. Psychologische Ondersteuning

Deze EVI 360 dienst biedt diepergaande psychologische begeleiding voor werknemers met complexe mentale gezondheidsuitdagingen.

* Voordelen voor [Naam]
Professionele begeleiding voor onderliggende psychologische factoren die bijdragen aan burn-out.

* Voordelen voor [Bedrijf]
Voldoet aan zorgplicht en ondersteunt duurzaam herstel met specialistische zorg.

* Ondersteunende Nederlandse Richtlijnen
NVAB Richtlijn Psychische problemen, GGZ standaard Arbeid als medicijn

* Details & Boekingsinformatie
[https://portal.evi360.nl/products/9]
```

---

**Performance:**
- Stage 1: 80ms
- Stage 2: 1.4s
- Total: 1.48s ✅ (under 2.5s target)

**Quality Improvements vs FEAT-004+011:**
- Burn-out preventie workshop (similarity 0.87) NOT recommended (preventive, not suitable for 6 months verzuim)
- Executive coaching ranked #2 (recognizes management context)
- All products show guideline citations
- All products show working URLs

---

## Testing Strategy

### Unit Tests (10 tests)

1. **Stage 1 Candidate Generation**
   - Test: Returns ≤50 candidates
   - Test: All candidates above similarity threshold
   - Test: Latency <100ms

2. **Canonicalization**
   - Test: Removes exact duplicates (same product_id)
   - Test: Merges fuzzy duplicates (≥0.9 name similarity)
   - Test: Keeps highest similarity score

3. **Stage 2 LLM Ranking**
   - Test: Returns exactly top_k products
   - Test: Products ranked by relevance_score (descending)
   - Test: All products have reasoning

4. **Product-Guideline Linking**
   - Test: Products have 1-2 guideline citations
   - Test: Guidelines exist in chunks table
   - Test: Handle products with no guideline matches

5. **Edge Cases**
   - Test: < 3 candidates triggers interventie wijzer boosting
   - Test: 0 candidates returns fallback message
   - Test: Broken URLs replaced with fallback

### Integration Tests (10 tests)

1. **End-to-End Two-Stage Search**
   - Test: Query → Stage 1 → Stage 2 → Final results
   - Test: Total latency <2.5s
   - Test: Products include URLs and guideline citations

2. **Performance Benchmarks**
   - Test: Stage 1 latency <100ms (95th percentile)
   - Test: Stage 2 latency <2s (95th percentile)
   - Test: 100 concurrent queries (load test)

3. **Quality Comparison**
   - Test: FEAT-012 recommendations ≥ FEAT-004+011 (human evaluation)
   - Test: Guideline citation rate ≥80%
   - Test: URL display rate 100%

### Manual Testing (15 scenarios)

1. Query: "Burn-out klachten" (expect: Herstelcoaching, Psychologische ondersteuning)
2. Query: "Conflict met leidinggevende" (expect: Conflictbemiddeling, Executive coaching)
3. Query: "Fysieke klachten door tilwerk" (expect: Bedrijfsfysiotherapie, Ergonomie)
4. Query: "Lange termijn verzuim" (expect: Re-integratietrajecten)
5. Query: "Management problemen" (expect: Executive coaching, Leiderschapstrajecten)
6. Query: "Werkdruk team" (expect: Team interventies, Werkdrukanalyse)
7. Query: "Zwangerschap en werk" (expect: Arbeidsdeskundige advies)
8. Query: "Onveilige werksituatie" (expect: Veiligheidsadvies, RI&E)
9. Query: "Zeer specifieke niche query" (expect: <3 results, graceful handling)
10. Query: "Gibberish xyz123" (expect: 0 results, fallback message)
11. Query: "Korte termijn verzuim" (expect: Snelle interventies, feasibility weighs high)
12. Query: "Productiewerk fysieke belasting" (expect: Fit with sector weighs high)
13. Query: "Overbelasting leidinggevende" (expect: Management focus, guideline alignment)
14. Query: "Crisis situatie" (expect: Impact weighs high, immediate interventions)
15. Query: "Preventie burn-out" (expect: Preventive products, not recovery-focused)

---

## Dependencies & Blockers

### Dependencies

**Blocking (Must Complete Before FEAT-012):**
- ✅ FEAT-004: Product Catalog Core - Must have products + URLs
- ✅ FEAT-002: Notion integration - Must have guidelines in chunks table

**Highly Recommended (Optimal Quality):**
- ⚠️ FEAT-011: Interventie Wijzer - Provides query expansion and metadata for better Stage 1 results
- **Note:** FEAT-012 CAN work without FEAT-011, but quality will be lower (~80% vs ~90% relevance)

---

### Blockers

**Critical:**
1. **LLM API Access:**
   - Need OpenAI API key (GPT-4) or Anthropic API key (Claude 3.5)
   - Budget: ~$0.10 per query (Stage 2 LLM call)
   - Estimate: $30/month for 300 queries

2. **FEAT-004 URLs Complete:**
   - All products must have working URLs from web scraping
   - Cannot display "Details & Boekingsinformatie" without URLs

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Stage 2 latency exceeds 2s** | High | Medium | Use streaming LLM, optimize prompt length, cache common queries |
| **LLM ranking inconsistent** | High | Medium | Test with 50+ queries, refine prompt, add few-shot examples |
| **Guideline linking poor quality** | Medium | Medium | Let LLM handle linking (uses RAG context), validate with human eval |
| **Broken product URLs** | Low | Medium | Add URL validation, fallback to catalog homepage |
| **Cost exceeds budget** | Low | Low | Monitor per-query cost, set usage alerts, optimize prompt tokens |

---

## Open Questions

1. **LLM Choice:** GPT-4 (best Dutch) or Claude 3.5 (faster, cheaper)?
2. **Caching Strategy:** Should we cache Stage 2 rankings for common queries? (Phase 2 optimization)
3. **Guideline Linking:** Let LLM handle OR implement separate semantic search?
4. **Interventie Wijzer Fallback:** If FEAT-011 not complete, skip query expansion or block FEAT-012?

**Recommendations:**
1. GPT-4 for MVP (best quality), consider Claude 3.5 in Phase 2 if cost concerns
2. No caching for MVP, add in Phase 2 if needed
3. Let LLM handle guideline linking (simpler, leverages RAG context)
4. FEAT-012 should work without FEAT-011, but log warning if not available

---

## Acceptance Criteria (Summary)

**FEAT-012 is COMPLETE when:**

1. ✅ Stage 1 candidate generation returns ≤50 products in <100ms
2. ✅ Canonicalization removes duplicates correctly
3. ✅ Stage 2 LLM ranking applies weighted scoring (0.4/0.3/0.2/0.1)
4. ✅ LLM returns top 3-5 products with reasoning
5. ✅ Products linked to 1-2 relevant guidelines (≥80% citation rate)
6. ✅ All products display working URLs (100% display rate)
7. ✅ Total search latency <2.5s (95th percentile)
8. ✅ Edge cases handled: <3 candidates, 0 candidates, broken URLs
9. ✅ Test suite passes (20+ tests)
10. ✅ Human evaluation shows ≥90% relevance (vs 85% baseline with FEAT-011)
11. ✅ Expert satisfaction +40% (vs baseline)

---

## Timeline Estimate

**Total Effort:** 20 hours (2.5 working days)

- Phase 1 (Stage 1): 2 hours
- Phase 2 (Stage 2): 4 hours
- Phase 3 (Linking): 3 hours
- Phase 4 (URLs): 2 hours
- Phase 5 (Integration): 3 hours
- Phase 6 (Edge Cases): 2 hours
- Phase 7 (Testing): 4 hours

**Dependencies:**
- FEAT-004 must complete first (6-9 hours)
- FEAT-011 highly recommended but not blocking (16 hours)

**Sequential Timeline:**
- Ideal: Start FEAT-012 after FEAT-004 + FEAT-011 complete (22-25 hours total)
- Acceptable: Start FEAT-012 after FEAT-004 only (6-9 hours), lower quality

---

## Future Enhancements (Post-MVP)

1. **Explainable Ranking:** Show score breakdown (impact, fit, guidelines, feasibility) to user
2. **User Feedback Loop:** Thumbs up/down on recommendations, retrain scoring weights
3. **A/B Testing:** Test different scoring weight combinations (0.4/0.3/0.2/0.1 vs alternatives)
4. **Query Intent Classification:** Detect if query is preventive vs recovery, urgent vs routine
5. **Multi-Modal Search:** Include product images, video demos
6. **Real-Time Guideline Updates:** Sync with government websites for latest regulations
7. **Personalization:** Learn from EVI specialist's past selections, personalize rankings
8. **Cost Optimization:** Use smaller LLM for simple queries, GPT-4 only for complex

---

## Appendix

### Scoring Formula (Weighted)

```
relevance_score = (
    impact_score * 0.4 +
    fit_score * 0.3 +
    guideline_alignment_score * 0.2 +
    feasibility_score * 0.1
)
```

**Example Calculation:**
- Herstelcoaching for burn-out (management, 6 months verzuim):
  - Impact: 0.95 (proven effective)
  - Fit: 0.90 (management role)
  - Guidelines: 0.85 (NVAB, Wet poortwachter)
  - Feasibility: 0.90 (6-9 months matches)
  - **Relevance: 0.95 * 0.4 + 0.90 * 0.3 + 0.85 * 0.2 + 0.90 * 0.1 = 0.92**

---

### References

- Original System Prompt: `agent/intervention_specialist_prompt.md` (lines 35-90, kb_reference_protocol)
- FEAT-004 PRD: `docs/features/FEAT-004_product-catalog/archive/prd-v1-broad-scope.md`
- FEAT-011 PRD: `docs/features/FEAT-011_interventie-wijzer/prd.md`

---

**Document Version:** 1.0
**Last Updated:** 2025-11-03
**Author:** AI Workflow Starter (Manual PRD Creation)
**Status:** Ready for Review → Plan → Build
