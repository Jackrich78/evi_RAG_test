# Manual Testing Guide - FEAT-003 Specialist Agent

This guide helps you manually test the specialist agent with real OpenAI API calls.

## Prerequisites

✅ **Before testing, ensure:**

1. **Database is running** with ingested Dutch guidelines:
   ```bash
   docker-compose up -d postgres
   ```

2. **Check database has chunks**:
   ```bash
   docker-compose exec postgres psql -U eviadmin -d evi_rag -c "SELECT COUNT(*) FROM chunks;"
   ```
   Expected: **10,833 chunks** (87 guidelines from Notion)

3. **Environment variables set** in `.env`:
   ```bash
   # Check these exist
   grep "LLM_API_KEY" .env
   grep "EMBEDDING_API_KEY" .env
   ```

4. **Virtual environment activated**:
   ```bash
   source venv/bin/activate
   ```

---

## Test 1: Quick Unit Tests (Free, Mocked)

**Purpose**: Verify code logic without API costs

```bash
python3 -m pytest tests/agent/test_specialist_agent.py -v
```

**Expected output**:
```
✓ Using MOCKED API (free, fast unit tests)
============================== test session starts ===============================
...
tests/agent/test_specialist_agent.py::test_specialist_agent_basic PASSED
tests/agent/test_specialist_agent.py::test_specialist_agent_citations PASSED
tests/agent/test_specialist_agent.py::test_specialist_agent_search_metadata PASSED
tests/agent/test_specialist_agent.py::test_run_specialist_query_convenience PASSED
tests/agent/test_specialist_agent.py::test_specialist_agent_no_english PASSED
tests/agent/test_specialist_agent.py::test_specialist_agent_empty_query PASSED

============================== 6 passed in 0.43s
```

✅ **If this passes**: Code structure and mocking are correct

---

## Test 2: Python Script Test (Real API, ~$0.01)

**Purpose**: Test the agent with real OpenAI API calls

### Create test script

Create `test_specialist_manual.py` in project root:

```python
"""
Manual test script for specialist agent with REAL OpenAI API.
Cost: ~$0.01 per query (gpt-4.1-mini + embeddings)
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import agent
from agent.specialist_agent import run_specialist_query

async def test_specialist_agent():
    """Test specialist agent with real Dutch query"""

    print("\n" + "="*70)
    print("🧪 TESTING SPECIALIST AGENT WITH REAL OPENAI API")
    print("="*70)

    # Dutch workplace safety query
    query = "Wat zijn de vereisten voor werken op hoogte?"

    print(f"\n📝 Query: {query}")
    print("\n🔍 Searching guidelines and generating response...")
    print("   (This will take 5-10 seconds and cost ~$0.01)")

    try:
        # Run specialist query with real API
        response = await run_specialist_query(
            query=query,
            session_id="manual-test-001",
            user_id="test-user"
        )

        print("\n✅ RESPONSE GENERATED")
        print("="*70)

        # Display response
        print("\n📄 Content:")
        print(response.content)

        print(f"\n📚 Citations ({len(response.citations)}):")
        for i, citation in enumerate(response.citations, 1):
            print(f"   {i}. {citation.title}")
            print(f"      Source: {citation.source}")
            if citation.quote:
                print(f"      Quote: {citation.quote[:100]}...")

        print(f"\n📊 Search Metadata:")
        for key, value in response.search_metadata.items():
            print(f"   {key}: {value}")

        # Validation checks
        print("\n🔍 VALIDATION CHECKS:")
        checks = {
            "Response is in Dutch": any(word in response.content.lower() for word in ["de", "het", "een", "zijn", "voor"]),
            "Response is not empty": len(response.content) > 0,
            "Has minimum 2 citations": len(response.citations) >= 2,
            "All citations have titles": all(c.title for c in response.citations),
            "All citations have sources": all(c.source for c in response.citations),
            "No obvious English": not any(word in response.content.lower() for word in [" the ", " and ", " with "]),
        }

        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")

        all_passed = all(checks.values())
        if all_passed:
            print("\n🎉 ALL VALIDATION CHECKS PASSED!")
        else:
            print("\n⚠️  SOME VALIDATION CHECKS FAILED")

        return all_passed

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_specialist_agent())
    exit(0 if success else 1)
```

### Run the test

```bash
python3 test_specialist_manual.py
```

### Expected output (example)

```
==================================================================
🧪 TESTING SPECIALIST AGENT WITH REAL OPENAI API
==================================================================

📝 Query: Wat zijn de vereisten voor werken op hoogte?

🔍 Searching guidelines and generating response...
   (This will take 5-10 seconds and cost ~$0.01)

✅ RESPONSE GENERATED
==================================================================

📄 Content:
Voor werken op hoogte boven 2,5 meter zijn strikte veiligheidseisen
van toepassing. Valbeveiliging is verplicht volgens de NVAB-richtlijnen.
Je moet zorgen voor geschikte valbescherming zoals hekwerken, netten of
persoonlijke beschermingsmiddelen zoals een veiligheidsharnas.

Belangrijke punten:
- Werk alleen op hoogte met juiste training
- Inspecteer apparatuur vooraf
- Gebruik altijd valbeveiliging vanaf 2,5 meter
- Zorg voor noodprocedures

Neem bij twijfel contact op met een arbeidsveiligheidsdeskundige.

📚 Citations (3):
   1. NVAB Richtlijn: Werken op Hoogte
      Source: NVAB
   2. Arbowet Artikel 3.16: Valgevaar
      Source: Arboportaal
   3. STECR Guideline: Fall Protection
      Source: STECR

📊 Search Metadata:
   chunks_retrieved: 8

🔍 VALIDATION CHECKS:
   ✅ Response is in Dutch
   ✅ Response is not empty
   ✅ Has minimum 2 citations
   ✅ All citations have titles
   ✅ All citations have sources
   ✅ No obvious English

🎉 ALL VALIDATION CHECKS PASSED!
```

---

## Test 3: Interactive Testing

Create an interactive testing script `interactive_test.py`:

```python
"""
Interactive testing for specialist agent.
Allows you to submit multiple queries and see responses.
"""

import asyncio
from agent.specialist_agent import run_specialist_query

async def interactive_test():
    """Interactive testing loop"""

    print("\n" + "="*70)
    print("🤖 EVI 360 SPECIALIST AGENT - INTERACTIVE TEST")
    print("="*70)
    print("\nSubmit Dutch workplace safety questions.")
    print("Type 'quit' to exit.\n")

    session_id = "interactive-session"
    query_count = 0

    while True:
        # Get query from user
        query = input("\n📝 Your question (in Dutch): ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Exiting interactive test.")
            break

        if not query:
            print("⚠️  Please enter a question.")
            continue

        query_count += 1

        try:
            print(f"\n🔍 Processing query {query_count}...")

            response = await run_specialist_query(
                query=query,
                session_id=f"{session_id}-{query_count}",
                user_id="interactive-user"
            )

            print("\n" + "-"*70)
            print("📄 RESPONSE:")
            print("-"*70)
            print(response.content)

            if response.citations:
                print(f"\n📚 CITATIONS ({len(response.citations)}):")
                for i, citation in enumerate(response.citations, 1):
                    print(f"   {i}. {citation.title} ({citation.source})")

            if response.search_metadata:
                print(f"\n📊 Search retrieved {response.search_metadata.get('chunks_retrieved', 'N/A')} chunks")

        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_test())
```

### Run interactive test

```bash
python3 interactive_test.py
```

### Example interaction

```
==================================================================
🤖 EVI 360 SPECIALIST AGENT - INTERACTIVE TEST
==================================================================

Submit Dutch workplace safety questions.
Type 'quit' to exit.

📝 Your question (in Dutch): Wat zijn de regels voor lawaai op de werkplek?

🔍 Processing query 1...

----------------------------------------------------------------------
📄 RESPONSE:
----------------------------------------------------------------------
Voor lawaai op de werkplek gelden specifieke richtlijnen...

📚 CITATIONS (2):
   1. NVAB Richtlijn: Gehoorbescherming (NVAB)
   2. Arbowet Geluidsnormen (Arboportaal)

📊 Search retrieved 6 chunks

📝 Your question (in Dutch): quit

👋 Exiting interactive test.
```

---

## Test 4: Acceptance Criteria Validation

Run this checklist manually after running the tests above:

### AC-FEAT-003-001: Dutch Query Processing
- [ ] Agent accepts Dutch queries
- [ ] No errors with Dutch characters (ë, ï, ü, ö)

### AC-FEAT-003-002: Dutch Response Generation
- [ ] Response is entirely in Dutch (no English)
- [ ] Uses informal tone (je/jij, not u)
- [ ] Clear and practical advice

### AC-FEAT-003-003: Citation Requirements
- [ ] Response includes ≥2 citations
- [ ] Each citation has title and source
- [ ] Sources are valid (NVAB, STECR, UWV, ARBO, Arboportaal)

### AC-FEAT-003-004: Hybrid Search
- [ ] Search retrieves relevant chunks (score >0.6)
- [ ] Top results relate to query
- [ ] Hybrid combines vector + full-text

### AC-FEAT-003-005: Response Structure
- [ ] Response has content field (main text)
- [ ] Response has citations array
- [ ] Response has search_metadata dict

### AC-FEAT-003-006: Performance
- [ ] Query completes in <10 seconds
- [ ] No crashes or exceptions
- [ ] Graceful error handling

### AC-FEAT-003-007: No Products (MVP)
- [ ] Response does NOT mention EVI 360 products
- [ ] No product recommendations in MVP

---

## Troubleshooting

### Error: "Database connection failed"

**Check PostgreSQL is running:**
```bash
docker-compose ps postgres
```

**Restart if needed:**
```bash
docker-compose restart postgres
```

### Error: "No chunks found"

**Verify chunks exist:**
```bash
docker-compose exec postgres psql -U eviadmin -d evi_rag -c "SELECT COUNT(*) FROM chunks WHERE document_source = 'NVAB';"
```

**Re-ingest if needed:**
```bash
python3 -m ingestion.ingest_notion
```

### Error: "OpenAI API key invalid"

**Check .env file:**
```bash
grep "LLM_API_KEY" .env
```

**Test API key:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"
```

### Error: "Agent returns English instead of Dutch"

**Check system prompt:**
- System prompt explicitly says "Antwoord ALLEEN in het Nederlands"
- Validator checks for English words

**Possible causes:**
- LLM model not following instructions (try different model)
- No relevant Dutch chunks found (check database)

---

## Cost Estimation

Testing costs with real OpenAI API:

| Test Type | Calls | Cost |
|-----------|-------|------|
| Single query | 1 embedding + 1 LLM call | ~$0.01 |
| 10 queries | 10 embeddings + 10 LLM calls | ~$0.10 |
| Interactive (30 min) | ~20 queries | ~$0.20 |

**Model costs (gpt-4.1-mini-2025-04-14)**:
- Input: $0.15 / 1M tokens (~$0.001 per query)
- Output: $0.60 / 1M tokens (~$0.005 per response)
- Embeddings: $0.00002 / 1K tokens (~$0.0001 per query)

**Total per query**: ~$0.01 (mostly LLM output tokens)

---

## Next Steps After Manual Testing

Once manual testing confirms the specialist agent works:

1. **Integrate into API** (`agent/api.py`)
   - Add `/chat/stream` endpoint
   - Wire up specialist agent
   - Add SSE streaming

2. **CLI Testing** (via API)
   - Test via `curl` or `httpie`
   - Test streaming responses

3. **Integration Tests**
   - End-to-end API → Agent → Database
   - Test with real Docker environment

4. **Production Readiness**
   - Add logging
   - Add error handling
   - Add rate limiting
   - Add monitoring

---

## Summary

**Unit Tests** (mocked): ✅ Fast, free, validates logic
**Manual Tests** (real API): Test end-to-end with real OpenAI + database
**Interactive Tests**: Best for UX validation and edge case discovery

**Recommended workflow**:
1. Run unit tests after every code change (free)
2. Run manual test script after feature changes (~$0.01)
3. Use interactive test for UX validation (~$0.20)
4. Run full integration tests before deployment

Good luck testing! 🚀
