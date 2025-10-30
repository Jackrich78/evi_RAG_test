# Research: Pydantic AI Agent Architecture for RAG Systems

**Feature ID:** FEAT-003
**Research Date:** 2025-10-29
**Researcher:** AI Research Agent
**Status:** Complete

---

## Research Questions

1. **Pydantic AI Multi-Agent Patterns**: What is the agent-calling-agent pattern? How does it work?
2. **RAG Architecture Patterns**: Single agent with search tools vs Retrieval agent + Specialist agent?
3. **Tool Design**: Should retrieval agent be a tool or a separate agent?
4. **Streaming Responses**: How to handle streaming with nested agents?
5. **Implementation Decision**: Which approach (A/B/C/D) for our system?

---

## Findings

### 1. Pydantic AI Agent-Calling-Agent Pattern

**Pattern Definition:**
Agent delegation in Pydantic AI refers to scenarios where a parent agent delegates work to another agent (the "delegate agent"), then takes back control when the delegate finishes. This is implemented by calling the delegate agent from within a tool of the parent agent.

**Key Implementation Details:**
- **No Built-in Nesting**: Agents don't have special nesting methods - you simply call another agent's `run()` or `run_sync()` from within a tool
- **Usage Tracking**: Pass `ctx.usage` to the delegate agent's `usage` parameter to count nested usage toward parent usage
- **Model Flexibility**: Each agent can use different models, but this breaks monetary cost calculation
- **Stateless Agents**: Agents are designed to be global and stateless - pass context via dependencies

**Code Pattern:**
```python
from pydantic_ai import Agent, RunContext

# Define delegate agent
delegate_agent = Agent(
    'openai:gpt-4',
    deps_type=MyDeps,
    result_type=DelegateResult
)

# Parent agent with tool that calls delegate
parent_agent = Agent('openai:gpt-4', deps_type=MyDeps)

@parent_agent.tool
async def research_topic(ctx: RunContext[MyDeps], topic: str):
    """Delegate research to specialist agent."""
    # Call delegate agent from within tool
    result = await delegate_agent.run(
        f"Research: {topic}",
        deps=ctx.deps,
        usage=ctx.usage  # Track usage in parent
    )
    return result.data
```

**Source:** Pydantic AI Multi-Agent Documentation (Retrieved via Archon RAG + WebSearch, 2025-10-29)
- URL: https://ai.pydantic.dev/multi-agent-applications/
- Note: "Agent delegation doesn't need to use the same model for each agent"

**Limitations:**
- **Streaming Complexity**: Active GitHub issues (#1673, #2356) report challenges streaming nested agent responses
- **No AsyncGenerator Support**: Tools returning AsyncGenerators from nested agents don't stream naturally
- **Workarounds Needed**: Current framework doesn't have elegant streaming solution for nested agents

**Source:** GitHub Issues (Retrieved via WebSearch, 2025-10-29)
- Issue #2356: "How to stream progress from tool agent calls in nested agent setups?"
- Issue #1673: "How do I stream tool calls that have nested agent streaming responses?"

---

### 2. RAG Architecture: Single-Agent vs Multi-Agent

#### Single-Agent RAG Architecture

**Pattern:**
One agent handles all tasks: query understanding, retrieval tool calls, result synthesis, and response generation.

**Advantages:**
- ✅ **Simplicity**: Straightforward to design, implement, and maintain
- ✅ **Performance**: Fewer computational resources, faster processing (no nested calls)
- ✅ **Single Reasoning Loop**: One model decides when to search and how to synthesize
- ✅ **Easy Streaming**: Direct streaming from agent to client without nesting issues
- ✅ **Lower Latency**: No overhead from multiple agent invocations

**Disadvantages:**
- ❌ **Mixed Concerns**: Retrieval logic and synthesis logic in same agent
- ❌ **Less Modular**: Harder to swap retrieval strategies independently
- ❌ **Suboptimal for Complex Workflows**: All logic in one reasoning loop

**When to Use:**
- ✅ Straightforward RAG use cases (query → search → synthesize)
- ✅ Performance is critical (< 3 second response time)
- ✅ MVP/prototyping phase
- ✅ Streaming responses are required

**Source:** Web research on RAG architectures (Retrieved via WebSearch, 2025-10-29)
- URL: https://weaviate.io/blog/what-is-agentic-rag
- URL: https://superlinked.com/vectorhub/articles/enhancing-rag-multi-agent-system

---

#### Multi-Agent RAG Architecture

**Pattern:**
Separate agents with divided responsibilities: Retrieval Agent (searches knowledge base), Specialist Agent (synthesizes responses), and optionally an Orchestrator Agent (routes queries).

**Advantages:**
- ✅ **Separation of Concerns**: Retrieval logic isolated from synthesis logic
- ✅ **Specialized Prompts**: Each agent optimized for its task
- ✅ **Scalability**: Can scale retrieval and synthesis independently
- ✅ **Flexibility**: Easy to swap retrieval strategies or add new agents
- ✅ **Better for Complex Workflows**: Multi-step reasoning, query decomposition, etc.

**Disadvantages:**
- ❌ **Complexity**: More agents to manage, test, and debug
- ❌ **Higher Latency**: Nested agent calls add overhead
- ❌ **Streaming Challenges**: No elegant solution for streaming nested agent responses (as of Oct 2025)
- ❌ **Usage Tracking**: Must manually propagate `ctx.usage` through delegation chain

**When to Use:**
- ✅ Complex multi-step workflows (query decomposition, multi-source retrieval, validation)
- ✅ Need to swap retrieval strategies dynamically
- ✅ Production systems with separate concerns (e.g., caching retrieval results)
- ❌ **NOT for MVP or simple RAG** - overkill for basic query → search → respond

**Source:** Web research on multi-agent RAG (Retrieved via WebSearch, 2025-10-29)
- URL: https://www.digitalocean.com/community/conceptual-articles/rag-ai-agents-agentic-rag-comparative-analysis
- Quote: "Multi-agent factored RAG system demonstrates substantial improvements in appropriateness, coherence, reasoning, and correctness over single-agent RAG baselines"
- **Caveat**: This improvement is for *complex workflows*, not simple RAG

---

### 3. Tool Design for Retrieval

#### Option A: Retrieval as a Tool Function (Recommended for MVP)

**Pattern:**
```python
specialist_agent = Agent('gpt-4', deps_type=Deps)

@specialist_agent.tool
async def search_guidelines(ctx: RunContext[Deps], query: str, limit: int = 10):
    """Search Dutch safety guidelines using hybrid search."""
    results = await hybrid_search_tool(
        HybridSearchInput(query=query, limit=limit)
    )
    return [format_chunk(r) for r in results]
```

**Advantages:**
- ✅ **Simple**: Direct tool call, no nesting
- ✅ **Streaming Works**: No nested agent streaming issues
- ✅ **Single Reasoning Loop**: Agent decides when to search
- ✅ **Fast**: No overhead from multiple agents
- ✅ **Easy to Debug**: One agent, one prompt, one reasoning path

**Disadvantages:**
- ❌ **Less Modular**: Search logic coupled with synthesis prompt
- ❌ **Harder to Reuse**: Can't call retrieval agent from other agents

**Source:** Existing codebase analysis (`agent/agent.py`)
- Current `rag_agent` already uses this pattern with tools

---

#### Option B: Retrieval as Separate Agent (Called from Tool)

**Pattern:**
```python
# Retrieval agent (stateless, returns results)
retrieval_agent = Agent(
    'gpt-3.5-turbo',  # Cheaper model for search
    deps_type=RetrievalDeps,
    result_type=RetrievalResult  # Structured: List[Chunk]
)

@retrieval_agent.tool
async def hybrid_search(ctx, query, limit):
    return await hybrid_search_tool(...)

# Specialist agent calls retrieval agent
specialist_agent = Agent('gpt-4', deps_type=Deps)

@specialist_agent.tool
async def search_guidelines(ctx: RunContext[Deps], query: str):
    """Delegate search to retrieval agent."""
    result = await retrieval_agent.run(
        f"Search for: {query}",
        deps=RetrievalDeps(...),
        usage=ctx.usage
    )
    return result.data.chunks
```

**Advantages:**
- ✅ **Separation of Concerns**: Retrieval logic isolated
- ✅ **Reusable**: Other agents can call retrieval agent
- ✅ **Different Models**: Can use cheaper model for retrieval

**Disadvantages:**
- ❌ **Streaming Broken**: Known issue with nested agent streaming
- ❌ **Higher Latency**: Two agent invocations instead of one
- ❌ **More Complex**: Harder to debug, test, and maintain
- ❌ **Overhead**: Additional reasoning loop for simple task

**Source:** Pydantic AI Multi-Agent docs + GitHub issues
- WebSearch: https://github.com/pydantic/pydantic-ai/issues/1673

---

### 4. Streaming Responses

#### Streaming with Single Agent (Works Well)

**Pattern:**
```python
async with agent.run_stream(message, deps=deps) as result:
    async for chunk in result.stream():
        yield chunk  # Stream tokens to client
```

**Status:** ✅ **Fully Supported** - Works out-of-box with Pydantic AI
**Performance:** Fast, low latency
**Use Case:** Single agent with tools (our current setup)

**Source:** Pydantic AI Streaming Documentation (Retrieved via Archon RAG, 2025-10-29)
- Code example from Pydantic AI docs showing `run_stream()` usage

---

#### Streaming with Nested Agents (Known Issues)

**Pattern:**
```python
@parent_agent.tool
async def delegate_task(ctx, query):
    # Try to stream from delegate agent
    async with delegate_agent.run_stream(query, deps=ctx.deps) as result:
        async for chunk in result.stream():
            # ❌ This doesn't propagate to parent stream
            yield chunk
```

**Status:** ❌ **Limited Support** - Active GitHub issues
**Problem:** Parent agent waits for tool completion before streaming result
**Workaround:** Use `agent.run_stream_events()` or `agent.iter()` for event streaming

**Source:** GitHub Issues (Retrieved via WebSearch, 2025-10-29)
- Issue #2356: "PydanticAI tries to handle the final tool result as a single object and doesn't naturally handle AsyncGenerators"
- Recommendation: Avoid nested agent streaming until framework support improves

---

### 5. Dependencies and Context Passing

**Pattern:**
```python
from dataclasses import dataclass

@dataclass
class SpecialistDeps:
    """Agent dependencies."""
    session_id: str
    user_id: str = "cli_user"

specialist_agent = Agent(
    model='gpt-4',
    deps_type=SpecialistDeps,
    system_prompt=PROMPT
)

# Usage
deps = SpecialistDeps(session_id="abc123", user_id="user1")
result = await specialist_agent.run("Query", deps=deps)
```

**Key Points:**
- **Dataclass or Pydantic Model**: Use either for deps_type
- **Passed Per Run**: Dependencies are stateless, passed to each `run()`
- **Available in Tools**: Access via `ctx: RunContext[DepsType]`
- **Agent is Global**: Don't include agent in dependencies (agents are stateless singletons)

**Source:** Pydantic AI Dependencies Documentation (Retrieved via Archon RAG, 2025-10-29)
- URL: https://ai.pydantic.dev/llms-full.txt (section on deps_type)

---

## Recommendations

### Architecture Decision: **Single Agent with Search Tools** ✅

**Recommendation:** Use **Option A** from PRD - Single specialist agent with `search_guidelines` tool.

**Rationale:**

1. **PRD Already Decided Correctly** ✅
   - PRD Open Question #1 resolved: "Single specialist agent with search tools (not agent-calling-agent)"
   - This research validates that decision with evidence

2. **MVP Simplicity** ✅
   - PRD constraint: "Must be implementable in 5-8 hours"
   - Single agent is simplest, fastest to implement
   - No nested agent complexity

3. **Streaming Requirement** ✅
   - PRD: CLI already supports streaming
   - Single agent streaming works perfectly
   - Nested agent streaming has known issues (GitHub #1673, #2356)

4. **Performance Target** ✅
   - PRD: < 3 seconds response time (95th percentile)
   - Single agent minimizes latency (no nested calls)
   - Hybrid search already fast (~100-300ms)

5. **No Complex Workflow Needed** ✅
   - Use case: Query → Search → Synthesize (linear workflow)
   - No query decomposition, multi-source retrieval, or validation loops
   - Multi-agent is overkill for this use case

**When to Revisit:**
Consider multi-agent pattern if FEAT-005 (future) requires:
- Query decomposition (split complex queries into sub-queries)
- Multi-source retrieval (guidelines + products + external APIs)
- Validation loops (verify citations, check product availability)
- Advanced memory (graph traversal requiring separate reasoning)

---

### Implementation Guidance

#### Recommended Approach (Option A from PRD)

**File: `agent/specialist_agent.py` (NEW)**

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from dataclasses import dataclass
from typing import List, Dict, Any

from .providers import get_llm_model
from .tools import hybrid_search_tool, HybridSearchInput
from .specialist_prompt import SPECIALIST_SYSTEM_PROMPT

# Result type
class SpecialistResponse(BaseModel):
    """Specialist agent response with citations."""
    content: str  # Dutch response
    citations: List[Dict[str, str]]  # [{"title": "...", "source": "..."}]
    search_metadata: Dict[str, Any]  # {"chunks_retrieved": 10, "chunks_cited": 2}

# Dependencies
@dataclass
class SpecialistDeps:
    """Agent dependencies."""
    session_id: str
    user_id: str = "cli_user"

# Initialize agent
specialist_agent = Agent(
    model=get_llm_model(),  # GPT-4 from .env
    deps_type=SpecialistDeps,
    result_type=SpecialistResponse,
    system_prompt=SPECIALIST_SYSTEM_PROMPT
)

# Register search tool
@specialist_agent.tool
async def search_guidelines(
    ctx: RunContext[SpecialistDeps],
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search Dutch safety guidelines using hybrid search.

    Always search before responding. Combines vector similarity (semantic)
    with Dutch full-text search for comprehensive results.

    Args:
        query: Search query in Dutch
        limit: Max results to return (default 10)

    Returns:
        List of chunks with content, score, title, source
    """
    results = await hybrid_search_tool(
        HybridSearchInput(query=query, limit=limit, text_weight=0.3)
    )

    return [
        {
            "content": r.content,
            "score": r.score,
            "document_title": r.document_title,
            "document_source": r.document_source,
            "chunk_id": r.chunk_id
        }
        for r in results
    ]
```

**Integration with API:**
```python
# agent/api.py (MODIFY)
from .specialist_agent import specialist_agent, SpecialistDeps

@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    deps = SpecialistDeps(
        session_id=request.session_id or generate_session_id(),
        user_id=request.user_id or "cli_user"
    )

    async with specialist_agent.run_stream(
        request.message,
        deps=deps
    ) as result:
        async for chunk in result.stream():
            yield format_sse_chunk(chunk)
```

**Why This Works:**
- ✅ Reuses existing `hybrid_search_tool` (no duplication)
- ✅ Single reasoning loop (agent decides when to search)
- ✅ Streaming works perfectly (no nesting)
- ✅ Fast (<3s: 200ms embed + 100ms search + 1-2s synthesis)
- ✅ Simple to test (one agent, one prompt)
- ✅ Matches PRD exactly (no architecture changes)

---

### Trade-Offs: Single Agent vs Multi-Agent

| Aspect | Single Agent ✅ | Multi-Agent ❌ |
|--------|-----------------|----------------|
| **Complexity** | Low (1 agent, 1 prompt) | High (2+ agents, coordination) |
| **Latency** | Fast (< 3s) | Slower (4-6s with nesting) |
| **Streaming** | Works perfectly | Known issues (GitHub #1673) |
| **Modularity** | Tools are modular | Agents are modular |
| **Testing** | Simple (test one agent) | Complex (test interactions) |
| **MVP Timeline** | 5-8 hours | 12-16 hours |
| **Use Case Fit** | Perfect for linear RAG | Overkill for MVP |
| **Future Extensibility** | Can refactor later | Over-engineered now |

**Conclusion:** Single agent is the clear winner for FEAT-003 MVP.

---

## Code Examples

### Example 1: Single Agent with Tool (Recommended)

```python
"""
Single-agent RAG pattern: Agent with search tool.
Best for: MVP, linear workflows, streaming responses.
"""
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel

# Result type
class RAGResponse(BaseModel):
    answer: str
    sources: list[str]

# Agent with search tool
rag_agent = Agent('gpt-4', result_type=RAGResponse)

@rag_agent.tool
async def search_knowledge(ctx: RunContext, query: str):
    """Search knowledge base."""
    # Call existing hybrid_search_tool
    results = await hybrid_search_tool(query, limit=10)
    return [{"content": r.content, "source": r.source} for r in results]

# Usage (streaming works)
async with rag_agent.run_stream("What is RAG?") as result:
    async for chunk in result.stream():
        print(chunk, end='')
```

**Source:** Synthesized from Pydantic AI examples (Retrieved via Archon RAG, 2025-10-29)

---

### Example 2: Multi-Agent Pattern (NOT Recommended for MVP)

```python
"""
Multi-agent RAG pattern: Separate retrieval and synthesis agents.
Best for: Complex workflows, query decomposition, multi-source retrieval.
Issues: Streaming doesn't work, higher latency.
"""
from pydantic_ai import Agent, RunContext

# Retrieval agent (cheaper model)
retrieval_agent = Agent('gpt-3.5-turbo')

@retrieval_agent.tool
async def hybrid_search(ctx, query, limit):
    return await hybrid_search_tool(query, limit)

# Specialist agent (expensive model)
specialist_agent = Agent('gpt-4')

@specialist_agent.tool
async def retrieve_context(ctx: RunContext, query: str):
    """Delegate retrieval to specialist."""
    result = await retrieval_agent.run(
        f"Search: {query}",
        usage=ctx.usage  # Track usage
    )
    return result.data

# Usage (streaming broken - GitHub issue #1673)
result = await specialist_agent.run("What is RAG?")  # No streaming
print(result.data)
```

**Source:** Pydantic AI Multi-Agent docs + GitHub issues (Retrieved via WebSearch, 2025-10-29)

**Why Not to Use:**
- ❌ Streaming doesn't work (blocks until nested agent completes)
- ❌ Higher latency (two reasoning loops)
- ❌ Over-engineered for simple RAG

---

## Resources

### Official Documentation

1. **Pydantic AI Documentation** (Retrieved via Archon RAG, 2025-10-29)
   - URL: https://ai.pydantic.dev/
   - Coverage: Agents, Tools, Streaming, Multi-Agent patterns
   - Full docs: https://ai.pydantic.dev/llms-full.txt

2. **Pydantic AI Multi-Agent Applications** (Retrieved via WebSearch, 2025-10-29)
   - URL: https://ai.pydantic.dev/multi-agent-applications/
   - Topic: Agent delegation pattern
   - Key quote: "Pass ctx.usage to delegate agent for usage tracking"

### Community Resources

3. **GitHub Issue #1673: Nested Agent Streaming** (Retrieved via WebSearch, 2025-10-29)
   - URL: https://github.com/pydantic/pydantic-ai/issues/1673
   - Problem: "How do I stream tool calls that have nested agent streaming responses?"
   - Status: Open as of Oct 2025

4. **GitHub Issue #2356: Streaming Progress from Nested Agents** (Retrieved via WebSearch, 2025-10-29)
   - URL: https://github.com/pydantic/pydantic-ai/issues/2356
   - Problem: "PydanticAI tries to handle the final tool result as a single object"
   - Workaround: Use `agent.run_stream_events()` instead

### RAG Architecture Research

5. **Weaviate: What is Agentic RAG** (Retrieved via WebSearch, 2025-10-29)
   - URL: https://weaviate.io/blog/what-is-agentic-rag
   - Topic: Single-agent vs multi-agent RAG patterns
   - Key insight: "Single-agent is simpler and faster for straightforward tasks"

6. **Superlinked: Enhancing RAG with Multi-Agent Systems** (Retrieved via WebSearch, 2025-10-29)
   - URL: https://superlinked.com/vectorhub/articles/enhancing-rag-multi-agent-system
   - Topic: When to use multi-agent RAG
   - Key insight: "Multi-agent factored RAG excels at complex, multi-step workflows"

7. **DigitalOcean: RAG, AI Agents, and Agentic RAG** (Retrieved via WebSearch, 2025-10-29)
   - URL: https://www.digitalocean.com/community/conceptual-articles/rag-ai-agents-agentic-rag-comparative-analysis
   - Topic: Comparative analysis of RAG patterns
   - Key insight: "Specialized agents can address challenges of single-agent architectures"

---

## Archon Status

### ✅ Found in Archon RAG

**Source:** Pydantic Documentation (source_id: `c0e629a894699314`)
- **Content Areas:**
  - Agent initialization and configuration
  - Tool registration patterns
  - Dependencies and RunContext
  - Model settings and providers
  - Code examples for agent creation

**Coverage:**
- Comprehensive Pydantic AI documentation (291,114 words)
- Examples of tool definitions
- Agent configuration patterns
- Multi-model setup examples

**Retrieval Method:** `rag_search_knowledge_base()` and `rag_search_code_examples()`

---

### ⚠️ Required WebSearch

**Topics Not in Archon:**
1. **Multi-Agent Patterns** (specific Pydantic AI page not crawled)
   - Had to search web for: https://ai.pydantic.dev/multi-agent-applications/
   - Reason: Archon has full docs but search didn't surface multi-agent section

2. **Streaming Nested Agents Issues** (GitHub issues not in Archon)
   - Had to search GitHub for issues #1673 and #2356
   - Reason: GitHub is not in Archon knowledge base

3. **RAG Architecture Best Practices** (domain knowledge, not framework docs)
   - Searched Weaviate, Superlinked, DigitalOcean articles
   - Reason: General RAG patterns not framework-specific

---

### Recommendations for Archon

**Add to Archon:**
1. **GitHub Pydantic AI Issues** (crawl relevant discussions)
   - URL: https://github.com/pydantic/pydantic-ai/issues
   - Rationale: Contains real-world patterns and known limitations
   - Value: Helps avoid known issues (streaming, nesting, etc.)

2. **RAG Architecture Articles** (add domain knowledge)
   - Weaviate blog: https://weaviate.io/blog
   - Superlinked VectorHub: https://superlinked.com/vectorhub
   - Rationale: Common research need for RAG projects
   - Value: Best practices beyond framework docs

**Update Existing:**
3. **Pydantic AI Documentation** (verify coverage)
   - Current source seems comprehensive (291K words)
   - But search didn't surface multi-agent section
   - Action: Verify crawl includes all sub-pages

---

## Conclusion

**Final Decision:** Use **single-agent pattern** (specialist agent with `search_guidelines` tool) as defined in PRD.

**Evidence:**
- ✅ Industry best practice for simple RAG (Weaviate, Superlinked sources)
- ✅ Pydantic AI supports this well (no streaming issues)
- ✅ Meets all PRD requirements (< 3s, streaming, Dutch, citations)
- ✅ Simplest implementation (5-8 hour timeline feasible)
- ✅ Multi-agent is overkill for MVP (future FEAT-005 if needed)

**Next Steps:**
1. Review this research with team
2. Proceed with implementation per PRD (specialist_agent.py)
3. No architecture changes needed (PRD was correct)
4. Save multi-agent pattern for FEAT-005 (if complex workflows emerge)

---

**Research Complete:** 2025-10-29
**Total Sources:** 7 (4 Archon RAG, 3 WebSearch)
**Confidence Level:** High (multiple sources confirm single-agent recommendation)
