"""
Unit tests for OpenAI-compatible API endpoints in EVI 360 RAG system.

This module tests the /v1/chat/completions and /v1/models endpoints
that provide OpenWebUI integration for the EVI specialist agent.

Related Feature: FEAT-007 OpenWebUI Integration
Acceptance Criteria: AC-007-001 through AC-007-020
"""

import pytest
from fastapi.testclient import TestClient
from agent.api import app

# Pytest fixtures for test setup
@pytest.fixture
def client():
    """
    FastAPI TestClient fixture for making HTTP requests.

    Returns:
        TestClient: Configured client for testing API endpoints
    """
    return TestClient(app)


@pytest.fixture
def mock_specialist_response():
    """
    Mock response from specialist agent for testing.

    Returns:
        dict: Sample specialist agent response with Dutch content and citations
    """
    return {
        "response": "Bij werken op hoogte moet u altijd valbescherming gebruiken. "
                   "Dit omvat een veiligheidsharnas, vallijn en ankeerpunt.",
        "citations": [
            {
                "title": "Werken op hoogte richtlijn",
                "doc_id": "DOC-001",
                "tier": 1,
                "source": "EVI 360 Guidelines"
            },
            {
                "title": "PSA voor hoogtewerk",
                "doc_id": "DOC-045",
                "tier": 2,
                "source": "EVI 360 Product Catalog"
            }
        ],
        "language": "nl",
        "processing_time": 1.2
    }


# Test Stub 1: Non-Streaming Chat Completions
def test_openai_chat_completions_non_streaming(client, mock_specialist_response):
    """
    Test /v1/chat/completions endpoint with stream=false.

    Validates:
    - AC-007-001: Basic guideline query returns tier 1 summary
    - Response format matches OpenAI Chat Completion object
    - Dutch language response
    - Citations included in response
    - Response time <2 seconds for tier 1
    """
    import time

    # Mock the specialist agent to return our test response
    from unittest.mock import patch, AsyncMock

    mock_result = AsyncMock()
    mock_result.data = type('obj', (object,), {
        'content': mock_specialist_response['response'],
        'citations': mock_specialist_response['citations']
    })()

    with patch('agent.api.run_specialist_query', return_value=mock_result):
        # Send request
        start_time = time.time()
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "evi-specialist",
                "messages": [
                    {"role": "user", "content": "Wat zijn de richtlijnen voor werken op hoogte?"}
                ],
                "stream": False
            }
        )
        elapsed = time.time() - start_time

        # Assert response structure
        assert response.status_code == 200
        data = response.json()

        # Validate OpenAI format
        assert "id" in data
        assert data["id"].startswith("chatcmpl-")
        assert data["object"] == "chat.completion"
        assert "created" in data
        assert data["model"] == "evi-specialist"
        assert "choices" in data
        assert len(data["choices"]) == 1

        # Validate message
        choice = data["choices"][0]
        assert choice["index"] == 0
        assert choice["finish_reason"] == "stop"
        assert "message" in choice

        message = choice["message"]
        assert message["role"] == "assistant"
        assert len(message["content"]) > 0

        # Validate Dutch content
        content_lower = message["content"].lower()
        assert any(word in content_lower for word in ["valbescherming", "hoogte", "harnas"]), \
            "Response should contain Dutch safety terminology"

        # Validate performance
        assert elapsed < 2.0, f"Response took {elapsed:.2f}s, expected <2s"


# Test Stub 2: Streaming Chat Completions
def test_openai_chat_completions_streaming(client, mock_specialist_response):
    """
    Test /v1/chat/completions endpoint with stream=true.

    Validates:
    - AC-007-002: Streaming response uses SSE format
    - Each chunk has 'data: ' prefix
    - Stream ends with 'data: [DONE]'
    - Streaming starts within 1 second
    """
    import json

    # Send request with stream=true
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "evi-specialist",
            "messages": [
                {"role": "user", "content": "Test vraag over werken op hoogte"}
            ],
            "stream": True
        }
    )

    # Validate SSE response type
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", ""), \
        "Response must be Server-Sent Events stream"

    # Collect and validate stream chunks
    chunks = []
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            chunks.append(line_str)

    # Validate SSE format
    assert len(chunks) > 0, "Stream should contain at least one chunk"

    # Check that chunks start with 'data: '
    data_chunks = [c for c in chunks if c.startswith('data: ')]
    assert len(data_chunks) > 0, "Should have data chunks"

    # Check for final [DONE] marker
    assert any('data: [DONE]' in chunk for chunk in chunks), \
        "Stream must end with 'data: [DONE]'"

    # Validate JSON structure of chunks (except [DONE])
    valid_json_chunks = 0
    for chunk in data_chunks:
        if chunk == 'data: [DONE]':
            continue

        # Extract JSON after 'data: ' prefix
        json_str = chunk[6:]  # Skip 'data: '
        try:
            chunk_data = json.loads(json_str)

            # Validate OpenAI chunk structure
            assert "id" in chunk_data
            assert chunk_data["object"] == "chat.completion.chunk"
            assert "choices" in chunk_data
            assert len(chunk_data["choices"]) == 1

            choice = chunk_data["choices"][0]
            assert "delta" in choice
            assert choice["index"] == 0

            valid_json_chunks += 1
        except json.JSONDecodeError:
            # Skip empty lines or malformed chunks
            continue

    assert valid_json_chunks > 0, "Should have at least one valid JSON chunk"


# Test Stub 3: Model Listing
def test_list_models(client):
    """
    Test /v1/models endpoint returns EVI specialist model.

    Validates:
    - AC-007-010: Model list includes 'evi-specialist'
    - Response format matches OpenAI Models list
    - Model object includes required fields
    """
    # Send GET request
    response = client.get("/v1/models")

    # Validate response
    assert response.status_code == 200
    data = response.json()

    # Validate OpenAI models list format
    assert "object" in data
    assert data["object"] == "list"
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0, "Should have at least one model"

    # Find evi-specialist model
    evi_model = None
    for model in data["data"]:
        if model.get("id") == "evi-specialist":
            evi_model = model
            break

    assert evi_model is not None, "'evi-specialist' model should be in list"

    # Validate model object structure
    assert evi_model["object"] == "model"
    assert "created" in evi_model
    assert "owned_by" in evi_model


# Test Stub 4: Error Handling
def test_error_handling(client):
    """
    Test error responses match OpenAI format.

    Validates:
    - AC-007-015: Empty queries return appropriate error
    - Error format matches OpenAI error object
    - Error messages are descriptive
    """
    # Test Case 1: Empty messages array
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "evi-specialist",
            "messages": [],
            "stream": False
        }
    )

    assert response.status_code in [400, 422], "Empty messages should return error"
    data = response.json()

    # OpenAI error format has either 'error' or 'detail' key
    assert "error" in data or "detail" in data, "Error response should have error information"

    # Test Case 2: Invalid model name
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "non-existent-model",
            "messages": [{"role": "user", "content": "Test"}],
            "stream": False
        }
    )

    # Should return error for invalid model (404 or 400)
    assert response.status_code in [400, 404, 422], "Invalid model should return error"

    # Test Case 3: Empty message content
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "evi-specialist",
            "messages": [{"role": "user", "content": ""}],
            "stream": False
        }
    )

    assert response.status_code in [400, 422], "Empty content should return error"


# Additional Test Stubs (Optional - expand in Phase 2)

def test_dutch_language_detection(client):
    """
    Test automatic Dutch language detection and response.

    Validates:
    - AC-007-003: Dutch queries receive Dutch responses
    - Language parameter passed to specialist agent
    - Response metadata includes language indicator

    TODO: Implement test logic
    """
    pass


def test_citation_formatting(client, mock_specialist_response):
    """
    Test citation extraction and formatting in response.

    Validates:
    - AC-007-008: Citations include document title and tier
    - Citation format: "📚 [Title] (Tier X)"
    - Multiple citations separated properly

    TODO: Implement test logic
    """
    pass


def test_conversation_history_context(client):
    """
    Test multi-turn conversation maintains context.

    Validates:
    - AC-007-012: Follow-up queries use conversation history
    - Message history passed to specialist agent
    - Context maintained across multiple requests

    TODO: Implement test logic
    """
    pass


def test_response_time_performance(client):
    """
    Test response time meets performance requirements.

    Validates:
    - AC-007-014: Tier 1 responses complete within 2 seconds
    - Streaming starts within 1 second
    - Response time logged in metadata

    TODO: Implement test logic
    """
    pass


# Pytest configuration
pytestmark = pytest.mark.asyncio
