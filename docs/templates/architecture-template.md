# Architecture Decision: [Feature Name]

**Feature ID:** FEAT-XXX
**Decision Date:** YYYY-MM-DD
**Status:** [Proposed / Accepted / Implemented]

## Context

*Brief overview of the technical challenge and why we need to make an architecture decision. ≤80 words.*

[What technical problem needs solving? What constraints exist? What's the scope of this decision?]

## Options Considered

*Exactly 3 mainstream, viable implementation approaches.*

### Option 1: [Approach Name]

**Description:** [2-3 sentences explaining this approach]

**Key Characteristics:**
- [Characteristic 1]
- [Characteristic 2]
- [Characteristic 3]

**Example Implementation:**
```
[Brief code or architecture sketch if helpful]
```

### Option 2: [Approach Name]

**Description:** [2-3 sentences explaining this approach]

**Key Characteristics:**
- [Characteristic 1]
- [Characteristic 2]
- [Characteristic 3]

**Example Implementation:**
```
[Brief code or architecture sketch if helpful]
```

### Option 3: [Approach Name]

**Description:** [2-3 sentences explaining this approach]

**Key Characteristics:**
- [Characteristic 1]
- [Characteristic 2]
- [Characteristic 3]

**Example Implementation:**
```
[Brief code or architecture sketch if helpful]
```

## Comparison Matrix

*Evaluate each option across 7 critical criteria. Use ✅ (good), ⚠️ (acceptable with caveats), ❌ (poor/problematic).*

| Criteria | Option 1 | Option 2 | Option 3 |
|----------|----------|----------|----------|
| **Feasibility** | ✅ Easy to implement | ⚠️ Moderate complexity | ❌ High complexity |
| **Performance** | [Rating + note] | [Rating + note] | [Rating + note] |
| **Maintainability** | [Rating + note] | [Rating + note] | [Rating + note] |
| **Cost** | [Rating + note] | [Rating + note] | [Rating + note] |
| **Complexity** | [Rating + note] | [Rating + note] | [Rating + note] |
| **Community/Support** | [Rating + note] | [Rating + note] | [Rating + note] |
| **Integration** | [Rating + note] | [Rating + note] | [Rating + note] |

### Criteria Definitions

- **Feasibility:** Can we implement this with current resources/skills/timeline?
- **Performance:** Will it meet performance requirements (speed, scale, resource usage)?
- **Maintainability:** How easy will it be to modify, debug, and extend over time?
- **Cost:** Financial cost (licenses, services, infrastructure)?
- **Complexity:** Implementation and operational complexity?
- **Community/Support:** Quality of documentation, community, and ecosystem?
- **Integration:** How well does it integrate with existing systems?

## Recommendation

**Chosen Approach:** Option [X] - [Approach Name]

**Rationale:** ≤120 words

[Why is this the best choice for our context? What makes it superior to the alternatives?]

### Why Not Other Options?

**Option [Y]:**
- [Key reason it wasn't chosen]
- [Specific drawback that disqualified it]

**Option [Z]:**
- [Key reason it wasn't chosen]
- [Specific drawback that disqualified it]

### Trade-offs Accepted

*What we're giving up by choosing this approach:*
- **Trade-off 1:** [What we're sacrificing and why it's acceptable]
- **Trade-off 2:** [What we're sacrificing and why it's acceptable]
- **Trade-off 3:** [What we're sacrificing and why it's acceptable]

## Spike Plan

*5 concrete steps to validate this approach before full implementation.*

### Step 1: [Validation Task]
- **Action:** [What to do]
- **Success Criteria:** [How to know it works]
- **Time Estimate:** [X minutes/hours]

### Step 2: [Validation Task]
- **Action:** [What to do]
- **Success Criteria:** [How to know it works]
- **Time Estimate:** [X minutes/hours]

### Step 3: [Validation Task]
- **Action:** [What to do]
- **Success Criteria:** [How to know it works]
- **Time Estimate:** [X minutes/hours]

### Step 4: [Validation Task]
- **Action:** [What to do]
- **Success Criteria:** [How to know it works]
- **Time Estimate:** [X minutes/hours]

### Step 5: [Validation Task]
- **Action:** [What to do]
- **Success Criteria:** [How to know it works]
- **Time Estimate:** [X minutes/hours]

**Total Spike Time:** [Sum of estimates]

## Implementation Notes

### Architecture Diagram
```
[ASCII diagram or description of system architecture]

User → [Component A] → [Component B] → [Data Store]
        ↓
    [Component C]
```

### Key Components
- **Component 1:** [Purpose and responsibility]
- **Component 2:** [Purpose and responsibility]
- **Component 3:** [Purpose and responsibility]

### Data Flow
1. [Step 1 in data flow]
2. [Step 2 in data flow]
3. [Step 3 in data flow]

### Technical Dependencies
- [Library/Framework 1]: Version X.Y.Z
- [Library/Framework 2]: Version X.Y.Z
- [Service/API]: [Details]

### Configuration Required
- [Config item 1]: [Purpose]
- [Config item 2]: [Purpose]
- [Environment variables needed]

## Risks & Mitigation

### Risk 1: [Potential Issue]
- **Impact:** [High / Medium / Low]
- **Likelihood:** [High / Medium / Low]
- **Mitigation:** [How we'll address or monitor this risk]

### Risk 2: [Potential Issue]
- **Impact:** [Level]
- **Likelihood:** [Level]
- **Mitigation:** [Strategy]

### Risk 3: [Potential Issue]
- **Impact:** [Level]
- **Likelihood:** [Level]
- **Mitigation:** [Strategy]

## References

- [Research findings]: `docs/features/FEAT-XXX/research.md`
- [Related architecture]: `docs/system/architecture.md`
- [External documentation]: [URL]

---

**Decision Status:** [Proposed / Accepted / Rejected / Superseded]
**Next Steps:** Proceed to acceptance criteria and testing strategy
