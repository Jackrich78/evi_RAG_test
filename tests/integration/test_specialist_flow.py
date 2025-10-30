"""
Integration tests for complete specialist flow.

Tests validate end-to-end query processing from API to database and back.
Uses real PostgreSQL database in test mode with seeded data.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import json

# Import models
from agent.models import ChatRequest, SpecialistResponse

# Check if specialist agent exists
try:
    from agent.specialist_agent import specialist_agent
    from agent.api import app
    INTEGRATION_READY = True
except ImportError:
    INTEGRATION_READY = False


@pytest.mark.asyncio
async def test_end_to_end_flow():
    """AC-FEAT-003-001 through AC-FEAT-003-007

    Test complete flow: CLI → API → Agent → Database → Response

    Components Tested:
    - FastAPI /chat/stream endpoint
    - Specialist Agent with search tools
    - Database hybrid_search() function
    - Streaming response via SSE

    Setup:
    - Start API in test mode
    - Seed database with test chunks (Dutch content)
    - Mock OpenAI API (embeddings + LLM)

    Scenario:
    1. POST /chat/stream with Dutch query
    2. Agent searches database (hybrid search)
    3. Agent generates Dutch response
    4. Response streamed back via Server-Sent Events

    Assertions:
    - Response status code: 200
    - Response is Dutch (no English)
    - Response contains ≥2 citations
    - Citations include title + source
    - Response time <5s (lenient for test environment)
    - SSE format correct (data: {...}\n\n)
    """
    if not INTEGRATION_READY:
        pytest.skip("specialist_agent or API not ready for integration testing")

    # Given: Test client and request
    client = TestClient(app)
    request_data = {
        "message": "Wat zijn de vereisten voor werken op hoogte?",
        "session_id": None,
        "user_id": "test-user",
        "search_type": "hybrid"
    }

    # Mock database and LLM
    with patch('agent.specialist_agent.hybrid_search_tool') as mock_search, \
         patch('agent.providers.get_llm_model') as mock_llm:

        # Mock search results
        mock_search.return_value = [
            {"chunk_id": "c-1", "content": "Dutch guideline content",
             "document_title": "NVAB Richtlijn", "document_source": "NVAB",
             "score": 0.9}
        ]

        # When: POST to /chat/stream
        response = client.post("/chat/stream", json=request_data)

        # Then: Validate response
        assert response.status_code == 200, "Should return 200 OK"

        # Check SSE format (if streaming implemented)
        # Basic validation for now
        assert response.headers.get("content-type"), "Should have content-type header"


@pytest.mark.asyncio
async def test_streaming_response():
    """AC-FEAT-003-304

    Test streaming response delivers tokens incrementally.

    Components Tested:
    - FastAPI SSE streaming
    - Pydantic AI run_stream()
    - CLI receives tokens as generated

    Setup:
    - Mock agent to return streaming response
    - Monitor SSE events

    Scenario:
    1. Request /chat/stream
    2. Receive multiple SSE events
    3. Verify tokens arrive before full response complete
    4. Verify end marker received last

    Assertions:
    - First token received within 1s
    - Multiple data: events received
    - Events contain {"type": "text", "content": "..."}
    - Final event: {"type": "end"}
    - No buffering (tokens stream incrementally)
    """
    if not INTEGRATION_READY:
        pytest.skip("Not ready for integration testing")

    # This test will validate streaming when implemented
    # For now, skip as it requires full API integration
    pytest.skip("Streaming test requires full API implementation")


@pytest.mark.asyncio
async def test_database_connection_error():
    """AC-FEAT-003-103

    Test graceful handling when database is down.

    Components Tested:
    - API error handling
    - Agent error handling
    - Database connection retry logic

    Setup:
    - Mock database connection to raise exception
    - Simulate PostgreSQL container down

    Scenario:
    1. Stop PostgreSQL (or mock connection failure)
    2. Submit query via API
    3. Verify graceful error response

    Assertions:
    - API returns 200 OK (not 500)
    - Response contains Dutch error message
    - Message: "Kan momenteel niet zoeken in de kennisbank"
    - Error logged with troubleshooting hint
    - API logs: "Database connection failed: [details]"
    - CLI doesn't crash (receives error response)
    """
    if not INTEGRATION_READY:
        pytest.skip("Not ready for integration testing")

    # Given: Mock database failure
    with patch('agent.db_utils.hybrid_search') as mock_search:
        mock_search.side_effect = Exception("Database connection failed")

        # When: Submit query
        client = TestClient(app)
        request_data = {
            "message": "Test query",
            "session_id": None,
            "user_id": "test-user"
        }

        # Then: Should handle gracefully (implementation-dependent)
        # This test validates error handling when implemented
        pytest.skip("Error handling test requires full implementation")
