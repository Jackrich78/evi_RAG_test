# PRD: FEAT-008 - Advanced Memory & Session Management

**Feature ID:** FEAT-008
**Phase:** 8 (Memory & Context) - **FUTURE FEATURE**
**Status:** 📋 Planned (Post-MVP)
**Priority:** Medium
**Owner:** TBD
**Dependencies:** FEAT-003 (MVP), FEAT-006 (Knowledge Graph population)
**Created:** 2025-10-26
**Last Updated:** 2025-10-26

---

## ⚠️ MVP Status: DESCOPED - Stateless Queries Only

**This feature is NOT part of the MVP (FEAT-003).** The MVP operates in stateless mode: each query is independent.

**Why Descoped:**
- Session memory adds complexity without improving single-query accuracy
- Tables exist (`sessions`, `messages`) but unused for MVP
- Focus on proving RAG quality first, then add conversation context
- Stateless is simpler to test and debug

**Current State:**
- `sessions` table: Empty
- `messages` table: Empty
- `db_utils.py` functions: `create_session()`, `add_message()` exist but unused
- Specialist agent: No deps on session history

**When to Implement:** After FEAT-003 MVP proves multi-turn conversations are needed (e.g., user testing shows specialists ask follow-up questions).

---

## Problem Statement

EVI 360 specialists often ask follow-up questions that require context from previous queries. Without session memory, users must repeat information, reducing efficiency and user experience.

**Example:**
- Query 1: "Wat zijn de vereisten voor werken op hoogte?"
- Query 2: "Welke producten heb je daarvoor?" ← Agent doesn't know "daarvoor" refers to fall protection

**Challenge:** Maintain conversation context without degrading response quality or accuracy. Balance between context retention and token limits (GPT-4 8k/32k context windows).

---

## Goals

1. **Session Tracking**: Store user queries and agent responses in `sessions` and `messages` tables
2. **Context Injection**: Include last N messages in agent prompt for follow-up understanding
3. **Graph-Based Memory**: Use Neo4j to track entities and relationships across conversations (FEAT-006 dependency)
4. **Entity Persistence**: Remember mentioned guidelines, products, and topics for session
5. **Session Expiry**: Auto-expire sessions after 60 minutes of inactivity

---

## User Stories

### Story 1: Follow-Up Question with Context

**As a** specialist
**I want** to ask "Welke producten?" after asking about fall protection
**So that** the agent knows I'm asking about fall protection products

**Acceptance Criteria:**
- [ ] Query 1: "Wat zijn de vereisten voor valbeveiliging?"
- [ ] Agent responds with guidelines
- [ ] Query 2: "Welke producten heb je daarvoor?"
- [ ] Agent understands "daarvoor" = valbeveiliging context
- [ ] Agent recommends fall protection products

### Story 2: Entity Tracking Across Queries

**As a** specialist researching noise regulations
**I want** the agent to remember I'm focused on noise/geluid
**So that** follow-up queries are interpreted in that context

**Acceptance Criteria:**
- [ ] Query 1: "Wat is de maximale blootstelling aan geluid?"
- [ ] Agent tracks entity: "geluid" (noise)
- [ ] Query 2: "Welke normen gelden daarvoor?"
- [ ] Agent interprets "normen" in context of noise/sound
- [ ] Cites EN standards for hearing protection

### Story 3: Session Resume After Break

**As a** specialist who pauses for 10 minutes
**I want** my conversation to persist
**So that** I can continue where I left off

**Acceptance Criteria:**
- [ ] Ask 3 questions in session
- [ ] Close browser
- [ ] Reopen within 60 minutes
- [ ] Session history is preserved
- [ ] Can resume with follow-up questions

---

## Scope

### In Scope ✅

**Basic Session Management:**
- Use existing `create_session()` and `add_message()` functions from `db_utils.py`
- Store session_id, user_id, query, response, timestamp
- Session expires after 60 minutes of inactivity

**Context Injection:**
- Include last 3-5 messages in agent prompt
- Format: "Previous conversation: Q1: ... A1: ... Q2: ... A2: ..."
- Truncate if context exceeds token limit

**Entity Tracking (Simple):**
- Extract key entities from queries (Dutch NER or GPT-4 extraction)
- Store in session metadata: `{"entities": ["valbeveiliging", "EN 361"]}`
- Agent can reference entities for context

**Graph-Based Memory (Advanced - requires FEAT-006):**
- Store conversation facts in Neo4j knowledge graph
- Link queries to guideline nodes
- Track entity relationships across sessions

### Out of Scope ❌

**Not included in v1:**
- Cross-session memory (remembering user across days/weeks)
- User profiles or preferences
- Conversation branching (tree structure)
- Undo/redo conversation steps
- Memory compaction (summarizing old conversations)

---

## Architecture

```
User Query
    ↓
API: Retrieve session history
    ↓
API: Format last N messages as context
    ↓
Specialist Agent (with context)
    ├─ Tools: search_guidelines (as before)
    └─ Additional context: Previous messages
    ↓
Agent Response
    ↓
API: Store query + response in messages table
    ↓
Return to user
```

**Key Changes from MVP:**
1. **SpecialistDeps**: Add `session_history: List[Dict]` field
2. **API Endpoint**: Call `get_session_messages()` before running agent
3. **System Prompt**: Append context section with previous messages
4. **Message Storage**: Call `add_message()` after agent completes

---

## Technical Notes

### Context Format

**Injected into system prompt:**
```
**Eerdere gesprek:**

Vraag 1: "Wat zijn de vereisten voor werken op hoogte?"
Antwoord 1: "Voor werken op hoogte gelden..."

Vraag 2: "Welke producten heb je daarvoor?"
Antwoord 2: [CURRENT RESPONSE]
```

### Session Storage

**sessions table:**
```sql
id UUID PRIMARY KEY
user_id TEXT
metadata JSONB (stores entities, topics)
expires_at TIMESTAMP
created_at TIMESTAMP
```

**messages table:**
```sql
id UUID PRIMARY KEY
session_id UUID FOREIGN KEY
role TEXT ('user' or 'assistant')
content TEXT
metadata JSONB (search results, citations)
created_at TIMESTAMP
```

### Entity Extraction

**Option 1: GPT-4 Extraction**
```python
async def extract_entities(query: str) -> List[str]:
    """Extract Dutch entities from query."""
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "system",
            "content": "Extract key Dutch workplace safety entities (topics, standards, equipment) from the query. Return as comma-separated list."
        }, {
            "role": "user",
            "content": query
        }]
    )
    return response.choices[0].message.content.split(", ")
```

**Option 2: spaCy Dutch NER**
```python
import spacy
nlp = spacy.load("nl_core_news_sm")
doc = nlp(query)
entities = [ent.text for ent in doc.ents]
```

---

## Implementation Plan

### Phase 1: Basic Session Storage (2 hours)

1. Modify API to call `create_session()` on first query
2. Store session_id in response, CLI persists it
3. Call `add_message()` after each query/response
4. Test: Verify messages stored in database

### Phase 2: Context Injection (2-3 hours)

1. Modify API to call `get_session_messages(session_id, limit=5)`
2. Format messages as context string
3. Append to system prompt before running agent
4. Test: Ask follow-up question, verify agent uses context

### Phase 3: Entity Tracking (2 hours)

1. Add entity extraction function
2. Store entities in session metadata
3. Include entities in context injection
4. Test: Multi-turn conversation about single topic

### Phase 4: Graph Memory (4-6 hours - requires FEAT-006)

1. Create conversation facts in Neo4j after each query
2. Link facts to guideline nodes
3. Query graph for relevant past conversations
4. Test: Cross-session memory retrieval

---

## Success Criteria

**Basic Memory:**
- ✅ Session persists across multiple queries
- ✅ Messages stored correctly in database
- ✅ Session expires after 60 minutes

**Context Understanding:**
- ✅ Agent correctly interprets "Welke producten?" after fall protection query
- ✅ Agent references previous answer when appropriate
- ✅ No context confusion (mixing up unrelated queries)

**Performance:**
- ✅ Context injection adds <200ms latency
- ✅ No degradation in response quality
- ✅ Token limits respected (no truncation errors)

---

## Dependencies

### Infrastructure
- ✅ PostgreSQL sessions and messages tables (already exist)
- ⏳ FEAT-006: Neo4j knowledge graph (for advanced graph memory)

### External
- OpenAI API (GPT-4 for entity extraction, optional)
- spaCy Dutch model (for NER, alternative to GPT-4)

---

## References

**Code:**
- Session functions: `agent/db_utils.py` (`create_session`, `add_message`, `get_session_messages`)
- Specialist agent: `agent/specialist_agent.py` (needs SpecialistDeps update)

**Documentation:**
- FEAT-003: MVP Specialist Agent
- FEAT-006: Knowledge Graph (dependency for graph memory)

---

**Last Updated:** 2025-10-26
**Status:** 📋 Planned (Post-MVP)
**Estimated Effort:** 6-10 hours (basic) or 10-16 hours (with graph memory)
**Risk Level:** Medium (context management can be tricky, token limits)
