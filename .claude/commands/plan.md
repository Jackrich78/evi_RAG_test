---
description: Create comprehensive planning documentation for a feature
argument-hint: [FEAT-ID]
---

# Feature Planning Workflow

You are creating comprehensive planning documentation for feature: **$ARGUMENTS**

## Your Mission

Orchestrate the Planner agent to transform PRD and research into actionable technical planning including architecture, acceptance criteria, testing strategy, and test stubs.

## Prerequisites

Verify that exploration is complete:
```
Required files must exist:
- docs/features/$ARGUMENTS/prd.md
- docs/features/$ARGUMENTS/research.md

If missing, tell user to run: /explore [topic] first
```

## Workflow Steps

### Step 1: Validate Prerequisites

Check that required files exist:
1. Read docs/features/$ARGUMENTS/prd.md
2. Read docs/features/$ARGUMENTS/research.md
3. If either missing, stop and instruct user to run `/explore` first

### Step 2: Invoke Planner Agent

Use the Task tool to invoke the Planner agent:
```
Task(
  subagent_type="general-purpose",
  description="Create planning documentation",
  prompt="""
  You are the Planner agent. Create comprehensive planning documentation for: '$ARGUMENTS'

  Follow the Planner agent definition in .claude/subagents/planner.md

  ## Input Files
  - docs/features/$ARGUMENTS/prd.md (requirements)
  - docs/features/$ARGUMENTS/research.md (findings)

  ## Your Tasks

  ### 1. Architecture Documentation
  - Identify 3 viable implementation approaches
  - Create comparison matrix (7 criteria × 3 options)
  - Make recommendation with rationale
  - Define 5-step spike plan
  - Write docs/features/$ARGUMENTS/architecture.md (follow template)

  ### 2. Acceptance Criteria
  - Extract user stories from PRD
  - Convert to Given/When/Then format
  - Add edge cases and error scenarios
  - Include non-functional requirements
  - Write docs/features/$ARGUMENTS/acceptance.md (follow template)
  - Append criteria to /AC.md with format: AC-$ARGUMENTS-###

  ### 3. Testing Strategy
  - Determine test levels (unit, integration, E2E)
  - Specify test files to create
  - Define coverage goals
  - Document manual testing requirements
  - Write docs/features/$ARGUMENTS/testing.md (follow template)

  ### 4. Manual Testing Guide
  - Create step-by-step instructions for non-technical users
  - Include setup and prerequisites
  - Define test scenarios with expected results
  - Write docs/features/$ARGUMENTS/manual-test.md (follow template)

  ### 5. Generate Test Stubs
  - Create test files in tests/ directory based on testing strategy
  - Follow language conventions (detect from codebase)
  - Add TODO comments with test descriptions
  - Reference acceptance criteria IDs
  - Provide basic test structure (imports, describe blocks)

  ### 6. Invoke Reviewer
  After all documents created, invoke Reviewer agent for validation.

  ## Templates to Follow
  @docs/templates/architecture-template.md
  @docs/templates/acceptance-template.md
  @docs/templates/testing-template.md
  @docs/templates/manual-test-template.md

  ## Agent Definitions
  @.claude/subagents/planner.md
  @.claude/subagents/reviewer.md

  ## Context
  @docs/features/$ARGUMENTS/prd.md
  @docs/features/$ARGUMENTS/research.md
  """
)
```

### Step 3: Reviewer Validation

The Planner will automatically invoke the Reviewer agent. Wait for validation results.

**If Reviewer returns FAIL:**
1. Review the specific issues identified
2. Fix the issues (re-invoke Planner with fixes)
3. Re-run Reviewer validation
4. Repeat until PASS

**If Reviewer returns PASS:**
1. Proceed to Archon task update (if available)
2. Then proceed to documentation update

### Step 3.5: Update Archon Task Status (If Available)

If Archon MCP is available and tasks exist for this feature, mark planning complete.

**Find Planning Task:**
```
Try to find tasks for this feature:
  tasks = mcp__archon__find_tasks(filter_by="feature", filter_value="$ARGUMENTS")

If tasks found:
  Find planning task:
    planning_task = [t for t in tasks if "Plan Architecture" in t["title"]]

  If planning task exists:
    Mark as done:
      mcp__archon__manage_task("update",
        task_id=planning_task["id"],
        status="done"
      )
```

**Report to User:**
```
If task updated successfully:
  Print:
    "✅ Marked Archon task complete: $ARGUMENTS - Plan Architecture & Tests"
    "   Next: Run /build $ARGUMENTS to begin implementation"
```

**Error Handling (Graceful Degradation):**
```
If Archon MCP unavailable:
  Skip silently, continue to Step 4

If no tasks found for this feature:
  Skip (user may not have run /explore with Archon)
  Continue to Step 4

If task update fails:
  Log warning but continue workflow
  Never block planning workflow on Archon failures
```

**Important:**
- This step is entirely optional
- Planning workflow must complete successfully with or without Archon
- Task updates are best-effort only

### Step 4: Update Documentation Index

Invoke the Documenter agent:
```
Task(
  subagent_type="general-purpose",
  description="Update documentation index",
  prompt="""
  You are the Documenter agent. Update the documentation index for completed planning.

  Follow the Documenter agent definition in .claude/subagents/documenter.md

  1. Update docs/README.md:
     - Change $ARGUMENTS status from "Exploring" to "Ready for Implementation"
     - List all planning docs (architecture, acceptance, testing, manual-test)
     - Add creation date
  2. Append to CHANGELOG.md:
     "### Added\n- $ARGUMENTS: Planning documentation complete - Ready for implementation"
  3. Include test stub count and locations

  @.claude/subagents/documenter.md
  """
)
```

### Step 5: Present Planning Summary

Show the user:
```
✅ Planning Complete: $ARGUMENTS

## Documents Created
- Architecture: docs/features/$ARGUMENTS/architecture.md
  → Recommendation: [Chosen approach]
  → Spike plan: [5 steps]

- Acceptance Criteria: docs/features/$ARGUMENTS/acceptance.md
  → [X] criteria defined
  → Appended to AC.md

- Testing Strategy: docs/features/$ARGUMENTS/testing.md
  → [X] test stubs created in tests/

- Manual Testing: docs/features/$ARGUMENTS/manual-test.md
  → [X] test scenarios for human validation

## Test Stubs Generated
- tests/[paths to test files]
- [X] total test stubs (unit + integration + E2E)

## Validation
✅ Reviewer validation passed - All planning docs complete

## Next Steps (Phase 2 - Coming Soon)
1. Run `/build $ARGUMENTS` to implement feature (Phase 2)
2. Tests will be implemented first (TDD approach)
3. Code will be written to make tests pass

## Current Actions Available
1. Review planning documentation (read files above)
2. Refine plans if needed (edit docs, re-run /plan)
3. Begin manual implementation following architecture.md
4. Update AC.md when implementation complete
```

## Important Notes

- **Prerequisites Required:** Must run `/explore` before `/plan`
- **Quality Gate:** Reviewer must pass before completion
- **Test Stubs Only:** Creates empty test files with TODOs, no implementation
- **No Code:** Planning phase does not write feature implementation
- **Iterative:** Can re-run planning if requirements change

## Example Invocation

```
User: /plan FEAT-001

→ Validates PRD and research exist
→ Planner creates architecture doc (3 options, matrix, recommendation)
→ Planner creates acceptance criteria (12 criteria, Given/When/Then)
→ Planner creates testing strategy (unit, integration, E2E plan)
→ Planner creates manual test guide (6 scenarios)
→ Planner generates test stubs (15 test functions in 3 files)
→ Planner appends AC-FEAT-001-* to AC.md
→ Reviewer validates all docs (PASS)
→ Documenter updates docs/README.md and CHANGELOG.md
→ Present summary: "Planning complete, ready for Phase 2"
```

## Handling Failures

### If Prerequisites Missing
```
❌ Cannot plan $ARGUMENTS - missing prerequisites

Required files not found:
- docs/features/$ARGUMENTS/prd.md
- docs/features/$ARGUMENTS/research.md

Please run: /explore [topic] first to create these files.
```

### If Reviewer Fails
```
⚠️ Planning validation failed for $ARGUMENTS

Issues found:
1. [Specific issue with file and line number]
2. [Specific issue with file and line number]

Fixing issues and re-validating...
[Planner makes corrections]
[Reviewer re-validates]
```

## Success Criteria

✅ All 4 planning docs created and template-compliant
✅ Test stubs generated in tests/ directory
✅ Acceptance criteria appended to AC.md
✅ Reviewer validation passed
✅ Documentation index updated
✅ CHANGELOG entry added
✅ Feature status: "Ready for Implementation"

## After Planning

Feature is fully planned and ready for:
- **Phase 2:** `/build` command (implementation)
- **Manual:** Developers can implement following architecture.md
- **Validation:** Tests defined, manual testing guide ready
