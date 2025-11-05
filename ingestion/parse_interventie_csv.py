"""
Parse Intervention Matrix CSV and enrich product database with problem mappings.

This module implements Phase 2 of FEAT-004:
- Parse Intervention_matrix.csv (26 rows → 23 unique products)
- Load manual CSV → portal product mappings
- Fuzzy match CSV products to portal products (0.85 threshold)
- Enrich database with problem_mappings metadata

Usage:
    python3 -m ingestion.parse_interventie_csv
"""

import asyncio
import csv
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

import asyncpg
from fuzzywuzzy import fuzz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "docs/features/FEAT-004_product-catalog/Intervention_matrix.csv"
MANUAL_MAPPINGS_PATH = PROJECT_ROOT / "docs/features/FEAT-004_product-catalog/manual_product_mappings.json"
UNRESOLVED_PATH = PROJECT_ROOT / "docs/features/FEAT-004_product-catalog/unresolved_products.json"

# Fuzzy matching threshold (validated in spike - 0.9 was too strict)
FUZZY_THRESHOLD = 0.85


async def get_db_pool() -> asyncpg.Pool:
    """Create database connection pool."""
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/evi_rag")
    return await asyncpg.create_pool(
        database_url,
        min_size=5,
        max_size=20
    )


def parse_interventie_csv() -> Dict[str, Dict]:
    """
    Parse Intervention Matrix CSV and aggregate problems by product.

    CSV Structure (26 rows):
        - Probleem: Dutch problem description
        - Category: CSV category (e.g., "Verbetering belastbaarheid")
        - Soort interventie: Product name (key for matching)
        - Link interventie: IGNORE (outdated URLs)

    Returns:
        Dict mapping product name to aggregated data:
        {
            "Product Name": {
                "problems": ["Problem 1", "Problem 2", ...],
                "category": "CSV Category"
            }
        }

    Note: 26 rows aggregate to 23 unique products (many-to-one relationship)
    """
    logger.info(f"Parsing CSV from {CSV_PATH}")

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

    products = {}
    row_count = 0

    # Handle UTF-8-BOM encoding (CSV has ﻿ at start)
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            row_count += 1

            # Extract fields
            problem = row.get('Probleem', '').strip()
            category = row.get('Category', '').strip()
            product_name = row.get('Soort interventie', '').strip()

            # Skip rows with missing critical fields
            if not problem or not product_name:
                logger.warning(f"Row {row_count}: Missing problem or product name, skipping")
                continue

            # Aggregate problems by product
            if product_name not in products:
                products[product_name] = {
                    "problems": [],
                    "category": category
                }

            # Add problem if not already present (avoid duplicates)
            if problem not in products[product_name]["problems"]:
                products[product_name]["problems"].append(problem)

    logger.info(f"Parsed {row_count} CSV rows into {len(products)} unique products")

    # Log products with multiple problems (many-to-one validation)
    multi_problem_count = sum(1 for p in products.values() if len(p["problems"]) > 1)
    logger.info(f"Products with multiple problems: {multi_problem_count}")

    return products


def load_manual_mappings() -> Dict[str, str]:
    """
    Load manual CSV → portal product mappings.

    Manual mappings take priority over fuzzy matching to ensure
    high-quality matches for products with naming differences.

    Returns:
        Dict mapping CSV product name to portal product name:
        {
            "CSV Product Name": "Portal Product Name"
        }
    """
    logger.info(f"Loading manual mappings from {MANUAL_MAPPINGS_PATH}")

    if not MANUAL_MAPPINGS_PATH.exists():
        logger.warning(f"Manual mappings file not found: {MANUAL_MAPPINGS_PATH}")
        return {}

    with open(MANUAL_MAPPINGS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mappings = {
        m["csv_product"]: m["portal_product"]
        for m in data.get("mappings", [])
    }

    logger.info(f"Loaded {len(mappings)} manual mappings")
    return mappings


def normalize_product_name(name: str) -> str:
    """
    Normalize product name for fuzzy matching.

    Normalization:
        - Convert to lowercase
        - Remove special characters (keep alphanumeric + spaces)
        - Strip whitespace

    Args:
        name: Product name to normalize

    Returns:
        Normalized product name

    Example:
        "Gewichtsconsulent - Intake Online" → "gewichtsconsulent intake online"
    """
    # Convert to lowercase
    name = name.lower()

    # Remove special characters (keep letters, numbers, spaces)
    name = re.sub(r'[^\w\s]', '', name)

    # Strip and collapse multiple spaces
    name = ' '.join(name.split())

    return name


async def get_portal_products() -> List[Dict]:
    """
    Fetch all products from database.

    Returns:
        List of product dicts with id, name, url fields
    """
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name, url
            FROM products
            ORDER BY name
        """)

    products = [dict(row) for row in rows]
    logger.info(f"Fetched {len(products)} portal products from database")

    return products


def fuzzy_match_products(
    csv_products: Dict[str, Dict],
    portal_products: List[Dict],
    manual_mappings: Dict[str, str],
    threshold: float = FUZZY_THRESHOLD
) -> Tuple[List[Tuple], List[str]]:
    """
    Match CSV products to portal products using manual mappings + fuzzy matching.

    Matching Strategy:
        1. Check manual_mappings first (priority - 10 products)
        2. Fallback to fuzzy matching with threshold (9 products expected)
        3. Log unmatched products (4 expected)

    Args:
        csv_products: Dict from parse_interventie_csv()
        portal_products: List of dicts from database
        manual_mappings: Dict from load_manual_mappings()
        threshold: Fuzzy matching threshold (default: 0.85)

    Returns:
        Tuple of:
            - matched: List of (csv_name, portal_product_dict, score, source)
            - unmatched: List of CSV product names that couldn't be matched
    """
    logger.info(f"Starting fuzzy matching with threshold: {threshold}")

    matched = []
    unmatched = []

    # Create portal product lookup by normalized name for exact matches
    portal_by_name = {p["name"]: p for p in portal_products}

    for csv_name, csv_data in csv_products.items():
        match_found = False

        # Strategy 1: Check manual mappings first (PRIORITY)
        if csv_name in manual_mappings:
            portal_name = manual_mappings[csv_name]

            # Find portal product by exact name match
            if portal_name in portal_by_name:
                portal_product = portal_by_name[portal_name]
                matched.append((csv_name, portal_product, 1.0, "manual"))
                match_found = True
                logger.info(f"✓ Manual match: '{csv_name}' → '{portal_name}'")
            else:
                logger.warning(
                    f"Manual mapping target not found in portal: '{portal_name}' "
                    f"(mapped from '{csv_name}')"
                )

        # Strategy 2: Fuzzy matching fallback
        if not match_found:
            best_match = None
            best_score = 0.0

            csv_normalized = normalize_product_name(csv_name)

            for portal_product in portal_products:
                portal_normalized = normalize_product_name(portal_product["name"])

                # Use token_sort_ratio (handles word order differences)
                score = fuzz.token_sort_ratio(csv_normalized, portal_normalized) / 100.0

                if score > best_score:
                    best_score = score
                    best_match = portal_product

            # Check if best match exceeds threshold
            if best_score >= threshold:
                matched.append((csv_name, best_match, best_score, "fuzzy"))
                match_found = True
                logger.info(
                    f"✓ Fuzzy match ({best_score:.2f}): '{csv_name}' → '{best_match['name']}'"
                )

        # Log unmatched products
        if not match_found:
            unmatched.append(csv_name)
            logger.warning(f"✗ No match found for: '{csv_name}'")

    logger.info(f"Matching complete: {len(matched)} matched, {len(unmatched)} unmatched")
    logger.info(
        f"Match breakdown: "
        f"{sum(1 for m in matched if m[3] == 'manual')} manual, "
        f"{sum(1 for m in matched if m[3] == 'fuzzy')} fuzzy"
    )

    return matched, unmatched


async def enrich_database(
    matched_products: List[Tuple],
    csv_products: Dict[str, Dict]
) -> int:
    """
    Enrich database with problem_mappings metadata for matched products.

    Updates:
        - metadata: Add problem_mappings array and csv_category
        - category: Set to CSV category
        - updated_at: Set to NOW()

    Args:
        matched_products: List of (csv_name, portal_product, score, source) tuples
        csv_products: Dict from parse_interventie_csv() with problems and category

    Returns:
        Number of products enriched
    """
    logger.info(f"Enriching {len(matched_products)} products in database")

    pool = await get_db_pool()
    enriched_count = 0

    async with pool.acquire() as conn:
        for csv_name, portal_product, score, source in matched_products:
            csv_data = csv_products[csv_name]

            # Build metadata JSON
            metadata = {
                "problem_mappings": csv_data["problems"],
                "csv_category": csv_data["category"],
                "match_score": score,
                "match_source": source
            }

            # Update product in database
            try:
                await conn.execute(
                    """
                    UPDATE products
                    SET
                        metadata = COALESCE(metadata, '{}'::jsonb) || $1::jsonb,
                        category = $2,
                        updated_at = NOW()
                    WHERE id = $3
                    """,
                    json.dumps(metadata),
                    csv_data["category"],
                    portal_product["id"]
                )
                enriched_count += 1
                logger.info(
                    f"✓ Enriched: {portal_product['name']} "
                    f"({len(csv_data['problems'])} problems, category: {csv_data['category']})"
                )
            except Exception as e:
                logger.error(f"Failed to enrich {portal_product['name']}: {e}")

    logger.info(f"Database enrichment complete: {enriched_count} products updated")
    return enriched_count


def write_unresolved_products(
    unmatched: List[str],
    csv_products: Dict[str, Dict]
) -> None:
    """
    Write unresolved products to JSON file for stakeholder review.

    Args:
        unmatched: List of CSV product names that couldn't be matched
        csv_products: Dict from parse_interventie_csv() with problems and category
    """
    logger.info(f"Writing {len(unmatched)} unresolved products to {UNRESOLVED_PATH}")

    unresolved_data = {
        "count": len(unmatched),
        "last_updated": "2025-11-05",
        "note": "These products require manual stakeholder review for portal mapping",
        "products": []
    }

    for csv_name in unmatched:
        csv_data = csv_products[csv_name]
        unresolved_data["products"].append({
            "csv_product": csv_name,
            "category": csv_data["category"],
            "problems": csv_data["problems"],
            "reason": "No fuzzy match found above 0.85 threshold and no manual mapping exists"
        })

    with open(UNRESOLVED_PATH, 'w', encoding='utf-8') as f:
        json.dump(unresolved_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Unresolved products written to {UNRESOLVED_PATH}")


async def validate_enrichment() -> Dict:
    """
    Validate database enrichment with SQL queries.

    Returns:
        Dict with validation metrics
    """
    logger.info("Validating database enrichment")

    pool = await get_db_pool()

    async with pool.acquire() as conn:
        # Count products with problem_mappings
        enriched_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM products
            WHERE metadata ? 'problem_mappings'
        """)

        # Count total products
        total_count = await conn.fetchval("SELECT COUNT(*) FROM products")

        # Sample enriched products
        samples = await conn.fetch("""
            SELECT name, category, metadata->'problem_mappings' AS problems
            FROM products
            WHERE metadata ? 'problem_mappings'
            LIMIT 3
        """)

    validation = {
        "enriched_count": enriched_count,
        "total_count": total_count,
        "enrichment_rate": f"{enriched_count / total_count * 100:.1f}%",
        "samples": [dict(row) for row in samples]
    }

    logger.info(f"Validation results:")
    logger.info(f"  - Enriched products: {enriched_count}/{total_count}")
    logger.info(f"  - Enrichment rate: {validation['enrichment_rate']}")

    return validation


async def main():
    """
    Main orchestrator for Phase 2: CSV parsing and database enrichment.

    Workflow:
        1. Parse Intervention_matrix.csv (26 rows → 23 products)
        2. Load manual mappings (10 products)
        3. Fetch portal products from database (60 products)
        4. Fuzzy match CSV → portal (threshold: 0.85)
        5. Enrich database with problem_mappings metadata
        6. Write unresolved products to JSON
        7. Validate enrichment
    """
    logger.info("=" * 60)
    logger.info("Starting FEAT-004 Phase 2: CSV Parsing & Fuzzy Matching")
    logger.info("=" * 60)

    try:
        # Step 1: Parse CSV
        csv_products = parse_interventie_csv()
        logger.info(f"Parsed {len(csv_products)} unique products from CSV")

        # Step 2: Load manual mappings
        manual_mappings = load_manual_mappings()
        logger.info(f"Loaded {len(manual_mappings)} manual mappings")

        # Step 3: Fetch portal products
        portal_products = await get_portal_products()
        logger.info(f"Fetched {len(portal_products)} portal products")

        # Step 4: Fuzzy match
        matched, unmatched = fuzzy_match_products(
            csv_products,
            portal_products,
            manual_mappings,
            threshold=FUZZY_THRESHOLD
        )
        logger.info(f"Matched: {len(matched)}, Unmatched: {len(unmatched)}")

        # Step 5: Enrich database
        enriched_count = await enrich_database(matched, csv_products)
        logger.info(f"Enriched {enriched_count} products in database")

        # Step 6: Write unresolved products
        if unmatched:
            write_unresolved_products(unmatched, csv_products)

        # Step 7: Validate
        validation = await validate_enrichment()

        logger.info("=" * 60)
        logger.info("Phase 2 Complete!")
        logger.info("=" * 60)
        logger.info(f"Summary:")
        logger.info(f"  - CSV products: {len(csv_products)}")
        logger.info(f"  - Matched: {len(matched)} ({len(matched)/len(csv_products)*100:.1f}%)")
        logger.info(f"  - Unmatched: {len(unmatched)}")
        logger.info(f"  - Database enriched: {enriched_count} products")
        logger.info(f"  - Enrichment rate: {validation['enrichment_rate']}")

        # Check if acceptance criteria met
        if enriched_count >= 19:
            logger.info("✅ AC-004-003: Fuzzy matching success rate ≥83% (19/23)")
        else:
            logger.warning(f"⚠️  AC-004-003: Expected ≥19 matches, got {enriched_count}")

        if validation["enriched_count"] >= 19:
            logger.info("✅ AC-004-004: Problem mapping enrichment complete")
        else:
            logger.warning(f"⚠️  AC-004-004: Expected ≥19 enriched, got {validation['enriched_count']}")

    except Exception as e:
        logger.error(f"Phase 2 failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
