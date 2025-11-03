# Manual Testing Guide: FEAT-003 - Specialist Agent with Vector Search

**Feature ID:** FEAT-003
**Created:** 2025-10-29
**Intended Audience:** Developers, QA testers, EVI 360 specialists

## Overview

This guide provides step-by-step instructions for manually testing the Specialist Agent MVP. Test scenarios validate Dutch language quality, citation accuracy, and performance targets.

**Prerequisites:**
- PostgreSQL container running with 10,833 Dutch chunks
- API server started on port 8058
- Virtual environment activated
- OpenAI API key configured in `.env`

**Estimated Time:** 30-45 minutes for all scenarios

## Test Setup

### Before You Begin

1. **Environment:** Local development
2. **Data Reset:** Not needed (read-only queries)
3. **Tools Needed:** Terminal, stopwatch/timer
4. **Screen Size:** Any (CLI-based)

### Start API Server

```bash
# 1. Ensure Docker containers running
docker-compose ps  # Should show postgres as (healthy)

# 2. Activate venv
source venv/bin/activate

# 3. Start API server
python3 -m uvicorn agent.api:app --host 0.0.0.0 --port 8058 --reload

# Expected output:
# INFO: Uvicorn running on http://0.0.0.0:8058
# INFO: Database initialized
# INFO: Application startup complete
```

### Start CLI

**English mode (default):**
```bash
# In new terminal:
source venv/bin/activate
python3 cli.py --language en  # or: python3 cli.py -l en

# Expected output:
# ============================================================
# 🤖 Agentic RAG with Knowledge Graph CLI
# ============================================================
# ✓ API is healthy
# Ready to chat!
# You:
```

**Dutch mode:**
```bash
python3 cli.py --language nl  # or: python3 cli.py -l nl
```

**Note:** Language parameter controls response language. Guidelines in database remain in Dutch.

## Test Scenarios

### Test Scenario 1: Basic Safety Question - Werken op Hoogte

**Acceptance Criteria:** AC-FEAT-003-001, 002, 003, 005, 007

**Purpose:** Validate Dutch response with citations and performance

**Steps:**
1. **Enter Query:** "Wat zijn de vereisten voor werken op hoogte?"
   - **Start Timer:** When you press Enter

2. **Observe Response Generation:**
   - **Expected:** Tokens appear incrementally (streaming)
   - **Expected:** Response completes within 3 seconds

3. **Stop Timer:** When response fully displayed
   - **Record Time:** ___________ seconds

4. **Verify Response Content:**
   - [ ] Response is in Dutch (no English)
   - [ ] Mentions specific height requirements (e.g., "2,5 meter", "valbeveiliging")
   - [ ] Provides actionable safety measures

5. **Verify Citations:**
   - [ ] At least 2 guideline titles shown
   - [ ] Each citation includes source (e.g., "NVAB", "ARBO", "UWV")
   - [ ] Citations appear relevant to fall protection

**✅ Pass Criteria:**
- Response time ≤3 seconds
- Response in Dutch
- ≥2 relevant citations
- Specific safety requirements mentioned

**❌ Fail Scenarios:**
- English words in response
- No citations or only 1 citation
- Generic advice without specifics
- Response time >5 seconds

---

### Test Scenario 2: Employee Health - Rugklachten Preventie

**Acceptance Criteria:** AC-FEAT-003-002, 003, 004

**Purpose:** Validate semantic search finds related terms

**Steps:**
1. **Enter Query:** "Hoe voorkom ik rugklachten bij werknemers?"

2. **Verify Response Content:**
   - [ ] Mentions ergonomics ("ergonomie")
   - [ ] Mentions lifting techniques ("tillen", "heffen")
   - [ ] Mentions workplace setup ("werkplek inrichting")

3. **Verify Citations:**
   - [ ] Guidelines about physical strain or ergonomics cited
   - [ ] NVAB or ARBO guidelines included

**✅ Pass Criteria:**
- Ergonomics or lifting guidelines cited
- Practical prevention measures mentioned
- Citations relevant to back pain prevention

**❌ Fail Scenarios:**
- Generic health advice unrelated to workplace
- No mention of lifting or ergonomics
- Irrelevant citations

---

### Test Scenario 3: Workplace Noise - Lawaai Maatregelen

**Acceptance Criteria:** AC-FEAT-003-003, 004

**Purpose:** Validate technical standards and regulations retrieved

**Steps:**
1. **Enter Query:** "Welke maatregelen zijn nodig voor lawaai op de werkplek?"

2. **Verify Response Content:**
   - [ ] Mentions decibel limits ("80 dB", "85 dB")
   - [ ] Mentions hearing protection ("gehoorbescherming")
   - [ ] Mentions noise reduction measures

3. **Verify Citations:**
   - [ ] Arbowet or technical standards cited
   - [ ] Specific regulations mentioned

**✅ Pass Criteria:**
- Decibel limits or technical standards mentioned
- Hearing protection referenced
- Regulatory guidelines cited

---

### Test Scenario 4: Employer Duty - Zorgplicht Werkgever

**Acceptance Criteria:** AC-FEAT-003-003, 005

**Purpose:** Validate legal/regulatory guideline retrieval

**Steps:**
1. **Enter Query:** "Wat is de zorgplicht van de werkgever?"

2. **Verify Response Content:**
   - [ ] Mentions Arbowet
   - [ ] Explains employer responsibilities
   - [ ] Uses legal/formal terminology

3. **Verify Citations:**
   - [ ] Arbowet or UWV guidelines cited
   - [ ] Legal obligations explained

**✅ Pass Criteria:**
- Arbowet mentioned
- Employer obligations clearly stated
- Legal citations included

---

### Test Scenario 5: Edge Case - Empty Query

**Acceptance Criteria:** AC-FEAT-003-101

**Purpose:** Validate graceful error handling

**Steps:**
1. **Enter Query:** Press Enter without typing anything

2. **Verify Response:**
   - [ ] No server crash
   - [ ] Helpful Dutch message displayed
   - [ ] Suggests entering a question

**✅ Pass Criteria:**
- No crash or error
- Polite Dutch message
- CLI remains responsive

**❌ Fail Scenarios:**
- Server crash or exception
- Error message in English
- CLI becomes unresponsive

---

### Test Scenario 6: Edge Case - Nonsense Query

**Acceptance Criteria:** AC-FEAT-003-102

**Purpose:** Validate handling of irrelevant queries

**Steps:**
1. **Enter Query:** "xyzabc qwerty foobar"

2. **Verify Response:**
   - [ ] Acknowledges no relevant results found
   - [ ] Message in Dutch: "Geen relevante richtlijnen gevonden"
   - [ ] No hallucinated citations

**✅ Pass Criteria:**
- Honest acknowledgment of no results
- No made-up guidelines
- Suggests rephrasing or provides help

---

### Test Scenario 7: Performance - Sequential Queries

**Acceptance Criteria:** AC-FEAT-003-201

**Purpose:** Validate consistent performance over multiple queries

**Steps:**
1. **Run 10 Queries:** Submit these queries sequentially:
   - "werken op hoogte"
   - "rugklachten preventie"
   - "lawaai werkplek"
   - "zorgplicht werkgever"
   - "arbeidsongeval"
   - "werkdruk Arbowet"
   - "nachtwerk regels"
   - "valbeveiliging EN normen"
   - "geluid blootstelling"
   - "zieke werknemer begeleiding"

2. **Record Times:** Track response time for each

3. **Verify Consistency:**
   - [ ] No significant slowdown from query 1 to 10
   - [ ] 9/10 queries complete in ≤3 seconds
   - [ ] No memory leak indicators (CLI stays responsive)

**✅ Pass Criteria:**
- 90% of queries ≤3 seconds
- No performance degradation
- All queries return valid responses

---

### Test Scenario 8: Dutch Quality Review

**Acceptance Criteria:** AC-FEAT-003-203

**Purpose:** Validate native Dutch language quality

**Steps:**
1. **Review 5 Responses:** From previous scenarios

2. **Check Each Response:**
   - [ ] Grammar is correct (verb conjugation, articles)
   - [ ] Uses informal "je/jij" (not formal "u")
   - [ ] Terminology is appropriate for workplace safety
   - [ ] Sounds natural (not machine-translated)
   - [ ] No awkward phrasings

3. **Optional:** Have Dutch native speaker review

**✅ Pass Criteria:**
- 5/5 responses grammatically correct
- Natural Dutch phrasing
- Proper workplace safety terminology

---

### Test Scenario 9: Citation Format Verification

**Acceptance Criteria:** AC-FEAT-003-005

**Purpose:** Validate citation formatting and clarity

**Steps:**
1. **Review Citations:** From scenarios 1-4

2. **Verify Format:**
   - [ ] Guideline title clearly visible
   - [ ] Source attribution present (NVAB, STECR, UWV, ARBO)
   - [ ] Quote or summary from guideline included
   - [ ] Format is consistent across responses

**✅ Pass Criteria:**
- All citations have title + source
- Format is readable and consistent
- Quotes are relevant

---

### Test Scenario 10: Concurrent Queries (Optional)

**Acceptance Criteria:** AC-FEAT-003-202

**Purpose:** Validate handling of simultaneous queries

**Steps:**
1. **Open 3 CLI Sessions:** In 3 separate terminals

2. **Submit Queries Simultaneously:** Different query in each

3. **Verify:**
   - [ ] All 3 queries complete successfully
   - [ ] No connection errors
   - [ ] Response times ≤5 seconds under load

**✅ Pass Criteria:**
- All concurrent queries succeed
- No timeouts or errors
- Acceptable performance degradation

---

### Test Scenario 11: Language Configuration (Added 2025-10-30)

**Acceptance Criteria:** AC-FEAT-003-301 (Language Support)

**Purpose:** Validate English and Dutch response modes with identical queries

**Steps:**

**Part A: English Mode**
1. **Start CLI in English:**
   ```bash
   python3 cli.py --language en
   ```

2. **Test Query:**
   ```
   You: What is NVAB?
   ```

3. **Verify Response:**
   - [ ] Response is in English
   - [ ] Content explains NVAB (Nederlandse Vereniging voor Arbeids- en Bedrijfsgeneeskunde)
   - [ ] Citations show document titles (not filenames with .md)
   - [ ] Minimum 2 citations present
   - [ ] Response time <3s

**Part B: Dutch Mode**
4. **Restart CLI in Dutch:**
   ```bash
   python3 cli.py --language nl
   ```

5. **Test Same Query:**
   ```
   You: Wat is NVAB?
   ```

6. **Verify Response:**
   - [ ] Response is in Dutch
   - [ ] Content identical meaning to English version
   - [ ] Citations format identical to English mode
   - [ ] Minimum 2 citations present

**Part C: Data Source Validation**
7. **Test Non-EVI Query (English mode):**
   ```
   You: Who is Sam Altman?
   ```

8. **Expected Result:**
   - [ ] Response: "I couldn't find specific workplace safety guidelines..."
   - [ ] NO information about OpenAI/tech companies
   - [ ] This confirms no contamination from test data

**✅ Pass Criteria:**
- Both modes return accurate answers
- English responses in English, Dutch in Dutch
- Citations show clean document titles
- No big_tech_docs contamination
- Response quality equivalent in both languages

**🎯 Key Learning:**
This test validates the language configuration feature added on 2025-10-30. The system:
- Uses dual system prompts (English/Dutch)
- Searches Dutch guidelines regardless of query language
- Translates key points when in English mode
- Citations are language-agnostic (just document titles)

---

## Visual & UX Validation

### CLI Output Check
- [ ] Response text is readable (proper line breaks)
- [ ] Citations are visually distinct (formatting, spacing)
- [ ] Dutch characters display correctly (ë, ï, ü)
- [ ] No text overflow or truncation
- [ ] Colors enhance readability (if used)

### User Experience Check
- [ ] Workflow feels intuitive
- [ ] Response wait time feels reasonable
- [ ] Citations are easy to identify
- [ ] Error messages are helpful (not cryptic)

### Performance Check
- [ ] First query may be slower (cold start <5s acceptable)
- [ ] Subsequent queries consistent <3s
- [ ] No noticeable lag in CLI responsiveness

## Bug Reporting

**If You Find a Bug, Report:**
1. **Title:** Brief description
2. **Scenario:** Which test scenario
3. **Steps to Reproduce:** Exact query entered
4. **Expected Result:** What should have happened
5. **Actual Result:** What actually happened
6. **Screenshot:** Terminal output
7. **Environment:**
   - API logs (check terminal)
   - Database status: `docker-compose ps`
   - Test account: CLI user

## Test Completion Checklist

### All Scenarios Complete
- [ ] Test Scenario 1: Basic Safety Question - PASS / FAIL
- [ ] Test Scenario 2: Employee Health - PASS / FAIL
- [ ] Test Scenario 3: Workplace Noise - PASS / FAIL
- [ ] Test Scenario 4: Employer Duty - PASS / FAIL
- [ ] Test Scenario 5: Edge Case - Empty Query - PASS / FAIL
- [ ] Test Scenario 6: Edge Case - Nonsense Query - PASS / FAIL
- [ ] Test Scenario 7: Performance - Sequential Queries - PASS / FAIL
- [ ] Test Scenario 8: Dutch Quality Review - PASS / FAIL
- [ ] Test Scenario 9: Citation Format Verification - PASS / FAIL
- [ ] Test Scenario 10: Concurrent Queries (Optional) - PASS / FAIL

### Additional Checks
- [ ] Visual & UX validation complete
- [ ] Performance acceptable
- [ ] Dutch quality validated

### Summary
- **Total Scenarios:** 10
- **Passed:** _____
- **Failed:** _____
- **Bugs Filed:** _____

**Overall Assessment:**
- [ ] ✅ Feature is ready for use
- [ ] ⚠️ Feature has minor issues (specify below)
- [ ] ❌ Feature has blocking issues (specify below)

**Notes:** ___________________________________________________________

**Tester Sign-off:**
- **Name:** _________________
- **Date:** _________________
- **Dutch Native Speaker:** Yes / No

---

**Next Steps:**
- If all tests pass: Mark FEAT-003 as complete
- If bugs found: File issues and retest after fixes
- Update implementation notes with any observations
