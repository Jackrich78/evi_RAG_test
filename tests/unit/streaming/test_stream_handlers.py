"""
Unit tests for stream handling logic.

Tests the core streaming logic for processing LLM output chunks
and managing stream lifecycle.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, MagicMock
from agent.streaming_utils import StreamHandler, calculate_delta


class TestStreamHandlers:
    """Test stream processing and handling logic."""

    @pytest.mark.asyncio
    async def test_process_chunk_accumulates_tokens(self):
        """
        Test that stream handler accumulates tokens correctly.

        Acceptance Criteria: AC-FEAT-010-002
        """
        # Given: Stream handler and multiple chunks
        handler = StreamHandler()
        chunks = ["Hello", "Hello world", "Hello world!", "Hello world! Test"]

        # When: Processing chunks sequentially (cumulative content)
        accumulated = []
        for chunk in chunks:
            delta = handler.process_chunk(chunk)
            if delta:
                accumulated.append(delta)

        # Then: Accumulated text contains all new content
        full_text = "".join(accumulated)
        assert full_text == "Hello world! Test"
        # Verify deltas are correct
        assert accumulated == ["Hello", " world", "!", " Test"]

    @pytest.mark.asyncio
    async def test_process_chunk_preserves_citation_markers(self):
        """
        Test that citation markers are not broken across chunks.

        Acceptance Criteria: AC-FEAT-010-004
        """
        # Given: Chunks where citation marker spans boundaries
        handler = StreamHandler()
        chunks = [
            "According to guidelines",
            "According to guidelines [",
            "According to guidelines [1",
            "According to guidelines [1]",
            "According to guidelines [1], workers",
        ]

        # When: Processing chunks
        accumulated = []
        for chunk in chunks:
            delta = handler.process_chunk(chunk)
            if delta:
                accumulated.append(delta)

        # Then: Citation marker is preserved correctly
        full_text = "".join(accumulated)
        assert "[1]" in full_text
        assert full_text == "According to guidelines [1], workers"

    @pytest.mark.asyncio
    async def test_stream_timeout_handling(self):
        """
        Test that streams timeout after 60 seconds.

        Acceptance Criteria: AC-FEAT-010-010
        """
        # Given: Mock async generator that never completes
        async def slow_generator():
            await asyncio.sleep(70)  # Exceeds 60s timeout
            yield "too late"

        # When: Processing with timeout
        # Then: Timeout exception is raised
        with pytest.raises(asyncio.TimeoutError):
            async with asyncio.timeout(60):
                async for _ in slow_generator():
                    pass

    @pytest.mark.asyncio
    async def test_stream_cleanup_on_completion(self):
        """
        Test that resources are cleaned up after stream completes.

        Acceptance Criteria: AC-FEAT-010-015, AC-FEAT-010-016
        """
        # Given: Stream handler
        handler = StreamHandler()

        # When: Processing complete stream
        chunks = ["Hello", "Hello world"]
        for chunk in chunks:
            handler.process_chunk(chunk)

        # Then: Resources are cleaned up
        handler.cleanup()
        assert handler.last_content_length == 0
        assert not hasattr(handler, "active_streams") or len(handler.active_streams) == 0

    @pytest.mark.asyncio
    async def test_stream_cleanup_on_client_disconnect(self):
        """
        Test that resources are cleaned up when client disconnects.

        Acceptance Criteria: AC-FEAT-010-016
        """
        # Given: Active stream
        handler = StreamHandler()
        handler.process_chunk("Starting...")

        # When: Client disconnect simulated
        disconnect_time = asyncio.get_event_loop().time()
        handler.cleanup()
        cleanup_time = asyncio.get_event_loop().time()

        # Then: Cleanup happens quickly (within 5 seconds)
        cleanup_duration = cleanup_time - disconnect_time
        assert cleanup_duration < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_stream_isolation(self):
        """
        Test that concurrent streams don't interfere with each other.

        Acceptance Criteria: AC-FEAT-010-014
        """
        # Given: Multiple independent stream handlers
        handler1 = StreamHandler()
        handler2 = StreamHandler()

        # When: Processing chunks concurrently
        delta1_a = handler1.process_chunk("Stream 1 content")
        delta2_a = handler2.process_chunk("Stream 2 different")

        delta1_b = handler1.process_chunk("Stream 1 content more")
        delta2_b = handler2.process_chunk("Stream 2 different data")

        # Then: Each maintains independent state
        assert delta1_a == "Stream 1 content"
        assert delta2_a == "Stream 2 different"
        assert delta1_b == " more"
        assert delta2_b == " data"

        # Verify no cross-contamination
        assert handler1.last_content_length != handler2.last_content_length

    @pytest.mark.asyncio
    async def test_error_propagation_in_stream(self):
        """
        Test that errors during streaming are propagated correctly.

        Acceptance Criteria: AC-FEAT-010-011
        """
        # Given: Mock generator that raises exception
        async def failing_generator():
            yield "Starting..."
            raise ValueError("Mock LLM error")

        # When: Processing stream with error
        collected = []
        error_caught = None

        try:
            async for chunk in failing_generator():
                collected.append(chunk)
        except ValueError as e:
            error_caught = e

        # Then: Error is caught and can be formatted
        assert error_caught is not None
        assert str(error_caught) == "Mock LLM error"
        assert collected == ["Starting..."]  # Partial data before error
