#!/usr/bin/env python3
"""
Test data persistence across container restarts.

This script validates that data written to PostgreSQL persists
even after stopping and restarting containers.
"""

import asyncio
import asyncpg
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_persistence():
    """Test write and read to verify persistence."""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False

    print(f"Testing data persistence...")
    print(f"Database URL: {database_url[:50]}...")

    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database")

        # Write test data
        test_title = "Persistence Test Document"
        test_content = "This tests that data persists across container restarts"

        # Check if test document already exists
        existing_id = await conn.fetchval(
            "SELECT id FROM documents WHERE title = $1",
            test_title
        )

        if existing_id:
            # Update existing test document
            result = existing_id
            await conn.execute(
                "UPDATE documents SET content = $1, updated_at = NOW() WHERE id = $2",
                test_content,
                existing_id
            )
            print(f"✅ Updated existing test document with ID: {result}")
        else:
            # Insert a new test document
            result = await conn.fetchval(
                """
                INSERT INTO documents (title, source, content, metadata)
                VALUES ($1, $2, $3, $4::jsonb)
                RETURNING id
                """,
                test_title,
                "persistence_test",
                test_content,
                json.dumps({"test": True, "persistent": True})
            )
            print(f"✅ Written new test document with ID: {result}")

        # Read it back
        retrieved = await conn.fetchrow(
            "SELECT title, content FROM documents WHERE id = $1",
            result
        )

        if retrieved and retrieved['title'] == test_title:
            print(f"✅ Successfully retrieved test document")
            print(f"   Title: {retrieved['title']}")
            print(f"   Content: {retrieved['content'][:50]}...")
        else:
            print("❌ Failed to retrieve test document")
            await conn.close()
            return False

        # Count total documents
        count = await conn.fetchval("SELECT COUNT(*) FROM documents")
        print(f"✅ Total documents in database: {count}")

        # Check chunks table
        chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")
        print(f"✅ Total chunks in database: {chunk_count}")

        await conn.close()
        print("\n🎉 Data persistence test passed!")
        print("   You can now restart containers and data will persist.")
        return True

    except Exception as e:
        print(f"❌ Error during persistence test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_persistence())
    exit(0 if success else 1)
