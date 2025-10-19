# Supabase Setup Guide for EVI RAG System

This guide walks you through setting up a Supabase PostgreSQL database with pgvector extension for the EVI 360 RAG system.

## Prerequisites

- A Supabase account (sign up at https://supabase.com)
- Basic familiarity with SQL and PostgreSQL

## Step 1: Create a New Supabase Project

1. Go to https://app.supabase.com
2. Click "New Project"
3. Choose your organization
4. Fill in project details:
   - **Name**: `evi-rag-system` (or your preferred name)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose closest to your location
   - **Pricing Plan**: Free tier is sufficient for development
5. Click "Create new project"
6. Wait for the project to be provisioned (2-3 minutes)

## Step 2: Enable pgvector Extension

1. In your Supabase project dashboard, go to **Database** → **Extensions**
2. Search for "vector"
3. Enable the **vector** extension
4. Alternatively, run this SQL in the SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

## Step 3: Run Base Schema

1. Go to **SQL Editor** in your Supabase dashboard
2. Click "+ New query"
3. Copy the contents of `sql/schema.sql` from this repository
4. Paste into the SQL editor
5. Click "Run" or press `Ctrl+Enter`
6. Verify tables were created successfully

## Step 4: Run EVI Schema Additions

1. In the SQL Editor, create another new query
2. Copy the contents of `sql/evi_schema_additions.sql`
3. Paste into the SQL editor
4. Click "Run"
5. Verify the following were created:
   - `tier` column added to `chunks` table
   - `products` table created
   - New functions: `search_guidelines_by_tier`, `search_products`
   - Views: `guideline_tier_stats`, `product_catalog_summary`

## Step 5: Get Connection Details

1. Go to **Project Settings** → **Database**
2. Scroll to "Connection string"
3. Choose "URI" format
4. Copy the connection string
5. It should look like:
   ```
   postgresql://postgres.xxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
   ```

## Step 6: Update Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update `DATABASE_URL` in your `.env` file:
   ```bash
   DATABASE_URL=postgresql://postgres.xxxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
   ```

3. Replace `[YOUR-PASSWORD]` with your actual database password

## Step 7: Test Connection

Run this Python script to test the connection:

```python
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

async def test_connection():
    """Test Supabase database connection."""
    database_url = os.getenv("DATABASE_URL")

    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to Supabase successfully!")

        # Test pgvector extension
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        print(f"✅ pgvector extension enabled: {result}")

        # Test tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['tablename']}")

        # Test tier column
        tier_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns
                WHERE table_name='chunks' AND column_name='tier'
            )
        """)
        print(f"✅ Tier column exists: {tier_exists}")

        # Test products table
        products_exists = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name='products'
            )
        """)
        print(f"✅ Products table exists: {products_exists}")

        await conn.close()
        print("\n🎉 All checks passed! Database is ready for use.")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Save this as `tests/test_supabase_connection.py` and run:

```bash
python3 tests/test_supabase_connection.py
```

## Step 8: Verify Dutch Language Support

Run this SQL to verify Dutch full-text search is working:

```sql
-- Test Dutch language support
SELECT to_tsvector('dutch', 'Dit is een test van de Nederlandse taal');

-- Should return something like: 'nederlands':7 'taal':8 'test':4

-- Test the hybrid_search function
SELECT * FROM hybrid_search(
    NULL::vector(1536),  -- No embedding (just text search)
    'veiligheid',        -- Dutch word for "safety"
    10,
    1.0                  -- 100% text weight
);
```

## Common Issues and Troubleshooting

### Issue: "Could not connect to database"
- **Solution**: Check your connection string is correct
- Verify your IP is allowed in Supabase settings (Database → Settings → Database)
- Ensure you're using the correct password

### Issue: "Extension 'vector' does not exist"
- **Solution**: Enable the pgvector extension in Supabase dashboard
- Go to Database → Extensions → Enable "vector"

### Issue: "Permission denied for table"
- **Solution**: Ensure you're using the `postgres` role connection string
- Check RLS (Row Level Security) policies aren't blocking access

### Issue: Dutch text search not working
- **Solution**: Verify the `hybrid_search` function was updated correctly
- Check that lines 138 and 145 in `evi_schema_additions.sql` use 'dutch' not 'english'

## Next Steps

After completing this setup:

1. ✅ Database is ready
2. ✅ pgvector extension enabled
3. ✅ Schema deployed with EVI customizations
4. ✅ Dutch language support configured

You can now proceed to:
- Set up Notion integration
- Run guideline ingestion
- Scrape and ingest products
- Test the multi-agent system

## Performance Tuning (Optional)

For production use, consider these optimizations:

```sql
-- Increase ivfflat lists for better performance with larger datasets
DROP INDEX idx_chunks_embedding;
CREATE INDEX idx_chunks_embedding ON chunks
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

DROP INDEX idx_products_embedding;
CREATE INDEX idx_products_embedding ON products
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- Add partial indexes for common queries
CREATE INDEX idx_chunks_tier_1_2 ON chunks (tier)
WHERE tier IN (1, 2);
```

## Security Recommendations

1. **Use connection pooling**: Supabase provides pooled connections automatically
2. **Rotate credentials**: Change database password periodically
3. **Enable RLS**: For production, enable Row Level Security policies
4. **Backup regularly**: Use Supabase's built-in backup features
5. **Monitor usage**: Check Supabase dashboard for usage metrics

## Support

- Supabase Documentation: https://supabase.com/docs
- pgvector GitHub: https://github.com/pgvector/pgvector
- EVI RAG Issues: [Your GitHub repo]/issues
