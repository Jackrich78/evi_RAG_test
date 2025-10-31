"""
Integration tests for SSE streaming endpoint.

Tests the FastAPI SSE endpoint integration with Pydantic AI agent streaming.
Validates end-to-end streaming behavior from API to client.
"""

import pytest
import time
import asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from agent.api import app
from agent.models import ChatRequest


class TestSSEEndpoint:
    """Test FastAPI SSE streaming endpoint."""

    @pytest.mark.asyncio
    async def test_sse_endpoint_returns_streaming_response(self):
        """
        Test that SSE endpoint returns proper streaming response.

        Acceptance Criteria: AC-FEAT-010-002
        """
        # Given: Test client and mock specialist agent
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                # Mock streaming response
                async def mock_generator():
                    yield "Hello"
                    yield " world"

                mock_stream.return_value = mock_generator()

                # When: Sending POST request to streaming endpoint
                request = ChatRequest(
                    message="Test query",
                    session_id="test-session",
                    language="nl"
                )

                response = await client.post(
                    "/api/v1/chat/stream",
                    json=request.dict(),
                    headers={"Authorization": "Bearer test-token"}
                )

                # Then: Response headers contain "text/event-stream"
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")

                # Verify streaming response starts immediately
                assert response.is_stream_consumed is False

    @pytest.mark.asyncio
    async def test_first_token_latency_under_500ms(self):
        """
        Test that first token arrives within 500ms.

        Acceptance Criteria: AC-FEAT-010-001, AC-FEAT-010-012
        """
        # Given: Test client with mock that yields immediately
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                async def mock_generator():
                    yield "First token"
                    await asyncio.sleep(0.1)
                    yield " more content"

                mock_stream.return_value = mock_generator()

                request = ChatRequest(
                    message="Quick test",
                    session_id="test-session",
                    language="nl"
                )

                # When: Sending request and measuring time to first token
                start_time = time.time()
                response = await client.post(
                    "/api/v1/chat/stream",
                    json=request.dict(),
                    headers={"Authorization": "Bearer test-token"}
                )

                # Read first chunk
                first_chunk = None
                async for chunk in response.aiter_bytes():
                    if chunk:
                        first_chunk = chunk
                        break

                elapsed = (time.time() - start_time) * 1000  # Convert to ms

                # Then: First token arrives within 500ms
                assert elapsed < 500, f"First token took {elapsed}ms, expected <500ms"
                assert first_chunk is not None

    @pytest.mark.asyncio
    async def test_sse_endpoint_with_citations(self):
        """
        Test that citations stream correctly through SSE endpoint.

        Acceptance Criteria: AC-FEAT-010-004, AC-FEAT-010-005
        """
        # Given: Mock response with citation markers
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                async def mock_generator():
                    yield "According to guidelines "
                    yield "[1], workers must "
                    yield "[2] wear helmets."

                mock_stream.return_value = mock_generator()

                request = ChatRequest(message="Test", session_id="test", language="nl")

                # When: Streaming response
                response = await client.post(
                    "/api/v1/chat/stream",
                    json=request.dict(),
                    headers={"Authorization": "Bearer test-token"}
                )

                # Collect all chunks
                chunks = []
                async for chunk in response.aiter_text():
                    chunks.append(chunk)

                full_response = "".join(chunks)

                # Then: Citation markers appear intact
                assert "[1]" in full_response
                assert "[2]" in full_response
                # Verify markers aren't broken across boundaries
                assert "[ 1]" not in full_response
                assert "[1 ]" not in full_response

    @pytest.mark.asyncio
    async def test_sse_endpoint_authentication_required(self):
        """
        Test that SSE endpoint enforces authentication.

        Acceptance Criteria: AC-FEAT-010-017
        """
        # Given: Test client without auth token
        async with AsyncClient(app=app, base_url="http://test") as client:
            request = ChatRequest(message="Test", session_id="test", language="nl")

            # When: Sending request without authorization header
            response = await client.post(
                "/api/v1/chat/stream",
                json=request.dict()
                # No Authorization header
            )

            # Then: Response is 401 Unauthorized
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sse_endpoint_rate_limiting(self):
        """
        Test that rate limiting prevents abuse.

        Acceptance Criteria: AC-FEAT-010-018
        """
        # Given: Test client
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                async def mock_generator():
                    yield "Response"

                mock_stream.return_value = mock_generator()

                request = ChatRequest(message="Test", session_id="test", language="nl")
                headers = {"Authorization": "Bearer test-token"}

                # When: Sending 21 requests rapidly
                responses = []
                for i in range(21):
                    response = await client.post(
                        "/api/v1/chat/stream",
                        json=request.dict(),
                        headers=headers
                    )
                    responses.append(response.status_code)

                # Then: 21st request returns 429 Too Many Requests
                assert 429 in responses, "Expected rate limiting after 20 requests"

    @pytest.mark.asyncio
    async def test_sse_endpoint_handles_backend_errors(self):
        """
        Test that backend errors are returned as SSE error events.

        Acceptance Criteria: AC-FEAT-010-011
        """
        # Given: Mock that raises exception
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                async def failing_generator():
                    yield "Starting..."
                    raise ValueError("Mock backend error")

                mock_stream.return_value = failing_generator()

                request = ChatRequest(message="Test", session_id="test", language="nl")

                # When: Streaming with error
                response = await client.post(
                    "/api/v1/chat/stream",
                    json=request.dict(),
                    headers={"Authorization": "Bearer test-token"}
                )

                # Collect events
                events = []
                async for chunk in response.aiter_text():
                    events.append(chunk)

                full_text = "".join(events)

                # Then: Error event is received
                assert "event: error" in full_text or "error" in full_text.lower()

    @pytest.mark.asyncio
    async def test_sse_endpoint_with_long_response(self):
        """
        Test that long responses (2000+ tokens) stream correctly.

        Acceptance Criteria: AC-FEAT-010-013
        """
        # Given: Mock with 2000+ character response
        long_text = "A " * 1000  # 2000 characters
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                async def mock_generator():
                    # Stream in small chunks
                    for i in range(0, len(long_text), 50):
                        yield long_text[i:i+50]

                mock_stream.return_value = mock_generator()

                request = ChatRequest(message="Test", session_id="test", language="nl")

                # When: Streaming long response
                response = await client.post(
                    "/api/v1/chat/stream",
                    json=request.dict(),
                    headers={"Authorization": "Bearer test-token"}
                )

                # Collect all content
                chunks = []
                async for chunk in response.aiter_text():
                    chunks.append(chunk)

                full_response = "".join(chunks)

                # Then: All tokens received without interruption
                assert len(full_response) >= 2000

    @pytest.mark.asyncio
    async def test_sse_endpoint_concurrent_requests(self):
        """
        Test that endpoint handles concurrent streams.

        Acceptance Criteria: AC-FEAT-010-014
        """
        # Given: Multiple concurrent requests
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                async def mock_generator():
                    yield "Response"

                mock_stream.return_value = mock_generator()

                request = ChatRequest(message="Test", session_id="test", language="nl")
                headers = {"Authorization": "Bearer test-token"}

                # When: Sending 10 concurrent requests
                tasks = [
                    client.post("/api/v1/chat/stream", json=request.dict(), headers=headers)
                    for _ in range(10)
                ]

                responses = await asyncio.gather(*tasks)

                # Then: All complete successfully
                assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_sse_endpoint_dutch_language_support(self):
        """
        Test that Dutch responses stream correctly with UTF-8 encoding.

        Acceptance Criteria: AC-FEAT-010-007
        """
        # Given: Dutch response with special characters
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                async def mock_generator():
                    yield "Werknemers moeten "
                    yield "veiligheidsmaatregelen "
                    yield "naleven: ë, ö, ü"

                mock_stream.return_value = mock_generator()

                request = ChatRequest(message="Test", session_id="test", language="nl")

                # When: Streaming Dutch response
                response = await client.post(
                    "/api/v1/chat/stream",
                    json=request.dict(),
                    headers={"Authorization": "Bearer test-token"}
                )

                # Collect content
                chunks = []
                async for chunk in response.aiter_text():
                    chunks.append(chunk)

                full_text = "".join(chunks)

                # Then: Dutch characters decoded correctly
                assert "ë" in full_text or "\\u00eb" in full_text
                assert "ö" in full_text or "\\u00f6" in full_text

    @pytest.mark.asyncio
    async def test_sse_endpoint_english_language_support(self):
        """
        Test that English responses stream correctly.

        Acceptance Criteria: AC-FEAT-010-008
        """
        # Given: English response
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("agent.api.run_specialist_query_stream") as mock_stream:
                async def mock_generator():
                    yield "Workers must follow "
                    yield "safety regulations."

                mock_stream.return_value = mock_generator()

                request = ChatRequest(message="Test", session_id="test", language="en")

                # When: Streaming English response
                start_time = time.time()
                response = await client.post(
                    "/api/v1/chat/stream",
                    json=request.dict(),
                    headers={"Authorization": "Bearer test-token"}
                )

                # Collect first chunk for timing
                first_chunk = None
                async for chunk in response.aiter_bytes():
                    if chunk:
                        first_chunk = chunk
                        break

                elapsed = (time.time() - start_time) * 1000

                # Then: Performance matches Dutch (< 500ms)
                assert elapsed < 500
                assert first_chunk is not None
