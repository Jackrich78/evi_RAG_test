# Manual Testing Guide: True Token Streaming

**Feature:** FEAT-010: True Token Streaming
**Status:** Planning
**Created:** 2025-10-31
**Target Audience:** QA testers, product owners, non-technical stakeholders

## Overview

This guide provides step-by-step instructions for manually testing the token streaming feature in the EVI 360 RAG system. Follow these scenarios to validate that streaming works correctly across different browsers, devices, and network conditions.

## Prerequisites

### Setup Requirements

1. **Access to EVI 360 System:**
   - URL: [Your deployment URL]
   - Valid user credentials (safety specialist account)

2. **Test Browsers Installed:**
   - Google Chrome (latest version)
   - Mozilla Firefox (latest version)
   - Safari (latest version, macOS only)
   - Microsoft Edge (latest version)

3. **Test Devices:**
   - Desktop computer (Windows or macOS)
   - iPhone or iPad (iOS 15+)
   - Android phone or tablet (Android 10+)

4. **Network Access:**
   - Stable internet connection for baseline tests
   - Ability to simulate slow/interrupted connections (optional: browser dev tools)

### Test Data

Prepare these test queries for consistent testing:

- **Short Query (Dutch):** "Wat zijn de veiligheidsregels voor hoogwerkers?"
- **Long Query (Dutch):** "Geef een gedetailleerde uitleg over alle veiligheidsmaatregelen, procedures en richtlijnen voor het werken op hoogte met hoogwerkers in de bouwsector."
- **Short Query (English):** "What are the safety rules for aerial work platforms?"
- **Citation-Heavy Query:** "Welke producten bevelen jullie aan voor veiligheid op hoogte?" (Expected: multiple product citations)

## Test Scenarios

### Scenario 1: Basic Streaming Functionality

**Objective:** Verify that tokens stream progressively instead of appearing all at once

**Steps:**
1. Open Chrome browser and navigate to EVI 360 system
2. Log in with test credentials
3. In the chat interface, enter the short Dutch query
4. Click "Send" or press Enter
5. **Observe:** Watch the response area carefully

**Expected Results:**
- ✅ First word/token appears within 1 second of clicking Send
- ✅ Response builds progressively, word by word or phrase by phrase
- ✅ You can see the text appearing in real-time (not all at once)
- ✅ A cursor or animation indicates streaming is in progress
- ✅ Full response completes within 5-10 seconds

**Actual Results:**
- [ ] PASS / [ ] FAIL
- Notes: ___________________________________________

---

### Scenario 2: Citation Streaming

**Objective:** Verify that citations render correctly during streaming

**Steps:**
1. Clear the previous conversation or start a new session
2. Enter the citation-heavy query
3. Click Send and watch the response stream
4. **Observe:** Pay attention to citation markers `[1]`, `[2]`, etc.

**Expected Results:**
- ✅ Citation markers appear correctly as text streams
- ✅ Markers are not broken across chunks (e.g., no `[` appearing separately from `1]`)
- ✅ Citation panel on the right updates as markers appear
- ✅ Clicking a citation marker scrolls to the correct source in the panel
- ✅ All citations are clickable after streaming completes

**Actual Results:**
- [ ] PASS / [ ] FAIL
- Notes: ___________________________________________

---

### Scenario 3: Long Response Streaming

**Objective:** Verify streaming remains stable for long responses

**Steps:**
1. Enter the long Dutch query (detailed safety explanation)
2. Click Send and monitor the entire streaming process
3. **Observe:** Watch for smooth, continuous streaming

**Expected Results:**
- ✅ Streaming begins within 1 second
- ✅ Text continues to appear smoothly without freezing or stuttering
- ✅ No visible delays or pauses mid-stream
- ✅ Full response appears within 15-20 seconds
- ✅ UI remains responsive (can scroll, highlight text, etc.)

**Actual Results:**
- [ ] PASS / [ ] FAIL
- Notes: ___________________________________________

---

### Scenario 4: Bilingual Streaming

**Objective:** Verify streaming works correctly for both Dutch and English

**Steps:**
1. Test with short Dutch query, observe streaming
2. Test with short English query, observe streaming
3. Compare the streaming experience between languages

**Expected Results:**
- ✅ Dutch text streams correctly with proper character encoding (ë, ö, etc.)
- ✅ English text streams correctly
- ✅ No noticeable performance difference between languages
- ✅ Both languages complete streaming without errors

**Actual Results:**
- [ ] PASS / [ ] FAIL
- Notes: ___________________________________________

---

### Scenario 5: Error Handling - Network Interruption

**Objective:** Verify system handles network interruptions gracefully

**Steps:**
1. Open browser Developer Tools (F12)
2. Go to Network tab
3. Start a query streaming
4. After 2-3 seconds of streaming, click "Offline" in Network tab to simulate disconnection
5. **Observe:** How the system responds to the interruption

**Expected Results:**
- ✅ An error message appears indicating connection lost
- ✅ The text accumulated before disconnection remains visible
- ✅ A "Retry" or "Try Again" button is available
- ✅ Clicking retry re-submits the query and streaming resumes
- ✅ No browser console errors (check Console tab)

**Actual Results:**
- [ ] PASS / [ ] FAIL
- Notes: ___________________________________________

---

### Scenario 6: Rapid Consecutive Queries

**Objective:** Verify system handles rapid query submissions

**Steps:**
1. Enter a query and click Send
2. Immediately enter a second query and click Send (before first completes)
3. **Observe:** How the system handles the second query

**Expected Results:**
- ✅ First query streaming stops
- ✅ Second query streaming begins immediately
- ✅ No overlap or confusion between responses
- ✅ UI clearly shows which response is current
- ✅ No browser errors or crashes

**Actual Results:**
- [ ] PASS / [ ] FAIL
- Notes: ___________________________________________

---

### Scenario 7: Browser Compatibility

**Objective:** Verify streaming works across all supported browsers

**Steps:**
1. Repeat Scenario 1 (basic streaming) in each browser:
   - Chrome
   - Firefox
   - Safari (macOS only)
   - Edge
2. Note any differences in behavior

**Expected Results:**
- ✅ Streaming works consistently across all browsers
- ✅ Performance is similar (first token within 1 second)
- ✅ Visual appearance is consistent
- ✅ No browser-specific errors

**Actual Results per Browser:**
- Chrome: [ ] PASS / [ ] FAIL - Notes: ___________
- Firefox: [ ] PASS / [ ] FAIL - Notes: ___________
- Safari: [ ] PASS / [ ] FAIL - Notes: ___________
- Edge: [ ] PASS / [ ] FAIL - Notes: ___________

---

### Scenario 8: Mobile Device Testing

**Objective:** Verify streaming works on mobile devices

**Steps:**
1. Open EVI 360 on a mobile device (iOS or Android)
2. Log in and navigate to chat interface
3. Enter the short Dutch query
4. **Observe:** Streaming behavior on mobile

**Expected Results:**
- ✅ Streaming works on mobile browser
- ✅ First token appears within 2 seconds (allowing for mobile network)
- ✅ Text is readable and properly formatted
- ✅ UI is responsive and doesn't break layout
- ✅ Can scroll while streaming is in progress

**Actual Results:**
- iOS: [ ] PASS / [ ] FAIL - Notes: ___________
- Android: [ ] PASS / [ ] FAIL - Notes: ___________

---

## Acceptance Checklist

Before approving the feature, verify:

- [ ] All 8 test scenarios pass
- [ ] No critical bugs or crashes observed
- [ ] Performance meets expectations (first token < 1 second on desktop)
- [ ] Citations render correctly in all tests
- [ ] Error handling is user-friendly
- [ ] Works across all required browsers
- [ ] Mobile experience is acceptable
- [ ] Dutch and English responses stream correctly

## Known Limitations

Document any known limitations discovered during testing:

- ___________________________________________
- ___________________________________________
- ___________________________________________

## Bug Reporting Template

If you find issues during testing, report them with this format:

**Bug Title:** Brief description
**Severity:** Critical / High / Medium / Low
**Browser/Device:** Chrome on Windows 11 / Safari on iPhone 13, etc.
**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:** What should happen
**Actual Behavior:** What actually happened
**Screenshots:** [Attach if applicable]

---

**Template Version:** 1.0.0
**Word Count:** 795 words
