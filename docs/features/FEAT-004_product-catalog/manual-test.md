# Manual Testing Guide: Product Catalog with Interventie Wijzer Integration

**Feature ID:** FEAT-004
**Created:** 2025-11-04
**Intended Audience:** Non-technical testers, QA team, EVI 360 specialists

## Overview

This guide provides step-by-step instructions for manually testing the Product Catalog feature. You'll verify that the specialist agent can recommend EVI 360 intervention products with working URLs and relevant suggestions for workplace safety problems.

**Prerequisites:**
- Access to OpenWebUI or API endpoint (ask developer for URL)
- No login required (testing uses test database)
- Chrome or Firefox browser (latest version)
- **Estimated Time:** 30-40 minutes for all scenarios

## Test Setup

### Before You Begin

1. **Environment:** Testing environment (not production)
2. **Data Reset:** Developer should run: `python3 -m ingestion.ingest_products` before testing
3. **Browser:** Chrome (recommended) or Firefox
4. **Screen Size:** Desktop resolution (1920x1080 or similar)

### Verification Steps

Before starting test scenarios, verify the system is ready:

**Step 1:** Confirm database has products
- Ask developer to run: `psql -c "SELECT COUNT(*) FROM products;"`
- Expected: Should return ~60 products

**Step 2:** Confirm OpenWebUI is accessible
- Open browser to [OpenWebUI URL from developer]
- Expected: Chat interface loads without errors

## Test Scenarios

### Test Scenario 1: Burn-out Begeleiding (Primary Happy Path)

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify agent recommends burn-out related products

**Steps:**

1. **Navigate** to OpenWebUI chat interface
   - **Expected:** You should see empty chat with text input box
   - **Screenshot location:** (Optional - save screenshot to `test-results/scenario-1-step-1.png`)

2. **Type** the following query in Dutch:
   ```
   Werknemer heeft burn-out klachten, 6 maanden verzuim
   ```

3. **Click** Send button or press Enter
   - **Expected:** Agent starts typing response (loading indicator visible)

4. **Wait** for complete response (may take 10-30 seconds)
   - **Expected:** Response includes both guideline information AND product recommendations

5. **Verify** the response contains product section:
   - [ ] Section header like "Relevante EVI 360 interventies:" or similar
   - [ ] At least 2-3 products listed
   - [ ] Product names in **bold** (surrounded by asterisks)
   - [ ] URLs visible in format: https://portal.evi360.nl/products/...

**Expected Products (should include at least 2 of these):**
- **Herstelcoaching** - Burn-out recovery coaching
- **Multidisciplinaire Burnout Aanpak** - Multidisciplinary burn-out approach
- **Psychologische Ondersteuning** - Psychological support

6. **Click** on one product URL (e.g., Herstelcoaching link)
   - **Expected:** Opens portal.evi360.nl product page in new tab
   - **Expected:** Product page loads successfully (not 404 error)

**✅ Pass Criteria:**
- Agent response includes products section
- At least 2 burn-out related products shown
- All product names are bolded
- All URLs are clickable and work (return HTTP 200)
- Products are relevant to burn-out query

**❌ Fail Scenarios:**
- If no products shown, note: "Agent did not recommend products"
- If URLs are broken (404), note: "Product URL X is broken"
- If products are irrelevant (e.g., pregnancy advice for burn-out query), note: "Products not relevant"

---

### Test Scenario 2: Fysieke Klachten door Tilwerk

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify agent recommends physical therapy and ergonomic products

**Steps:**

1. **Start new chat** (refresh page or click "New Chat" button)

2. **Enter** query:
   ```
   Werknemer heeft fysieke klachten door tilwerk
   ```

3. **Submit** and wait for response

4. **Verify** response includes:
   - [ ] Physical therapy or ergonomic intervention products
   - [ ] URLs present and formatted correctly
   - [ ] Product descriptions mention physical complaints, lifting, or ergonomics

**Expected Products (should include at least 1-2 of these):**
- **Bedrijfsfysiotherapie** - Occupational physiotherapy
- **Werkplekonderzoek** - Workplace ergonomic assessment
- **Vroegconsult Arbeidsfysiotherapeut** - Early physiotherapy consultation

5. **Test** one product URL by clicking
   - **Expected:** Opens correct product page

**✅ Pass Criteria:**
- Physical therapy or ergonomic products recommended
- Products match the physical complaints context
- URLs work correctly

**❌ Fail Scenarios:**
- Psychological products shown instead of physical therapy
- No products related to lifting or physical complaints

---

### Test Scenario 3: Conflict met Leidinggevende

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify mediation and conflict resolution products

**Steps:**

1. **New chat**

2. **Enter** query:
   ```
   Mijn werknemer heeft een ernstig conflict met de leidinggevende
   ```

3. **Verify** response includes conflict resolution products

**Expected Products:**
- **Mediation** - Mediation services
- **Inzet van een Mediator** - Mediator deployment
- Possibly: **Bedrijfsmaatschappelijk Werk** - Social work support

4. **Check** that products address conflict/relationships

**✅ Pass:** Mediation or conflict resolution products shown

**❌ Fail:** Unrelated products (e.g., physical therapy for conflict query)

---

### Test Scenario 4: Lange Termijn Verzuim

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify re-integration and long-term absence products

**Steps:**

1. **New chat**

2. **Enter** query:
   ```
   Werknemer is al 18 maanden ziek, hoe kan hij re-integreren?
   ```

3. **Verify** response includes re-integration products

**Expected Products:**
- **Re-integratietraject** - Re-integration trajectory
- **Arbeidsdeskundig Onderzoek** - Labor expert assessment
- **Loopbaanbegeleiding** - Career guidance

**✅ Pass:** Re-integration or assessment products shown

**❌ Fail:** Only short-term intervention products shown

---

### Test Scenario 5: Werkdruk Problemen

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify workload and stress management products

**Steps:**

1. **New chat**

2. **Enter** query:
   ```
   Team heeft last van te hoge werkdruk
   ```

3. **Verify** workload/stress management products

**Expected Products:**
- **Coaching** - Stress/workload coaching
- **Werkdrukanalyse** - Workload analysis
- Possibly: **Herstelcoaching** - Recovery coaching

**✅ Pass:** Workload or stress-related products shown

---

### Test Scenario 6: Zwangerschap en Werk

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify pregnancy and work accommodation products

**Steps:**

1. **New chat**

2. **Enter** query:
   ```
   Zwangere werknemer heeft advies nodig over werk aanpassen
   ```

3. **Verify** pregnancy-related products or workplace adjustment advice

**Expected Products:**
- **Vroegconsult Arbeidsdeskundige** - Early labor expert consultation
- Workplace adjustment advice products

**✅ Pass:** Pregnancy or workplace accommodation products shown

---

### Test Scenario 7: Psychische Klachten

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify psychological support products

**Steps:**

1. **New chat**

2. **Enter** query:
   ```
   Werknemer heeft psychische klachten
   ```

3. **Verify** psychological support products

**Expected Products:**
- **Vroegconsult Arbeidspsycholoog** - Early work psychologist consultation
- **Psychologische Ondersteuning** - Psychological support
- **Bedrijfsmaatschappelijk Werk** - Social work support

**✅ Pass:** Psychological support products shown (at least 2)

---

### Test Scenario 8: Leefstijl Coaching

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify lifestyle and wellness products

**Steps:**

1. **New chat**

2. **Enter** query:
   ```
   Werknemer wil werken aan gezondere leefstijl
   ```

3. **Verify** lifestyle coaching products

**Expected Products:**
- **Leefstijlprogramma's** - Lifestyle programs
- **Inzet Leefstijlcoach** - Lifestyle coach deployment
- **Gewichtsconsulent** - Weight consultant

**✅ Pass:** Lifestyle or wellness products shown

---

### Test Scenario 9: Re-integratie Traject

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify re-integration trajectory products

**Steps:**

1. **New chat**

2. **Enter** query:
   ```
   Werknemer moet re-integreren naar ander werk
   ```

3. **Verify** re-integration or career transition products

**Expected Products:**
- **Re-integratietraject 2e/3e Spoor** - Re-integration trajectory to other employer
- **Loopbaanbegeleiding** - Career guidance

**✅ Pass:** Re-integration or career products shown

---

### Test Scenario 10: Bedrijfsmaatschappelijk Werk

**Acceptance Criteria:** AC-004-012

**Purpose:** Verify social work support products

**Steps:**

1. **New chat**

2. **Enter** query:
   ```
   Werknemer heeft het emotioneel zwaar (scheiding, rouwverwerking)
   ```

3. **Verify** social work or emotional support products

**Expected Products:**
- **Inzet Bedrijfsmaatschappelijk Werk** - Social work deployment
- **Psychologische Ondersteuning** - Psychological support

**✅ Pass:** Social work or emotional support products shown

---

## Visual & UX Validation

*Things to check that aren't captured in specific test steps.*

### Overall Visual Check
- [ ] All product names are readable (not cut-off)
- [ ] Product URLs are underlined or clearly clickable
- [ ] Product descriptions are concise (not full paragraphs)
- [ ] Pricing shown if available (format: €X - €Y)
- [ ] Dutch language used throughout (no English products)
- [ ] No visual glitches (overlapping text, missing formatting)

### User Experience Check
- [ ] Response time feels acceptable (<30 seconds per query)
- [ ] Products section clearly separated from guideline citations
- [ ] Product list is scannable (numbered or bulleted)
- [ ] Clicking URL opens in new tab (doesn't lose chat context)
- [ ] Agent response feels natural (not robotic)

### Performance Check
- [ ] Page loads quickly (<3 seconds for OpenWebUI)
- [ ] No browser console errors (press F12 → Console tab)
- [ ] Chat doesn't freeze or hang during response
- [ ] Multiple consecutive queries work without refresh

## Cross-Browser Testing

*Test in multiple browsers if time allows.*

**Browsers to Test:**
- [ ] Chrome (primary test browser)
- [ ] Firefox (secondary)
- [ ] Safari (macOS users)

**For Each Browser:**
- [ ] Run Scenario 1 (Burn-out) at minimum
- [ ] Verify URLs are clickable
- [ ] Verify no formatting issues

## Bug Reporting

**If You Find a Bug, Report:**

1. **Title:** Brief description (e.g., "Product URLs broken for burn-out query")
2. **Scenario:** Which test scenario (e.g., "Scenario 1: Burn-out Begeleiding")
3. **Steps to Reproduce:**
   - Opened OpenWebUI at [URL]
   - Entered query: "Werknemer heeft burn-out klachten"
   - Clicked on "Herstelcoaching" URL
4. **Expected Result:** URL opens product page on portal.evi360.nl
5. **Actual Result:** URL returns 404 error
6. **Screenshot:** (Attach screenshot showing error)
7. **Environment:**
   - Browser: Chrome 120
   - Device: MacBook Pro (macOS 14)
   - Test Date: 2025-11-04

**Where to Report:**
- Create GitHub issue or
- Message developer directly or
- Add to testing spreadsheet

## Test Completion Checklist

### All Scenarios Complete
- [ ] Scenario 1: Burn-out Begeleiding - PASS / FAIL
- [ ] Scenario 2: Fysieke Klachten - PASS / FAIL
- [ ] Scenario 3: Conflict Leidinggevende - PASS / FAIL
- [ ] Scenario 4: Lange Termijn Verzuim - PASS / FAIL
- [ ] Scenario 5: Werkdruk Problemen - PASS / FAIL
- [ ] Scenario 6: Zwangerschap en Werk - PASS / FAIL
- [ ] Scenario 7: Psychische Klachten - PASS / FAIL
- [ ] Scenario 8: Leefstijl Coaching - PASS / FAIL
- [ ] Scenario 9: Re-integratie Traject - PASS / FAIL
- [ ] Scenario 10: Bedrijfsmaatschappelijk Werk - PASS / FAIL

### Additional Checks
- [ ] Visual & UX validation complete
- [ ] Cross-browser testing complete (or N/A)
- [ ] All product URLs tested (at least 1 per scenario)

### Summary
- **Total Scenarios:** 10
- **Passed:** [Y]
- **Failed:** [Z]
- **Bugs Filed:** [Number and description]

**Overall Assessment:**
- [ ] ✅ Feature is ready for release (≥7/10 pass)
- [ ] ⚠️ Feature has minor issues (5-6/10 pass, specify issues)
- [ ] ❌ Feature has blocking issues (<5/10 pass, specify issues)

**Tester Sign-off:**
- **Name:** [Your name]
- **Date:** [Testing completion date]
- **Notes:** [Any additional observations, e.g., "Burn-out products are excellent, but physical therapy products could be more specific"]

---

**Next Steps:**
- If ≥7/10 scenarios pass: Feature approved for production deployment
- If 5-6/10 pass: Developer fixes minor issues, retest affected scenarios only
- If <5/10 pass: Feature blocked, developer investigates root cause, full retest required

**Contact:**
- **For testing questions:** [Developer contact]
- **For bug reporting:** [GitHub issues link or Slack channel]
