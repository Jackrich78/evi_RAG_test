#!/usr/bin/env python3
"""
Real-time monitoring script for ingestion progress.

Displays live statistics from PostgreSQL and Neo4j databases.
Run in a separate terminal while ingestion is running.

Usage:
    python3 monitor_progress.py [--interval SECONDS]

Example:
    python3 monitor_progress.py --interval 3
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def get_postgres_stats(conn):
    """Get statistics from PostgreSQL database."""

    # Count documents
    doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")

    # Count chunks
    chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")

    # Count chunks with embeddings
    embedded_count = await conn.fetchval(
        "SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL"
    )

    # Get notion-specific counts
    notion_docs = await conn.fetchval(
        "SELECT COUNT(*) FROM documents WHERE source LIKE '%notion_guidelines%'"
    )

    notion_chunks = await conn.fetchval("""
        SELECT COUNT(*) FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.source LIKE '%notion_guidelines%'
    """)

    # Get latest document
    latest_doc = await conn.fetchrow("""
        SELECT title, created_at
        FROM documents
        ORDER BY created_at DESC
        LIMIT 1
    """)

    return {
        "total_documents": doc_count,
        "total_chunks": chunk_count,
        "embedded_chunks": embedded_count,
        "notion_documents": notion_docs,
        "notion_chunks": notion_chunks,
        "embedding_progress": (embedded_count / chunk_count * 100) if chunk_count > 0 else 0,
        "latest_document": latest_doc["title"] if latest_doc else "None",
        "latest_time": latest_doc["created_at"] if latest_doc else None
    }


async def get_neo4j_stats():
    """Get statistics from Neo4j knowledge graph."""
    try:
        from neo4j import GraphDatabase

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not neo4j_password:
            return {"error": "NEO4J_PASSWORD not set"}

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:
            # Count all nodes
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]

            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]

            # Count episodes
            result = session.run("MATCH (e:Episode) RETURN count(e) as episode_count")
            episode_count = result.single()["episode_count"]

        driver.close()

        return {
            "total_nodes": node_count,
            "total_relationships": rel_count,
            "episodes": episode_count
        }

    except Exception as e:
        return {"error": str(e)}


def format_stats(pg_stats, neo4j_stats, start_time):
    """Format statistics for display."""

    elapsed = (datetime.now() - start_time).total_seconds()
    elapsed_mins = int(elapsed // 60)
    elapsed_secs = int(elapsed % 60)

    output = []
    output.append("\n" + "=" * 80)
    output.append("INGESTION PROGRESS MONITOR")
    output.append("=" * 80)
    output.append(f"⏱️  Runtime: {elapsed_mins}m {elapsed_secs}s | Updated: {datetime.now().strftime('%H:%M:%S')}")
    output.append("")

    # PostgreSQL stats
    output.append("📊 POSTGRESQL DATABASE")
    output.append("-" * 80)
    output.append(f"  Total Documents:     {pg_stats['total_documents']:>6,}")
    output.append(f"  ├─ Notion Guidelines: {pg_stats['notion_documents']:>6,}")
    output.append(f"  └─ Other:             {pg_stats['total_documents'] - pg_stats['notion_documents']:>6,}")
    output.append("")
    output.append(f"  Total Chunks:        {pg_stats['total_chunks']:>6,}")
    output.append(f"  ├─ From Notion:       {pg_stats['notion_chunks']:>6,}")
    output.append(f"  └─ With Embeddings:   {pg_stats['embedded_chunks']:>6,} ({pg_stats['embedding_progress']:.1f}%)")
    output.append("")

    if pg_stats['latest_document'] and pg_stats['latest_document'] != "None":
        doc_title = pg_stats['latest_document'][:60] + "..." if len(pg_stats['latest_document']) > 60 else pg_stats['latest_document']
        time_str = pg_stats['latest_time'].strftime('%H:%M:%S') if pg_stats['latest_time'] else "Unknown"
        output.append(f"  Latest Document:     {doc_title}")
        output.append(f"  Ingested at:         {time_str}")
    else:
        output.append(f"  Latest Document:     None yet")

    output.append("")

    # Neo4j stats
    output.append("🕸️  NEO4J KNOWLEDGE GRAPH")
    output.append("-" * 80)

    if "error" in neo4j_stats:
        output.append(f"  ❌ Error: {neo4j_stats['error']}")
    else:
        output.append(f"  Total Nodes:         {neo4j_stats['total_nodes']:>6,}")
        output.append(f"  Total Relationships: {neo4j_stats['total_relationships']:>6,}")
        output.append(f"  Episodes Created:    {neo4j_stats['episodes']:>6,}")

    output.append("")
    output.append("=" * 80)
    output.append("Press Ctrl+C to exit")
    output.append("=" * 80)

    return "\n".join(output)


async def monitor_loop(interval=3):
    """Main monitoring loop."""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)

    print("🚀 Starting ingestion monitor...")
    print(f"📊 Refresh interval: {interval} seconds")
    print("⌨️  Press Ctrl+C to stop")

    start_time = datetime.now()

    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(database_url)

        while True:
            try:
                # Get stats
                pg_stats = await get_postgres_stats(conn)
                neo4j_stats = await get_neo4j_stats()

                # Clear screen and display
                os.system('clear' if os.name == 'posix' else 'cls')
                print(format_stats(pg_stats, neo4j_stats, start_time))

                # Wait
                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Error during monitoring: {e}")
                await asyncio.sleep(interval)

        # Close connection
        await conn.close()
        print("\n\n✅ Monitor stopped")

    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)


def main():
    """Parse arguments and run monitor."""
    parser = argparse.ArgumentParser(
        description="Monitor ingestion progress in real-time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 monitor_progress.py                    # Default 3-second refresh
  python3 monitor_progress.py --interval 5       # 5-second refresh
  python3 monitor_progress.py --interval 1       # 1-second refresh (fast)
        """
    )

    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=3,
        help='Refresh interval in seconds (default: 3)'
    )

    args = parser.parse_args()

    if args.interval < 1:
        print("❌ Interval must be at least 1 second")
        sys.exit(1)

    try:
        asyncio.run(monitor_loop(args.interval))
    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped by user")


if __name__ == "__main__":
    main()
