#!/bin/bash
###############################################################################
# Simple Monitor Script for FEAT-002 Ingestion
#
# Usage: bash simple_monitor.sh
###############################################################################

clear

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           FEAT-002 INGESTION MONITOR                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

while true; do
    # PostgreSQL counts
    PG_STATS=$(psql postgresql://postgres:postgres@localhost:5432/evi_rag -t -c "
        SELECT
            COUNT(DISTINCT d.id) as docs,
            COUNT(c.id) as chunks,
            COUNT(CASE WHEN c.embedding IS NOT NULL THEN 1 END) as embedded
        FROM documents d
        LEFT JOIN chunks c ON d.id = c.document_id;
    ")

    # Neo4j count
    NEO4J_COUNT=$(docker exec evi_rag_neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n);" 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo "0")

    # Parse PostgreSQL stats
    DOC_COUNT=$(echo $PG_STATS | awk '{print $1}')
    CHUNK_COUNT=$(echo $PG_STATS | awk '{print $3}')
    EMBEDDED_COUNT=$(echo $PG_STATS | awk '{print $5}')

    # Calculate percentage
    if [ "$CHUNK_COUNT" -gt 0 ]; then
        EMBED_PCT=$(awk "BEGIN {printf \"%.1f\", ($EMBEDDED_COUNT/$CHUNK_COUNT)*100}")
    else
        EMBED_PCT="0.0"
    fi

    # Display
    clear
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║           FEAT-002 INGESTION MONITOR                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 POSTGRESQL DATABASE"
    echo "────────────────────────────────────────────────────────────────"
    echo "  Documents:       $DOC_COUNT"
    echo "  Chunks:          $CHUNK_COUNT"
    echo "  Embedded:        $EMBEDDED_COUNT ($EMBED_PCT%)"
    echo ""
    echo "🕸️  NEO4J KNOWLEDGE GRAPH"
    echo "────────────────────────────────────────────────────────────────"
    echo "  Nodes:           $NEO4J_COUNT"
    echo ""
    echo "⏱️  Last updated: $(date '+%H:%M:%S')"
    echo ""
    echo "────────────────────────────────────────────────────────────────"
    echo "Press Ctrl+C to exit | Refreshing every 3 seconds..."
    echo "────────────────────────────────────────────────────────────────"

    sleep 3
done
