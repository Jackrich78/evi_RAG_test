"""
Streaming utilities for SSE formatting and delta tracking.

Supports true token-by-token streaming with Server-Sent Events (SSE) format.
"""

import json
from typing import Optional, Any


def format_sse_text(text: str) -> str:
    """
    Format text content as Server-Sent Event.

    Args:
        text: Text content to send

    Returns:
        SSE-formatted string: "data: {json}\n\n"
    """
    data = {"type": "text", "content": text}
    return f"data: {json.dumps(data)}\n\n"


def format_sse_error(error_message: str) -> str:
    """
    Format error as Server-Sent Event.

    Args:
        error_message: Error message to send

    Returns:
        SSE-formatted error event
    """
    data = {"type": "error", "message": error_message}
    return f"event: error\ndata: {json.dumps(data)}\n\n"


def format_sse_done() -> str:
    """
    Format stream completion event.

    Returns:
        SSE-formatted done event
    """
    data = {"type": "done"}
    return f"event: done\ndata: {json.dumps(data)}\n\n"


class StreamHandler:
    """
    Handles delta calculation for cumulative streaming content.

    Pydantic AI's .stream_output() returns cumulative content, not deltas.
    This class tracks the last content length and calculates new portions.
    """

    def __init__(self):
        """Initialize stream handler with zero content length."""
        self.last_content_length = 0

    def process_chunk(self, cumulative_content: str) -> Optional[str]:
        """
        Calculate delta from cumulative content.

        Args:
            cumulative_content: Full content received so far (cumulative)

        Returns:
            Only the NEW portion since last call, or None if no new content
        """
        current_length = len(cumulative_content)

        if current_length > self.last_content_length:
            # Extract only the new portion
            delta = cumulative_content[self.last_content_length:]
            self.last_content_length = current_length
            return delta

        return None

    def cleanup(self):
        """Clean up resources after stream completes."""
        self.last_content_length = 0


def calculate_delta(
    cumulative_content: str,
    last_length: int
) -> tuple[Optional[str], int]:
    """
    Calculate delta from cumulative content (functional approach).

    Args:
        cumulative_content: Full content so far
        last_length: Length of content from previous call

    Returns:
        Tuple of (delta_text, new_length)
    """
    current_length = len(cumulative_content)

    if current_length > last_length:
        delta = cumulative_content[last_length:]
        return delta, current_length

    return None, last_length
