# SOP Template: How to Write Standard Operating Procedures

**Purpose:** This template defines how to create and maintain SOPs in this project.

## What is an SOP?

A Standard Operating Procedure (SOP) is a documented process that describes **how we do things** in this project. SOPs capture best practices, lessons learned, and standardized workflows that AI agents should enforce.

## When to Create an SOP

Create an SOP when:
- A process is repeated multiple times
- A mistake has been made that should be prevented
- A best practice has been established
- A decision affects how code is written or deployed
- Team coordination requires a standard approach

## SOP Structure

### 1. Header
```markdown
# SOP: [Descriptive Title]

**Purpose:** [One sentence describing why this SOP exists]
**Applies To:** [Who/what this affects: all code, specific features, certain tools]
**Last Updated:** YYYY-MM-DD
```

### 2. Overview
*2-3 sentences explaining the context and importance of this SOP.*

### 3. The Standard (Descriptive Style)

**Use descriptive language** that explains how things are done:
- "We use X for Y because Z"
- "Feature branches follow the pattern: feature/FEAT-XXX-description"
- "Commits use conventional format: type(scope): description"

**Avoid prescriptive commands:**
- ❌ "ALWAYS do X"
- ❌ "NEVER do Y"
- ✅ "We do X because it prevents Y"

### 4. Rationale
*Explain WHY this standard exists.*
- What problem does it solve?
- What benefit does it provide?
- What happens if this isn't followed?

### 5. Examples

**Good Examples:**
```
[Show correct implementation]
```

**Anti-Patterns:**
```
[Show what NOT to do]
```

### 6. Exceptions
*When is it okay to deviate from this SOP?*
- Exception 1: [Condition and rationale]
- Exception 2: [Condition and rationale]

### 7. Related Documentation
- [Link to related SOPs]
- [Link to tools or resources]
- [Link to external documentation]

## Agent Enforcement

SOPs are **descriptive** (how we work) but agents **enforce** them:
- Agents read SOPs to understand project standards
- Agents validate code/docs against SOPs
- Agents flag deviations for human review
- Agents suggest corrections based on SOPs

## Updating SOPs

SOPs evolve based on:
- Mistakes made (captured in mistakes.md)
- New tools or practices adopted
- Team feedback
- Project growth

**Update Process:**
1. Identify need for change (mistake, new practice, feedback)
2. Update SOP document
3. Update Last Updated date
4. Inform team / update CHANGELOG.md
5. Ensure agents are aware of change

## SOP Best Practices

✅ **Do:**
- Keep SOPs concise (≤800 words)
- Use descriptive language ("we do X")
- Include rationale (the "why")
- Provide examples
- Update when practices change

❌ **Don't:**
- Write prescriptive commands ("MUST/SHALL")
- Include implementation details (belongs in code)
- Create SOPs for one-time tasks
- Let SOPs become outdated

## Example SOP

```markdown
# SOP: Git Commit Messages

**Purpose:** Standardize commit messages for clarity and automated changelog generation
**Applies To:** All commits to the repository
**Last Updated:** 2025-10-24

## Overview

We use conventional commit format for all commit messages. This provides clear history, enables automated changelog generation, and helps team members understand changes at a glance.

## The Standard

Commit messages follow this format:
```
type(scope): description

Longer explanation if needed

- Bullet points for details
- Can reference issues: Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or fixes
- `refactor`: Code refactoring (no functional change)
- `chore`: Maintenance tasks

**Scope:** Feature ID or component affected (e.g., `FEAT-001`, `auth`, `api`)

**Description:** Imperative mood, lowercase, no period, ≤50 chars

## Rationale

Conventional commits:
- Enable automated CHANGELOG.md generation
- Make git history scannable
- Facilitate semantic versioning
- Integrate with CI/CD tools

## Examples

**Good:**
```
feat(FEAT-001): add user authentication
fix(auth): resolve login validation bug
docs(readme): update installation instructions
```

**Anti-Patterns:**
```
❌ "Fixed stuff" (not descriptive)
❌ "FEAT: New feature." (wrong format)
❌ "add authentication and fix bugs and update docs" (too many changes in one commit)
```

## Exceptions

- Merge commits use default git format
- Initial commit can be "init: project setup"
- Emergency hotfixes can have simpler messages if needed (but should be rare)

## Related Documentation

- [Git Workflow SOP](git-workflow.md)
- [Conventional Commits Spec](https://www.conventionalcommits.org/)
```

---

**Use this template when creating new SOPs for this project.**
