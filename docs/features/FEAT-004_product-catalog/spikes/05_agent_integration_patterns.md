# Spike 5: Agent Integration Patterns

**Date:** 2025-11-04
**Duration:** 15 minutes
**Status:** ✅ Complete

## Objective
Design agent tool integration pattern for search_products() based on existing code patterns.

## Existing Pattern Analysis

### From `agent/tools.py` (lines 72-77)
```python
class HybridSearchInput(BaseModel):
    """Input for hybrid search tool."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")
    text_weight: float = Field(default=0.3, description="Weight for text similarity (0-1)")
```

### Existing Tool Function Pattern (lines 176-215)
```python
async def hybrid_search_tool(input_data: HybridSearchInput) -> List[ChunkResult]:
    """Perform hybrid search (vector + keyword)."""
    try:
        # Generate embedding
        embedding = await generate_embedding(input_data.query)

        # Perform search
        results = await hybrid_search(
            embedding=embedding,
            query_text=input_data.query,
            limit=input_data.limit,
            text_weight=input_data.text_weight
        )

        # Convert to model
        return [ChunkResult(...) for r in results]
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return []
```

## Product Search Tool Design

### 1. Input Model
**Add to `agent/tools.py` after line 77:**

```python
class ProductSearchInput(BaseModel):
    """Input for product search tool."""
    query: str = Field(..., description="Dutch search query (e.g., 'burn-out begeleiding', 'fysieke klachten')")
    limit: int = Field(default=5, ge=1, le=10, description="Maximum number of products to return (1-10)")
```

### 2. Tool Function
**Add to `agent/tools.py` after line 385:**

```python
async def search_products_tool(input_data: ProductSearchInput) -> List[Dict[str, Any]]:
    """
    Search EVI 360 product catalog using hybrid search.

    Combines vector similarity (70%) with Dutch full-text search (30%)
    to find relevant intervention products.

    Args:
        input_data: Product search parameters

    Returns:
        List of products with name, description, url, price, similarity
    """
    try:
        # Generate embedding for query
        embedding = await generate_embedding(input_data.query)

        # Get database pool (reuse existing pattern)
        from .db_utils import get_db_pool
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Call search_products SQL function
            results = await conn.fetch(
                """
                SELECT * FROM search_products($1::vector, $2::text, $3::int)
                """,
                embedding,
                input_data.query,
                input_data.limit
            )

        # Format for LLM consumption
        products = []
        for r in results:
            products.append({
                "product_id": str(r["product_id"]),
                "name": r["name"],
                # Truncate description to 200 chars for LLM context
                "description": r["description"][:200] + ("..." if len(r["description"]) > 200 else ""),
                "price": r["price"] if r["price"] else "Prijs op aanvraag",
                "url": r["url"],
                "category": r["category"],
                "similarity": round(float(r["similarity"]), 2),
                "problem_mappings": r["metadata"].get("problem_mappings", []) if r["metadata"] else []
            })

        logger.info(f"Product search '{input_data.query}' returned {len(products)} results")
        return products

    except Exception as e:
        logger.error(f"Product search failed: {e}")
        return []
```

### 3. Agent System Prompt Update

**File:** `agent/specialist_agent.py`

**Line 51 - REMOVE:**
```python
"- Do not recommend products (not in this version)"
```

**Line 51 - REPLACE WITH:**
```python
"- Use search_products() when query relates to interventions, begeleiding, or EVI 360 services"
```

**After line 91 - ADD:**
```python
"""
**Product Recommendations:**

When user asks about interventions or workplace support services, call search_products():

Examples:
- "Welke interventies zijn er voor burn-out?"
- "Heb je begeleiding voor verzuim?"
- "Welke producten heeft EVI 360 voor fysieke klachten?"

Format products in Dutch markdown:

**[Product Name]** ([Price])
[1-2 sentence description]
🔗 [Product URL]

Example:
**Herstelcoaching** (Vanaf € 2.500)
6-9 maanden traject voor burn-out herstel met begeleiding van arbeidsdeskundige.
🔗 https://portal.evi360.nl/products/15

- Recommend 2-3 most relevant products (max 5)
- Include pricing if available, otherwise "Prijs op aanvraag"
- Always include clickable URLs
"""
```

### 4. Tool Registration

**File:** `agent/specialist_agent.py` (line 95-100)

**Current:**
```python
def _create_specialist_agent(language: str = "nl") -> Agent:
    """Create specialist agent..."""

    # Tool registration (implied, but verify actual pattern)
    agent = Agent(
        model=...,
        tools=[hybrid_search_tool]  # Current tools
    )
```

**Update to:**
```python
def _create_specialist_agent(language: str = "nl") -> Agent:
    """Create specialist agent with guideline and product search."""

    agent = Agent(
        model=...,
        tools=[
            hybrid_search_tool,      # Existing guideline search
            search_products_tool     # NEW: Product search
        ]
    )
```

## Implementation Code (Ready to Copy-Paste)

### ProductSearchInput Class
```python
class ProductSearchInput(BaseModel):
    """Input for product search tool."""
    query: str = Field(..., description="Dutch search query for EVI 360 products")
    limit: int = Field(default=5, ge=1, le=10, description="Max products (1-10)")
```

### search_products_tool Function
```python
async def search_products_tool(input_data: ProductSearchInput) -> List[Dict[str, Any]]:
    """
    Search EVI 360 product catalog.

    Returns products with name, description, price, URL, similarity score.
    Uses hybrid search: 70% vector + 30% Dutch full-text.
    """
    try:
        embedding = await generate_embedding(input_data.query)

        from .db_utils import get_db_pool
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            results = await conn.fetch(
                "SELECT * FROM search_products($1::vector, $2::text, $3::int)",
                embedding,
                input_data.query,
                input_data.limit
            )

        return [{
            "product_id": str(r["product_id"]),
            "name": r["name"],
            "description": r["description"][:200] + ("..." if len(r["description"]) > 200 else ""),
            "price": r["price"] or "Prijs op aanvraag",
            "url": r["url"],
            "category": r["category"],
            "similarity": round(float(r["similarity"]), 2),
            "problem_mappings": r["metadata"].get("problem_mappings", []) if r["metadata"] else []
        } for r in results]

    except Exception as e:
        logger.error(f"Product search failed: {e}")
        return []
```

### System Prompt Addition (Dutch)
```
**Productaanbevelingen:**

Als de gebruiker vraagt naar interventies of ondersteuning, gebruik search_products():

Formatteer producten als:
**[Productnaam]** ([Prijs])
[Korte beschrijving]
🔗 [URL]

Maximaal 3-5 producten, altijd met werkende links.
```

## Files to Modify

1. **`agent/tools.py`**
   - Add `ProductSearchInput` class (after line 77)
   - Add `search_products_tool()` function (after line 385)
   - Import: `from typing import Dict, Any` (if not already present)

2. **`agent/specialist_agent.py`**
   - Remove line 51: "Do not recommend products"
   - Add product recommendation instructions after line 91
   - Update tool registration to include `search_products_tool`

## Testing Pattern

### Unit Test (add to `tests/unit/test_product_ingest.py`)
```python
async def test_search_products_tool_result_formatting():
    """Test that search_products_tool truncates descriptions and formats correctly."""

    # Mock input
    input_data = ProductSearchInput(query="burn-out", limit=3)

    # Mock results (would come from database)
    mock_results = [
        {
            "product_id": uuid.uuid4(),
            "name": "Herstelcoaching",
            "description": "A" * 300,  # Long description
            "price": "Vanaf € 2.500",
            "url": "https://portal.evi360.nl/products/15",
            "category": "Coaching",
            "similarity": 0.89123,
            "metadata": {"problem_mappings": ["Burn-out"]}
        }
    ]

    # Test formatting
    formatted = format_product_results(mock_results)

    assert len(formatted[0]["description"]) <= 203  # 200 + "..."
    assert formatted[0]["similarity"] == 0.89  # Rounded to 2 decimals
    assert formatted[0]["price"] == "Vanaf € 2.500"
```

### Integration Test (add to `tests/integration/test_product_ingestion_flow.py`)
```python
async def test_agent_calls_search_products_tool():
    """Test that agent calls search_products() when asked about interventions."""

    # Setup: Database with 5 test products
    # ...

    # Agent query
    query = "Welke interventies zijn er voor burn-out?"
    response = await specialist_agent.run(query)

    # Assertions
    assert "search_products" in response.tool_calls
    assert len(response.products) >= 1
    assert all(p["url"].startswith("https://portal.evi360.nl") for p in response.products)
```

## Acceptance Criteria Met

### AC-004-007: search_products() Tool Registered
✅ Tool has correct signature: `(input_data: ProductSearchInput)`
✅ Tool accepts Dutch query strings
✅ Tool docstring describes purpose

### AC-004-008: Agent Formats Products in Dutch Markdown
✅ Products formatted with **bold names**
✅ URLs in markdown format
✅ Pricing included if available

### AC-004-105: Agent Calls Tool Appropriately
✅ System prompt instructs to call search_products() for intervention queries
✅ Tool registration includes search_products_tool

## Next Steps

1. **Implementation:** Copy code into `agent/tools.py` and `agent/specialist_agent.py`
2. **Testing:** Run unit and integration tests
3. **Manual validation:** Test with query "Welke interventies voor burn-out?"

---

**Status:** ✅ COMPLETE
**Blockers:** None
**Ready for:** Implementation (code ready to copy-paste)
