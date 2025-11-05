"""
Diagnostic script to investigate product search returning 0 results.

Tests:
1. SQL function search_products() directly with sample query
2. Shows ALL similarity scores (no threshold filtering)
3. Helps determine if 0.5 threshold is too high
4. Validates embedding generation and SQL function logic

Run: python3 test_product_search_diagnostic.py
"""

import asyncio
import asyncpg
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROVIDER = os.getenv("OPENAI_PROVIDER", "openai")

# Determine embedding model based on provider
if OPENAI_PROVIDER == "azure":
    EMBEDDING_MODEL = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
else:
    EMBEDDING_MODEL = "text-embedding-3-small"

# Test queries (same as used in CLI testing)
TEST_QUERIES = [
    "burn-out",
    "fysieke klachten",
    "stress begeleiding",
    "verzuim ondersteuning",
    "psychologische hulp"
]

# Initialize OpenAI client
if OPENAI_PROVIDER == "azure":
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        api_version=os.getenv("OPENAI_API_VERSION", "2024-08-01-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
else:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding using configured provider."""
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


async def test_product_search_direct(query: str, limit: int = 10):
    """
    Test search_products SQL function directly.

    Shows ALL results with similarity scores (no threshold filtering).
    """
    print(f"\n{'='*80}")
    print(f"Testing query: '{query}'")
    print(f"{'='*80}\n")

    # Generate embedding
    print("1. Generating embedding...")
    embedding = await generate_embedding(query)
    print(f"   ✓ Generated {len(embedding)}-dimensional embedding")

    # Convert to PostgreSQL vector format
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    print(f"   ✓ Converted to PostgreSQL vector format (length: {len(embedding_str)} chars)")

    # Connect to database
    print("\n2. Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    print("   ✓ Connected")

    try:
        # Execute SQL function
        print(f"\n3. Executing: search_products(embedding, '{query}', {limit})")
        results = await conn.fetch("""
            SELECT * FROM search_products($1::vector, $2::text, $3::int)
        """, embedding_str, query, limit)

        print(f"   ✓ Query returned {len(results)} products\n")

        # Display results with ALL similarity scores
        if not results:
            print("   ⚠️  NO PRODUCTS RETURNED - This indicates a deeper issue!")
            print("   Possible causes:")
            print("   - SQL function not returning any rows")
            print("   - Database has no products")
            print("   - Embedding mismatch")
        else:
            print(f"{'Product Name':<40} {'Category':<20} {'Similarity':<12} {'Pass 0.5?':<10} {'Pass 0.3?'}")
            print("-" * 100)

            above_05 = 0
            above_03 = 0

            for r in results:
                similarity = float(r["similarity"])
                pass_05 = "✓ YES" if similarity >= 0.5 else "✗ NO"
                pass_03 = "✓ YES" if similarity >= 0.3 else "✗ NO"

                if similarity >= 0.5:
                    above_05 += 1
                if similarity >= 0.3:
                    above_03 += 1

                product_name = r["name"][:37] + "..." if len(r["name"]) > 40 else r["name"]
                category = (r.get("category") or "Overig")[:17] + "..." if r.get("category") and len(r.get("category")) > 20 else (r.get("category") or "Overig")

                print(f"{product_name:<40} {category:<20} {similarity:<12.4f} {pass_05:<10} {pass_03}")

            print("\n" + "="*100)
            print(f"SUMMARY:")
            print(f"  Total products returned: {len(results)}")
            print(f"  Products with similarity >= 0.5: {above_05} ({above_05/len(results)*100:.1f}%)")
            print(f"  Products with similarity >= 0.3: {above_03} ({above_03/len(results)*100:.1f}%)")
            print(f"  Products with similarity < 0.3: {len(results) - above_03} ({(len(results)-above_03)/len(results)*100:.1f}%)")
            print("="*100)

            # Recommendation
            if above_05 == 0 and above_03 > 0:
                print(f"\n⚠️  RECOMMENDATION: Lower threshold from 0.5 to 0.3")
                print(f"   This would return {above_03} products instead of 0")
            elif above_05 == 0 and above_03 == 0:
                print(f"\n⚠️  WARNING: All products have similarity < 0.3")
                print(f"   This suggests:")
                print(f"   - Products not relevant to '{query}'")
                print(f"   - Or embedding model mismatch")
                print(f"   Consider reviewing product descriptions and embeddings")
            else:
                print(f"\n✓ Threshold 0.5 is appropriate - {above_05} products pass")

    finally:
        await conn.close()
        print("\n4. Database connection closed")


async def run_all_diagnostics():
    """Run diagnostics for all test queries."""
    print("\n" + "="*100)
    print("PRODUCT SEARCH DIAGNOSTIC TOOL")
    print("Testing search_products() SQL function with various queries")
    print("="*100)

    for query in TEST_QUERIES:
        try:
            await test_product_search_direct(query, limit=10)
        except Exception as e:
            print(f"\n❌ ERROR testing '{query}': {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*100)
    print("DIAGNOSTICS COMPLETE")
    print("="*100 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_diagnostics())
