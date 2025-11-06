# Vector Search Flow: OpenWebUI → Response

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        OpenWebUI (Port 3001)                             │
│                  User types: "Wat zijn vereisten                          │
│                   voor werken op hoogte?"                                │
└─────────────────────────┬──────────────────────────────────────────────┘
                          │
                          │ HTTP POST to /v1/chat/completions
                          │ with conversation history
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Server (Port 8058)                            │
│                   agent/api.py → routes request                          │
│                 to specialist_agent.py                                   │
└─────────────────────────┬──────────────────────────────────────────────┘
                          │
                          │ Passes query to Pydantic AI Agent
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              Specialist Agent (Pydantic AI)                              │
│                                                                          │
│  Agent has access to tools:                                             │
│  • hybrid_search_tool()  ← Main tool for guidelines                     │
│  • search_products_tool() ← For product/intervention queries            │
└─────────────────────────────┬──────────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
        ┌───────────▼───────────┐   ┌───▼──────────────────────┐
        │  Question about        │   │  Question about          │
        │  guidelines?           │   │  interventions/products? │
        │  (most common)         │   │  (rare in MVP)           │
        │                        │   │                          │
        │ "Wat zijn vereisten    │   │ "Welke interventies      │
        │ voor werken op hoogte?"│   │ voor burn-out?"          │
        └───────────┬────────────┘   └───────┬──────────────────┘
                    │                        │
                    │ Call                    │ Call
                    │ hybrid_search_tool      │ search_products_tool
                    │                        │
                    ▼                        ▼
        ┌──────────────────────┐   ┌──────────────────────┐
        │ HYBRID SEARCH        │   │ PRODUCT SEARCH       │
        │ (PostgreSQL)         │   │ (PostgreSQL)         │
        │                      │   │                      │
        │ 1. Generate query    │   │ Find products in     │
        │    embedding via     │   │ products table that  │
        │    OpenAI API        │   │ match keywords       │
        │                      │   │                      │
        │ 2. Vector search:    │   │ Return: Product      │
        │    Find 10,833       │   │ names, descriptions, │
        │    chunks by         │   │ URLs                 │
        │    cosine similarity │   │                      │
        │                      │   │ (Note: Empty in MVP) │
        │ 3. Text search:      │   └──────────────────────┘
        │    Find chunks by    │
        │    Dutch FTS match   │
        │                      │
        │ 4. Combine scores:   │
        │    70% vector +      │
        │    30% text          │
        │                      │
        │ Return: Top 10       │
        │ guideline chunks     │
        │ with citations       │
        └──────────┬───────────┘
                   │
                   │ Agent receives search results
                   │ (typically 8-10 relevant chunks)
                   │
                   ▼
        ┌──────────────────────────────────────┐
        │  Agent Decides: Do I have enough     │
        │  context to generate a response?     │
        │                                      │
        │  If YES → Call LLM to synthesize     │
        │  If NO → Return search results       │
        │                                      │
        │  For guidelines: Usually YES         │
        │  For products: Usually NO (empty)    │
        └──────────┬───────────────────────────┘
                   │
                   │ Call OpenAI LLM with:
                   │ • User question (Dutch)
                   │ • Search results (10 chunks)
                   │ • System prompt (cite sources)
                   │
                   ▼
        ┌──────────────────────────────────────┐
        │  OpenAI LLM (gpt-4o-mini)            │
        │                                      │
        │  Input:                              │
        │  "Answer in Dutch about working      │
        │   at height. Use these 10 guidelines │
        │   as context. Cite 2+ sources."      │
        │                                      │
        │  Output: Streaming response          │
        │  token by token...                   │
        └──────────┬───────────────────────────┘
                   │
                   │ Stream back to FastAPI
                   │ (Server-Sent Events)
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Returns Streaming                             │
│                     Response to OpenWebUI                                │
│                                                                          │
│  SSE Format:                                                             │
│  data: {"choices":[{"delta":{"content":"Werken"}}]}                    │
│  data: {"choices":[{"delta":{"content":" op"}}]}                       │
│  data: {"choices":[{"delta":{"content":" hoogte"}}]}                   │
│  ...                                                                    │
│  data: [DONE]                                                           │
└─────────────────────────┬──────────────────────────────────────────────┘
                          │
                          │ Real-time SSE stream
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        OpenWebUI Browser                                 │
│                                                                          │
│  Displays response as it streams:                                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ Werken op hoogte vereist specifieke voorzorgsmaatregelen:       │   │
│  │                                                                  │   │
│  │ - Valbeveiliging moet aangebracht zijn                          │   │
│  │ - Werknemers moeten training hebben                             │   │
│  │                                                                  │   │
│  │ 📚 Bronnen                                                       │   │
│  │ [Richtlijn Werken op Hoogte](https://nvab-online.nl/...)        │   │
│  │ [Arbowet artikel 3](https://uwv.nl/...)                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  • Citations are clickable links                                         │
│  • User can ask follow-up questions (multi-turn)                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Where search_products_tool Fits In

```
Agent Decision Logic:
├─ Query about guidelines? → Use hybrid_search_tool
│  Examples: "Wat zijn risico's van...?"
│            "Hoe voorkom ik...?"
│            "Welke vereisten..."
│
└─ Query about products/interventions? → Use search_products_tool
   Examples: "Welke interventies biedt EVI 360?"
             "Hebben jullie begeleiding?"
             "Wat kan ik bestellen?"

   Status in MVP: Products table is EMPTY
   → Tool would work but returns no results
   → Agent falls back to citing only guidelines
```

---

## Key Components

| Component | Role |
|-----------|------|
| **OpenWebUI** | User interface (browser) |
| **FastAPI** | HTTP server, routes requests |
| **Specialist Agent** | Orchestrates which tool to use |
| **hybrid_search_tool** | Vector + text search in guidelines |
| **OpenAI Embedding** | Converts query to 1536-dim vector |
| **PostgreSQL + pgvector** | Stores embeddings, performs search |
| **OpenAI LLM** | Synthesizes response from search results |
| **Streaming SSE** | Real-time response to browser |

---

## Performance

| Step | Time |
|------|------|
| OpenWebUI → API | ~50ms |
| Generate embedding | ~100-200ms |
| Hybrid search (vector + FTS) | ~200-500ms |
| LLM response generation | ~2-3 seconds |
| Stream to browser | Continuous |
| **Total (first word)** | **~2-3 seconds** |
| **Total (full response)** | **~4-5 seconds** |
