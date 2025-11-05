"""
Unit tests for FEAT-004: Product Catalog Ingestion Pipeline

Tests cover:
- Portal scraping with Crawl4AI (5 tests)
- CSV parsing and fuzzy matching (5 tests)
- Product enrichment and embedding (3 tests)
- Database operations (4 tests)
- Search tool functionality (1 test)

Total: 18 unit test stubs

Related Acceptance Criteria:
- AC-004-001 through AC-004-005 (Portal Scraping & CSV Integration)
- AC-004-006 (Hybrid Search)
- AC-004-007 (Search Tool)
- AC-004-102 through AC-004-103 (Edge Cases)
- AC-004-203 (Maintainability)
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import MagicMock, AsyncMock, patch


# ============================================================================
# Portal Scraping Tests (5 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_portal_scraping_product_listing_fetch():
    """
    Test: Portal Scraping - Product Listing Fetch (AC-004-001)

    Given: Mocked Crawl4AI returns HTML with product links
    When: scrape_all_products() is called
    Then: Product URLs are extracted (55-65 count), header/footer links ignored
    """
    from ingestion.scrape_portal_products import extract_product_urls

    # Mock HTML with product listing (main content + header/footer noise)
    mock_html = """
    <html>
        <header>
            <nav>
                <a href="/products">All Products</a>
                <a href="/about">About</a>
            </nav>
        </header>
        <main>
            <a href="/products/1">Product 1</a>
            <a href="/products/2">Product 2</a>
            <a href="/products/3">Product 3</a>
            <a href="/products/15">Herstelcoaching</a>
            <a href="/products/27">Burnout Aanpak</a>
        </main>
        <footer>
            <a href="/products">Back to Products</a>
            <a href="/contact">Contact</a>
        </footer>
    </html>
    """

    # Extract product URLs
    urls = extract_product_urls(mock_html)

    # Assertions
    assert len(urls) == 5, f"Expected 5 product URLs, got {len(urls)}"
    assert all(url.startswith("https://portal.evi360.nl/products/") for url in urls), "All URLs should be absolute"
    assert "https://portal.evi360.nl/products/1" in urls
    assert "https://portal.evi360.nl/products/15" in urls
    # Should not include listing link or footer links
    assert "https://portal.evi360.nl/products" not in urls
    assert "https://portal.evi360.nl/about" not in urls


@pytest.mark.asyncio
async def test_portal_scraping_product_urls_extraction():
    """
    Test: Portal Scraping - Product URLs Extraction (AC-004-001)

    Given: Mocked product listing HTML contains <main> with product links
    When: Product URLs are extracted using BeautifulSoup selectors
    Then: Only portal.evi360.nl/products/* URLs returned, navigation links excluded
    """
    from ingestion.scrape_portal_products import extract_product_urls
    import re

    # HTML with main content and navigation noise
    mock_html = """
    <html>
        <nav>
            <a href="/products">Products Home</a>
            <a href="/services">Services</a>
        </nav>
        <main>
            <div class="products-grid">
                <a href="/products/10">Product A</a>
                <a href="/products/20">Product B</a>
                <a href="/products/30">Product C</a>
            </div>
        </main>
        <footer>
            <a href="/products">Back to Products</a>
        </footer>
    </html>
    """

    # Extract URLs
    urls = extract_product_urls(mock_html)

    # Assertions
    assert len(urls) == 3, f"Expected 3 URLs, got {len(urls)}"

    # All URLs should match pattern: https://portal.evi360.nl/products/[number]
    url_pattern = re.compile(r'^https://portal\.evi360\.nl/products/\d+$')
    for url in urls:
        assert url_pattern.match(url), f"URL {url} doesn't match expected pattern"

    # Navigation links should be excluded
    assert all("services" not in url for url in urls)
    assert urls.count("https://portal.evi360.nl/products") == 0, "Listing page URL should not be included"


@pytest.mark.asyncio
async def test_portal_scraping_individual_product_click():
    """
    Test: Portal Scraping - Individual Product Click (AC-004-001)

    Given: Mocked Crawl4AI clicks into product page
    When: extract_product_details() parses product HTML
    Then: name, description, price, category extracted correctly
    """
    from ingestion.scrape_portal_products import extract_product_details

    # Mock product page HTML (using validated selectors)
    mock_html = """
    <html>
        <body>
            <h1>Herstelcoaching</h1>
            <div class="platform-product-description">
                <p>6-9 maanden traject voor burn-out herstel met begeleiding van arbeidsdeskundige.</p>
                <p>Gericht op veerkracht en geleidelijke werkhervatting.</p>
            </div>
            <div class="product-price">€2.500 - €3.500</div>
        </body>
    </html>
    """

    url = "https://portal.evi360.nl/products/15"

    # Extract product details
    product = extract_product_details(mock_html, url)

    # Assertions
    assert product is not None, "Product should be extracted"
    assert product["name"] == "Herstelcoaching"
    assert len(product["description"]) > 50, "Description should be substantial"
    assert "burn-out herstel" in product["description"].lower()
    assert product["price"] == "€2.500 - €3.500"
    assert product["url"] == url
    assert product["category"] is None  # Category not available on product pages


@pytest.mark.asyncio
async def test_portal_scraping_missing_price_field():
    """
    Test: Portal Scraping - Missing Price Field Handling (AC-004-103)

    Given: Product HTML lacks price element
    When: extract_product_details() is called
    Then: Product returned with price=None, other fields intact
    """
    from ingestion.scrape_portal_products import extract_product_details

    # Mock HTML without price element
    mock_html = """
    <html>
        <body>
            <h1>Bedrijfsfysiotherapie</h1>
            <div class="platform-product-description">
                <p>Arbeidsgerichte fysiotherapie voor preventie en behandeling van bewegingsklachten.</p>
            </div>
            <!-- No product-price element -->
        </body>
    </html>
    """

    url = "https://portal.evi360.nl/products/8"

    # Extract product details
    product = extract_product_details(mock_html, url)

    # Assertions
    assert product is not None, "Product should still be extracted"
    assert product["name"] == "Bedrijfsfysiotherapie"
    assert len(product["description"]) > 30
    assert product["price"] is None, "Price should be None when missing"
    assert product["url"] == url
    assert product["category"] is None


@pytest.mark.asyncio
async def test_portal_scraping_error_handling():
    """
    Test: Portal Scraping - Error Handling for Failed Requests (AC-004-101)

    Given: Product extraction fails (missing name)
    When: extract_product_details() is called
    Then: None returned, error logged
    """
    from ingestion.scrape_portal_products import extract_product_details

    # Mock HTML without h1 (name) element - should fail gracefully
    mock_html = """
    <html>
        <body>
            <!-- No h1 element - this is an error page or invalid product -->
            <div class="error">Product not found</div>
        </body>
    </html>
    """

    url = "https://portal.evi360.nl/products/999"

    # Extract product details
    product = extract_product_details(mock_html, url)

    # Assertions
    assert product is None, "Should return None for invalid product pages"


# ============================================================================
# CSV Parsing Tests (5 tests)
# ============================================================================

def test_csv_parsing_problem_product_mapping_extraction():
    """
    Test: CSV Parsing - Problem-Product Mapping Extraction (AC-004-003)

    Given: Intervention_matrix.csv with 26 rows
    When: parse_interventie_csv() is called
    Then: 23 unique products extracted, problems aggregated by product name
    """
    from ingestion.parse_interventie_csv import parse_interventie_csv

    # Parse actual CSV file
    csv_products = parse_interventie_csv()

    # Assertions
    assert isinstance(csv_products, dict), "Should return dict mapping product → data"
    assert len(csv_products) == 23, f"Expected 23 unique products, got {len(csv_products)}"

    # Validate structure of each product
    for product_name, product_data in csv_products.items():
        assert isinstance(product_name, str), "Product name should be string"
        assert len(product_name) > 0, "Product name should not be empty"

        assert "problems" in product_data, f"Product {product_name} missing 'problems' key"
        assert "category" in product_data, f"Product {product_name} missing 'category' key"

        assert isinstance(product_data["problems"], list), "Problems should be a list"
        assert len(product_data["problems"]) > 0, f"Product {product_name} has no problems"

        # Validate all problems are non-empty strings
        for problem in product_data["problems"]:
            assert isinstance(problem, str), "Problem should be string"
            assert len(problem) > 0, "Problem should not be empty"

        assert isinstance(product_data["category"], str), "Category should be string"


def test_csv_parsing_many_to_one_aggregation():
    """
    Test: CSV Parsing - Many-to-One Problem Aggregation (AC-004-004)

    Given: CSV has 26 rows aggregating to 23 unique products
    When: Problems are aggregated
    Then: Products with multiple rows have multiple problems in array
    """
    from ingestion.parse_interventie_csv import parse_interventie_csv

    # Parse actual CSV
    csv_products = parse_interventie_csv()

    # Assertions
    # CSV has 26 rows → 23 unique products, so at least 3 products must have multiple problems
    products_with_multiple_problems = [
        p for p in csv_products.values() if len(p["problems"]) > 1
    ]

    assert len(products_with_multiple_problems) >= 3, (
        f"Expected at least 3 products with multiple problems "
        f"(26 rows → 23 products), got {len(products_with_multiple_problems)}"
    )

    # Validate no duplicate problems within a product
    for product_name, product_data in csv_products.items():
        problems = product_data["problems"]
        unique_problems = set(problems)
        assert len(problems) == len(unique_problems), (
            f"Product {product_name} has duplicate problems: {problems}"
        )


def test_fuzzy_matching_high_similarity_match():
    """
    Test: Fuzzy Matching - High Similarity Match (≥0.85) (AC-004-003)

    Given: CSV product "Coaching" and portal product "Coaching"
    When: fuzzy_match_products(threshold=0.85) is called
    Then: Products matched with high similarity score
    """
    from ingestion.parse_interventie_csv import fuzzy_match_products

    # Mock CSV products
    csv_products = {
        "Coaching": {
            "problems": ["Mijn werknemer heeft begeleiding nodig bij motivatieproblemen"],
            "category": "Verbetering belastbaarheid"
        }
    }

    # Mock portal products
    portal_products = [
        {
            "id": "test-uuid-1",
            "name": "Coaching",
            "url": "https://portal.evi360.nl/products/50"
        }
    ]

    # No manual mappings
    manual_mappings = {}

    # Fuzzy match
    matched, unmatched = fuzzy_match_products(
        csv_products,
        portal_products,
        manual_mappings,
        threshold=0.85
    )

    # Assertions
    assert len(matched) == 1, f"Expected 1 match, got {len(matched)}"
    assert len(unmatched) == 0, f"Expected 0 unmatched, got {len(unmatched)}"

    csv_name, portal_product, score, source = matched[0]
    assert csv_name == "Coaching"
    assert portal_product["name"] == "Coaching"
    assert score >= 0.85, f"Score {score} below threshold 0.85"
    assert source == "fuzzy", "Should be fuzzy matched (no manual mapping)"


def test_fuzzy_matching_low_similarity_rejection():
    """
    Test: Fuzzy Matching - Low Similarity Rejection (<0.85) (AC-004-102)

    Given: CSV product "Totally Different Name" and portal product "Coaching"
    When: Fuzzy matching is attempted with threshold 0.85
    Then: No match, product logged to unmatched list
    """
    from ingestion.parse_interventie_csv import fuzzy_match_products

    # Mock CSV products (completely dissimilar to portal)
    csv_products = {
        "Totally Different Service Name ABC": {
            "problems": ["Some problem"],
            "category": "Test Category"
        }
    }

    # Mock portal products
    portal_products = [
        {
            "id": "test-uuid-1",
            "name": "Coaching",
            "url": "https://portal.evi360.nl/products/50"
        }
    ]

    # No manual mappings
    manual_mappings = {}

    # Fuzzy match with 0.85 threshold
    matched, unmatched = fuzzy_match_products(
        csv_products,
        portal_products,
        manual_mappings,
        threshold=0.85
    )

    # Assertions
    assert len(matched) == 0, f"Expected 0 matches, got {len(matched)}"
    assert len(unmatched) == 1, f"Expected 1 unmatched, got {len(unmatched)}"
    assert "Totally Different Service Name ABC" in unmatched


def test_fuzzy_matching_unmatched_products_logged():
    """
    Test: Fuzzy Matching - Unmatched Products Logged (AC-004-102)

    Given: 4 CSV products cannot be matched (expected from real data)
    When: Fuzzy matching completes
    Then: Unmatched list returned with 4 products
    """
    from ingestion.parse_interventie_csv import fuzzy_match_products

    # Mock CSV products (intentionally dissimilar to portal)
    csv_products = {
        "Product A XYZ": {"problems": ["P1"], "category": "Cat1"},
        "Product B ABC": {"problems": ["P2"], "category": "Cat2"},
        "Product C DEF": {"problems": ["P3"], "category": "Cat3"},
        "Product D GHI": {"problems": ["P4"], "category": "Cat4"},
    }

    # Mock portal products (completely different names)
    portal_products = [
        {"id": "uuid-1", "name": "Coaching", "url": "https://portal.evi360.nl/products/1"},
        {"id": "uuid-2", "name": "Mediation", "url": "https://portal.evi360.nl/products/2"},
    ]

    # No manual mappings
    manual_mappings = {}

    # Fuzzy match
    matched, unmatched = fuzzy_match_products(
        csv_products,
        portal_products,
        manual_mappings,
        threshold=0.85
    )

    # Assertions
    assert len(unmatched) == 4, f"Expected 4 unmatched products, got {len(unmatched)}"
    assert "Product A XYZ" in unmatched
    assert "Product B ABC" in unmatched
    assert "Product C DEF" in unmatched
    assert "Product D GHI" in unmatched


# ============================================================================
# Product Enrichment Tests (3 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_product_enrichment_metadata_with_problem_mappings():
    """
    Test: Product Enrichment - Metadata with Problem Mappings (AC-004-004)

    Given: Portal product matched to CSV product with 2 problems
    When: enrich_database() is called
    Then: Database updated with problem_mappings and csv_category in metadata
    """
    from ingestion.parse_interventie_csv import enrich_database, get_db_pool
    import uuid
    import json

    # Create test product in database
    pool = await get_db_pool()
    test_id = str(uuid.uuid4())
    test_url = f"https://portal.evi360.nl/products/test-{test_id}"

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO products (id, name, description, url, category, metadata, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
        """, test_id, "Test Product", "Test description", test_url, None, json.dumps({}))

    try:
        # Mock CSV products
        csv_products = {
            "Test Product": {
                "problems": ["Problem 1", "Problem 2"],
                "category": "Test Category"
            }
        }

        # Mock matched products
        matched_products = [(
            "Test Product",
            {"id": test_id, "name": "Test Product", "url": test_url},
            0.95,
            "fuzzy"
        )]

        # Enrich database
        enriched_count = await enrich_database(matched_products, csv_products)

        # Assertions
        assert enriched_count == 1, f"Expected 1 enriched, got {enriched_count}"

        # Verify database update
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT metadata, category FROM products WHERE id = $1", test_id)

        assert row is not None, "Product should exist in database"
        metadata = row["metadata"]
        assert "problem_mappings" in metadata, "Metadata should have problem_mappings"
        assert metadata["problem_mappings"] == ["Problem 1", "Problem 2"]
        assert metadata["csv_category"] == "Test Category"
        assert row["category"] == "Test Category", "Category column should be updated"

    finally:
        # Cleanup
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM products WHERE id = $1", test_id)


def test_product_enrichment_embedding_generation_with_problems():
    """
    Test: Product Enrichment - Embedding Generation with Problems (AC-004-005)

    Given: Product with description and 2 problem mappings
    When: Embedding text is generated
    Then: Text = "description\\n\\nProblem 1\\nProblem 2"
    """
    # Import the function we're testing (will be created in enrich_and_embed.py)
    from ingestion.enrich_and_embed import generate_embedding_text

    # Given: Product with description and 2 problem mappings
    product = {
        "id": 1,
        "name": "Test Product",
        "description": "Test product description for embedding",
        "metadata": {
            "problem_mappings": [
                "Mijn werknemer heeft burn-out klachten",
                "Het gaat slecht met mijn werknemer, hoe krijgt hij gericht advies?"
            ],
            "csv_category": "Verbetering belastbaarheid"
        }
    }

    # When: Embedding text is generated
    embedding_text = generate_embedding_text(product)

    # Then: Text should be "description\n\nProblem 1\nProblem 2"
    expected_text = (
        "Test product description for embedding\n\n"
        "Mijn werknemer heeft burn-out klachten\n"
        "Het gaat slecht met mijn werknemer, hoe krijgt hij gericht advies?"
    )
    assert embedding_text == expected_text, f"Expected: {repr(expected_text)}, Got: {repr(embedding_text)}"

    # Verify structure
    parts = embedding_text.split("\n\n")
    assert len(parts) == 2, "Should have description and problems separated by double newline"
    assert parts[0] == "Test product description for embedding", "First part should be description"

    problems = parts[1].split("\n")
    assert len(problems) == 2, "Should have 2 problems"
    assert problems[0] == "Mijn werknemer heeft burn-out klachten"
    assert problems[1] == "Het gaat slecht met mijn werknemer, hoe krijgt hij gericht advies?"


def test_product_enrichment_no_csv_match_fallback():
    """
    Test: Product Enrichment - No CSV Match Fallback (AC-004-102)

    Given: Portal product with no CSV match
    When: Product is enriched
    Then: Embedding generated from description only, metadata.problem_mappings = []
    """
    # Import the function we're testing
    from ingestion.enrich_and_embed import generate_embedding_text

    # Given: Portal product without CSV match (no problem_mappings in metadata)
    product_no_metadata = {
        "id": 2,
        "name": "Bedrijfsfysiotherapie",
        "description": "Arbeidsgerichte fysiotherapie voor preventie en behandeling van bewegingsklachten op de werkplek.",
        "metadata": {}  # No problem_mappings
    }

    # When: Embedding text is generated
    embedding_text = generate_embedding_text(product_no_metadata)

    # Then: Text should be description only (no problems appended)
    expected_text = "Arbeidsgerichte fysiotherapie voor preventie en behandeling van bewegingsklachten op de werkplek."
    assert embedding_text == expected_text, f"Expected: {repr(expected_text)}, Got: {repr(embedding_text)}"
    assert "\n\n" not in embedding_text, "Should not have double newline separator when no problems"

    # Test with None metadata
    product_none_metadata = {
        "id": 3,
        "name": "Test Product",
        "description": "Test description without metadata",
        "metadata": None
    }

    embedding_text_none = generate_embedding_text(product_none_metadata)
    assert embedding_text_none == "Test description without metadata"

    # Test with empty problem_mappings list
    product_empty_problems = {
        "id": 4,
        "name": "Test Product 2",
        "description": "Test description with empty problems",
        "metadata": {"problem_mappings": []}
    }

    embedding_text_empty = generate_embedding_text(product_empty_problems)
    assert embedding_text_empty == "Test description with empty problems"


# ============================================================================
# Database Operations Tests (4 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_database_operations_insert_new_product():
    """
    Test: Database Operations - Insert New Product (AC-004-001)

    Given: Product dict with all fields
    When: insert_product() is called
    Then: Product inserted into database, UUID returned
    """
    # TODO: Implement test
    # 1. Create test database connection (asyncpg pool)
    # 2. Create product dict with name, description, url, embedding, metadata
    # 3. Call insert_product(conn, product)
    # 4. Assert UUID returned
    # 5. Assert product exists in database (SELECT COUNT WHERE id = uuid)
    # 6. Cleanup: DELETE product after test
    pytest.skip("Test stub - implement in Phase 2")


@pytest.mark.asyncio
async def test_database_operations_update_existing_product():
    """
    Test: Database Operations - Update Existing Product (AC-004-203)

    Given: Product with same name+URL exists in database
    When: upsert_product() is called
    Then: Existing product updated, not duplicated
    """
    # TODO: Implement test
    # 1. Insert product into test database
    # 2. Modify product description
    # 3. Call upsert_product(conn, product) (should update, not insert)
    # 4. Assert COUNT(*) WHERE name+url = 1 (no duplicate)
    # 5. Assert description updated in database
    # 6. Cleanup: DELETE product
    pytest.skip("Test stub - implement in Phase 2")


@pytest.mark.asyncio
async def test_database_operations_handle_duplicate_names():
    """
    Test: Database Operations - Handle Duplicate Names (AC-004-203)

    Given: Two products with same name but different URLs
    When: Both inserted
    Then: Two separate products created (URL distinguishes)
    """
    # TODO: Implement test
    # 1. Create 2 products: same name, different URLs
    # 2. Insert both products
    # 3. Assert COUNT(*) WHERE name = 2 (both inserted)
    # 4. Assert URLs differ in database
    # 5. Cleanup: DELETE both products
    pytest.skip("Test stub - implement in Phase 2")


@pytest.mark.asyncio
async def test_database_operations_upsert_logic():
    """
    Test: Database Operations - Upsert Logic (AC-004-203)

    Given: Product exists with same (name, URL, description)
    When: upsert_product() is called with updated metadata
    Then: Metadata updated, embedding refreshed, updated_at changed
    """
    # TODO: Implement test
    # 1. Insert product with initial metadata
    # 2. Modify product metadata (add problem_mappings)
    # 3. Call upsert_product(conn, product)
    # 4. Assert COUNT = 1 (no duplicate)
    # 5. Assert metadata updated in database
    # 6. Assert updated_at timestamp changed
    # 7. Cleanup: DELETE product
    pytest.skip("Test stub - implement in Phase 2")


# ============================================================================
# Hybrid Search Tool Test (1 test)
# ============================================================================

@pytest.mark.asyncio
async def test_hybrid_search_tool_result_formatting():
    """
    Test 18: Hybrid Search Tool - Result Formatting for LLM (AC-004-008, AC-004-010)

    Given: SQL function returns 4 products with varying description lengths
    When: search_products_tool() formats results
    Then:
      - Descriptions >200 chars truncated with "..."
      - Descriptions <200 chars unchanged
      - Similarity scores rounded to 2 decimals
      - NULL prices become "Geen prijsinformatie beschikbaar"
      - NULL metadata handled gracefully
      - Similarity threshold 0.3 applied (low similarity filtered out)
    """
    from agent.tools import search_products_tool, ProductSearchInput
    from unittest.mock import AsyncMock, patch

    # Mock database query results (4 products with different characteristics)
    mock_results = [
        {
            "product_id": "uuid-1",
            "name": "Herstelcoaching",
            "description": "A" * 500,  # 500 chars - should be truncated to 203
            "price": "€2.500 - €3.500",
            "url": "https://portal.evi360.nl/products/15",
            "category": "Coaching",
            "similarity": 0.876543,  # Should round to 0.88
            "metadata": {"problem_mappings": ["Burn-out", "Verzuim"], "contact_for_price": False}
        },
        {
            "product_id": "uuid-2",
            "name": "Bedrijfsfysiotherapie",
            "description": "B" * 150,  # 150 chars - should NOT be truncated
            "price": None,  # NULL price, no contact flag
            "url": "https://portal.evi360.nl/products/8",
            "category": "Fysio",
            "similarity": 0.654321,  # Should round to 0.65
            "metadata": {}  # Empty metadata
        },
        {
            "product_id": "uuid-3",
            "name": "Psychologische Ondersteuning",
            "description": "C" * 300,  # 300 chars - should be truncated
            "price": None,  # NULL price, but contact_for_price flag
            "url": "https://portal.evi360.nl/products/9",
            "category": None,  # NULL category
            "similarity": 0.543210,  # Should round to 0.54
            "metadata": {"contact_for_price": True}  # Price on request flag
        },
        {
            "product_id": "uuid-4",
            "name": "Low Similarity Product",
            "description": "Should be filtered out",
            "price": "€100",
            "url": "https://portal.evi360.nl/products/99",
            "category": "Test",
            "similarity": 0.2,  # Below 0.3 threshold - should be FILTERED OUT
            "metadata": None  # NULL metadata (not empty dict)
        }
    ]

    # Mock embedding generation
    mock_embedding = [0.1] * 1536

    # Mock database connection
    with patch('agent.tools.generate_embedding', new_callable=AsyncMock) as mock_embed, \
         patch('agent.db_utils.db_pool') as mock_pool:

        # Configure mocks
        mock_embed.return_value = mock_embedding
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_results
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Execute search
        search_input = ProductSearchInput(query="burn-out", limit=5)
        results = await search_products_tool(search_input)

    # Assertions
    # Should return 3 products (uuid-4 filtered out due to low similarity)
    assert len(results) == 3, f"Expected 3 products (4th filtered), got {len(results)}"

    # Test product 1: Long description truncation + similarity rounding
    assert results[0]["name"] == "Herstelcoaching"
    assert len(results[0]["description"]) <= 203, f"Description should be ≤203 chars, got {len(results[0]['description'])}"
    assert results[0]["description"].endswith("..."), "Truncated description should end with '...'"
    assert results[0]["similarity"] == 0.88, f"Similarity should be 0.88, got {results[0]['similarity']}"
    assert results[0]["price"] == "€2.500 - €3.500"
    assert results[0]["problem_mappings"] == ["Burn-out", "Verzuim"]
    assert results[0]["category"] == "Coaching"

    # Test product 2: Short description (no truncation) + NULL price (no flag)
    assert results[1]["name"] == "Bedrijfsfysiotherapie"
    assert len(results[1]["description"]) == 150, "Short description should not be truncated"
    assert not results[1]["description"].endswith("..."), "Short description should not have '...'"
    assert results[1]["similarity"] == 0.65, f"Similarity should be 0.65, got {results[1]['similarity']}"
    assert results[1]["price"] == "Geen prijsinformatie beschikbaar", f"NULL price without flag should show 'Geen prijsinformatie', got {results[1]['price']}"
    assert results[1]["problem_mappings"] == []
    assert results[1]["category"] == "Fysio"

    # Test product 3: NULL metadata + NULL price with contact flag + NULL category
    assert results[2]["name"] == "Psychologische Ondersteuning"
    assert len(results[2]["description"]) <= 203, "Long description should be truncated"
    assert results[2]["similarity"] == 0.54
    assert results[2]["price"] == "Prijs op aanvraag", f"NULL price with flag should show 'Prijs op aanvraag', got {results[2]['price']}"
    assert results[2]["problem_mappings"] == []
    assert results[2]["category"] == "Overig", "NULL category should default to 'Overig'"

    # Verify uuid-4 was filtered out (similarity 0.2 < 0.3 threshold)
    product_names = [p["name"] for p in results]
    assert "Low Similarity Product" not in product_names, "Low similarity product should be filtered out"

    print("✅ Test 18 passed: All formatting, truncation, rounding, and threshold logic works correctly")


# ============================================================================
# Test Fixtures (shared across tests)
# ============================================================================

@pytest.fixture
def sample_portal_product() -> Dict[str, Any]:
    """Fixture: Sample portal product for testing."""
    return {
        "name": "Herstelcoaching",
        "description": "6-9 maanden traject voor burn-out herstel",
        "price": "€2.500 - €3.500",
        "url": "https://portal.evi360.nl/products/15",
        "category": "Coaching"
    }


@pytest.fixture
def sample_csv_product() -> Dict[str, Any]:
    """Fixture: Sample CSV product for testing."""
    return {
        "product_name": "Herstelcoaching",
        "problems": ["Mijn werknemer heeft burn-out klachten"],
        "category": "Verbetering belastbaarheid"
    }


@pytest.fixture
def mock_crawl4ai_response() -> str:
    """Fixture: Mocked Crawl4AI HTML response."""
    return """
    <html>
      <main>
        <a href="/products/15">Herstelcoaching</a>
        <a href="/products/27">Multidisciplinaire Burnout Aanpak</a>
      </main>
      <footer><!-- ignore --></footer>
    </html>
    """
