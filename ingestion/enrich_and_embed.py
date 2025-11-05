"""
Product Embedding Generation Module

This module generates embeddings for products in the EVI 360 product catalog.
It handles both enriched products (with problem_mappings from CSV) and
non-enriched products (description only).

Phase 3 of FEAT-004: Product Catalog
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

from .embedder import EmbeddingGenerator

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def generate_embedding_text(product: Dict[str, Any]) -> str:
    """
    Generate text for product embedding.

    For enriched products (with problem_mappings), combines description with problems.
    For non-enriched products, uses description only.

    Args:
        product: Product dictionary with keys:
            - description (str): Product description
            - metadata (dict, optional): May contain problem_mappings list

    Returns:
        str: Text to be embedded

    Examples:
        >>> # Enriched product
        >>> product = {
        ...     "description": "Burn-out coaching",
        ...     "metadata": {
        ...         "problem_mappings": ["Problem 1", "Problem 2"]
        ...     }
        ... }
        >>> generate_embedding_text(product)
        'Burn-out coaching\\n\\nProblem 1\\nProblem 2'

        >>> # Non-enriched product
        >>> product = {"description": "Bedrijfsfysiotherapie", "metadata": {}}
        >>> generate_embedding_text(product)
        'Bedrijfsfysiotherapie'
    """
    description = product.get("description", "")
    metadata = product.get("metadata")

    # Handle None or missing metadata
    if not metadata:
        return description

    # Get problem_mappings from metadata
    problem_mappings = metadata.get("problem_mappings", [])

    # If no problems, return description only
    if not problem_mappings or len(problem_mappings) == 0:
        return description

    # Combine description with problems
    problems_text = "\n".join(problem_mappings)
    return f"{description}\n\n{problems_text}"


async def generate_and_store_embeddings(
    database_url: Optional[str] = None,
    batch_size: int = 100,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate embeddings for all products and store in database.

    This function:
    1. Fetches all products from database
    2. Generates embedding text (description + problems for enriched)
    3. Generates embeddings using OpenAI text-embedding-3-small
    4. Updates products table with embeddings

    Args:
        database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        batch_size: Number of products to process in each batch
        limit: Optional limit on number of products to process (for testing)

    Returns:
        Dict with statistics:
            - total_products: Total number of products in database
            - enriched_count: Number of products with problem_mappings
            - non_enriched_count: Number of products without problem_mappings
            - embeddings_generated: Number of embeddings successfully generated
            - embeddings_stored: Number of embeddings successfully stored in DB
            - errors: List of error messages (if any)
            - duration_seconds: Total processing time
    """
    start_time = datetime.now()

    # Get database URL
    if not database_url:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

    # Initialize embedding generator
    embedder = EmbeddingGenerator(
        model="text-embedding-3-small",
        batch_size=batch_size
    )

    # Connect to database
    pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)

    try:
        # Fetch all products
        async with pool.acquire() as conn:
            if limit:
                query = "SELECT * FROM products ORDER BY id LIMIT $1"
                products = await conn.fetch(query, limit)
            else:
                query = "SELECT * FROM products ORDER BY id"
                products = await conn.fetch(query)

        total_products = len(products)
        logger.info(f"Processing {total_products} products for embedding generation")

        # Convert to list of dicts and parse JSON metadata
        products_list = []
        for p in products:
            product_dict = dict(p)
            # Parse metadata JSON if it's a string
            if isinstance(product_dict.get("metadata"), str):
                try:
                    product_dict["metadata"] = json.loads(product_dict["metadata"])
                except (json.JSONDecodeError, TypeError):
                    product_dict["metadata"] = {}
            elif product_dict.get("metadata") is None:
                product_dict["metadata"] = {}
            products_list.append(product_dict)

        # Count enriched vs non-enriched
        enriched_count = sum(
            1 for p in products_list
            if p.get("metadata") and p["metadata"].get("problem_mappings")
        )
        non_enriched_count = total_products - enriched_count

        logger.info(f"Enriched products: {enriched_count}, Non-enriched: {non_enriched_count}")

        # Generate embedding texts
        embedding_texts = []
        product_ids = []

        for product in products_list:
            text = generate_embedding_text(product)
            embedding_texts.append(text)
            product_ids.append(product["id"])

        # Generate embeddings in batches
        logger.info(f"Generating embeddings (batch size: {batch_size})...")
        all_embeddings = []
        errors = []

        for i in range(0, len(embedding_texts), batch_size):
            batch_texts = embedding_texts[i:i + batch_size]
            batch_ids = product_ids[i:i + batch_size]

            try:
                # Generate embeddings for batch
                batch_embeddings = []
                for text in batch_texts:
                    embedding = await embedder.generate_embedding(text)
                    batch_embeddings.append(embedding)

                all_embeddings.extend(batch_embeddings)

                logger.info(f"Processed batch {i // batch_size + 1}/{(len(embedding_texts) + batch_size - 1) // batch_size}")

            except Exception as e:
                error_msg = f"Error generating embeddings for batch {i}-{i+len(batch_texts)}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                # Add None placeholders for failed embeddings
                all_embeddings.extend([None] * len(batch_texts))

        embeddings_generated = sum(1 for e in all_embeddings if e is not None)

        # Store embeddings in database
        logger.info(f"Storing {embeddings_generated} embeddings in database...")
        embeddings_stored = 0

        async with pool.acquire() as conn:
            for product_id, embedding in zip(product_ids, all_embeddings):
                if embedding is None:
                    continue

                try:
                    # Convert embedding list to PostgreSQL vector format string
                    embedding_str = '[' + ','.join(str(f) for f in embedding) + ']'

                    await conn.execute(
                        """
                        UPDATE products
                        SET embedding = $2::vector, updated_at = NOW()
                        WHERE id = $1
                        """,
                        product_id,
                        embedding_str
                    )
                    embeddings_stored += 1

                except Exception as e:
                    error_msg = f"Error storing embedding for product {product_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Prepare results
        results = {
            "total_products": total_products,
            "enriched_count": enriched_count,
            "non_enriched_count": non_enriched_count,
            "embeddings_generated": embeddings_generated,
            "embeddings_stored": embeddings_stored,
            "errors": errors,
            "duration_seconds": round(duration, 2)
        }

        logger.info(f"Embedding generation complete:")
        logger.info(f"  - Total products: {total_products}")
        logger.info(f"  - Enriched: {enriched_count}, Non-enriched: {non_enriched_count}")
        logger.info(f"  - Embeddings generated: {embeddings_generated}")
        logger.info(f"  - Embeddings stored: {embeddings_stored}")
        logger.info(f"  - Duration: {duration:.2f}s")
        logger.info(f"  - Errors: {len(errors)}")

        return results

    finally:
        await pool.close()


async def main():
    """
    Main entry point for running embedding generation from command line.

    Usage:
        python3 -m ingestion.enrich_and_embed
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=" * 60)
    logger.info("EVI 360 Product Embedding Generation")
    logger.info("Phase 3 of FEAT-004: Product Catalog")
    logger.info("=" * 60)

    try:
        results = await generate_and_store_embeddings()

        logger.info("=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✓ Total products: {results['total_products']}")
        logger.info(f"✓ Enriched products (with problems): {results['enriched_count']}")
        logger.info(f"✓ Non-enriched products (description only): {results['non_enriched_count']}")
        logger.info(f"✓ Embeddings generated: {results['embeddings_generated']}")
        logger.info(f"✓ Embeddings stored in database: {results['embeddings_stored']}")
        logger.info(f"✓ Processing time: {results['duration_seconds']}s")

        if results["errors"]:
            logger.warning(f"⚠ Errors encountered: {len(results['errors'])}")
            for error in results["errors"]:
                logger.warning(f"  - {error}")
        else:
            logger.info("✓ No errors encountered")

        logger.info("=" * 60)

        # Exit with error code if there were failures
        if results["embeddings_stored"] < results["total_products"]:
            logger.error(f"Failed to embed {results['total_products'] - results['embeddings_stored']} products")
            return 1

        logger.info("SUCCESS: All products embedded successfully")
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
