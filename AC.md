# Acceptance Criteria (Global)

**Purpose:** Central repository of all acceptance criteria across features

**Format:** AC-FEAT-XXX-### for feature-specific criteria, AC-GLOBAL-### for project-wide standards

---

## Global Standards

### AC-GLOBAL-001: Documentation Completeness
All features must have complete planning documentation before implementation (PRD, research, architecture, acceptance, testing, manual-test).

### AC-GLOBAL-002: Template Compliance
All planning documents must follow templates exactly with all required sections present.

### AC-GLOBAL-003: Word Limits
Planning documents must respect word limits: PRD ≤800 words, research ≤1000 words, others ≤800 words.

### AC-GLOBAL-004: Test Stubs Required
All features must have test stubs generated in tests/ directory with TODO comments and acceptance criteria references.

### AC-GLOBAL-005: Reviewer Validation
All planning workflows must pass Reviewer agent validation before being marked complete.

### AC-GLOBAL-006: No Placeholders
Planning documents must not contain TODO, TBD, or placeholder content (except in test stubs).

### AC-GLOBAL-007: Given/When/Then Format
All acceptance criteria must use Given/When/Then format for testability.

---

## Feature-Specific Criteria

*Feature acceptance criteria will be appended here by the Planner agent during `/plan` command*

### FEAT-001: Example Feature

**AC-FEAT-001-001:** Example Documentation Complete
Given a developer is using the AI workflow template, when they review FEAT-001 example feature, then all 6 planning documents are present and follow templates.

**AC-FEAT-001-002:** Templates Demonstrated
Given an AI agent is generating feature documentation, when the agent references FEAT-001 as an example, then the agent can replicate the structure and quality.

---

*New feature criteria will be appended here automatically during planning*

### FEAT-003: Specialist Sub-Agent Creation System

**AC-FEAT-003-001:** Library Detection During Explorer Q&A
Given user is in /explore conversation answering Explorer's discovery questions, when user mentions a library or framework in their response (e.g., "We'll use Supabase for database"), then Explorer detects the library mention via regex pattern matching.

**AC-FEAT-003-002:** Specialist Creation Suggestion After PRD
Given Explorer has detected library mention during Q&A and completed PRD creation, when Explorer is about to invoke Researcher agent, then Explorer prompts user with specialist creation choice: "Create [Library] Specialist? (narrow/broad/skip)".

**AC-FEAT-003-003:** Hybrid Template-Based Specialist Creation in <2 Minutes
Given user confirms specialist creation with scope choice, when creation workflow executes, then specialist file created at .claude/subagents/[library-name]-specialist.md with comprehensive instructions in <2 minutes.

**AC-FEAT-003-004:** Archon RAG Auto-Population (If Available)
Given Archon MCP is available and configured with library documentation, when specialist auto-population research phase executes, then specialist instructions populated with Archon RAG query results.

**AC-FEAT-003-005:** WebSearch Fallback Auto-Population
Given Archon MCP is unavailable or lacks library documentation coverage, when specialist auto-population research phase executes, then specialist instructions populated with WebSearch query results.

**AC-FEAT-003-006:** Specialist Review and Edit Before Finalization
Given specialist auto-population completes, when specialist file is written, then user is prompted to review and can edit specialist instructions before finalizing.

**AC-FEAT-003-007:** Specialist Invocation by Explorer Agent
Given specialist exists at .claude/subagents/[library-name]-specialist.md and user is in /explore workflow, when Explorer needs domain-specific clarification during discovery phase, then Explorer invokes specialist via Task tool: @.claude/subagents/[library-name]-specialist.md.

**AC-FEAT-003-008:** Specialist Invocation by Researcher Agent
Given specialist exists and user is in research phase after /explore, when Researcher encounters domain-specific questions from PRD, then Researcher invokes specialist via Task tool for deep-dive investigation.

**AC-FEAT-003-009:** Specialist Knowledge Cascade (Archon → Web → User)
Given specialist is invoked with a domain-specific question, when specialist gathers knowledge to answer, then specialist tries Archon RAG first, falls back to WebSearch, then asks user as last resort.

**AC-FEAT-003-010:** Specialist Findings Documentation
Given specialist completes knowledge gathering and answers question, when specialist returns findings to calling agent, then findings include answer, source attribution, and confidence level.

**AC-FEAT-003-101:** Multiple Libraries Mentioned in Single Response
Given user says "We'll use Supabase for database and FastAPI for backend", when Explorer detects multiple library mentions, then Explorer prompts for each specialist separately or offers batch creation.

**AC-FEAT-003-102:** Specialist Already Exists for Library
Given specialist file exists at .claude/subagents/supabase-specialist.md, when user mentions "Supabase" in new /explore session, then Explorer skips creation prompt and uses existing specialist.

**AC-FEAT-003-103:** Auto-Population Research Fails (No Results)
Given specialist creation for obscure or custom library, when Archon query returns no results and WebSearch finds no documentation, then specialist created with minimal static template, user prompted to populate manually.

**AC-FEAT-003-104:** Specialist Invocation When File Missing
Given Researcher attempts to invoke @.claude/subagents/supabase-specialist.md, when file does not exist at that path, then Researcher gracefully handles error and falls back to direct research.

**AC-FEAT-003-105:** User Skips Specialist Creation, Changes Mind Later
Given user skipped specialist creation during /explore, when user is in later workflow phase (research, planning), then user can manually trigger specialist creation (future enhancement documented).

**AC-FEAT-003-201:** Creation Performance
Given specialist creation workflow executes, when measured from user confirmation to file write complete, then total time is less than 120 seconds with static scaffolding <30s and research auto-population <90s.

**AC-FEAT-003-202:** Specialist File Quality
Given specialist auto-population completes, when specialist file content reviewed, then all required sections populated with accurate, library-specific content and source citations.

**AC-FEAT-003-203:** Graceful Archon Degradation
Given Archon MCP is unavailable, when specialist creation or invocation occurs, then system falls back to WebSearch seamlessly without errors or workflow failures.

**AC-FEAT-003-204:** Specialist File Naming and Storage
Given specialist file is created, when filename generated, then file uses kebab-case naming derived from library name and is stored in .claude/subagents/ directory.

**AC-FEAT-003-301:** Explorer Agent Integration
Given /explore workflow is running, when library mentioned during discovery Q&A, then Explorer integration activates without breaking existing functionality.

**AC-FEAT-003-302:** Researcher Agent Integration
Given research phase after /explore completion, when Researcher identifies domain-specific questions from PRD, then Researcher invokes relevant specialists via Task tool.

**AC-FEAT-003-303:** Documenter Agent Integration
Given specialists exist in .claude/subagents/ directory, when /update-docs runs, then Documenter lists all specialists in "Active Specialists" section of docs/README.md.

**AC-FEAT-003-401:** TEMPLATE.md Requirements
Given specialist creation workflow needs base structure, when TEMPLATE.md loaded, then template contains all required placeholders ({{NAME}}, {{DESCRIPTION}}, {{LIBRARY}}, {{TOOLS}}, {{OBJECTIVE}}) and sections.

**AC-FEAT-003-402:** Library Detection Patterns
Given user response contains library name, when library detection regex applied, then well-known libraries (Supabase, FastAPI, PydanticAI, Django, React, PostgreSQL, Prisma, Next.js, TypeScript, Tailwind) detected accurately with <5% false positive rate.

---

**Note:** This file is append-only. Criteria are added by agents during `/plan` command and should not be manually edited or removed.

**Last Updated:** 2025-10-24
