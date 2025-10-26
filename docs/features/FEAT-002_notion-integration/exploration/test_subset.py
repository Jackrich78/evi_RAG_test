#!/usr/bin/env python3
"""
Test subset ingestion script for FEAT-002.

Ingests only the first N files from Notion guidelines for testing.
Provides detailed validation and quality reporting.

Usage:
    python3 test_subset.py [--count N] [--verbose] [--clean]

Example:
    python3 test_subset.py --count 5 --verbose --clean
"""

import asyncio
import argparse
import os
import sys
import logging
import glob
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def run_ingestion(file_paths, clean_first=False, verbose=False):
    """
    Run ingestion on a subset of files.

    Args:
        file_paths: List of file paths to ingest
        clean_first: Whether to clean databases before ingestion
        verbose: Enable verbose logging

    Returns:
        Ingestion results
    """
    from ingestion.ingest import DocumentIngestionPipeline
    from agent.models import IngestionConfig

    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create temporary directory with subset of files
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp(prefix="feat002_test_")
    print(f"📁 Created temporary directory: {temp_dir}")

    try:
        # Copy files to temp directory
        for file_path in file_paths:
            shutil.copy(file_path, temp_dir)

        print(f"📋 Copied {len(file_paths)} files to temporary directory")

        # Create ingestion configuration
        config = IngestionConfig(
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            use_semantic_chunking=os.getenv("USE_SEMANTIC_CHUNKING", "true").lower() == "true",
            extract_entities=True,
            skip_graph_building=False  # Enable knowledge graph for full test
        )

        # Create and run pipeline
        pipeline = DocumentIngestionPipeline(
            config=config,
            documents_folder=temp_dir,
            clean_before_ingest=clean_first
        )

        def progress_callback(current, total):
            progress_pct = (current / total) * 100
            print(f"📊 Progress: {current}/{total} files ({progress_pct:.1f}%)")

        start_time = datetime.now()

        print("\n" + "="*80)
        print("🚀 STARTING INGESTION")
        print("="*80)
        print(f"Files: {len(file_paths)}")
        print(f"Clean first: {clean_first}")
        print(f"Knowledge graph: Enabled")
        print(f"Chunk size: {config.chunk_size}")
        print("="*80 + "\n")

        results = await pipeline.ingest_documents(progress_callback)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        print("\n" + "="*80)
        print("✅ INGESTION COMPLETE")
        print("="*80)
        print(f"Total time: {total_time:.2f} seconds ({total_time/60:.1f} minutes)")
        print(f"Documents processed: {len(results)}")
        print(f"Total chunks: {sum(r.chunks_created for r in results)}")
        print(f"Total entities: {sum(r.entities_extracted for r in results)}")
        print(f"Total graph episodes: {sum(r.relationships_created for r in results)}")
        print(f"Total errors: {sum(len(r.errors) for r in results)}")
        print("="*80 + "\n")

        # Print individual results
        print("📄 DOCUMENT RESULTS:")
        print("-"*80)
        for i, result in enumerate(results, 1):
            status = "✅" if not result.errors else "⚠️"
            title = result.title[:60] + "..." if len(result.title) > 60 else result.title

            print(f"{status} [{i}/{len(results)}] {title}")
            print(f"    Chunks: {result.chunks_created}, Entities: {result.entities_extracted}, "
                  f"Episodes: {result.relationships_created}, Time: {result.processing_time_ms/1000:.1f}s")

            if result.errors:
                for error in result.errors:
                    print(f"    ⚠️  Error: {error}")

        await pipeline.close()

        return results, total_time

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🧹 Cleaned up temporary directory")


async def validate_results(file_count):
    """
    Validate ingestion results in database.

    Args:
        file_count: Expected number of files ingested

    Returns:
        Validation report
    """
    import asyncpg

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    print("\n" + "="*80)
    print("🔍 VALIDATING RESULTS")
    print("="*80)

    conn = await asyncpg.connect(database_url)

    try:
        # Count documents
        doc_count = await conn.fetchval(
            "SELECT COUNT(*) FROM documents WHERE source LIKE '%notion_guidelines%'"
        )

        # Count chunks
        chunk_count = await conn.fetchval("""
            SELECT COUNT(*) FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.source LIKE '%notion_guidelines%'
        """)

        # Count chunks with embeddings
        embedded_count = await conn.fetchval("""
            SELECT COUNT(*) FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.source LIKE '%notion_guidelines%'
            AND c.embedding IS NOT NULL
        """)

        # Check metadata extraction
        metadata_sample = await conn.fetch("""
            SELECT
                title,
                metadata->>'guideline_category' as category,
                metadata->>'source_url' as url,
                metadata->>'summary' as summary
            FROM documents
            WHERE source LIKE '%notion_guidelines%'
            LIMIT 3
        """)

        # Check tier column (should be NULL)
        tier_check = await conn.fetchval("""
            SELECT COUNT(DISTINCT tier) FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.source LIKE '%notion_guidelines%'
        """)

        print(f"📊 Documents: {doc_count} (expected: {file_count})")
        print(f"📊 Chunks: {chunk_count}")
        print(f"📊 Chunks with embeddings: {embedded_count} ({embedded_count/chunk_count*100:.1f}%)")
        print(f"📊 Tier values: {tier_check} distinct values (should be 1 = NULL only)")
        print()

        # Display metadata sample
        print("📋 METADATA SAMPLE (first 3 documents):")
        print("-"*80)
        for i, row in enumerate(metadata_sample, 1):
            print(f"{i}. {row['title'][:60]}")
            print(f"   Category: {row['category'] or 'MISSING'}")
            print(f"   URL: {(row['url'][:70] + '...') if row['url'] and len(row['url']) > 70 else (row['url'] or 'MISSING')}")
            print(f"   Summary: {(row['summary'][:100] + '...') if row['summary'] and len(row['summary']) > 100 else (row['summary'] or 'MISSING')}")
            print()

        # Validation checks
        checks = {
            "documents_count": doc_count == file_count,
            "all_chunks_embedded": embedded_count == chunk_count,
            "tier_is_null": tier_check == 1,
            "metadata_extracted": all(row['category'] and row['url'] for row in metadata_sample)
        }

        print("✅ VALIDATION RESULTS:")
        print("-"*80)
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {'PASS' if passed else 'FAIL'}")

        all_passed = all(checks.values())

        return {
            "documents": doc_count,
            "chunks": chunk_count,
            "embedded": embedded_count,
            "checks": checks,
            "all_passed": all_passed
        }

    finally:
        await conn.close()


async def check_knowledge_graph():
    """Check Neo4j knowledge graph."""
    try:
        from neo4j import GraphDatabase

        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not neo4j_password:
            print("⚠️  NEO4J_PASSWORD not set, skipping graph validation")
            return None

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]

            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = result.single()["rel_count"]

            # Count episodes
            result = session.run("MATCH (e:Episode) RETURN count(e) as episode_count")
            episode_count = result.single()["episode_count"]

        driver.close()

        print("\n🕸️  KNOWLEDGE GRAPH:")
        print("-"*80)
        print(f"Total nodes: {node_count}")
        print(f"Total relationships: {rel_count}")
        print(f"Episodes: {episode_count}")

        return {
            "nodes": node_count,
            "relationships": rel_count,
            "episodes": episode_count
        }

    except Exception as e:
        print(f"⚠️  Failed to check knowledge graph: {e}")
        return None


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test ingestion with subset of Notion guidelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_subset.py                          # Test with 5 files (default)
  python3 test_subset.py --count 10 --clean       # Test with 10 files, clean first
  python3 test_subset.py --count 25 --verbose     # Test with 25 files, verbose logging
        """
    )

    parser.add_argument(
        '--count', '-n',
        type=int,
        default=5,
        help='Number of files to process (default: 5)'
    )

    parser.add_argument(
        '--clean', '-c',
        action='store_true',
        help='Clean existing data before ingestion'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Find markdown files
    guidelines_dir = Path(__file__).parent.parent.parent.parent / "documents" / "notion_guidelines"

    if not guidelines_dir.exists():
        print(f"❌ Notion guidelines directory not found: {guidelines_dir}")
        sys.exit(1)

    markdown_files = sorted(glob.glob(str(guidelines_dir / "*.md")))

    if not markdown_files:
        print(f"❌ No markdown files found in {guidelines_dir}")
        sys.exit(1)

    # Take subset
    file_subset = markdown_files[:args.count]

    print("="*80)
    print("FEAT-002 SUBSET INGESTION TEST")
    print("="*80)
    print(f"Total files available: {len(markdown_files)}")
    print(f"Files to process: {args.count}")
    print(f"Clean before ingest: {args.clean}")
    print(f"Verbose logging: {args.verbose}")
    print("="*80)
    print()

    print("📁 FILES TO PROCESS:")
    for i, file_path in enumerate(file_subset, 1):
        filename = os.path.basename(file_path)
        print(f"  {i}. {filename}")
    print()

    # Run ingestion
    try:
        results, total_time = await run_ingestion(file_subset, args.clean, args.verbose)

        # Validate results
        validation = await validate_results(args.count)

        # Check knowledge graph
        graph_stats = await check_knowledge_graph()

        # Final summary
        print("\n" + "="*80)
        print("🎉 TEST COMPLETE")
        print("="*80)
        print(f"✅ Processed {len(results)} files in {total_time:.2f}s")
        print(f"✅ Created {validation['documents']} documents")
        print(f"✅ Created {validation['chunks']} chunks")
        print(f"✅ Generated {validation['embedded']} embeddings")

        if graph_stats:
            print(f"✅ Created {graph_stats['episodes']} knowledge graph episodes")

        if validation['all_passed']:
            print("\n✅ ALL VALIDATION CHECKS PASSED")
        else:
            print("\n⚠️  SOME VALIDATION CHECKS FAILED - Review output above")

        print("="*80)

        sys.exit(0 if validation['all_passed'] else 1)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
