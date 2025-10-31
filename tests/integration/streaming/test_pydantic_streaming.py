"""
Integration tests for Pydantic AI streaming.

Tests the integration between Pydantic AI agent.run_stream() and the
FastAPI streaming infrastructure.

CORRECT STREAMING PATTERN (Pydantic AI 0.3.2):
==============================================
```python
async with agent.run_stream(query, deps=deps) as result:
    # Stream partial responses
    async for message, is_last in result.stream_structured():
        validated = await result.validate_structured_output(message, allow_partial=True)
        # Process validated partial...

    # After streaming completes, get final validated output
    final_response = await result.get_output()  # ✅ MUST AWAIT
```

KEY POINTS:
- `stream_structured()` yields `(message, is_last)` tuples
- `validate_structured_output(msg, allow_partial=True)` for partials
- `await result.get_output()` to get final response with citations (MUST AWAIT!)
- DO NOT use deprecated `result.get_data()` (but if you do, MUST AWAIT!)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent.specialist_agent import run_specialist_query_stream
from agent.models import SpecialistResponse, Citation


class TestPydanticAIStreaming:
    """Test Pydantic AI StreamedRunResult integration."""

    @pytest.mark.asyncio
    async def test_pydantic_stream_yields_chunks(self):
        """
        Test that Pydantic AI agent.run_stream() yields chunks correctly.

        Acceptance Criteria: AC-FEAT-010-002

        UPDATED: Now uses stream_structured() which yields (message, is_last) tuples
        and requires validate_structured_output() and await get_output()
        """
        # Given: Mock specialist agent with streaming capability
        with patch("agent.specialist_agent._create_specialist_agent") as mock_create:
            mock_agent = MagicMock()
            mock_create.return_value = mock_agent

            # Create mock StreamedRunResult
            mock_result = MagicMock()

            # Mock stream_structured() to yield (message, is_last) tuples with cumulative content
            async def mock_stream():
                messages = [
                    (MagicMock(content="Hello", citations=[]), False),
                    (MagicMock(content="Hello world", citations=[]), False),
                    (MagicMock(content="Hello world!", citations=[]), True),
                ]
                for msg, is_last in messages:
                    yield (msg, is_last)

            mock_result.stream_structured = mock_stream

            # Mock validate_structured_output to return the message as-is
            async def mock_validate(msg, allow_partial=False):
                return msg
            mock_result.validate_structured_output = mock_validate

            # Mock get_output() to return final response with citations
            final_response = SpecialistResponse(
                content="Hello world!",
                citations=[Citation(title="Test", source="Test", quote="Test")],
                search_metadata={}
            )
            async def mock_get_output():
                return final_response
            mock_result.get_output = mock_get_output

            mock_result.__aenter__ = AsyncMock(return_value=mock_result)
            mock_result.__aexit__ = AsyncMock(return_value=None)

            mock_agent.run_stream.return_value = mock_result

            # When: Calling run_specialist_query_stream
            items = []
            async for item in run_specialist_query_stream(
                query="Test query",
                session_id="test-session",
                language="nl"
            ):
                items.append(item)

            # Then: Items are yielded as (type, data) tuples
            assert len(items) > 0

            # Extract text items only
            text_items = [data for item_type, data in items if item_type == "text"]

            # Verify deltas are calculated correctly
            assert text_items[0] == "Hello"
            assert text_items[1] == " world"
            assert text_items[2] == "!"

            # Verify final response is yielded
            final_items = [data for item_type, data in items if item_type == "final"]
            assert len(final_items) == 1
            assert isinstance(final_items[0], SpecialistResponse)

    @pytest.mark.asyncio
    async def test_pydantic_stream_preserves_citations(self):
        """
        Test that citations are preserved through Pydantic AI streaming.

        Acceptance Criteria: AC-FEAT-010-004
        """
        # Given: Mock response with citation markers
        with patch("agent.specialist_agent.specialist_agent") as mock_agent:
            mock_result = MagicMock()

            async def mock_stream():
                # Simulate cumulative content with citations
                messages = [
                    MagicMock(content="According to "),
                    MagicMock(content="According to guidelines ["),
                    MagicMock(content="According to guidelines [1"),
                    MagicMock(content="According to guidelines [1]"),
                ]
                for msg in messages:
                    yield msg

            mock_result.stream_output = mock_stream
            mock_result.__aenter__ = AsyncMock(return_value=mock_result)
            mock_result.__aexit__ = AsyncMock(return_value=None)

            mock_agent.run_stream.return_value = mock_result

            # When: Streaming response
            chunks = []
            async for chunk in run_specialist_query_stream(
                query="Test",
                session_id="test",
                language="nl"
            ):
                chunks.append(chunk)

            full_text = "".join(chunks)

            # Then: Citation markers are intact
            assert "[1]" in full_text
            # Verify marker wasn't broken across chunks
            assert not any("[" in c and "]" not in c for c in chunks[:-1])

    @pytest.mark.asyncio
    async def test_pydantic_stream_error_handling(self):
        """
        Test that Pydantic AI streaming errors are handled correctly.

        Acceptance Criteria: AC-FEAT-010-011
        """
        # Given: Mock agent that raises exception during streaming
        with patch("agent.specialist_agent.specialist_agent") as mock_agent:
            mock_result = MagicMock()

            async def failing_stream():
                yield MagicMock(content="Starting...")
                raise ValueError("Mock Pydantic AI error")

            mock_result.stream_output = failing_stream
            mock_result.__aenter__ = AsyncMock(return_value=mock_result)
            mock_result.__aexit__ = AsyncMock(return_value=None)

            mock_agent.run_stream.return_value = mock_result

            # When: Streaming with error
            error_caught = None
            chunks = []

            try:
                async for chunk in run_specialist_query_stream(
                    query="Test",
                    session_id="test",
                    language="nl"
                ):
                    chunks.append(chunk)
            except ValueError as e:
                error_caught = e

            # Then: Exception is caught
            assert error_caught is not None
            assert "Mock Pydantic AI error" in str(error_caught)
            # Verify partial content was yielded before error
            assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_pydantic_stream_completion(self):
        """
        Test that stream completion is detected correctly.

        Acceptance Criteria: AC-FEAT-010-015
        """
        # Given: Complete streaming response
        with patch("agent.specialist_agent.specialist_agent") as mock_agent:
            mock_result = MagicMock()

            async def mock_stream():
                messages = [
                    MagicMock(content="Complete"),
                    MagicMock(content="Complete response"),
                ]
                for msg in messages:
                    yield msg
                # Stream completes naturally

            mock_result.stream_output = mock_stream
            mock_result.__aenter__ = AsyncMock(return_value=mock_result)
            mock_result.__aexit__ = AsyncMock(return_value=None)

            mock_agent.run_stream.return_value = mock_result

            # When: Streaming complete response
            chunks = []
            async for chunk in run_specialist_query_stream(
                query="Test",
                session_id="test",
                language="nl"
            ):
                chunks.append(chunk)

            # Then: All chunks received and stream completed
            full_text = "".join(chunks)
            assert full_text == "Complete response"
            # StopAsyncIteration is raised naturally at end (implicit in async for)

    @pytest.mark.asyncio
    async def test_pydantic_stream_with_tool_calls(self):
        """
        Test streaming when agent makes tool calls (RAG retrieval).

        Acceptance Criteria: AC-FEAT-010-002
        """
        # Given: Mock agent with RAG tool dependencies
        with patch("agent.specialist_agent.specialist_agent") as mock_agent:
            mock_result = MagicMock()

            async def mock_stream_with_tools():
                # Simulate tool execution before content streaming
                # In real Pydantic AI, tool calls happen before text generation
                messages = [
                    MagicMock(content="Based on search results, "),
                    MagicMock(content="Based on search results, the answer is..."),
                ]
                for msg in messages:
                    yield msg

            mock_result.stream_output = mock_stream_with_tools
            mock_result.__aenter__ = AsyncMock(return_value=mock_result)
            mock_result.__aexit__ = AsyncMock(return_value=None)

            mock_agent.run_stream.return_value = mock_result

            # When: Streaming response that required tool calls
            chunks = []
            async for chunk in run_specialist_query_stream(
                query="What is UWV?",
                session_id="test",
                language="nl"
            ):
                chunks.append(chunk)

            full_text = "".join(chunks)

            # Then: Streaming continues after tool execution
            assert "Based on search results" in full_text
            assert len(chunks) > 0
            # Tool results are incorporated in response
            assert "answer" in full_text
