# SOP: GitHub Repository Setup

**Purpose:** Guide for setting up and configuring GitHub repositories for projects using this template
**Applies To:** New projects, repository initialization
**Last Updated:** 2025-10-24

## Overview

This guide walks through setting up a GitHub repository for a project based on the AI Workflow Starter template, including protection rules, CI/CD setup (Phase 2), and team collaboration.

## Prerequisites

- GitHub account
- Git installed locally
- `gh` CLI installed (optional but recommended)
- This template cloned/forked

## Initial Repository Setup

### Option 1: Using GitHub Web Interface

1. **Create Repository**
   - Go to https://github.com/new
   - Repository name: `your-project-name`
   - Description: Brief project description
   - Visibility: Public or Private
   - **Do NOT** initialize with README, .gitignore, or license (template has these)
   - Click "Create repository"

2. **Push Template**
   ```bash
   cd ai-workflow-starter  # Or your copy of this template
   git remote add origin https://github.com/your-username/your-project-name.git
   git branch -M main
   git push -u origin main
   ```

### Option 2: Using gh CLI

```bash
cd ai-workflow-starter

# Create repo and push
gh repo create your-project-name --public --source=. --remote=origin --push

# Or private
gh repo create your-project-name --private --source=. --remote=origin --push
```

## Repository Configuration

### Branch Protection Rules

**Protect `main` branch:**

1. Go to repo Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require approvals: 1 (or more for teams)
   - ✅ Dismiss stale reviews when new commits are pushed
   - ✅ Require status checks to pass (Phase 2: CI tests)
   - ✅ Require conversation resolution before merging
   - ✅ Do not allow bypassing the above settings
   - ✅ Restrict who can push to matching branches (only via PRs)

**Result:** Direct commits to `main` blocked, all changes via PRs

### Repository Settings

**General:**
- ✅ Allow merge commits (or choose "Squash and merge")
- ✅ Automatically delete head branches (clean up after merge)
- ❌ Allow rebase merging (can rewrite history, risky)
- ❌ Allow force pushes (dangerous)

**Pull Requests:**
- ✅ Allow auto-merge
- ✅ Automatically delete head branches

**Issues:**
- ✅ Enable issues (for bug tracking)
- Create issue templates (optional):
  - Bug report
  - Feature request
  - Documentation improvement

### GitHub Labels

**Add useful labels:**
```bash
gh label create "FEAT" --description "Feature work" --color "0052CC"
gh label create "bug" --description "Something isn't working" --color "d73a4a"
gh label create "docs" --description "Documentation" --color "0075ca"
gh label create "enhancement" --description "New feature or request" --color "a2eeef"
gh label create "Phase 1" --description "Planning phase" --color "fbca04"
gh label create "Phase 2" --description "Implementation phase" --color "d876e3"
```

## Collaboration Setup

### Adding Collaborators

**For personal repos:**
1. Settings → Collaborators → Add people
2. Enter GitHub username
3. Choose role:
   - **Write:** Can push, create branches, create PRs
   - **Maintain:** Write + manage issues, PRs
   - **Admin:** Full access

**For organization repos:**
1. Create team in organization
2. Add team members
3. Grant team access to repo with appropriate role

### Team Workflow

**Recommended roles:**
- **Product Owner:** Write (creates issues, reviews PRs)
- **Developers:** Write (creates branches, PRs)
- **Reviewers:** Maintain (approves PRs, manages issues)
- **Project Lead:** Admin (repo settings, security)

## CI/CD Setup (Phase 2)

*Phase 2 will add automated testing and deployment*

### GitHub Actions (Future)

**`.github/workflows/ci.yml` (Phase 2):**
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3  # Or python, etc.
        with:
          node-version: '18'
      - run: npm install
      - run: npm test
      - run: npm run build
```

**Future workflows:**
- Run tests on every commit
- Build and deploy on merge to main
- Generate coverage reports
- Notify on failures

## Security Configuration

### Secrets Management

**Never commit:**
- API keys
- Passwords
- Tokens
- Private keys
- `.env` files

**Use GitHub Secrets instead:**
1. Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `API_KEY`, `DATABASE_URL`, etc.
4. Value: Secret value
5. Accessible in GitHub Actions as `${{ secrets.API_KEY }}`

### Dependabot (Automated Dependency Updates)

**Enable Dependabot:**
1. Settings → Security & analysis
2. Enable:
   - ✅ Dependency graph
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates

**Configure `.github/dependabot.yml`:**
```yaml
version: 2
updates:
  - package-ecosystem: "npm"  # or pip, cargo, etc.
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

## Repository Documentation

### README.md

**Should include:**
- Project description
- Features
- Installation instructions
- Usage examples
- Development setup
- Contributing guide
- License

**Template structure:**
```markdown
# Project Name

Brief description

## Features
- Feature 1
- Feature 2

## Installation
```bash
npm install  # or equivalent
```

## Usage
```bash
npm start
```

## Development
See [CLAUDE.md](.claude/CLAUDE.md) for AI workflow

## Contributing
1. Fork repo
2. Create feature branch: `git checkout -b feature/FEAT-XXX-description`
3. Commit changes: `git commit -m "feat(FEAT-XXX): description"`
4. Push: `git push origin feature/FEAT-XXX-description`
5. Create Pull Request

## License
[Your chosen license]
```

### Additional Documentation

**Recommended files:**
- `LICENSE` - Open source license (MIT, Apache 2.0, etc.)
- `CONTRIBUTING.md` - Contribution guidelines
- `CODE_OF_CONDUCT.md` - Community standards
- `.github/ISSUE_TEMPLATE/` - Issue templates
- `.github/PULL_REQUEST_TEMPLATE.md` - PR template

## Git Configuration

### Global Git Config

```bash
# Set identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Default branch name
git config --global init.defaultBranch main

# Rebase on pull (cleaner history)
git config --global pull.rebase true

# Auto-setup remote tracking
git config --global push.autoSetupRemote true
```

### Repository-Specific .gitignore

**Template .gitignore should include:**
```
# Dependencies
node_modules/
venv/
vendor/

# Build outputs
dist/
build/
*.pyc
__pycache__/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Claude Code
.claude/session-state.json
.claude/transcripts/

# Logs
*.log
logs/

# Test coverage
coverage/
.coverage
*.lcov
```

## PR and Issue Templates

### `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Feature ID
FEAT-XXX

## Testing
How to test these changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Follows code style guide
- [ ] All tests pass

## Related Issues
Closes #issue-number
```

### `.github/ISSUE_TEMPLATE/bug_report.md`

```markdown
---
name: Bug report
about: Report a bug
---

## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to...
2. Click on...
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Browser/OS:
- Version:

## Screenshots
If applicable
```

## Maintenance

### Regular Tasks

**Weekly:**
- Review open issues and PRs
- Update dependencies (Dependabot PRs)
- Check GitHub Actions status

**Monthly:**
- Review branch protection rules
- Audit collaborator access
- Update documentation if stale

**Quarterly:**
- Security audit
- Review and archive old branches/PRs
- Update README and contributing guide

## Troubleshooting

### Can't push to main
- **Cause:** Branch protection enabled
- **Solution:** Create feature branch, open PR

### PR blocked by status checks
- **Cause:** Tests failing or CI not configured
- **Solution:** Fix tests, or configure CI (Phase 2)

### Merge conflicts
- **Cause:** Main branch changed since branch created
- **Solution:** `git merge origin/main`, resolve conflicts, commit

### Large files rejected
- **Cause:** File >50MB (GitHub limit)
- **Solution:** Use Git LFS or remove file from history

## Related Documentation

- [git-workflow.md](git-workflow.md) - Git branching and commit standards
- [code-style.md](code-style.md) - Code formatting and quality
- [GitHub Docs](https://docs.github.com/)

---

**This SOP covers:** Repository setup, branch protection, collaboration, and security basics
