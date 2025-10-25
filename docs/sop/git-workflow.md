# SOP: Git Workflow

**Purpose:** Standardize git branching, committing, and merging practices
**Applies To:** All code changes in the repository
**Last Updated:** 2025-10-24

## Overview

We use a feature-branch workflow with conventional commits. Each feature gets its own branch, changes are committed with structured messages, and merging happens via pull requests with review.

## Branching Strategy

### Branch Types

**main** (protected)
- Production-ready code only
- All tests must pass
- Direct commits not allowed
- Merges only via approved PRs

**feature/FEAT-XXX-description**
- One branch per feature
- Branches from `main`
- Named with feature ID: `feature/FEAT-001-authentication`
- Deleted after merge

**fix/brief-description**
- Bug fixes not tied to features
- Named descriptively: `fix/login-validation-error`
- Branches from `main`

**docs/description**
- Documentation-only changes
- Named: `docs/update-readme`
- Can merge without full test suite

### Creating Branches

```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/FEAT-001-authentication

# Start bug fix
git checkout -b fix/login-validation
```

## Commit Messages

We follow conventional commit format. See [sop-template.md](sop-template.md) for detailed commit message examples.

**Format:**
```
type(scope): description

Optional longer explanation

- Optional bullet points
- Can reference issues
```

**Common types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring

**Examples:**
```bash
git commit -m "feat(FEAT-001): add JWT authentication"
git commit -m "fix(auth): resolve token expiration bug"
git commit -m "docs(readme): update setup instructions"
```

## Commit Frequency

**Commit often:**
- After completing a logical unit of work
- Before switching tasks
- At end of work session
- When tests pass

**Avoid:**
- Committing broken code (tests should pass)
- Huge commits with many unrelated changes
- Commits with generic messages like "updates" or "fixes"

## Pull Requests

### Creating PRs

```bash
# Push feature branch
git push -u origin feature/FEAT-001-authentication

# Create PR (if using gh CLI)
gh pr create --title "feat(FEAT-001): Add authentication" \
  --body "Implements user authentication with JWT tokens..."
```

**PR Title:** Same format as commit: `type(scope): description`

**PR Description:**
```markdown
## Summary
- What this PR does
- Why it's needed

## Changes
- File/component changed
- Approach taken

## Testing
- How to test
- Test coverage added

## Related
- Closes #issue-number
- Related to FEAT-XXX
```

### PR Review Process

1. **Create PR** from feature branch to `main`
2. **CI runs** (tests, linting, build)
3. **Review** by team member (if team project)
4. **Address feedback** with new commits
5. **Merge** when approved and CI passes
6. **Delete** feature branch after merge

## Merge Strategy

**Squash and Merge (Preferred)**
- Combines all feature commits into one
- Keeps `main` history clean
- Single revert point if needed

**Regular Merge**
- Preserves commit history
- Use for significant features with meaningful commit history

**Rebase (Advanced)**
- Use only for personal branches
- Never rebase shared branches

## Handling Conflicts

```bash
# Update feature branch with latest main
git checkout feature/FEAT-001-authentication
git fetch origin
git merge origin/main

# Resolve conflicts in files
# Then:
git add [resolved-files]
git commit -m "merge: resolve conflicts with main"
git push
```

## Common Workflows

### Starting New Feature

```bash
git checkout main
git pull
git checkout -b feature/FEAT-XXX-feature-name

# Make changes
git add .
git commit -m "feat(FEAT-XXX): implement feature"
git push -u origin feature/FEAT-XXX-feature-name

# Create PR
gh pr create
```

### Fixing a Bug

```bash
git checkout -b fix/bug-description

# Fix bug
git add [fixed-files]
git commit -m "fix(component): resolve bug description"
git push -u origin fix/bug-description

# Create PR
gh pr create
```

### Updating Documentation

```bash
git checkout -b docs/update-description

# Update docs
git add docs/
git commit -m "docs: update documentation"
git push -u origin docs/update-description

# Can merge quickly, doesn't need full review
```

## What NOT to Do

❌ **Never commit:**
- Secrets (.env files, API keys, passwords)
- Dependencies (node_modules/, vendor/, etc. - use .gitignore)
- Build artifacts (dist/, build/, *.pyc, etc.)
- Personal config files (.vscode/, .idea/)
- Large binary files (use Git LFS if needed)

❌ **Never force push:**
- To `main` branch (should be blocked)
- To shared feature branches
- After someone else has pulled your branch

❌ **Never:**
- Commit directly to `main`
- Rewrite history on shared branches
- Create branches with unclear names

## Git Configuration

**Set up user info:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Useful aliases:**
```bash
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
```

## Phase 2 Automation

In Phase 2, the `/commit` command will automate:
- Staging changed files
- Generating conventional commit messages
- Running pre-commit tests
- Creating commits with Co-authored-by metadata

For now, use git commands directly or ask Claude to help with git operations.

## Related Documentation

- [sop-template.md](sop-template.md) - Commit message format examples
- [github-setup.md](github-setup.md) - GitHub repository configuration
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**This SOP is enforced by:** Code review, CI checks (Phase 2), Reviewer agent validation
