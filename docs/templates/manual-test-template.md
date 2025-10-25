# Manual Testing Guide: [Feature Name]

**Feature ID:** FEAT-XXX
**Created:** YYYY-MM-DD
**Intended Audience:** Non-technical testers, QA, product managers

## Overview

This guide provides step-by-step instructions for manually testing the [Feature Name] feature. Each test scenario is designed to be clear and actionable for non-technical users.

**Prerequisites:**
- [Access level required: admin, user, etc.]
- [Test environment URL or setup]
- [Test credentials if needed]
- [Sample data or files needed]

**Estimated Time:** [X minutes for all scenarios]

## Test Setup

### Before You Begin

1. **Environment:** [Which environment to test in: staging, dev, local]
2. **Data Reset:** [How to reset test data between tests if needed]
3. **Browser:** [Recommended browser and version]
4. **Screen Size:** [Desktop, mobile, specific resolution]

### Test Account Setup

**Test Credentials:**
- **Username:** [test username or how to create one]
- **Password:** [test password]
- **Role:** [user role/permissions needed]

### Sample Data Needed

- [File 1 to download/upload]
- [Sample data to enter]
- [Prerequisites completed]

## Test Scenarios

### Test Scenario 1: [Primary Happy Path]

**Acceptance Criteria:** AC-FEAT-XXX-001

**Purpose:** [What this test validates]

**Steps:**
1. **Navigate** to [URL or location in app]
   - **Expected:** You should see [specific element/page]
   - **Screenshot:** [Optional placeholder for screenshot]

2. **Click/Tap** on [specific button/link]
   - **Expected:** [What should happen]
   - **Screenshot:** [Optional]

3. **Enter** the following information:
   - **Field 1:** `[Value to enter]`
   - **Field 2:** `[Value to enter]`
   - **Expected:** Fields should accept input without errors

4. **Click** the [Submit/Save/etc.] button
   - **Expected:** [Success message, redirect, or result]
   - **Screenshot:** [Optional]

5. **Verify** the result:
   - [ ] [Specific thing to check 1]
   - [ ] [Specific thing to check 2]
   - [ ] [Specific thing to check 3]

**✅ Pass Criteria:**
- All expected results occurred
- No error messages appeared
- [Specific outcome achieved]

**❌ Fail Scenarios:**
- If [specific error], report: [details to capture]
- If [unexpected behavior], note exact steps to reproduce

---

### Test Scenario 2: [Error Handling / Edge Case]

**Acceptance Criteria:** AC-FEAT-XXX-002

**Purpose:** [What error condition this tests]

**Steps:**
1. **Navigate** to [location]
   - **Expected:** [State]

2. **Enter** invalid data:
   - **Field:** `[Invalid value to enter]`
   - **Reason:** [Why this is invalid]

3. **Click** [Submit button]
   - **Expected:** Error message displayed: "[Exact error text]"
   - **Expected:** Form NOT submitted
   - **Expected:** [Field highlighted or indicated]

4. **Correct** the error:
   - **Field:** `[Valid value]`

5. **Click** [Submit button] again
   - **Expected:** Submission succeeds
   - **Expected:** [Success outcome]

**✅ Pass Criteria:**
- Error message appeared for invalid input
- Error message was clear and actionable
- After correction, submission succeeded

**❌ Fail Scenarios:**
- No error message shown
- Error message unclear or incorrect
- Valid data still rejected

---

### Test Scenario 3: [Another Key Workflow]

**Acceptance Criteria:** AC-FEAT-XXX-003

**Purpose:** [What this validates]

**Steps:**
1. [Step 1]
   - **Expected:** [Result]

2. [Step 2]
   - **Expected:** [Result]

3. [Step 3]
   - **Expected:** [Result]

4. [Step 4]
   - **Expected:** [Result]

**✅ Pass Criteria:**
- [Criterion 1]
- [Criterion 2]

**❌ Fail Scenarios:**
- [What to report if fails]

---

*[Continue with 3-6 total test scenarios covering critical paths]*

## Visual & UX Validation

*Things to check that aren't captured in specific test steps.*

### Overall Visual Check
- [ ] All text is readable (no cut-off text, appropriate font sizes)
- [ ] Buttons and links are clearly identifiable
- [ ] Colors and contrast meet accessibility standards (text readable)
- [ ] Layout is responsive (test at different screen sizes if applicable)
- [ ] Images/icons load correctly
- [ ] No visual glitches (overlapping elements, alignment issues)

### User Experience Check
- [ ] Workflow feels intuitive (can complete without instructions)
- [ ] Error messages are helpful (not just "Error" or "Something went wrong")
- [ ] Success feedback is clear (user knows action completed)
- [ ] Loading states appear for slow operations (spinners, progress bars)
- [ ] Forms remember entered data if user navigates away and back
- [ ] Keyboard navigation works (can Tab through form fields logically)

### Performance Check
- [ ] Page loads in reasonable time (< 3 seconds)
- [ ] Actions complete without noticeable delay
- [ ] No browser console errors (F12 → Console tab should be clean)
- [ ] No memory leaks (page doesn't slow down after extended use)

## Accessibility Testing

*Basic accessibility checks for non-experts.*

### Keyboard Navigation
1. **Tab Key:** Press Tab repeatedly
   - [ ] Focus moves logically through interactive elements
   - [ ] Focus indicator is clearly visible
   - [ ] Can activate buttons/links with Enter or Space

2. **Escape Key:** Press Escape on modals/dialogs
   - [ ] Closes modal and returns focus appropriately

### Screen Reader (Optional)
*If screen reader available (NVDA on Windows, VoiceOver on Mac):*
- [ ] All interactive elements announced clearly
- [ ] Form fields have labels read aloud
- [ ] Error messages are announced

### Color & Contrast
- [ ] Text is readable without relying on color alone
- [ ] Information isn't conveyed by color only (use icons/text too)

## Cross-Browser Testing

*Test in multiple browsers if applicable.*

**Browsers to Test:**
- [ ] Chrome (latest version)
- [ ] Firefox (latest version)
- [ ] Safari (latest version)
- [ ] Edge (latest version)

**For Each Browser:**
- [ ] All test scenarios pass
- [ ] Visual appearance is consistent
- [ ] No JavaScript errors in console

## Device Testing (If Applicable)

**Devices to Test:**
- [ ] Desktop (1920x1080)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

**For Each Device:**
- [ ] Layout adapts appropriately
- [ ] Touch interactions work (if touch device)
- [ ] Text is readable without zooming

## Bug Reporting

**If You Find a Bug, Report:**
1. **Title:** [Brief description of issue]
2. **Scenario:** [Which test scenario: e.g., "Test Scenario 2"]
3. **Steps to Reproduce:**
   - [Exact steps taken]
   - [What you entered/clicked]
4. **Expected Result:** [What should have happened]
5. **Actual Result:** [What actually happened]
6. **Screenshot/Video:** [If possible, attach visual evidence]
7. **Environment:**
   - Browser: [Name and version]
   - Device: [Desktop/tablet/mobile]
   - OS: [Windows 11, macOS 14, iOS 17, etc.]
   - Test Account: [Which account you used]

## Test Completion Checklist

### All Scenarios Complete
- [ ] Test Scenario 1: [Name] - PASS / FAIL
- [ ] Test Scenario 2: [Name] - PASS / FAIL
- [ ] Test Scenario 3: [Name] - PASS / FAIL
- [ ] Test Scenario 4: [Name] - PASS / FAIL
- [ ] Test Scenario 5: [Name] - PASS / FAIL
- [ ] Test Scenario 6: [Name] - PASS / FAIL

### Additional Checks
- [ ] Visual & UX validation complete
- [ ] Accessibility checks complete (or N/A)
- [ ] Cross-browser testing complete (or N/A)
- [ ] Device testing complete (or N/A)

### Summary
- **Total Scenarios:** [X]
- **Passed:** [Y]
- **Failed:** [Z]
- **Bugs Filed:** [Number and links]

**Overall Assessment:**
- [ ] ✅ Feature is ready for release
- [ ] ⚠️ Feature has minor issues (specify)
- [ ] ❌ Feature has blocking issues (specify)

**Tester Sign-off:**
- **Name:** [Tester name]
- **Date:** [Testing completion date]
- **Notes:** [Any additional observations]

---

**Next Steps:**
- If all tests pass: Feature approved for deployment
- If bugs found: Development team will fix and retest affected scenarios
- Update this document if feature changes significantly
