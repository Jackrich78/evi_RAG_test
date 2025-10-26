#!/usr/bin/env python3
"""
Test knowledge graph functionality with current data.
Tests Graphiti search and relationship queries.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agent.graph_utils import GraphitiClient


async def test_knowledge_graph():
    """Test knowledge graph search and relationships."""

    print("=" * 80)
    print("🧪 Testing Knowledge Graph with Current Data")
    print("=" * 80)
    print()

    # Initialize Graphiti client
    client = GraphitiClient()
    await client.initialize()

    print("✅ Graphiti client initialized")
    print()

    # Test queries (Dutch - matching EVI 360 content)
    test_queries = [
        "veiligheid op de werkplek",  # workplace safety
        "prikaccidenten",  # needle stick accidents
        "beschermingsmiddelen",  # protective equipment
        "aanstellingskeuring",  # pre-employment medical exam
        "ARBO regelgeving",  # occupational health regulations
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"📍 Test {i}/{len(test_queries)}: '{query}'")
        print("-" * 80)

        try:
            # Search knowledge graph
            results = await client.search(query)

            if results:
                print(f"✅ Found {len(results)} results")
                print()

                # Show first 3 results
                for j, result in enumerate(results[:3], 1):
                    print(f"  Result {j}:")
                    print(f"    Fact: {result.get('fact', 'N/A')[:200]}...")
                    print(f"    UUID: {result.get('uuid', 'N/A')}")
                    if result.get('valid_at'):
                        print(f"    Valid At: {result['valid_at']}")
                    print()

                if len(results) > 3:
                    print(f"  ... and {len(results) - 3} more results")
                    print()
            else:
                print("❌ No results found")
                print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print()

        print()

    # Test relationship query
    print("=" * 80)
    print("🔗 Testing Entity Relationships")
    print("=" * 80)
    print()

    try:
        entity_name = "werkgever"  # employer
        print(f"📍 Getting entities related to: '{entity_name}'")
        print("-" * 80)

        related = await client.get_related_entities(entity_name)

        if related.get('facts'):
            print(f"✅ Found {len(related['facts'])} related facts")
            print()

            for i, fact in enumerate(related['facts'][:5], 1):
                print(f"  Fact {i}:")
                print(f"    {fact.get('fact', 'N/A')[:200]}...")
                print()
        else:
            print("❌ No related entities found")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")
        print()

    # Get graph statistics
    print("=" * 80)
    print("📊 Knowledge Graph Statistics")
    print("=" * 80)
    print()

    try:
        # Query Neo4j directly for stats
        from neo4j import AsyncGraphDatabase
        import os

        driver = AsyncGraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password123"))
        )

        async with driver.session() as session:
            # Count nodes by type
            result = await session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            records = await result.data()

            print("Node counts by type:")
            for record in records:
                print(f"  {record['label']}: {record['count']}")
            print()

            # Count relationships
            result = await session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            records = await result.data()

            print("Relationship counts by type:")
            for record in records:
                print(f"  {record['type']}: {record['count']}")
            print()

        await driver.close()

    except Exception as e:
        print(f"⚠️  Could not get detailed statistics: {e}")
        print()

    # Close client
    await client.close()
    print("✅ Test complete")
    print()


if __name__ == "__main__":
    asyncio.run(test_knowledge_graph())
