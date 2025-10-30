---
description: "Load project context quickly - current state, features, and recent work"
---

# Project Context Loader

Quickly load project context at session start.

## Workflow Steps

### Step 1: Load Project Understanding

Read these files:
- `CLAUDE.md` - Project goal, stack, workflow rules (if exists)
- `README.md` - First 30 lines only (if exists)
- `docs/system/stack.md` - Tech stack (if exists)
- `docs/system/architecture.md` - Tech stack (if exists)
- `docs/system/database.md` - Tech stack (if exists)
- `docs/system/integrations.md` - Tech stack (if exists)

Extract: project goal, stack, any critical constraints.

### Step 2: Check directory structure
```bash
tree -L 3
```

### Step 3: Check Git State

```bash
git branch --show-current
git status --short
git log --oneline -3
```

### Step 4: Scan Features

```bash
ls -1 docs/features/
```

Just list the FEAT-XXX directories. Don't read full docs.

### Step 5: Query Archon (Optional)

If Archon MCP available, search for recent tasks:
```
mcp__archon__find_tasks(filter_by="project", limit=5)
```

If unavailable or fails, skip silently.

### Step 6: Present Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PROJECT: [name]
🛠️  STACK: [technologies]
🎯 GOAL: [one-line goal]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CURRENT STATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 BRANCH: [branch-name]
📝 STATUS: [clean OR X files changed]
📌 LAST COMMITS:
   • [commit 1]
   • [commit 2]
   • [commit 3]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ COMPLETE: [list]
🚧 IN PROGRESS: [FEAT-XXX or "None"]
📋 PLANNED: [list]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready. What should we work on?
```

Keep output under 20 lines total.

## Notes

- Target: under 30 seconds
- Read-only operation
- Archon optional, fails silently
- Generic - works with any project structure