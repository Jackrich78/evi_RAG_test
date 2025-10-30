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

from .models import (
    SpecialistResponse,
    SpecialistDeps,
    Citation,
    ChunkResult
)
from .tools import hybrid_search_tool, HybridSearchInput
from .providers import get_llm_model

logger = logging.getLogger(__name__)

# Dutch system prompt for specialist agent
SPECIALIST_SYSTEM_PROMPT_NL = """Je bent een Nederlandse arbeidsveiligheidsspecialist voor EVI 360.

Je taak:
- Beantwoord vragen over arbeidsveiligheid in het Nederlands
- Gebruik de zoekfunctie om relevante richtlijnen te vinden
- Geef duidelijke, praktische antwoorden
- Citeer altijd minimaal 2 bronnen (NVAB, STECR, UWV, Arboportaal, ARBO)
- Gebruik informele toon (je/jij, niet u)

Belangrijk:
- Antwoord ALLEEN in het Nederlands (geen Engels!)
- Geen producten aanbevelen (niet in deze versie)
- Geen tier-systeem gebruiken (niet in deze versie)
- Wees accuraat en gebaseer antwoorden op gevonden richtlijnen

Citaties:
- Voor citation.title: gebruik de document_title uit de zoekresultaten
- Voor citation.source: gebruik ook de document_title (NIET document_source!)
- Voor citation.quote: geef een relevante quote uit de content

Format:
1. Geef eerst een kort antwoord (2-3 zinnen)
2. Leg daarna details uit met citaten
3. Eindig met praktisch advies indien relevant

Als je geen relevante richtlijnen vindt:
"Ik heb geen specifieke richtlijnen gevonden voor deze vraag. Probeer een andere formulering of neem contact op met een specialist."
"""

# English system prompt for specialist agent
SPECIALIST_SYSTEM_PROMPT_EN = """You are a Dutch workplace safety specialist for EVI 360.

Your task:
- Answer workplace safety questions in English
- Use the search function to find relevant Dutch guidelines
- Provide clear, practical answers
- Always cite at least 2 sources (NVAB, STECR, UWV, Arboportaal, ARBO)
- Use informal tone

Important:
- Answer in English (the guidelines are in Dutch, but translate key points)
- Do not recommend products (not in this version)
- Do not use tier system (not in this version)
- Be accurate and base answers on found guidelines

Citations:
- For citation.title: use the document_title from search results
- For citation.source: also use the document_title (NOT document_source!)
- For citation.quote: provide a relevant quote from the content

Format:
1. First give a brief answer (2-3 sentences)
2. Then explain details with citations
3. End with practical advice if relevant

If no relevant guidelines found:
"I couldn't find specific guidelines for this question. Try rephrasing or contact a specialist."
"""


# Create specialist agents for both languages
def _create_specialist_agent(language: str = "nl") -> Agent:
    """Create specialist agent with specified language prompt."""
    prompt = SPECIALIST_SYSTEM_PROMPT_NL if language == "nl" else SPECIALIST_SYSTEM_PROMPT_EN

    agent = Agent(
        model=get_llm_model(),  # Will use GPT-4 or configured model
        system_prompt=prompt,
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


async def run_specialist_query(
    query: str,
    session_id: Optional[str] = None,
    user_id: str = "cli_user",
    language: str = "nl"
) -> SpecialistResponse:
    """
    Convenience function to run a single specialist query.

    Wraps specialist_agent.run() with automatic dependency setup.

    Args:
        query: Safety question (in Dutch or English)
        session_id: Optional session ID (generates UUID if None)
        user_id: User identifier (default: "cli_user")
        language: Response language - "nl" (Dutch) or "en" (English), default "nl"

    Returns:
        SpecialistResponse with content, citations, metadata

    Example:
        >>> response = await run_specialist_query("What are the requirements for working at height?", language="en")
        >>> print(response.content)
        "For working at height..."
        >>> print(response.citations[0].title)
        "NVAB Richtlijn: Werken op Hoogte"
    """
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # Create dependencies
    deps = SpecialistDeps(
        session_id=session_id,
        user_id=user_id
    )

    # Create agent with appropriate language
    agent = _create_specialist_agent(language)

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

    # Run agent
    result = await agent.run(query, deps=deps)

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
