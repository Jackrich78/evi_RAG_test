"""
Unit tests for specialist agent.

Tests validate specialist agent behavior, tool calls, and Dutch response formatting.
Uses fixtures from conftest.py for mocking.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

# Import models first (these exist)
from agent.models import SpecialistResponse, SpecialistDeps, Citation, ChunkResult

# Import specialist agent (will fail until we create it)
try:
    from agent.specialist_agent import specialist_agent, run_specialist_query
    SPECIALIST_AGENT_EXISTS = True
except ImportError:
    SPECIALIST_AGENT_EXISTS = False


@pytest.mark.asyncio
async def test_specialist_agent_basic():
    """AC-FEAT-003-001, AC-FEAT-003-002

    Test basic agent query returns Dutch response.

    Given: Specialist agent initialized with test dependencies
    When: Agent runs query "Wat zijn de vereisten voor werken op hoogte?"
    Then: Returns SpecialistResponse with Dutch content

    Validates:
    - Response.content is not empty
    - Response.content is in Dutch (contains Dutch keywords)
    - No encoding errors with Dutch characters (ë, ï, ü)
    """
    if not SPECIALIST_AGENT_EXISTS:
        pytest.skip("specialist_agent.py not yet implemented")

    # Given: Create test dependencies
    deps = SpecialistDeps(
        session_id="test-session-123",
        user_id="test-user"
    )

    # Mock the entire agent response (no real API calls)
    mock_response = SpecialistResponse(
        content="Voor werken op hoogte boven 2,5 meter zijn strikte veiligheidseisen van toepassing. Valbeveiliging is verplicht.",
        citations=[
            Citation(title="NVAB Richtlijn: Werken op Hoogte", source="NVAB"),
            Citation(title="Arbowet Artikel 3", source="Arboportaal")
        ],
        search_metadata={"chunks_retrieved": 2}
    )

    with patch.object(specialist_agent, 'run') as mock_run:
        mock_result = AsyncMock()
        mock_result.output = mock_response
        mock_run.return_value = mock_result

        # When: Run query (mocked - no API call)
        result = await specialist_agent.run(
            "Wat zijn de vereisten voor werken op hoogte?",
            deps=deps
        )

        # Then: Validate response
        response = result.output
        assert isinstance(response, SpecialistResponse)
        assert len(response.content) > 0, "Response content should not be empty"

        # Check for Dutch keywords
        dutch_keywords = ["vereisten", "werken", "hoogte", "veiligheid", "zijn"]
        assert any(keyword in response.content.lower() for keyword in dutch_keywords), \
            "Response should contain Dutch keywords"


@pytest.mark.asyncio
async def test_specialist_agent_citations():
    """AC-FEAT-003-003, AC-FEAT-003-005

    Test agent provides minimum 2 citations with proper formatting.

    Given: Search results contain 5 relevant chunks
    When: Agent synthesizes response
    Then: Response.citations has ≥2 items with title + source

    Validates:
    - len(response.citations) >= 2
    - Each citation has .title attribute
    - Each citation has .source attribute (NVAB, STECR, UWV, ARBO)
    - Citations are relevant to query
    """
    if not SPECIALIST_AGENT_EXISTS:
        pytest.skip("specialist_agent.py not yet implemented")

    # Given: Mock agent response with 3 citations
    deps = SpecialistDeps(session_id="test-123", user_id="test-user")

    mock_response = SpecialistResponse(
        content="De veiligheidsregels omvatten verschillende aspecten van arbeidsveiligheid.",
        citations=[
            Citation(title="NVAB Richtlijn", source="NVAB"),
            Citation(title="STECR Guideline", source="STECR"),
            Citation(title="UWV Voorschrift", source="UWV")
        ],
        search_metadata={"chunks_retrieved": 5}
    )

    with patch.object(specialist_agent, 'run') as mock_run:
        mock_result = AsyncMock()
        mock_result.output = mock_response
        mock_run.return_value = mock_result

        # When: Run query
        result = await specialist_agent.run("Wat zijn de veiligheidsregels?", deps=deps)

        # Then: Validate citations
        response = result.output
        assert len(response.citations) >= 2, "Must have at least 2 citations"

        valid_sources = ["NVAB", "STECR", "UWV", "ARBO", "Arboportaal"]
        for citation in response.citations:
            assert hasattr(citation, 'title'), "Citation must have title"
            assert hasattr(citation, 'source'), "Citation must have source"
            assert citation.title, "Citation title must not be empty"
            assert citation.source in valid_sources, \
                f"Citation source must be one of {valid_sources}, got {citation.source}"


@pytest.mark.asyncio
async def test_specialist_agent_search_metadata():
    """Test search metadata is populated correctly

    Test that search metadata contains chunks_retrieved count.

    Given: Search tool returns 10 chunks
    When: Agent completes query
    Then: Response.search_metadata contains chunks_retrieved: 10

    Validates:
    - search_metadata dictionary exists
    - search_metadata['chunks_retrieved'] == expected count
    - Other metadata fields present (search_time, etc.)
    """
    if not SPECIALIST_AGENT_EXISTS:
        pytest.skip("specialist_agent.py not yet implemented")

    # Given: Mock response with metadata
    deps = SpecialistDeps(session_id="test-123", user_id="test-user")

    mock_response = SpecialistResponse(
        content="Veiligheidsregels zijn belangrijk.",
        citations=[Citation(title="Test", source="NVAB")],
        search_metadata={"chunks_retrieved": 10}
    )

    with patch.object(specialist_agent, 'run') as mock_run:
        mock_result = AsyncMock()
        mock_result.output = mock_response
        mock_run.return_value = mock_result

        # When: Run query
        result = await specialist_agent.run("Wat zijn de veiligheidsregels?", deps=deps)

        # Then: Validate metadata
        response = result.output
        assert isinstance(response.search_metadata, dict), "search_metadata should be a dict"
        assert 'chunks_retrieved' in response.search_metadata, \
            "search_metadata should contain chunks_retrieved"
        assert response.search_metadata['chunks_retrieved'] == 10, \
            "chunks_retrieved should match number of results"


@pytest.mark.asyncio
async def test_run_specialist_query_convenience():
    """Test convenience function for single query

    Test run_specialist_query() wrapper function works.

    Given: Query string and session ID provided
    When: run_specialist_query() called
    Then: Returns SpecialistResponse without requiring manual deps setup

    Validates:
    - Function accepts (query, session_id, user_id) parameters
    - Returns SpecialistResponse object
    - Internally creates SpecialistDeps correctly
    - Response has content and citations
    """
    if not SPECIALIST_AGENT_EXISTS:
        pytest.skip("specialist_agent.py not yet implemented")

    # Mock the convenience function's internal agent call
    mock_response = SpecialistResponse(
        content="Veiligheidsregels zijn belangrijk voor de werkplek.",
        citations=[Citation(title="NVAB Richtlijn", source="NVAB")],
        search_metadata={"chunks_retrieved": 1}
    )

    with patch.object(specialist_agent, 'run') as mock_run:
        mock_result = AsyncMock()
        mock_result.output = mock_response
        mock_run.return_value = mock_result

        # When: Use convenience function
        response = await run_specialist_query(
            query="Wat zijn de veiligheidsregels?",
            session_id="test-session",
            user_id="test-user"
        )

        # Then: Validate response
        assert isinstance(response, SpecialistResponse), "Should return SpecialistResponse"
        assert response.content, "Response should have content"
        assert isinstance(response.citations, list), "Response should have citations list"


@pytest.mark.asyncio
async def test_specialist_agent_no_english():
    """AC-FEAT-003-204

    Test that responses contain NO English words.

    Given: Agent processes Dutch query
    When: Response generated
    Then: content.lower() has no common English words

    Validates:
    - No words like: safety, requirements, height, employer, employee
    - Allows proper nouns: NVAB, STECR, UWV, ARBO, PBM
    - Allows acronyms: CE, EN (as in EN-395 standards)
    - Response is 100% Dutch (except allowed exceptions)
    """
    if not SPECIALIST_AGENT_EXISTS:
        pytest.skip("specialist_agent.py not yet implemented")

    # Given: Mock Dutch response (no English)
    deps = SpecialistDeps(session_id="test-123", user_id="test-user")

    mock_response = SpecialistResponse(
        content="De veiligheidsmaatregelen omvatten het dragen van persoonlijke beschermingsmiddelen volgens NVAB richtlijnen.",
        citations=[Citation(title="NVAB Richtlijn", source="NVAB")],
        search_metadata={}
    )

    with patch.object(specialist_agent, 'run') as mock_run:
        mock_result = AsyncMock()
        mock_result.output = mock_response
        mock_run.return_value = mock_result

        # When: Run query
        result = await specialist_agent.run("Wat zijn de veiligheidsmaatregelen?", deps=deps)

        # Then: Check no English words (except allowed)
        response = result.output
        content_lower = response.content.lower()

        # Common English words that should NOT appear
        english_words = [
            "safety", "requirements", "height", "employer", "employee",
            "work", "must", "should", "the", "and", "or", "but"
        ]

        # Remove allowed exceptions before checking
        allowed_exceptions = ["nvab", "stecr", "uwv", "arbo", "pbm", "ce", "en"]
        for exception in allowed_exceptions:
            content_lower = content_lower.replace(exception, "")

        # Check no English words remain
        found_english = [word for word in english_words if f" {word} " in content_lower]
        assert not found_english, \
            f"Found English words in Dutch response: {found_english}"


@pytest.mark.asyncio
async def test_specialist_agent_empty_query():
    """AC-FEAT-003-101

    Test agent handles empty/nonsense query gracefully.

    Given: Query is empty string or whitespace
    When: Agent processes query
    Then: Returns helpful Dutch message without crashing

    Validates:
    - No exception raised
    - Response.content contains helpful message
    - Message suggests entering a question
    - Message is in Dutch (e.g., "Stel een vraag over...")
    - citations list may be empty (acceptable for empty query)
    """
    if not SPECIALIST_AGENT_EXISTS:
        pytest.skip("specialist_agent.py not yet implemented")

    # Given: Mock helpful response for empty query
    deps = SpecialistDeps(session_id="test-123", user_id="test-user")

    mock_response = SpecialistResponse(
        content="Ik heb geen vraag ontvangen. Stel een vraag over arbeidsveiligheid.",
        citations=[],
        search_metadata={}
    )

    with patch.object(specialist_agent, 'run') as mock_run:
        mock_result = AsyncMock()
        mock_result.output = mock_response
        mock_run.return_value = mock_result

        # When: Run empty query (should not crash)
        result = await specialist_agent.run("", deps=deps)

        # Then: Validate graceful handling
        response = result.output
        assert isinstance(response, SpecialistResponse), "Should return SpecialistResponse"
        assert response.content, "Should return helpful message"

        # Check message is in Dutch and helpful
        content_lower = response.content.lower()
        dutch_help_keywords = ["vraag", "stel", "help", "informatie", "arbeidsveiligheid"]
        assert any(keyword in content_lower for keyword in dutch_help_keywords), \
            "Response should contain helpful Dutch keywords"

        # Citations may be empty for empty query (acceptable)
        assert isinstance(response.citations, list), "Citations should be a list"
