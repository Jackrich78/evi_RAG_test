---
description: Explore a new feature idea and create initial planning documentation
argument-hint: [feature topic]
---

# Feature Exploration Workflow

You are beginning the exploration phase for a new feature: **$ARGUMENTS**

## Your Mission

Guide the user through structured feature discovery using the Explorer and Researcher agents to create comprehensive initial planning documentation.

## Workflow Steps

### Step 1: Initial Context Gathering

Before asking questions, search the existing codebase:
- Use Glob to find similar features or relevant files
- Use Grep to search for related functionality
- Identify existing patterns, architecture, or dependencies
- Note any codebase constraints or conventions

### Step 2: Invoke Explorer Agent

Use the Task tool to invoke the Explorer agent:
```
Task(
  subagent_type="general-purpose",
  description="Explore feature idea",
  prompt="""
  You are the Explorer agent. Your task is to explore the feature idea: '$ARGUMENTS'

  Follow the Explorer agent definition in .claude/subagents/explorer.md

  1. Review codebase context (already gathered above)
  2. Ask clarifying questions to understand:
     - Problem being solved
     - Goals and success criteria
     - User stories and workflows
     - Scope and constraints
     - Technical requirements
  3. Create docs/features/FEAT-XXX/prd.md following docs/templates/prd-template.md
  4. Generate feature slug (FEAT-XXX) from topic name
  5. Identify open questions for Researcher agent

  Be specific, ask targeted questions, avoid vague requirements.

  @.claude/subagents/explorer.md
  @docs/templates/prd-template.md
  """
)
```

### Step 3: Review PRD with User

After Explorer completes:
1. Show the generated PRD to the user
2. Ask if they want to refine any sections
3. Confirm the feature slug (FEAT-XXX) is appropriate
4. Verify open questions are captured

### Step 4: Invoke Researcher Agent

Use the Task tool to invoke the Researcher agent:
```
Task(
  subagent_type="general-purpose",
  description="Research feature approach",
  prompt="""
  You are the Researcher agent. Your task is to research the feature: '$ARGUMENTS'

  Follow the Researcher agent definition in .claude/subagents/researcher.md

  1. Read the PRD created by Explorer: docs/features/FEAT-XXX/prd.md
  2. Identify open questions that require research
  3. Check if Archon MCP is available (optional)
  4. If Archon available: Query knowledge base for framework docs
  5. If Archon unavailable or incomplete: Use WebSearch
  6. Create docs/features/FEAT-XXX/research.md following docs/templates/research-template.md
  7. Document sources (Archon vs WebSearch)
  8. Flag any framework docs missing from Archon for human to crawl

  Prioritize official documentation and maintained sources.

  @.claude/subagents/researcher.md
  @docs/templates/research-template.md
  @docs/features/FEAT-XXX/prd.md
  """
)
```

### Step 5: Present Results

After Researcher completes:
1. Summarize the feature exploration:
   - Feature ID and name
   - Problem statement (1-2 sentences)
   - Key research findings
   - Recommended approach
2. Show file paths:
   - `docs/features/FEAT-XXX/prd.md`
   - `docs/features/FEAT-XXX/research.md`
3. Ask if user wants to proceed to planning: `/plan FEAT-XXX`

### Step 6: Update Documentation Index

Invoke the Documenter agent to update the docs index:
```
Task(
  subagent_type="general-purpose",
  description="Update documentation index",
  prompt="""
  You are the Documenter agent. Update the documentation index for the new feature.

  Follow the Documenter agent definition in .claude/subagents/documenter.md

  1. Add FEAT-XXX to docs/README.md index under "Features → Exploring"
  2. Append entry to CHANGELOG.md:
     "### Added\n- FEAT-XXX: $ARGUMENTS exploration documentation"
  3. List the created files (prd.md, research.md)

  @.claude/subagents/documenter.md
  """
)
```

### Step 7: Create Archon Tasks (If Available)

If Archon MCP is available, create task tracking for this feature.

**Detect Repository Name:**
```
Use basename of current directory as project name (e.g., "ai-workflow-starter")
Optionally detect GitHub URL from: git remote get-url origin
```

**Find or Create Main Project:**
```
Try to find existing project:
  projects = mcp__archon__find_projects(query=<repo_name>)

If not found, create it:
  project = mcp__archon__manage_project("create",
    title=<repo_name>,
    description=f"AI-assisted software development for {repo_name}",
    github_repo=<git_remote_url if available>
  )
```

**Create 4 Workflow-Phase Tasks:**

```
Extract FEAT-XXX from feature directory name (e.g., "FEAT-001")

Task 1: Exploration (mark done immediately - already complete!)
  mcp__archon__manage_task("create",
    project_id=project.id,
    title=f"{FEAT-XXX} - Explore & Research",
    description=f"Understand requirements and research technical approaches\n\nDocs: docs/features/{FEAT-XXX}/prd.md, research.md",
    status="done",
    task_order=100,
    feature=FEAT-XXX,
    assignee="Explorer+Researcher"
  )

Task 2: Planning
  mcp__archon__manage_task("create",
    project_id=project.id,
    title=f"{FEAT-XXX} - Plan Architecture & Tests",
    description=f"Create architecture decision, acceptance criteria, and test strategy\n\nDocs: docs/features/{FEAT-XXX}/architecture.md, acceptance.md, testing.md, manual-test.md",
    status="todo",
    task_order=90,
    feature=FEAT-XXX,
    assignee="Planner+Reviewer"
  )

Task 3: Build
  mcp__archon__manage_task("create",
    project_id=project.id,
    title=f"{FEAT-XXX} - Build with TDD",
    description=f"Implement feature following TDD: Red-Green-Refactor\n\nSee: docs/features/{FEAT-XXX}/architecture.md for approach",
    status="todo",
    task_order=80,
    feature=FEAT-XXX,
    assignee="Claude Code"
  )

Task 4: Validate & Ship
  mcp__archon__manage_task("create",
    project_id=project.id,
    title=f"{FEAT-XXX} - Validate & Commit",
    description=f"Run tests, validate acceptance criteria, commit with conventional format\n\nSee: docs/features/{FEAT-XXX}/acceptance.md",
    status="todo",
    task_order=70,
    feature=FEAT-XXX,
    assignee="Claude Code"
  )
```

**Error Handling (Graceful Degradation):**

```
If Archon MCP tools not available:
  Print informational message:
    "ℹ️  Archon MCP not available - skipping task creation"
    "   Feature tracking will be manual via git and docs/"
  Continue workflow normally (do not fail)

If project creation fails:
  Log warning, continue without tasks
  Do not block exploration workflow

If individual task creation fails:
  Log which tasks were created successfully
  Continue with remaining tasks
```

**Report to User:**

```
If tasks created successfully:
  Print summary:
    "✅ Created 4 workflow tasks in Archon project '{repo_name}'"
    "   View at: http://localhost:3737"
    ""
    "Task Status:"
    "  ✓ Task 1: {FEAT-XXX} - Explore & Research (done)"
    "  ○ Task 2: {FEAT-XXX} - Plan Architecture & Tests (todo)"
    "  ○ Task 3: {FEAT-XXX} - Build with TDD (todo)"
    "  ○ Task 4: {FEAT-XXX} - Validate & Commit (todo)"
    ""
    "Next: Run /plan {FEAT-XXX} to continue"
```

**Important:**
- Never block exploration workflow on Archon failures
- Always allow workflow to complete successfully
- Archon is optional enhancement, not requirement

## Important Notes

- **Phase 1 Only:** This command creates planning documentation, not implementation code
- **User Interaction:** Explorer should ask questions before writing PRD
- **Research Quality:** Researcher must cite all sources
- **Archon Optional:** Workflow works without Archon, uses WebSearch fallback
- **Feature Slug:** Use format FEAT-XXX where XXX is zero-padded number (FEAT-001, FEAT-002, etc.)

## Example Invocation

```
User: /explore user authentication

→ Explorer searches codebase for auth patterns
→ Explorer asks: "OAuth? JWT? Social login?"
→ User answers questions
→ Explorer creates docs/features/FEAT-001_authentication/prd.md
→ Researcher searches for auth best practices (Archon → WebSearch)
→ Researcher creates docs/features/FEAT-001_authentication/research.md
→ Documenter updates docs/README.md and CHANGELOG.md
→ Present summary and suggest: /plan FEAT-001
```

## Next Steps

After exploration completes:
1. User reviews PRD and research docs
2. User refines if needed (edit files directly)
3. User runs `/plan FEAT-XXX` to create comprehensive planning documentation

## Success Criteria

✅ PRD created following template
✅ Research doc created with sources cited
✅ Feature slug assigned (FEAT-XXX)
✅ Documentation index updated
✅ User understands feature scope and approach
✅ Ready to proceed to planning phase
