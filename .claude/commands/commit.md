---
description: "Create git commit with validation, conventional format, and optional PR"
argument-hint: [message]
---

# Git Commit Workflow

Automate git workflows with validation, conventional commit format, and PR creation.

## Usage

```bash
# Basic commit (will prompt for type/scope)
/commit "Add user authentication"

# With explicit commit type
/commit "feat: Add user authentication"

# With scope detection from changed files
/commit "fix(auth): Resolve login validation bug"
```

## Workflow Steps

When you run `/commit`, I will:

1. **Check git status** - Show all changed files
2. **Validate tests** - Ensure tests pass before committing (if test command exists)
3. **Analyze changes** - Detect commit type and scope from changed files
4. **Generate commit message** - Create conventional commit format
5. **Show preview** - Display changes and proposed commit message
6. **Get approval** - Wait for your confirmation
7. **Stage files** - Add relevant files to git staging area
8. **Create commit** - Make the commit with proper metadata
9. **Optionally create PR** - Use `gh` CLI if you want to create a pull request
10. **Update Archon task** (if available) - Mark feature complete in Archon

## Archon Task Completion (If Available)

After successful commit, if this is a feature commit (FEAT-XXX detected), mark the feature complete in Archon:

```
If commit successful AND FEAT-XXX scope detected:
  If Archon MCP available:
    Find validation task:
      tasks = mcp__archon__find_tasks(filter_by="feature", filter_value="FEAT-XXX")
      validate_task = [t for t in tasks if "Validate & Commit" in t["title"]]

    Mark as done:
      mcp__archon__manage_task("update",
        task_id=validate_task["id"],
        status="done"
      )

    Print celebration:
      "🎉 FEAT-XXX complete - all 4 workflow tasks done!"
      "   ✓ Task 1: Explore & Research"
      "   ✓ Task 2: Plan Architecture & Tests"
      "   ✓ Task 3: Build with TDD"
      "   ✓ Task 4: Validate & Commit"
      ""
      "   View in Archon: http://localhost:3737"
```

**Error Handling:**
- If Archon unavailable: Skip silently
- If no tasks found: Skip (not all features use Archon)
- Never block commit on task update failures

## Conventional Commit Format

Commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: New feature (FEAT-XXX)
- **fix**: Bug fix
- **docs**: Documentation only changes
- **test**: Adding or updating tests
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **style**: Formatting, missing semicolons, etc.
- **chore**: Build process or auxiliary tool changes
- **perf**: Performance improvement
- **ci**: CI configuration changes

### Scope Detection

Scopes are automatically detected from changed file paths:

| Changed Files | Detected Scope |
|--------------|----------------|
| `docs/features/FEAT-123_*/**` | `FEAT-123` |
| `src/auth/**` | `auth` |
| `tests/**` | `test` |
| `.claude/**` | `tooling` |
| `docs/**` | `docs` |

## Examples

### Feature Commit

```bash
/commit "Add OAuth2 authentication"
```

**Result:**
```
feat(FEAT-123): Add OAuth2 authentication

- Implement OAuth2 provider integration
- Add user session management
- Create authentication middleware

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Bug Fix

```bash
/commit "Fix memory leak in session handler"
```

**Result:**
```
fix(auth): Fix memory leak in session handler

Resolves issue where session tokens were not being properly cleaned up
after user logout, causing memory usage to grow over time.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Documentation

```bash
/commit "Update API documentation"
```

**Result:**
```
docs(api): Update API documentation

- Add examples for new endpoints
- Update authentication flow diagram
- Fix typos in existing docs

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Test Updates

```bash
/commit "Add integration tests for auth flow"
```

**Result:**
```
test(auth): Add integration tests for auth flow

Comprehensive integration tests covering:
- OAuth2 login flow
- Token refresh
- Session expiration

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Validation Checks

Before committing, the following validations are performed:

1. **Git Repository** - Ensure we're in a git repository
2. **Changed Files** - Verify there are files to commit
3. **Tests Pass** - Run test suite if available (can be skipped with `--no-test`)
4. **No Secrets** - Check for common secret patterns (.env, credentials, API keys)
5. **Commit Message** - Validate conventional commit format

## Safety Features

- **No force push to main/master** - Prevents accidental force pushes
- **User approval required** - Always shows preview and waits for confirmation
- **Co-authored metadata** - Clearly marks AI-assisted commits
- **Conventional format** - Ensures consistent commit history
- **Secret detection** - Warns if secrets might be committed

## Creating Pull Requests

After committing, you can optionally create a PR:

```bash
# I'll ask after successful commit:
"Would you like to create a pull request?"

# If yes:
→ Push branch to remote
→ Create PR using gh CLI
→ Generate PR description from commits
→ Return PR URL
```

## Handling Errors

### Tests Fail

```
⚠️ Tests failed! Cannot commit with failing tests.

Run /test to see details, or use --no-test to skip validation.
```

### No Changes

```
⚠️ No changes to commit.

Working tree is clean. Make some changes first.
```

### Secrets Detected

```
⚠️ Potential secrets detected in:
  - .env (contains API_KEY)
  - config.json (contains PASSWORD)

Review these files carefully. To proceed anyway, use --force.
```

### Not on Feature Branch

```
⚠️ You're on branch 'main'.

Create a feature branch first:
  git checkout -b feat/FEAT-123-my-feature
```

## Command Options

```bash
# Skip test validation
/commit "Quick fix" --no-test

# Force commit (skip safety checks)
/commit "Emergency fix" --force

# Specify commit type explicitly
/commit "feat: New feature"

# Create PR after commit
/commit "Complete feature" --pr
```

## Best Practices

1. **Commit Often** - Make small, focused commits
2. **Clear Messages** - Describe what and why, not how
3. **Test First** - Ensure tests pass before committing
4. **Review Changes** - Always review the preview before confirming
5. **Feature Branches** - Work on branches, not main
6. **Conventional Format** - Use the standard commit types

## Integration with Other Commands

```bash
# Typical workflow
/plan "Add authentication"     # Create planning docs
/build                         # Implement feature
/test                          # Run tests
/commit "feat: Add auth"       # Commit changes
```

## Git Configuration

For best results, ensure your git is configured:

```bash
# Set your identity
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Enable GPG signing (optional)
git config commit.gpgsign true

# Install gh CLI for PR creation
brew install gh  # macOS
# or
curl -sS https://webi.sh/gh | sh
```

## See Also

- `.claude/hooks/stop.py` - Suggests commits after work
- `docs/sop/git-workflow.md` - Git workflow standards
- `docs/sop/github-setup.md` - GitHub configuration
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Implementation Note:** This command orchestrates the git workflow by:
1. Running validation checks (tests, secrets, branch)
2. Analyzing changed files to infer commit type/scope
3. Generating a conventional commit message
4. Showing preview and getting user approval
5. Executing git operations (stage, commit, push, PR)
