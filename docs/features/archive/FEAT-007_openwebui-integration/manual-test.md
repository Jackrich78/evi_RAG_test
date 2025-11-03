# Manual Testing Guide: FEAT-007 OpenWebUI Integration

**Feature ID:** FEAT-007
**Feature Name:** OpenWebUI Integration
**Last Updated:** 2025-10-30
**Tester Role:** EVI 360 Specialist or QA Tester
**Estimated Time:** 45 minutes

---

## Purpose

This guide provides step-by-step instructions for manually validating the OpenWebUI integration with the EVI 360 RAG system. Focus areas include Dutch language support, streaming responses, citation rendering, and conversation management.

---

## Prerequisites

Before starting manual tests, ensure:

1. **Docker containers are running:**
   ```bash
   docker ps
   # Should show: postgres, pgvector, redis, openwebui, evi_api
   ```

2. **EVI API is accessible:**
   ```bash
   curl http://localhost:8058/health
   # Should return: {"status": "healthy"}
   ```

3. **OpenWebUI is accessible:**
   - Open browser to `http://localhost:3000`
   - Should see OpenWebUI login/chat interface

4. **Test data loaded:**
   - At least 3 Dutch guideline documents in database
   - Topics: Werken op hoogte, PSA, Brandveiligheid

5. **Browser:** Chrome or Firefox (latest version)

---

## Test Scenario 1: Access OpenWebUI Interface

**Objective:** Verify OpenWebUI loads and connects to EVI API.

**Steps:**

1. Open browser to `http://localhost:3000`
2. Observe the OpenWebUI interface loads without errors
3. Check browser console (F12) for any JavaScript errors
4. Verify "EVI 360 Specialist" model appears in model dropdown
5. Click on settings/configuration icon
6. Verify API endpoint shows `http://localhost:8058/v1`

**Expected Results:**

- ✅ OpenWebUI interface loads within 3 seconds
- ✅ No console errors or network failures
- ✅ Model dropdown includes "evi-specialist"
- ✅ API endpoint correctly configured to port 8058

**Actual Results:**

- [ ] Pass
- [ ] Fail (describe issue): ___________________________________

**Screenshots:**

- [ ] OpenWebUI home screen
- [ ] Model selection dropdown
- [ ] Settings/configuration page

---

## Test Scenario 2: Basic Dutch Guideline Query

**Objective:** Verify system returns relevant Dutch guidelines with streaming and citations.

**Steps:**

1. In chat interface, type: **"Wat zijn de richtlijnen voor werken op hoogte?"**
2. Press Enter or click Send button
3. Observe streaming response (text appears progressively)
4. Start timer when clicking Send
5. Stop timer when response completes
6. Scroll to bottom of response to view citations section
7. Click on a citation link (if interactive)

**Expected Results:**

- ✅ Response starts streaming within 1 second
- ✅ Full response completes within 2 seconds
- ✅ Response text is in Dutch
- ✅ Response mentions "valbescherming" or "hoogte" (relevant)
- ✅ Citations section labeled "📚 Bronnen" or similar
- ✅ At least 1 citation with document title
- ✅ Citation includes tier indicator (Tier 1, Tier 2, etc.)

**Actual Results:**

- Response time: ______ seconds
- [ ] Pass
- [ ] Fail (describe issue): ___________________________________

**Screenshots:**

- [ ] Streaming response (mid-stream)
- [ ] Complete response with citations

---

## Test Scenario 3: Conversation History

**Objective:** Verify system maintains context across multiple turns.

**Steps:**

1. Continue from Scenario 2 (or start new chat)
2. Ask follow-up question: **"Welke PSA heb ik daarvoor nodig?"**
3. Observe response references previous context (werken op hoogte)
4. Refresh browser page
5. Check if conversation history persists

**Expected Results:**

- ✅ Follow-up response mentions "valbescherming" or "hoogtewerk PSA"
- ✅ Response is contextually relevant (not generic PSA info)
- ✅ After refresh, conversation history still visible
- ✅ Can continue conversation after refresh

**Actual Results:**

- [ ] Pass
- [ ] Fail (describe issue): ___________________________________

**Screenshots:**

- [ ] Multi-turn conversation
- [ ] Conversation after page refresh

---

## Test Scenario 4: Citation Rendering and Validation

**Objective:** Verify citations display correctly and contain accurate metadata.

**Steps:**

1. Ask: **"Geef me details over brandveiligheid op de werkplek"**
2. Scroll to citations section at bottom of response
3. Count number of citations
4. For each citation, verify:
   - Document title is visible
   - Tier level indicated (Tier 1, 2, or 3)
   - Source document ID (if shown)
5. Click citation link (if interactive)
6. Verify link action (opens modal, scrolls to source, etc.)

**Expected Results:**

- ✅ Citations section clearly labeled and visually distinct
- ✅ 1-3 citations per response
- ✅ Each citation has title and tier
- ✅ Citation format matches: "📚 [Title] (Tier X)"
- ✅ Clicking citation performs expected action (modal or highlight)

**Actual Results:**

- Number of citations: ______
- [ ] Pass
- [ ] Fail (describe issue): ___________________________________

**Screenshots:**

- [ ] Citations section
- [ ] Citation click action (modal/link)

---

## Test Scenario 5: Error Handling

**Objective:** Verify system handles edge cases gracefully.

**Steps:**

1. **Empty Query Test:**
   - Send empty message (just spaces or newline)
   - Observe error message
2. **Very Long Query Test:**
   - Paste 500-word question in chat
   - Observe response or error
3. **Non-Safety Query Test:**
   - Ask: "What's the weather today?"
   - Observe response stays on-topic or politely declines

**Expected Results:**

- ✅ Empty query shows error: "Please enter a question"
- ✅ Long query either processes or shows character limit error
- ✅ Off-topic query responds: "I specialize in workplace safety..." (Dutch)

**Actual Results:**

- [ ] Pass
- [ ] Fail (describe issue): ___________________________________

---

## Dutch Language Test Queries

Execute all 10 queries below and verify responses are relevant and in Dutch:

| # | Query | Expected Topic | Pass/Fail |
|---|-------|----------------|-----------|
| 1 | Wat zijn de richtlijnen voor werken op hoogte? | Valbescherming, hoogtewerk | [ ] |
| 2 | Welke PSA moet ik dragen bij lassen? | Lasbril, handschoenen, schort | [ ] |
| 3 | Hoe voorkom ik brandgevaar in werkplaatsen? | Brandblusser, nooduitgang, opslag | [ ] |
| 4 | Wat is de procedure bij een ongeval? | EHBO, melding, onderzoek | [ ] |
| 5 | Welke veiligheidsmaatregelen gelden voor machines? | Noodstop, beveiligingen, training | [ ] |
| 6 | Hoe ga ik om met gevaarlijke stoffen? | SDS, opslag, ventilatie | [ ] |
| 7 | Wat zijn de regels voor tillen en dragen? | Ergonomie, gewichtslimiet, hulpmiddelen | [ ] |
| 8 | Welke eisen gelden voor werkverlichting? | Luxniveau, noodverlichting | [ ] |
| 9 | Hoe zorg ik voor goede ventilatie? | Luchtverversing, filters, controle | [ ] |
| 10 | Wat moet ik weten over elektriciteit op de werkplek? | Aarding, isolatie, controles | [ ] |

**Acceptance Criteria:**
- All 10 queries return responses in Dutch
- Responses are contextually relevant to topic
- No English fallback or error messages
- Citations provided for each response

---

## Visual & UX Validation Checklist

Check the following UI/UX elements:

- [ ] Response text is readable (font size, contrast)
- [ ] Streaming animation is smooth (no flickering)
- [ ] Citations section is visually distinct (border, background color)
- [ ] Mobile responsive (if applicable - test on phone)
- [ ] Dark mode support (if OpenWebUI has theme toggle)
- [ ] No layout breaks or overflow issues
- [ ] Conversation scrolls smoothly
- [ ] Copy/paste response text works
- [ ] Timestamps on messages are accurate

---

## Performance Observations

Record approximate timings:

| Metric | Target | Actual |
|--------|--------|--------|
| Time to first token (streaming starts) | <1 second | ______ |
| Full response completion (tier 1) | <2 seconds | ______ |
| Full response completion (tier 3) | <5 seconds | ______ |
| Page load time (OpenWebUI) | <3 seconds | ______ |
| Citation click response | <500ms | ______ |

---

## Known Issues & Workarounds

Document any issues discovered during testing:

| Issue | Severity | Workaround | Ticket # |
|-------|----------|------------|----------|
| Example: Citations not clickable | Low | View source doc manually | FEAT-007-BUG-001 |
|  |  |  |  |
|  |  |  |  |

---

## Final Acceptance Checklist

Mark all items before approving feature:

- [ ] All 10 Dutch queries return relevant responses
- [ ] Streaming works smoothly without errors
- [ ] Citations render correctly with titles and tiers
- [ ] Conversation history persists across page refresh
- [ ] Error handling works for empty and off-topic queries
- [ ] Performance meets targets (<2s for tier 1)
- [ ] No console errors in browser
- [ ] Visual/UX elements render correctly
- [ ] All screenshots captured and attached
- [ ] Known issues documented with severity

**Tester Signature:** _________________________
**Date Completed:** _________________________
**Approval Status:** [ ] APPROVED  [ ] REJECTED

---

## Appendix: Debug Commands

If issues occur during testing:

```bash
# Check API logs
docker logs evi_api --tail 50

# Check OpenWebUI logs
docker logs openwebui --tail 50

# Test API directly (bypass OpenWebUI)
curl -X POST http://localhost:8058/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "evi-specialist",
    "messages": [{"role": "user", "content": "Test vraag"}],
    "stream": false
  }'

# Check database connection
docker exec -it postgres psql -U postgres -d evi_rag -c "SELECT COUNT(*) FROM evi_guidelines;"

# Restart services
docker-compose restart
```

---

**Template Version:** 1.0.0
**Word Count:** 798 words
**Status:** Ready for execution
