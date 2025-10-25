# SOP: Lessons Learned (Mistakes Log)

**Purpose:** Document mistakes made and lessons learned to prevent recurrence
**Applies To:** All development activities
**Last Updated:** 2025-10-24

## Overview

This document captures mistakes made during development, the impact they had, and how to prevent them in the future. Agents reference this SOP to avoid repeating errors.

**Culture:** Mistakes are learning opportunities. Document them without blame.

## How to Use This SOP

### When to Add an Entry

Add a mistake when:
- Something went wrong that could have been prevented
- A bug made it to production
- Time was wasted due to misunderstanding
- A process failed or was inefficient

### Entry Format

```markdown
## [Date] - [Brief Title]

**What Happened:** [Description of the mistake]
**Impact:** [Consequences: time lost, bugs, user impact]
**Root Cause:** [Why it happened]
**Prevention:** [How to avoid this in the future]
**Related:** [Links to relevant docs, PRs, issues]
```

---

## Documented Mistakes

### 2025-10-24 - Template Created

**What Happened:** This is a template/placeholder. No actual mistakes documented yet.

**Impact:** None - this is the initial project setup.

**Root Cause:** New project, no development history yet.

**Prevention:** As development progresses, document mistakes here promptly.

**Related:** Initial project setup

---

## Common Mistake Categories

*As the project matures, patterns will emerge. Categorize similar mistakes together.*

### Planning Mistakes
*Examples:*
- Insufficient research leading to wrong architecture choice
- Missing edge cases in requirements
- Underestimating complexity

### Implementation Mistakes
*Examples:*
- Not following TDD, leading to untested code
- Premature optimization causing complexity
- Ignoring error handling

### Testing Mistakes
*Examples:*
- Insufficient test coverage
- Flaky tests not fixed promptly
- Not testing edge cases

### Deployment Mistakes
*Examples:*
- Missing environment variables
- Database migration issues
- Breaking changes without notice

### Process Mistakes
*Examples:*
- Skipping code review
- Poor commit messages making debugging hard
- Not updating documentation

---

## Prevention Strategies

*General lessons that apply across categories*

### Before Starting Work
- [ ] Read feature requirements completely
- [ ] Review existing similar code
- [ ] Check acceptance criteria
- [ ] Verify test strategy exists

### During Implementation
- [ ] Write tests first (TDD)
- [ ] Commit frequently with clear messages
- [ ] Test edge cases
- [ ] Update docs as you go

### Before Completing
- [ ] Run full test suite
- [ ] Review own code for obvious issues
- [ ] Verify acceptance criteria met
- [ ] Update CHANGELOG.md

### During Review
- [ ] Check for similar past mistakes (reference this doc)
- [ ] Verify tests cover edge cases
- [ ] Ensure documentation updated

---

## Template for New Entries

*Copy this template when adding a new mistake:*

```markdown
## YYYY-MM-DD - [Brief Descriptive Title]

**What Happened:**
[Clear description of what went wrong. Be specific.]

**Impact:**
- Time lost: [X hours/days]
- User impact: [Did users experience issues?]
- Team impact: [Did this block other work?]
- Technical debt: [Did this create future problems?]

**Root Cause:**
[Why did this happen? What was the underlying cause?]
- Was it lack of knowledge?
- Rushed work?
- Missing process?
- Unclear requirements?

**Prevention:**
[Specific, actionable steps to prevent recurrence]
1. [Action 1: Update process, add check, create SOP, etc.]
2. [Action 2: Tool, automation, or documentation]
3. [Action 3: Team communication or training]

**Action Taken:**
[What did we do to fix this specific instance?]
- Fixed in: [PR link, commit hash]
- Documentation updated: [Link]
- SOP updated: [Link]

**Related:**
- Issue: #123
- PR: #456
- Related feature: FEAT-XXX
- Related SOP: [Link]
```

---

## Reviewing This Document

### Team Reviews
- Review quarterly as team
- Identify patterns
- Update SOPs based on lessons
- Celebrate improvements

### Agent Usage
- Agents reference this before implementing features
- Agents check for similar past mistakes
- Agents suggest preventive measures
- Agents validate against known pitfalls

### Continuous Improvement
- Don't just document mistakes - fix processes
- Update other SOPs based on lessons here
- Automate prevention where possible (linters, CI checks)
- Share learnings with team

---

## Success Metrics

Track improvements:
- [ ] Reduced repeat mistakes (same error doesn't happen twice)
- [ ] Faster development (fewer blocks and rework)
- [ ] Higher quality (fewer bugs in production)
- [ ] Better documentation (complete and up-to-date)

---

**Note:** This document will grow over time. That's good - it means we're learning and improving. An empty mistakes log doesn't mean no mistakes; it means we're not learning from them.
