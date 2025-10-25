# EVI 360 RAG System - Claude Code Configuration

## 🔄 Project Awareness & Context

**EVI 360 Project - CRITICAL CONTEXT**:
- **This is NOT a generic RAG system** - It's specifically for **EVI 360 workplace safety specialists**
- **Language**: All guidelines are in **Dutch** - system must support Dutch search and responses
- **3-Tier System**: Understand tier 1/2/3 guideline hierarchy (Summary → Key Facts → Details)
- **Product Focus**: System includes product catalog with compliance tags and recommendations
- **Archon Tracking**: Use **Archon MCP** for task management (project ID: `c5b0366e-d3a8-45cc-8044-997366030473`)

**Documentation**:
- **Always read `PROJECT_OVERVIEW.md`** at the start of a new conversation to understand EVI 360 architecture
- **Check `TASKS.md`** for how to use Archon MCP for task tracking (don't look for TASK.md file!)
- **Review `docs/IMPLEMENTATION_PROGRESS.md`** for current phase status and what's been completed
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PROJECT_OVERVIEW.md`

---

## Agent System & Workflows

This project now uses the **AI Workflow Starter** for structured feature planning and development.

### Active Sub-Agents

@.claude/subagents/explorer.md
@.claude/subagents/researcher.md
@.claude/subagents/planner.md
@.claude/subagents/documenter.md
@.claude/subagents/reviewer.md

**Note:** Sub-agents focus on planning, research, and documentation. The main Claude Code agent handles all code implementation, guided by planning documents created by sub-agents.

### Workflow Commands

Use these slash commands to orchestrate multi-agent workflows:

- `/explore [topic]` - Explore new feature idea, create initial PRD
- `/plan [FEAT-ID]` - Create comprehensive planning documentation
- `/update-docs` - Maintain documentation index and cross-references

*Phase 2 commands: `/build`, `/test`, `/commit` (coming soon)*

### Development Workflow

```
User has feature idea
  ↓
/explore [topic]
  ↓ Explorer agent asks clarifying questions
  ↓ Researcher agent conducts research (optional Archon, WebSearch)
  ↓ Creates docs/features/FEAT-XXX/prd.md and research.md
  ↓
User reviews and refines PRD
  ↓
/plan FEAT-XXX
  ↓ Planner agent orchestrates planning workflow
  ↓ Creates architecture.md, acceptance.md, testing.md, manual-test.md
  ↓ Generates test stubs in tests/ directory
  ↓ Appends acceptance criteria to AC.md
  ↓ Reviewer agent validates completeness
  ↓
/update-docs
  ↓ Documenter agent updates docs/README.md index
  ↓ Updates CHANGELOG.md with planning entry
  ↓
Ready for implementation
```

### Documentation Structure

All documentation lives in `docs/` with automatic indexing:

- **docs/templates/** - Document templates for agents to follow
- **docs/system/** - Technical architecture (architecture, database, API, integrations, stack)
- **docs/sop/** - Standard Operating Procedures (git workflow, testing, code style, lessons learned)
- **docs/features/** - Feature-specific docs (one folder per feature: FEAT-XXX/)
- **docs/archive/** - Completed or deprecated documentation

**Key files:**
- `docs/README.md` - Auto-updated index of all documentation
- `AC.md` - Global acceptance criteria (append-only)
- `CHANGELOG.md` - Conventional changelog (auto-updated)

---

## 🧱 Code Structure & Modularity

- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).

---

## 🧪 Testing & Reliability

### Test-Driven Development Approach

Phase 1 prepares for TDD:
1. **Test Strategy:** Documented in `docs/features/FEAT-XXX/testing.md`
2. **Test Stubs:** Empty test functions created in `tests/` with TODO comments
3. **Acceptance Criteria:** Clear pass/fail conditions in `AC.md`
4. **Manual Testing:** Human testing checklist in `manual-test.md`

### Pytest Requirements

- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case
- When testing, always activate the virtual environment in venv_linux and run python commands with 'python3'

---

## 🔌 MCP Server Usage

### Archon MCP (Task Management)

**Project ID:** `c5b0366e-d3a8-45cc-8044-997366030473`

This project integrates with Archon MCP for task tracking alongside git-based documentation.

**Task Management Philosophy:**
- **Git = Source of Truth** for all documentation and code
- **Archon = Tracker** for workflow progress and context

**Feature Tasks:** Each FEAT-XXX creates 4 workflow-phase tasks in Archon:
1. **Explore & Research** - Status: `done` after `/explore` completes
2. **Plan Architecture & Tests** - Status: `done` after `/plan` completes
3. **Build with TDD** - Status: `doing` during implementation
4. **Validate & Commit** - Status: `done` after merge

**Task Lifecycle:**
```
/explore FEAT-XXX → Create 4 tasks in Archon → Mark task 1 "done"
/plan FEAT-XXX → Mark task 2 "done"
/build FEAT-XXX → Mark task 3 "doing"
/test + /commit → Mark task 4 "done"
```

### Crawl4AI RAG MCP Server

- **Use for external documentation**: Get docs for Pydantic AI and other frameworks
- **Always check available sources first**: Use `get_available_sources` to see what's crawled
- **Code examples**: Use `search_code_examples` when looking for implementation patterns

### Neon MCP Server  

- **Database project management**: Use `create_project` to create new Neon database projects
- **Execute SQL**: Use `run_sql` to execute schema and data operations
- **Table management**: Use `get_database_tables` and `describe_table_schema` for inspection
- **Always specify project ID**: Pass the project ID to all database operations

---

## ✅ Task Completion

- **Use Archon MCP** for task management - see `TASKS.md` for how to use it
- **Mark completed tasks** immediately after finishing them using Archon MCP tools
- **Update `docs/IMPLEMENTATION_PROGRESS.md`** when completing major milestones or phases

---

## 📎 Style & Conventions

- **Use Python** as the primary language.
- **Follow PEP8**, use type hints, and format with `black`.
- **Use `pydantic` for data validation**.
- Use `FastAPI` for APIs and `SQLAlchemy` or `SQLModel` for ORM if applicable.
- Write **docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```

---

## 📚 Documentation & Explainability

- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

---

## 🧠 AI Behavior Rules

- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.

---

## Workflow Quality Gates

Every workflow includes validation:

1. **Reviewer Agent:** Validates all required sections exist in planning docs
2. **Template Compliance:** Docs follow templates in `docs/templates/`
3. **SOP Enforcement:** Agents follow procedures in `docs/sop/`
4. **Completeness Checks:** No TODOs left in planning docs before marking complete

---

## Standard Operating Procedures

Agents enforce SOPs documented in `docs/sop/`:
- **git-workflow.md** - Branching, commits, PRs
- **testing-strategy.md** - How we test (pytest, coverage requirements)
- **code-style.md** - Linting (black, ruff), formatting, type hints
- **mistakes.md** - Lessons learned, gotchas to avoid
- **github-setup.md** - Repository setup and CI/CD

---

## Phase Roadmap

**Phase 1:** Planning & Documentation ✅
- Feature exploration and research
- Comprehensive planning documentation
- Test strategy and stubs
- Documentation maintenance

**Phase 2 (Next):** Implementation & Testing
- Test-first implementation (TDD Red-Green-Refactor cycle)
- Automated formatting and linting hooks
- Git workflow automation via slash commands

**Phase 3 (Future):** Automation & Profiles
- Full Archon bidirectional sync
- Stack-specific profiles
- CI/CD integration
- Advanced hooks and automation

---

## Rules & Guardrails

### For Planning Agents (Phase 1):
1. Write ONLY to `docs/**`, `tests/**` (stubs only), and `AC.md`
2. Must not write implementation code
3. All feature docs must follow templates in `docs/templates/`
4. Reviewer agent must validate before workflow completes
5. Documenter agent maintains docs/README.md index

### For Main Agent (Implementation):
1. Follow architecture in `docs/features/FEAT-XXX/architecture.md`
2. Implement tests first, then code (TDD)
3. Never exceed 500 lines per file - refactor if approaching limit
4. Update unit tests when modifying existing logic
5. Use venv_linux virtual environment and python3 for all commands

---

## Context Management

### Memory Hierarchy
1. **CLAUDE.md** (this file) - Core orchestration, agent imports
2. **PROJECT_OVERVIEW.md** - EVI 360 architecture and context
3. **Subagents** - Specialized agent instructions (@imported above)
4. **Documentation** - JIT loading via Read tool when needed
5. **SOPs** - Referenced by agents for standards enforcement

### Session Recovery
The PreCompact hook (`.claude/hooks/pre_compact.py`) automatically saves session state before context compaction, including:
- Current feature being worked on
- Last agent invoked
- Pending tasks
- Links to key files

---

## Getting Help

- **EVI 360 Architecture:** Read `PROJECT_OVERVIEW.md` at start of new conversations
- **Current Status:** Check `docs/IMPLEMENTATION_PROGRESS.md` for phase completion
- **Template Documentation:** See `docs/README.md` for complete documentation index
- **Workflow Examples:** See `docs/features/` for sample workflows
- **Troubleshooting:** See `docs/sop/mistakes.md` for common issues
- **Task Tracking:** See `TASKS.md` for Archon MCP usage

---

**Project:** EVI 360 Workplace Safety RAG System
**Language:** Dutch (guidelines and responses)
**Development:** AI Workflow Starter (Phase 1 - Planning & Documentation)
**Task Management:** Archon MCP (Project ID: c5b0366e-d3a8-45cc-8044-997366030473)