"""
Portal product scraper using Crawl4AI.

Scrapes all products from portal.evi360.nl/products and writes to database.
Uses validated selectors from spike validation (2025-11-04).

Target: 76 products
Strategy: Incremental database writes (no JSON intermediary)
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
import asyncpg
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Portal configuration
PORTAL_BASE_URL = "https://portal.evi360.nl"
PORTAL_PRODUCTS_URL = f"{PORTAL_BASE_URL}/products"


def extract_product_urls(html: str) -> List[str]:
    """
    Extract product URLs from listing page HTML.

    Uses 'main' selector to ignore header/footer navigation links.

    Args:
        html: HTML content from products listing page

    Returns:
        List of absolute product URLs
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find main content area (ignore header/footer)
    main_content = soup.select_one("main")
    if not main_content:
        # Fallback: look for products grid
        main_content = soup.select_one(".products-grid")

    if not main_content:
        logger.warning("Could not find main content area, falling back to full page")
        main_content = soup

    # Extract product links
    product_links = []
    for link in main_content.select("a[href*='/products/']"):
        href = link.get("href")
        if href:
            # Convert to absolute URL
            absolute_url = urljoin(PORTAL_BASE_URL, href)
            # Only include product detail pages (not listing links)
            if absolute_url != PORTAL_PRODUCTS_URL:
                product_links.append(absolute_url)

    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in product_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    return unique_links


def extract_product_details(html: str, url: str) -> Dict[str, Any]:
    """
    Extract product details using VALIDATED selectors (2025-11-04).

    CRITICAL: Use div.platform-product-description container to avoid
    generic platform text (147 chars). Product-specific descriptions
    should be 922-2662 chars.

    Args:
        html: HTML content from product detail page
        url: Canonical URL of the product page

    Returns:
        Product dict with name, description, price, url, category
    """
    soup = BeautifulSoup(html, "html.parser")

    try:
        # Name (HIGH confidence selector)
        name_elem = soup.select_one("h1")
        name = name_elem.text.strip() if name_elem else None

        if not name:
            logger.error(f"No name found for product at {url}")
            return None

        # Description (CRITICAL: use container selector!)
        desc_container = soup.select_one("div.platform-product-description")
        if desc_container:
            paragraphs = desc_container.find_all("p")
            description = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
        else:
            logger.warning(f"No platform-product-description container found for {url}")
            description = None

        if not description or len(description) < 100:
            logger.warning(f"Short or missing description for {name} ({len(description) if description else 0} chars)")

        # Price (optional - may be NULL)
        price_elem = soup.select_one(".product-price")
        price = price_elem.text.strip() if price_elem else None

        # Category (NOT AVAILABLE on product pages - will be enriched from CSV)
        category = None

        return {
            "name": name,
            "description": description or "",  # Empty string fallback
            "price": price,
            "url": url,
            "category": category
        }

    except Exception as e:
        logger.error(f"Error extracting product details from {url}: {e}")
        return None


async def get_db_pool() -> asyncpg.Pool:
    """Create database connection pool."""
    return await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5
    )


async def insert_product(pool: asyncpg.Pool, product: Dict[str, Any]) -> bool:
    """
    Insert or update product in database.

    Upsert strategy: ON CONFLICT (url) DO UPDATE
    This allows re-scraping to update existing products.

    Args:
        pool: Database connection pool
        product: Product dict with name, description, price, url, category

    Returns:
        True if successful, False otherwise
    """
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO products (id, name, description, price, url, category, source, last_scraped_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW(), NOW())
                ON CONFLICT (url) DO UPDATE
                SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    category = EXCLUDED.category,
                    last_scraped_at = NOW(),
                    updated_at = NOW()
            """,
                uuid.uuid4(),
                product["name"],
                product["description"],
                product["price"],
                product["url"],
                product["category"],
                "portal"  # Source
            )
        return True
    except Exception as e:
        logger.error(f"Error inserting product {product['name']}: {e}")
        return False


async def scrape_and_insert_products() -> Dict[str, Any]:
    """
    Main scraping function: Scrape all portal products and write to database.

    Target: 76 products
    Strategy: Incremental writes (insert each product immediately after scraping)

    Returns:
        Summary dict with counts and any errors
    """
    logger.info("=" * 60)
    logger.info("Starting portal.evi360.nl product scraping")
    logger.info("=" * 60)

    # Initialize database pool
    pool = await get_db_pool()

    # Track progress
    stats = {
        "products_found": 0,
        "products_scraped": 0,
        "products_inserted": 0,
        "errors": []
    }

    try:
        async with AsyncWebCrawler() as crawler:
            # Step 1: Scrape product listing page
            logger.info(f"Fetching product listing from {PORTAL_PRODUCTS_URL}")
            listing_result = await crawler.arun(
                url=PORTAL_PRODUCTS_URL,
                bypass_cache=True
            )

            # Step 2: Extract product URLs
            product_urls = extract_product_urls(listing_result.html)
            stats["products_found"] = len(product_urls)
            logger.info(f"Found {len(product_urls)} product URLs")

            if len(product_urls) == 0:
                logger.error("No products found on listing page!")
                return stats

            # Step 3: Scrape each product page
            for idx, url in enumerate(product_urls, start=1):
                try:
                    logger.info(f"[{idx}/{len(product_urls)}] Scraping {url}")

                    # Fetch product page
                    product_result = await crawler.arun(
                        url=url,
                        bypass_cache=True
                    )

                    # Extract product details
                    product = extract_product_details(product_result.html, url)

                    if product:
                        stats["products_scraped"] += 1

                        # Insert to database immediately
                        success = await insert_product(pool, product)

                        if success:
                            stats["products_inserted"] += 1
                            logger.info(f"✓ Inserted: {product['name']} ({len(product['description'])} chars)")
                        else:
                            stats["errors"].append(f"Failed to insert: {url}")
                    else:
                        stats["errors"].append(f"Failed to extract details: {url}")

                    # Small delay to be respectful
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    stats["errors"].append(f"Error scraping {url}: {str(e)}")
                    continue

    except Exception as e:
        logger.error(f"Critical error during scraping: {e}")
        stats["errors"].append(f"Critical error: {str(e)}")
    finally:
        await pool.close()

    # Print summary
    logger.info("=" * 60)
    logger.info("Scraping Summary")
    logger.info("=" * 60)
    logger.info(f"Products found: {stats['products_found']}")
    logger.info(f"Products scraped: {stats['products_scraped']}")
    logger.info(f"Products inserted: {stats['products_inserted']}")
    logger.info(f"Errors: {len(stats['errors'])}")

    if stats['errors']:
        logger.warning("Errors encountered:")
        for error in stats['errors'][:10]:  # Show first 10
            logger.warning(f"  - {error}")

    return stats


async def main():
    """CLI entry point."""
    stats = await scrape_and_insert_products()

    # Exit code based on success
    if stats["products_inserted"] >= 70:  # Allow some failures
        logger.info("✅ Scraping completed successfully!")
        return 0
    else:
        logger.error(f"❌ Scraping failed: only {stats['products_inserted']} products inserted (expected ≥70)")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
