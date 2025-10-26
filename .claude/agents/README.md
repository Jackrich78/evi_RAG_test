# Sub-Agent Index

**Last Updated:** 2025-10-25
**Auto-generated index** - Lists all sub-agents available in this project

## Overview

This directory contains specialized sub-agents that orchestrate the AI workflow system. Each agent has a focused responsibility and well-defined integration points.

## Core Sub-Agents (Phase 1)

### Planning & Documentation Agents

#### [Explorer](explorer.md)
**Phase:** 1 | **Status:** Active | **Color:** Blue
**Description:** Initial feature exploration specialist that transforms vague ideas into structured Product Requirements Documents through discovery conversations
**Triggers:** `/explore [topic]` command
**Outputs:** `docs/features/FEAT-XXX/prd.md`
**Invokes:** Researcher agent, Specialist Creator agent (optional)
**Tools:** Read, Glob, Grep, Write, Task

#### [Researcher](researcher.md)
**Phase:** 1 | **Status:** Active | **Color:** Orange
**Description:** Deep research specialist that investigates technical approaches using optional Archon MCP and WebSearch to answer open questions from PRDs
**Triggers:** Automatically after Explorer completes
**Outputs:** `docs/features/FEAT-XXX/research.md`
**Invokes:** Specialist sub-agents (optional, for targeted domain research)
**Tools:** Read, WebSearch, Task, Glob, Archon RAG tools (optional)

#### [Planner](planner.md)
**Phase:** 1 | **Status:** Active | **Color:** Blue
**Description:** Planning workflow orchestrator that synthesizes PRD and research into comprehensive planning documentation including architecture, acceptance criteria, testing strategy, and test stubs
**Triggers:** `/plan FEAT-XXX` command
**Outputs:**
- `docs/features/FEAT-XXX/architecture.md`
- `docs/features/FEAT-XXX/acceptance.md`
- `docs/features/FEAT-XXX/testing.md`
- `docs/features/FEAT-XXX/manual-test.md`
- Test stubs in `tests/` directory
- Appends to `/AC.md`
**Invokes:** Reviewer agent
**Tools:** Read, Write, Edit, Task, Glob

#### [Reviewer](reviewer.md)
**Phase:** 1 | **Status:** Active | **Color:** Purple
**Description:** Quality gate validator that ensures completeness, template compliance, and documentation quality before workflows complete
**Triggers:** Automatically by Planner agent
**Outputs:** Validation report (PASS/FAIL)
**Invokes:** None (terminal validator)
**Tools:** Read, Glob, Grep

#### [Documenter](documenter.md)
**Phase:** 1 | **Status:** Active | **Color:** Green
**Description:** Documentation maintenance specialist that keeps the documentation index current, validates cross-references, and updates CHANGELOG with feature activities
**Triggers:** `/update-docs` command, post-workflow updates
**Outputs:**
- `docs/README.md` (regenerated)
- `CHANGELOG.md` (appended)
**Invokes:** None
**Tools:** Read, Edit, Glob, Grep

### Creation & Enhancement Agents

#### [Specialist Creator](specialist-creator.md) ✨ NEW
**Phase:** 1 | **Status:** Active | **Color:** Purple
**Description:** Creates comprehensive specialist sub-agents with research auto-population for libraries, frameworks, and technical domains
**Triggers:** `/create-specialist [library-name]` command, Explorer agent suggestion
**Outputs:** `.claude/subagents/[library-name]-specialist.md`
**Invokes:** None
**Tools:** Read, Write, WebSearch, Archon RAG tools (optional)
**Features:**
- Two-phase creation: Template scaffolding (<30s) + Research auto-population (<90s)
- Knowledge cascade: Archon RAG → WebSearch → User input
- Kebab-case filename generation
- Quality validation before file write

## Specialist Sub-Agents

**Dynamic domain experts** created via `/create-specialist` command for library/framework-specific expertise.

### How to Create Specialists

**Option 1: Automatic (Recommended)**
- Run `/explore [topic]` and mention libraries during Q&A
- Explorer detects libraries and suggests specialist creation
- Choose scope: narrow (library-specific) or broad (category-wide)

**Option 2: Manual**
```
/create-specialist Supabase           # Narrow scope (Supabase only)
/create-specialist PydanticAI narrow  # Explicit narrow scope
/create-specialist Database broad     # Broad scope (Postgres, Supabase, etc.)
```

### Available Specialist Sub-Agents

*No specialists created yet - create your first with `/create-specialist`*

**Common Examples:**
- **Library Specialists:** `supabase-specialist.md`, `pydantic-ai-specialist.md`, `prisma-specialist.md`
- **Framework Specialists:** `fastapi-specialist.md`, `nextjs-specialist.md`, `django-specialist.md`
- **Category Specialists:** `database-specialist.md`, `security-specialist.md`, `authentication-specialist.md`

### Specialist Naming Convention

- **Filename:** `[library-name]-specialist.md` (kebab-case)
- **Agent Name:** `[Library] Specialist` (in YAML frontmatter)
- **Examples:**
  - Supabase → `supabase-specialist.md`
  - PydanticAI → `pydantic-ai-specialist.md`
  - Next.js → `nextjs-specialist.md`

### How Specialists Are Used

Specialists are invoked as **subordinates** by:

1. **Explorer Agent** - During Q&A for library-specific clarifying questions
2. **Researcher Agent** - During research for targeted domain knowledge
3. **Main Claude Agent** - Direct invocation for framework expertise

**Invocation Pattern:**
```markdown
Task(
  subagent_type="general-purpose",
  description="Get [Library] domain expertise",
  prompt="""
  You are the [Library] Specialist. Answer this targeted question: [question]

  Context: [relevant context from PRD/research]

  @.claude/subagents/[library-name]-specialist.md
  """
)
```

## Agent Templates

### [TEMPLATE.md](TEMPLATE.md)
**Purpose:** Structural scaffold for all sub-agent definitions
**Sections:**
- YAML frontmatter (name, description, tools, phase, status, color)
- Primary Objective
- Simplicity Principles (5)
- Core Responsibilities (3-5)
- Tools Access
- Output Files
- Workflow (phases)
- Quality Criteria
- Integration Points
- Guardrails
- Example Workflow
- Assumptions & Defaults
- Error Handling
- Related Documentation

**Specialist Enhancement (FEAT-003):**
- Auto-population guidance
- Key sections for specialists
- Naming conventions (kebab-case)
- Knowledge source documentation

## Agent Design Principles

1. **Single Responsibility:** Each agent has ONE clear purpose
2. **Stateless Design:** Agents don't maintain session state (Phase 1)
3. **Template Compliance:** All agents follow TEMPLATE.md structure
4. **Tool Minimalism:** Only essential tools in frontmatter
5. **Quality Gates:** Validation before completion (Reviewer pattern)
6. **Documentation First:** Planning before implementation
7. **Graceful Degradation:** Work without optional dependencies (e.g., Archon)

## Agent Workflow Orchestration

```
User Request
    ↓
/explore [topic]
    ↓
Explorer Agent
    ├─→ Library Detection
    ├─→ Specialist Suggestion (optional)
    └─→ PRD Creation
         ↓
Researcher Agent
    ├─→ Specialist Invocation (if available)
    ├─→ Archon RAG / WebSearch
    └─→ Research Creation
         ↓
/plan FEAT-XXX
    ↓
Planner Agent
    ├─→ Architecture Creation
    ├─→ Acceptance Criteria
    ├─→ Testing Strategy
    ├─→ Test Stubs
    └─→ Reviewer Validation
         ↓
Reviewer Agent
    └─→ PASS / FAIL
         ↓
Documenter Agent
    ├─→ Update docs/README.md
    └─→ Update CHANGELOG.md
```

## Tool Access by Agent

| Agent | Read | Write | Edit | Glob | Grep | WebSearch | Task | Archon RAG |
|-------|------|-------|------|------|------|-----------|------|------------|
| Explorer | ✅ | ✅ | - | ✅ | ✅ | - | ✅ | - |
| Researcher | ✅ | ✅ | - | ✅ | - | ✅ | ✅ | ✅ (optional) |
| Planner | ✅ | ✅ | ✅ | ✅ | - | - | ✅ | - |
| Reviewer | ✅ | - | - | ✅ | ✅ | - | - | - |
| Documenter | ✅ | - | ✅ | ✅ | ✅ | - | - | - |
| Specialist Creator | ✅ | ✅ | - | ✅ | - | ✅ | - | ✅ (optional) |
| Specialists | ✅ | ✅ | - | - | - | ✅ | - | ✅ (optional) |

## Phase Roadmap

**Phase 1 (Complete):** Planning & Documentation Agents ✅
- Explorer, Researcher, Planner, Reviewer, Documenter
- Specialist Creator (FEAT-003) ✨

**Phase 1.5 (Complete):** Archon MCP Integration ✅
- RAG knowledge base for Researcher
- Task management across workflows

**Phase 2 (Next):** Implementation Agents
- Main Claude Code agent for TDD implementation
- Builder agent for code generation
- Tester agent for test execution
- Committer agent for git workflow

**Phase 3 (Future):** Advanced Automation
- Bidirectional Archon sync
- Specialist evolution and learning
- Stack-specific profiles
- CI/CD integration

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Main agent orchestration and project overview
- [docs/README.md](../../docs/README.md) - Documentation index
- [Slash Commands](../.claude/commands/) - Workflow command definitions
- [FEAT-003 Implementation](../../docs/features/FEAT-003_specialist_subagent_creation/implementation.md) - Specialist system details

---

**Note:** This index is manually maintained. Update when adding/removing sub-agents.
**Template Version:** 1.0.0
**Last Updated:** 2025-10-25
