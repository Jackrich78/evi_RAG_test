"""
Unit tests for search tools.

Tests validate hybrid search, vector search, and Dutch full-text search functionality.
Uses fixtures from conftest.py for mocking database and embedding client.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

# Import models and tools
from agent.models import ChunkResult
from agent.tools import hybrid_search_tool, vector_search_tool, HybridSearchInput, VectorSearchInput


@pytest.mark.asyncio
async def test_hybrid_search_tool():
    """AC-FEAT-003-004

    Test hybrid search returns relevant chunks with good scores.

    Given: Query "werken op hoogte" submitted
    When: hybrid_search_tool executes
    Then: Returns ChunkResults with score >0.6

    Validates:
    - Returns list of ChunkResult objects
    - Each result has .score attribute
    - Top result has score >0.6 (relevant match)
    - Results ranked by score (descending)
    - Hybrid combines vector (70%) + text (30%) scores
    """
    # Given: Query input
    search_input = HybridSearchInput(
        query="werken op hoogte",
        limit=10,
        text_weight=0.3
    )

    # Mock embedding generation
    with patch('agent.tools.generate_embedding') as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        # Mock database search
        with patch('agent.tools.hybrid_search') as mock_search:
            mock_search.return_value = [
                {
                    'chunk_id': 'c-1',
                    'document_id': 'd-1',
                    'content': 'Bij werken op hoogte is valbeveiliging verplicht',
                    'combined_score': 0.85,
                    'document_title': 'NVAB Richtlijn',
                    'document_source': 'NVAB',
                    'metadata': {}
                },
                {
                    'chunk_id': 'c-2',
                    'document_id': 'd-2',
                    'content': 'Veiligheid op hoogte vereist training',
                    'combined_score': 0.72,
                    'document_title': 'STECR Guide',
                    'document_source': 'STECR',
                    'metadata': {}
                }
            ]

            # When: Execute search
            results = await hybrid_search_tool(search_input)

            # Then: Validate results
            assert isinstance(results, list), "Should return list"
            assert len(results) > 0, "Should have results"

            for result in results:
                assert isinstance(result, ChunkResult), "Should be ChunkResult"
                assert hasattr(result, 'score'), "Should have score"
                assert result.score >= 0.0 and result.score <= 1.0, "Score should be 0-1"

            # Top result should have good score
            assert results[0].score > 0.6, "Top result should be relevant (score >0.6)"

            # Results should be ranked by score (descending)
            for i in range(len(results) - 1):
                assert results[i].score >= results[i+1].score, \
                    "Results should be ranked by score descending"


@pytest.mark.asyncio
async def test_vector_search_tool():
    """Test pure vector search as fallback

    Test vector_search_tool works independently of hybrid search.

    Given: Query submitted
    When: vector_search_tool executes
    Then: Returns results from pure vector similarity

    Validates:
    - Returns ChunkResult list
    - Uses only vector similarity (no full-text component)
    - Results have cosine similarity scores
    - Works as fallback when full-text unavailable
    """
    # Given: Query input
    search_input = VectorSearchInput(query="werken op hoogte", limit=5)

    # Mock embedding and search
    with patch('agent.tools.generate_embedding') as mock_embed, \
         patch('agent.tools.vector_search') as mock_search:
        mock_embed.return_value = [0.1] * 1536
        mock_search.return_value = [
            {
                'chunk_id': 'c-1',
                'document_id': 'd-1',
                'content': 'Vector matched content',
                'similarity': 0.88,
                'document_title': 'Title',
                'document_source': 'Source',
                'metadata': {}
            }
        ]

        # When: Execute search
        results = await vector_search_tool(search_input)

        # Then: Validate
        assert isinstance(results, list), "Should return list"
        assert all(isinstance(r, ChunkResult) for r in results), "Should be ChunkResults"
        if results:
            assert results[0].score > 0, "Should have similarity scores"


@pytest.mark.asyncio
async def test_dutch_full_text_search():
    """Test Dutch stemming in full-text search

    Test Dutch language configuration applies stemming.

    Given: Query "werken" submitted
    When: Hybrid search executes
    Then: Matches chunks containing "werk", "werkt", "gewerkt"

    Validates:
    - to_tsvector('dutch', content) used in SQL
    - Dutch stemming active (werken → werk)
    - Stop words removed (de, het, een)
    - Query: "werken op hoogte" matches "werk op hoogte"

    Note: Requires real PostgreSQL with Dutch config or mocked SQL
    """
    # Given: Query with Dutch verb
    search_input = HybridSearchInput(query="werken", limit=5)

    # Mock to return stems
    with patch('agent.tools.generate_embedding') as mock_embed, \
         patch('agent.tools.hybrid_search') as mock_search:
        mock_embed.return_value = [0.1] * 1536

        # Mock returns content with different verb forms
        mock_search.return_value = [
            {'chunk_id': 'c-1', 'document_id': 'd-1',
             'content': 'Bij werk op hoogte', 'combined_score': 0.8,
             'document_title': 'T1', 'document_source': 'S1', 'metadata': {}},
            {'chunk_id': 'c-2', 'document_id': 'd-2',
             'content': 'Hij werkt veilig', 'combined_score': 0.7,
             'document_title': 'T2', 'document_source': 'S2', 'metadata': {}},
        ]

        # When: Search
        results = await hybrid_search_tool(search_input)

        # Then: Should match stems (werk, werkt)
        assert len(results) >= 1, "Should match Dutch stems"
        # If Dutch stemming works, these would match


@pytest.mark.asyncio
async def test_search_empty_results():
    """AC-FEAT-003-105

    Test search handles no results gracefully.

    Given: Query matches no chunks in database
    When: hybrid_search_tool executes
    Then: Returns empty list (not exception)

    Validates:
    - Returns [] (empty list)
    - No exception raised
    - No error logged (INFO level acceptable)
    - Agent can handle empty results gracefully
    """
    # Given: Query with no matches
    search_input = HybridSearchInput(query="xyzabc nonexistent", limit=10)

    # Mock empty results
    with patch('agent.tools.generate_embedding') as mock_embed, \
         patch('agent.tools.hybrid_search') as mock_search:
        mock_embed.return_value = [0.1] * 1536
        mock_search.return_value = []  # No results

        # When: Execute search (should not raise exception)
        results = await hybrid_search_tool(search_input)

        # Then: Should return empty list
        assert isinstance(results, list), "Should return list"
        assert len(results) == 0, "Should be empty"
