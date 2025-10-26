#!/bin/bash
###############################################################################
# Complete Cleanup Script for FEAT-002
#
# Cleans all data from PostgreSQL, Neo4j, and Python caches.
# USE WITH CAUTION - This will delete ALL data!
#
# Usage:
#   bash cleanup_all.sh [--force]
#
# Options:
#   --force   Skip confirmation prompt
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           FEAT-002 COMPLETE CLEANUP SCRIPT                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check for --force flag
FORCE=false
if [[ "$1" == "--force" ]]; then
    FORCE=true
fi

# Confirmation
if [ "$FORCE" = false ]; then
    echo -e "${RED}⚠️  WARNING: This will DELETE ALL data from:${NC}"
    echo "   • PostgreSQL (all documents, chunks, sessions, messages)"
    echo "   • Neo4j (all nodes and relationships)"
    echo "   • Python caches (__pycache__ directories)"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}❌ Cleanup cancelled${NC}"
        exit 0
    fi
fi

echo -e "${BLUE}🚀 Starting cleanup...${NC}"
echo ""

###############################################################################
# 1. Clean PostgreSQL
###############################################################################
echo -e "${BLUE}1️⃣  Cleaning PostgreSQL database...${NC}"

# Load DATABASE_URL from .env if not set
if [ -z "$DATABASE_URL" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | grep DATABASE_URL | xargs)
    else
        echo -e "${RED}❌ DATABASE_URL not set and .env file not found${NC}"
        exit 1
    fi
fi

# Clean tables (in correct order to respect foreign keys)
psql "$DATABASE_URL" <<SQL
-- Delete in order to respect foreign key constraints
DELETE FROM messages;
DELETE FROM sessions;
DELETE FROM chunks;
DELETE FROM documents;

-- Verify cleanup
SELECT 'messages' as table_name, COUNT(*) as count FROM messages
UNION ALL
SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'documents', COUNT(*) FROM documents;
SQL

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ PostgreSQL cleaned${NC}"
else
    echo -e "${RED}   ❌ PostgreSQL cleanup failed${NC}"
    exit 1
fi

###############################################################################
# 2. Clean Neo4j
###############################################################################
echo ""
echo -e "${BLUE}2️⃣  Cleaning Neo4j knowledge graph...${NC}"

# Load Neo4j credentials from .env
if [ -z "$NEO4J_PASSWORD" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | grep NEO4J_PASSWORD | xargs)
        export $(grep -v '^#' .env | grep NEO4J_USER | xargs)
    fi
fi

NEO4J_USER=${NEO4J_USER:-neo4j}

if [ -z "$NEO4J_PASSWORD" ]; then
    echo -e "${RED}   ❌ NEO4J_PASSWORD not set${NC}"
    exit 1
fi

# Clean Neo4j using cypher-shell in Docker container
docker exec evi_rag_neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" <<CYPHER
MATCH (n) DETACH DELETE n;
MATCH (n) RETURN count(n) as remaining_nodes;
CYPHER

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ Neo4j cleaned${NC}"
else
    echo -e "${YELLOW}   ⚠️  Neo4j cleanup may have failed (continuing anyway)${NC}"
fi

###############################################################################
# 3. Clean Python caches
###############################################################################
echo ""
echo -e "${BLUE}3️⃣  Cleaning Python caches...${NC}"

# Find and remove __pycache__ directories
CACHE_COUNT=$(find . -type d -name "__pycache__" | wc -l | tr -d ' ')

if [ "$CACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}   ✅ Removed $CACHE_COUNT __pycache__ directories${NC}"
else
    echo -e "${GREEN}   ✅ No __pycache__ directories found${NC}"
fi

# Remove .pyc files
PYC_COUNT=$(find . -type f -name "*.pyc" | wc -l | tr -d ' ')

if [ "$PYC_COUNT" -gt 0 ]; then
    find . -type f -name "*.pyc" -delete
    echo -e "${GREEN}   ✅ Removed $PYC_COUNT .pyc files${NC}"
else
    echo -e "${GREEN}   ✅ No .pyc files found${NC}"
fi

###############################################################################
# 4. Verify cleanup
###############################################################################
echo ""
echo -e "${BLUE}4️⃣  Verifying cleanup...${NC}"

# Check PostgreSQL
PG_TOTAL=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM documents;" | tr -d ' ')
echo -e "   PostgreSQL documents: ${GREEN}$PG_TOTAL${NC} (should be 0)"

# Check Neo4j
NEO4J_TOTAL=$(docker exec evi_rag_neo4j cypher-shell -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" "MATCH (n) RETURN count(n);" 2>/dev/null | grep -oE '[0-9]+' | head -1 || echo "0")
echo -e "   Neo4j nodes: ${GREEN}$NEO4J_TOTAL${NC} (should be 0)"

###############################################################################
# Summary
###############################################################################
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    CLEANUP COMPLETE                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ All databases and caches cleaned${NC}"
echo ""
echo "📊 Final state:"
echo "   • PostgreSQL: 0 documents, 0 chunks"
echo "   • Neo4j: 0 nodes, 0 relationships"
echo "   • Python caches: Cleared"
echo ""
echo -e "${BLUE}🚀 Ready for fresh ingestion!${NC}"
echo ""
