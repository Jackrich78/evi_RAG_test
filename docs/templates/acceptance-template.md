# Acceptance Criteria: [Feature Name]

**Feature ID:** FEAT-XXX
**Created:** YYYY-MM-DD
**Status:** [Draft / Approved / Met]

## Overview

*Brief summary of what must be true for this feature to be considered "complete".*

This feature is complete when:
- [High-level completion criterion 1]
- [High-level completion criterion 2]
- [High-level completion criterion 3]

## Functional Acceptance Criteria

*Specific, testable conditions in Given/When/Then format. Each criterion should have a unique ID.*

### AC-FEAT-XXX-001: [Brief Description]

**Given** [precondition or initial state]
**When** [action or event occurs]
**Then** [expected outcome or result]

**Validation:**
- [ ] [How to verify this criterion is met]
- [ ] [Automated test exists]
- [ ] [Manual verification steps if needed]

**Priority:** [Must Have / Should Have / Nice to Have]

---

### AC-FEAT-XXX-002: [Brief Description]

**Given** [precondition]
**When** [action]
**Then** [outcome]

**Validation:**
- [ ] [Verification method]
- [ ] [Test coverage]

**Priority:** [Level]

---

### AC-FEAT-XXX-003: [Brief Description]

**Given** [precondition]
**When** [action]
**Then** [outcome]

**Validation:**
- [ ] [Verification method]

**Priority:** [Level]

---

*[Continue for all functional requirements from user stories]*

## Edge Cases & Error Handling

*Specific scenarios that might break the feature or require special handling.*

### AC-FEAT-XXX-101: [Edge Case Name]

**Scenario:** [Describe the edge case]

**Given** [unusual precondition]
**When** [edge case action]
**Then** [expected graceful handling]

**Validation:**
- [ ] [How to verify]

**Priority:** [Level]

---

### AC-FEAT-XXX-102: [Error Scenario]

**Scenario:** [Describe error condition]

**Given** [error precondition]
**When** [error trigger]
**Then** [expected error handling: message, recovery, logging]

**Validation:**
- [ ] [How to verify error is handled correctly]

**Priority:** [Level]

---

*[Continue for all edge cases and error scenarios]*

## Non-Functional Requirements

*Performance, security, accessibility, and other quality attributes.*

### AC-FEAT-XXX-201: Performance

**Requirement:** [Specific performance target]

**Criteria:**
- **Response Time:** [X milliseconds for Y operation]
- **Throughput:** [Z requests per second]
- **Resource Usage:** [Memory/CPU limits]

**Validation:**
- [ ] Performance tests demonstrate meeting targets
- [ ] Load testing completed
- [ ] Monitoring in place

---

### AC-FEAT-XXX-202: Security

**Requirement:** [Security standards to meet]

**Criteria:**
- **Authentication:** [How auth is verified]
- **Authorization:** [Permission checks required]
- **Data Protection:** [Encryption, sanitization required]
- **Audit:** [Logging requirements]

**Validation:**
- [ ] Security review completed
- [ ] Penetration testing passed (if applicable)
- [ ] No secrets in code/logs

---

### AC-FEAT-XXX-203: Accessibility

**Requirement:** [Accessibility standards to meet - WCAG 2.1 Level AA, etc.]

**Criteria:**
- **Keyboard Navigation:** [All functions accessible via keyboard]
- **Screen Readers:** [Content properly labeled for screen readers]
- **Color Contrast:** [WCAG contrast ratios met]
- **Focus Management:** [Focus indicators clear and logical]

**Validation:**
- [ ] Accessibility audit completed
- [ ] Tested with screen reader
- [ ] Keyboard navigation works

---

### AC-FEAT-XXX-204: Compatibility

**Requirement:** [Browser/device/OS compatibility]

**Criteria:**
- **Browsers:** [Chrome 90+, Firefox 88+, Safari 14+, Edge 90+]
- **Devices:** [Desktop, tablet, mobile]
- **Screen Sizes:** [320px to 4K]

**Validation:**
- [ ] Cross-browser testing completed
- [ ] Responsive design verified

---

## Integration Requirements

*How this feature integrates with existing systems.*

### AC-FEAT-XXX-301: [Integration Point]

**Requirement:** [What must integrate and how]

**Given** [existing system state]
**When** [integration event]
**Then** [expected integration behavior]

**Validation:**
- [ ] Integration tests pass
- [ ] No breaking changes to existing features
- [ ] Backward compatibility maintained

---

## Data Requirements

*Data validation, storage, and migration needs.*

### AC-FEAT-XXX-401: Data Validation

**Requirement:** [Data quality standards]

**Criteria:**
- **Input Validation:** [Required fields, formats, ranges]
- **Sanitization:** [XSS, SQL injection prevention]
- **Error Messages:** [Clear, actionable user feedback]

**Validation:**
- [ ] All inputs validated
- [ ] Appropriate error messages shown
- [ ] Invalid data rejected

---

### AC-FEAT-XXX-402: Data Storage

**Requirement:** [How data is persisted]

**Criteria:**
- **Schema:** [Database schema defined]
- **Indexes:** [Required indexes created]
- **Constraints:** [Foreign keys, unique constraints]
- **Migrations:** [Migration scripts created]

**Validation:**
- [ ] Schema matches specification
- [ ] Migrations run successfully
- [ ] Data integrity maintained

---

## Acceptance Checklist

*High-level checklist for feature completion.*

### Development Complete
- [ ] All functional criteria met (AC-FEAT-XXX-001 through AC-FEAT-XXX-0XX)
- [ ] All edge cases handled (AC-FEAT-XXX-101 through AC-FEAT-XXX-1XX)
- [ ] Non-functional requirements met (AC-FEAT-XXX-201 through AC-FEAT-XXX-2XX)
- [ ] Integration requirements met (AC-FEAT-XXX-301 through AC-FEAT-XXX-3XX)
- [ ] Data requirements met (AC-FEAT-XXX-401 through AC-FEAT-XXX-4XX)

### Testing Complete
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] E2E tests written and passing (if applicable)
- [ ] Manual testing completed per manual-test.md
- [ ] Performance testing completed
- [ ] Security review completed (if required)
- [ ] Accessibility testing completed (if applicable)

### Documentation Complete
- [ ] Code documented (inline comments, doc strings)
- [ ] API documentation updated (if applicable)
- [ ] User documentation updated (if applicable)
- [ ] docs/system/ updated with architecture changes
- [ ] CHANGELOG.md updated

### Deployment Ready
- [ ] Code reviewed and approved
- [ ] All tests passing in CI/CD
- [ ] No breaking changes (or migration plan in place)
- [ ] Monitoring and alerting configured
- [ ] Rollback plan documented

---

**Appended to `/AC.md`:** [Yes / No]
**Next Steps:** Proceed to testing strategy and test stub generation
