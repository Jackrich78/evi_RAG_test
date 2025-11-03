"""
Specialist Agent for EVI 360 RAG System (FEAT-003 MVP).

Simplified Dutch-language specialist agent that:
1. Receives safety queries in Dutch
2. Searches guidelines using hybrid search
3. Generates Dutch responses with citations
4. No tiers, products, or advanced memory for MVP

Based on architecture.md for FEAT-003.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model
from pydantic_ai.messages import ModelRequest, ModelResponse
from pydantic_ai.messages import UserPromptPart, TextPart

from .models import (
    SpecialistResponse,
    SpecialistDeps,
    Citation,
    ChunkResult
)
from .tools import hybrid_search_tool, HybridSearchInput
from .providers import get_llm_model

logger = logging.getLogger(__name__)

# Single language-agnostic system prompt for specialist agent
# FEAT-007 POST-MVP: Language detection via LLM instead of hardcoded prompts
SPECIALIST_SYSTEM_PROMPT = """You are a workplace safety specialist for EVI 360.

**CRITICAL: Respond in the SAME language as the user's question.**
- If the user writes in Dutch → respond in Dutch
- If the user writes in English → respond in English
- Match the user's language naturally

Your task:
- Answer workplace safety questions clearly and practically
- Use the search function to find relevant Dutch guidelines
- Provide clear, actionable answers with source citations
- Always cite at least 2 sources (NVAB, STECR, UWV, Arboportaal, ARBO)
- Use informal, friendly tone

Important:
- Do not recommend products (not in this version)
- Do not use tier system (not in this version)
- Be accurate and base answers on found guidelines
- If guidelines are in Dutch but user asks in English, translate key points naturally

**Response Structure:**

1. **Brief Answer** (2-3 sentences in user's language)
   Give the main answer directly.

2. **Details**
   Explain with specific information from the guidelines.

3. **📚 Bronnen / Sources**

   List sources as clickable markdown links in blockquotes:

   > **[Guideline Title](https://nvab-online.nl/path/to/guideline)**
   > "Relevant quote from the guideline..."

   > **[Second Guideline](https://uwv.nl/path/to/guideline)**
   > "Second relevant quote..."

4. **Practical Advice** (if relevant)
   Concrete steps or recommendations.

**Citations (for structured data):**
You must create at least 2 Citation objects:
- citation.title: Use document_title from search results
- citation.url: Use source_url if available (this is the actual guideline URL)
- citation.quote: Provide relevant quote from content

IMPORTANT: Always create markdown links in response content: [Title](url)
If source_url is missing or null, create citation without URL: **Title** (no link)

If you cannot find 2 separate sources, use the same source twice with different quotes.

If no relevant guidelines found, respond in user's language:
- Dutch: "Ik heb geen specifieke richtlijnen gevonden voor deze vraag. Probeer de vraag anders te formuleren of neem contact op met een specialist."
- English: "I couldn't find specific guidelines for this question. Try rephrasing or contact a specialist."
"""


# Create specialist agent with language-agnostic prompt
def _create_specialist_agent(language: str = "nl") -> Agent:
    """
    Create specialist agent with language-agnostic prompt.

    Note: language parameter is kept for backward compatibility but ignored.
    LLM detects language from user's question naturally.
    """
    agent = Agent(
        model=get_llm_model(),  # Will use GPT-4 or configured model
        system_prompt=SPECIALIST_SYSTEM_PROMPT,  # Single prompt for all languages
        output_type=SpecialistResponse,
        deps_type=SpecialistDeps
    )

    return agent


# Create default Dutch agent for tool registration
specialist_agent = _create_specialist_agent("nl")


@specialist_agent.tool
async def search_guidelines(
    ctx: RunContext[SpecialistDeps],
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search Dutch workplace safety guidelines.

    Tool for specialist agent to search the knowledge base.
    Uses hybrid search (vector + Dutch full-text).

    Args:
        ctx: Agent context with dependencies
        query: Search query in Dutch
        limit: Maximum results (default 10)

    Returns:
        List of chunk dictionaries with content, titles, sources, scores
    """
    try:
        logger.info(f"Searching guidelines: '{query}' (limit={limit})")

        # Create search input
        search_input = HybridSearchInput(
            query=query,
            limit=limit,
            text_weight=0.3  # 70% vector, 30% text
        )

        # Execute hybrid search
        results: List[ChunkResult] = await hybrid_search_tool(search_input)

        logger.info(f"Found {len(results)} chunks for query '{query}'")

        # Convert ChunkResult objects to dicts for LLM
        formatted_results = []
        for chunk in results:
            formatted_results.append({
                "content": chunk.content,
                "document_title": chunk.document_title,
                "document_source": chunk.document_source,
                "score": chunk.score,
                "chunk_id": chunk.chunk_id
            })

        # Debug: Log what search returned (first 2 results)
        if formatted_results:
            logger.info(f"Search results preview (first 2 of {len(formatted_results)}):")
            for idx, result in enumerate(formatted_results[:2], 1):
                logger.info(f"  Result {idx}:")
                logger.info(f"    document_title: '{result['document_title']}'")
                logger.info(f"    document_source: '{result['document_source']}'")
                logger.info(f"    content preview: '{result['content'][:80]}...'")

        return formatted_results

    except Exception as e:
        logger.error(f"Search failed: {e}")
        # Return empty list instead of raising (graceful degradation)
        return []


@specialist_agent.output_validator  # Updated from result_validator (deprecated)
async def validate_dutch_response(ctx: RunContext[SpecialistDeps], response: SpecialistResponse) -> SpecialistResponse:
    """
    Validate specialist response before returning.

    Ensures:
    1. Response has content
    2. Response appears to be in Dutch (basic check)
    3. Has at least some citations (warns if <2)

    Args:
        ctx: Agent context
        response: Generated response

    Returns:
        Validated response (with warnings logged if needed)
    """
    # Check content exists
    if not response.content or len(response.content.strip()) == 0:
        logger.warning("Empty response content generated")
        response.content = "Ik kon geen passend antwoord genereren. Probeer de vraag anders te formuleren."

    # Basic Dutch check (very simple - just check for common English words)
    common_english = ["the", "and", "or", "but", "with", "from", "this", "that", "these"]
    content_lower = response.content.lower()
    english_found = [word for word in common_english if f" {word} " in content_lower]

    if english_found:
        logger.warning(f"Possible English words in Dutch response: {english_found}")

    # Check citations
    if len(response.citations) < 2:
        logger.warning(f"Only {len(response.citations)} citations provided (expected ≥2)")

    # Ensure search_metadata exists
    if not response.search_metadata:
        response.search_metadata = {}

    return response


def convert_openai_to_pydantic_history(messages: List[Dict[str, str]]) -> List:
    """
    Convert OpenAI-format messages to PydanticAI message_history format.

    Extracts conversation history from OpenWebUI request messages and converts
    to PydanticAI's ModelRequest/ModelResponse format for agent.run().

    FEAT-008: Stateless multi-turn conversations
    - OpenWebUI sends full history in request.messages
    - Extract all messages except last (current query)
    - Convert user → ModelRequest, assistant → ModelResponse
    - Skip system messages (handled separately by agent config)

    Args:
        messages: List of OpenAI-format messages with role/content
                  Example: [{"role": "user", "content": "Hi"},
                           {"role": "assistant", "content": "Hello"},
                           {"role": "user", "content": "Current query"}]

    Returns:
        List of PydanticAI ModelMessage objects for message_history parameter
        Example: [ModelRequest(...), ModelResponse(...)]
        Note: Last message excluded (it's the current query)

    Handles:
        - AC-FEAT-008-NEW-101: Empty messages array → returns []
        - AC-FEAT-008-NEW-102: System messages filtered out
        - AC-FEAT-008-NEW-103: Order preserved exactly
        - AC-FEAT-008-NEW-104: Invalid messages skipped with warning
        - AC-FEAT-008-NEW-106: Mixed role sequences allowed
        - AC-FEAT-008-NEW-108: Unicode/Dutch characters preserved

    Related:
        - docs/features/FEAT-008_advanced-memory/architecture-v2.md (Pattern 1)
        - docs/features/FEAT-008_advanced-memory/acceptance-v2.md (AC criteria)
    """
    history = []

    # Handle edge case: empty or single message (AC-101, AC-105)
    if not messages or len(messages) <= 1:
        logger.debug("No history to convert (first message or empty array)")
        return history

    # Convert all messages except last (current query)
    for msg in messages[:-1]:
        try:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Skip system messages (AC-102)
            if role == "system":
                logger.debug("Skipping system message in history conversion")
                continue

            # Validate message has content (AC-104)
            if not content:
                logger.warning(f"Skipping message with empty content: role={role}")
                continue

            # Convert based on role
            if role == "user":
                # User message → ModelRequest with UserPromptPart
                history.append(
                    ModelRequest(parts=[UserPromptPart(content=content)])
                )
            elif role == "assistant":
                # Assistant message → ModelResponse with TextPart
                history.append(
                    ModelResponse(parts=[TextPart(content=content)])
                )
            else:
                # Unknown role (AC-104)
                logger.warning(f"Unknown message role '{role}', skipping")

        except Exception as e:
            # Graceful error handling (AC-104, AC-205)
            logger.warning(f"Error converting message: {e}, skipping message")
            continue

    logger.info(f"Converted {len(history)} messages from history (excluded last message)")
    return history


async def run_specialist_query(
    query: str,
    session_id: Optional[str] = None,
    user_id: str = "cli_user",
    message_history: Optional[List] = None
) -> SpecialistResponse:
    """
    Convenience function to run a single specialist query.

    Wraps specialist_agent.run() with automatic dependency setup.
    Language is automatically detected from the query - no need to specify.

    FEAT-008: Now supports conversation history for multi-turn interactions.

    Args:
        query: Safety question (in Dutch or English - language auto-detected)
        session_id: Optional session ID (generates UUID if None)
        user_id: User identifier (default: "cli_user")
        message_history: Optional conversation history (PydanticAI ModelMessage list)
                        Used by OpenWebUI integration for stateless multi-turn conversations

    Returns:
        SpecialistResponse with content, citations, metadata

    Example:
        >>> response = await run_specialist_query("What are the requirements for working at height?")
        >>> print(response.content)  # Responds in English
        "For working at height..."
        >>> response = await run_specialist_query("Wat zijn de vereisten voor werken op hoogte?")
        >>> print(response.content)  # Responds in Dutch
        "Voor werken op hoogte..."
    """
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # Create dependencies
    deps = SpecialistDeps(
        session_id=session_id,
        user_id=user_id
    )

    # Create agent (language detected automatically from query)
    agent = _create_specialist_agent()

    # Register the search_guidelines tool on this agent instance
    @agent.tool
    async def search_guidelines_local(
        ctx: RunContext[SpecialistDeps],
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search Dutch workplace safety guidelines."""
        return await search_guidelines(ctx, query, limit)

    # Register output validator
    @agent.output_validator
    async def validate_response_local(ctx: RunContext[SpecialistDeps], response: SpecialistResponse) -> SpecialistResponse:
        """Validate specialist response before returning."""
        return await validate_dutch_response(ctx, response)

    # Run agent (FEAT-008: pass message_history for multi-turn conversations)
    result = await agent.run(query, message_history=message_history or [], deps=deps)

    # Extract response (use .output, not .data which is deprecated)
    response = result.output

    # Add search metadata if not present
    if not response.search_metadata:
        response.search_metadata = {}

    # Add chunks_retrieved count from tool calls (if available)
    try:
        if hasattr(result, 'all_messages') and callable(result.all_messages):
            # Count search tool calls
            all_messages = result.all_messages()
            search_calls = [msg for msg in all_messages if hasattr(msg, 'tool_name') and msg.tool_name == 'search_guidelines']
            if search_calls:
                # Sum up results from all search calls
                total_chunks = 0
                for call in search_calls:
                    if hasattr(call, 'tool_return') and isinstance(call.tool_return, list):
                        total_chunks += len(call.tool_return)
                response.search_metadata['chunks_retrieved'] = total_chunks
    except (AttributeError, TypeError):
        # In tests or when messages not available, skip
        pass

    return response


async def run_specialist_query_stream(
    query: str,
    session_id: Optional[str] = None,
    user_id: str = "cli_user",
    message_history: Optional[List] = None
):
    """
    Stream specialist agent response token-by-token (FEAT-010).

    Uses Pydantic AI 0.3.2's .stream_structured() for true streaming.
    Yields text deltas during generation, then yields final response with citations.
    Language is automatically detected from the query.

    FEAT-008: Now supports conversation history for multi-turn streaming interactions.

    Args:
        query: Safety question (in Dutch or English - language auto-detected)
        session_id: Optional session ID (generates UUID if None)
        user_id: User identifier (default: "cli_user")
        message_history: Optional conversation history (PydanticAI ModelMessage list)
                        Used by OpenWebUI integration for stateless multi-turn conversations

    Yields:
        tuple[str, str | SpecialistResponse]:
            - ("text", delta): Text deltas during streaming
            - ("final", response): Complete SpecialistResponse with citations at end

    Example:
        >>> async for item_type, data in run_specialist_query_stream("Wat zijn de eisen voor werken op hoogte?"):
        ...     if item_type == "text":
        ...         print(data, end="", flush=True)
        ...     elif item_type == "final":
        ...         print(f"\nCitations: {len(data.citations)}")
    """
    from .streaming_utils import StreamHandler

    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # Create dependencies
    deps = SpecialistDeps(
        session_id=session_id,
        user_id=user_id
    )

    # Create agent (language detected automatically from query)
    agent = _create_specialist_agent()

    # Register the search_guidelines tool on this agent instance
    @agent.tool
    async def search_guidelines_local(
        ctx: RunContext[SpecialistDeps],
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search Dutch workplace safety guidelines."""
        return await search_guidelines(ctx, query, limit)

    # Register LENIENT output validator for streaming
    @agent.output_validator
    async def validate_response_stream(
        ctx: RunContext[SpecialistDeps],
        response: SpecialistResponse
    ) -> SpecialistResponse:
        """
        Lenient validation for streaming partials.

        OpenAI sends partial JSON: {} → {"content": ""} → {"content": "A"} → ...
        Only validate final response strictly.
        """
        # Detect partial response: has content but no citations yet
        is_partial = len(response.content) > 0 and len(response.citations) == 0

        if is_partial:
            # Allow partials through without strict validation
            return response
        else:
            # Final response: apply strict validation
            return await validate_dutch_response(ctx, response)

    # Initialize stream handler for delta tracking
    handler = StreamHandler()

    try:
        # Use run_stream() for structured output streaming (FEAT-008: pass message_history)
        async with agent.run_stream(query, message_history=message_history or [], deps=deps) as result:
            # Pydantic AI 0.3.2: stream_structured() yields (ModelResponse, is_last) tuples
            async for message, is_last in result.stream_structured():
                # Validate with partial support (allows incomplete citations during streaming)
                validated = await result.validate_structured_output(message, allow_partial=True)

                # Extract content from validated partial response
                if hasattr(validated, 'content') and isinstance(validated.content, str):
                    # Calculate delta (only NEW text)
                    delta = handler.process_chunk(validated.content)

                    if delta:
                        # Yield text delta for real-time streaming
                        yield ("text", delta)

            # After streaming completes, get final response with citations
            final_response = await result.get_output()

            # Add search metadata if not present
            if not final_response.search_metadata:
                final_response.search_metadata = {}

            # Yield final response with citations (eliminates need for duplicate agent run)
            yield ("final", final_response)

    finally:
        # Clean up resources
        handler.cleanup()
