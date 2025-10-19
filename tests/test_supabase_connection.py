"""
Test Supabase database connection and schema setup.

Run this script after setting up your Supabase project to verify:
1. Database connection works
2. pgvector extension is enabled
3. All required tables exist
4. EVI schema additions (tier column, products table) are in place
"""

import asyncio
import asyncpg
from dotenv import load_dotenv
import os
import sys

load_dotenv()


async def test_connection():
    """
    Test Supabase database connection and schema.

    Returns:
        bool: True if all checks pass, False otherwise.
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Please set DATABASE_URL in your .env file")
        return False

    try:
        print("Testing Supabase connection...")
        print(f"Database URL: {database_url[:30]}...")

        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to Supabase successfully!")

        # Test pgvector extension
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        if result:
            print("✅ pgvector extension enabled")
        else:
            print("❌ pgvector extension NOT enabled")
            print("   Enable it in Supabase: Database → Extensions → vector")
            return False

        # Test base tables from schema.sql
        expected_tables = ['documents', 'chunks', 'sessions', 'messages', 'products']
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        table_names = [t['tablename'] for t in tables]

        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            marker = "✓" if table['tablename'] in expected_tables else "•"
            print(f"   {marker} {table['tablename']}")

        # Check for missing tables
        missing_tables = set(expected_tables) - set(table_names)
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            print("   Run sql/schema.sql and sql/evi_schema_additions.sql")
            return False

        # Test tier column (from evi_schema_additions.sql)
        tier_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns
                WHERE table_name='chunks' AND column_name='tier'
            )
        """)
        if tier_exists:
            print("✅ Tier column exists in chunks table")
        else:
            print("❌ Tier column NOT found in chunks table")
            print("   Run sql/evi_schema_additions.sql")
            return False

        # Test products table
        products_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name='products'
            )
        """)
        if products_exists:
            print("✅ Products table exists")

            # Check products table columns
            product_columns = await conn.fetch("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='products'
                ORDER BY ordinal_position
            """)
            expected_product_cols = [
                'id', 'name', 'description', 'url', 'category',
                'subcategory', 'embedding', 'compliance_tags', 'metadata'
            ]
            product_col_names = [c['column_name'] for c in product_columns]

            missing_cols = set(expected_product_cols) - set(product_col_names)
            if missing_cols:
                print(f"⚠️  Products table missing columns: {', '.join(missing_cols)}")
            else:
                print(f"✅ Products table has all required columns ({len(product_col_names)} total)")
        else:
            print("❌ Products table NOT found")
            print("   Run sql/evi_schema_additions.sql")
            return False

        # Test Dutch language support in hybrid_search function
        print("\nTesting Dutch language support...")
        try:
            # Test to_tsvector with Dutch
            dutch_test = await conn.fetchval(
                "SELECT to_tsvector('dutch', 'Dit is een test van de Nederlandse taal')"
            )
            if dutch_test:
                print("✅ Dutch language support enabled in PostgreSQL")
            else:
                print("⚠️  Dutch language test returned empty result")

            # Check if hybrid_search function exists
            hybrid_search_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_proc
                    WHERE proname = 'hybrid_search'
                )
            """)
            if hybrid_search_exists:
                print("✅ hybrid_search function exists")
            else:
                print("❌ hybrid_search function NOT found")
                return False

            # Check if search_guidelines_by_tier function exists
            tier_search_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_proc
                    WHERE proname = 'search_guidelines_by_tier'
                )
            """)
            if tier_search_exists:
                print("✅ search_guidelines_by_tier function exists")
            else:
                print("❌ search_guidelines_by_tier function NOT found")
                print("   Run sql/evi_schema_additions.sql")
                return False

            # Check if search_products function exists
            product_search_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_proc
                    WHERE proname = 'search_products'
                )
            """)
            if product_search_exists:
                print("✅ search_products function exists")
            else:
                print("❌ search_products function NOT found")
                print("   Run sql/evi_schema_additions.sql")
                return False

        except Exception as e:
            print(f"⚠️  Error testing Dutch language support: {e}")

        # Test views
        print("\nTesting views...")
        views = await conn.fetch("""
            SELECT viewname FROM pg_views
            WHERE schemaname = 'public'
            ORDER BY viewname
        """)
        expected_views = [
            'document_summaries',
            'guideline_tier_stats',
            'product_catalog_summary'
        ]
        view_names = [v['viewname'] for v in views]

        for view in expected_views:
            if view in view_names:
                print(f"✅ View '{view}' exists")
            else:
                print(f"⚠️  View '{view}' NOT found (run sql/evi_schema_additions.sql)")

        await conn.close()

        print("\n" + "=" * 60)
        print("🎉 All essential checks passed! Database is ready for use.")
        print("=" * 60)
        return True

    except asyncpg.exceptions.InvalidPasswordError:
        print("❌ Invalid database password")
        print("   Check your DATABASE_URL in .env")
        return False
    except asyncpg.exceptions.InvalidCatalogNameError:
        print("❌ Database does not exist")
        print("   Check your DATABASE_URL in .env")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
