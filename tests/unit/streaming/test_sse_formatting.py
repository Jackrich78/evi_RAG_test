"""
Unit tests for SSE message formatting.

Tests the formatting of Server-Sent Events messages for token streaming.
Validates proper SSE format compliance and edge cases.
"""

import pytest
import json
from agent.streaming_utils import format_sse_text, format_sse_error, format_sse_done


class TestSSEFormatting:
    """Test SSE message formatting functions."""

    def test_format_sse_message_with_simple_text(self):
        """
        Test that simple text is formatted correctly as SSE message.

        Acceptance Criteria: AC-FEAT-010-002
        """
        # Given: Simple text string
        text = "Hello, this is a test message"

        # When: Formatting as SSE event
        result = format_sse_text(text)

        # Then: Output format is "data: {json}\n\n"
        expected = f'data: {json.dumps({"type": "text", "content": text})}\n\n'
        assert result == expected
        assert result.startswith("data: ")
        assert result.endswith("\n\n")

    def test_format_sse_message_with_special_characters(self):
        """
        Test that special characters are preserved in SSE format.

        Acceptance Criteria: AC-FEAT-010-023
        """
        # Given: Text with emojis, newlines, and special chars
        text = "Test 🎉 with\nnewlines and special: @#$%"

        # When: Formatting as SSE event
        result = format_sse_text(text)

        # Then: Characters are properly JSON-encoded
        assert "🎉" in result or "\\ud83c\\udf89" in result  # Unicode or escaped
        assert result.startswith("data: ")
        assert result.endswith("\n\n")

        # Verify SSE format is valid (can be parsed back)
        data_line = result.split("\n")[0]
        json_str = data_line.replace("data: ", "")
        parsed = json.loads(json_str)
        assert parsed["type"] == "text"

    def test_format_sse_message_with_citation_markers(self):
        """
        Test that citation markers [1], [2] are preserved correctly.

        Acceptance Criteria: AC-FEAT-010-004
        """
        # Given: Text containing citation markers
        text = "According to safety guidelines [1], workers must [2] wear helmets."

        # When: Formatting as SSE event
        result = format_sse_text(text)

        # Then: Markers are not split or corrupted
        assert "[1]" in result
        assert "[2]" in result

        # Verify markers can be extracted from JSON
        data_line = result.split("\n")[0]
        json_str = data_line.replace("data: ", "")
        parsed = json.loads(json_str)
        assert "[1]" in parsed["content"]
        assert "[2]" in parsed["content"]

    def test_format_sse_error_event(self):
        """
        Test formatting of SSE error events.

        Acceptance Criteria: AC-FEAT-010-011
        """
        # Given: Error message
        error_msg = "Database connection failed"

        # When: Formatting as SSE error event
        result = format_sse_error(error_msg)

        # Then: Format is "event: error\ndata: {json}\n\n"
        assert result.startswith("event: error\n")
        assert "data: " in result
        assert result.endswith("\n\n")

        # Verify error message is in JSON
        lines = result.strip().split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        json_str = data_line.replace("data: ", "")
        parsed = json.loads(json_str)
        assert parsed["type"] == "error"
        assert parsed["message"] == error_msg

    def test_format_sse_done_event(self):
        """
        Test formatting of stream completion event.

        Acceptance Criteria: AC-FEAT-010-002
        """
        # Given: Stream completion
        # When: Formatting done event
        result = format_sse_done()

        # Then: Format is "event: done\ndata: {json}\n\n"
        assert result.startswith("event: done\n")
        assert "data: " in result
        assert result.endswith("\n\n")

        # Verify JSON structure
        lines = result.strip().split("\n")
        data_line = [line for line in lines if line.startswith("data: ")][0]
        json_str = data_line.replace("data: ", "")
        parsed = json.loads(json_str)
        assert parsed["type"] == "done"

    def test_format_sse_message_with_dutch_characters(self):
        """
        Test that Dutch characters (ë, ö, etc.) are encoded correctly.

        Acceptance Criteria: AC-FEAT-010-007
        """
        # Given: Dutch text with special characters
        text = "Werknemers moeten veiligheidsmaatregelen naleven: ë, ö, ü, ñ"

        # When: Formatting as SSE event
        result = format_sse_text(text)

        # Then: UTF-8 encoding is correct
        assert result.startswith("data: ")
        assert result.endswith("\n\n")

        # Verify Dutch characters are preserved in JSON
        data_line = result.split("\n")[0]
        json_str = data_line.replace("data: ", "")
        parsed = json.loads(json_str)
        content = parsed["content"]

        # Characters should be preserved (either as-is or Unicode-escaped)
        assert "ë" in content or "\\u00eb" in json_str
        assert "ö" in content or "\\u00f6" in json_str

    def test_format_empty_message(self):
        """
        Test handling of empty message.

        Acceptance Criteria: AC-FEAT-010-021
        """
        # Given: Empty string
        text = ""

        # When: Formatting as SSE event
        result = format_sse_text(text)

        # Then: Valid SSE format is returned
        assert result.startswith("data: ")
        assert result.endswith("\n\n")

        # Verify JSON structure with empty content
        data_line = result.split("\n")[0]
        json_str = data_line.replace("data: ", "")
        parsed = json.loads(json_str)
        assert parsed["type"] == "text"
        assert parsed["content"] == ""
