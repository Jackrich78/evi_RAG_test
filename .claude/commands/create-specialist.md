---
description: Create a specialist sub-agent for a specific library or framework
argument-hint: [library-name] [scope]
---

# Create Specialist Sub-Agent

You are creating a specialist sub-agent for: **$ARGUMENTS**

## Your Mission

Create a comprehensive specialist sub-agent that provides domain-specific expertise for a library, framework, or technical domain using template-based generation with research auto-population.

## Arguments

- **library-name** (required): Name of the library/framework (e.g., "Supabase", "PydanticAI", "FastAPI")
- **scope** (optional): "narrow" (default, library-specific) or "broad" (category-wide like "Database")

## Workflow Steps

### Step 1: Validate Context

Check if specialist already exists:
```
Use Glob to check: .claude/subagents/*-specialist.md
If specialist for this library exists:
  Ask user: "A [Library] specialist already exists. Update it or create new?"
  If update: Read existing, merge new research
  If new: Continue with creation
```

### Step 2: Parse Arguments and Determine Scope

```
Parse ARGUMENTS:
  library_name = first argument (required)
  scope = second argument or "narrow" (default)

Determine scope:
  If scope = "narrow":
    Specialist focuses solely on [library_name]
    Example: "Supabase Specialist" for Supabase only

  If scope = "broad":
    Specialist covers category including [library_name]
    Example: "Database Specialist" for Postgres, Supabase, MySQL
    Ask user: "Which libraries should this cover?" for category definition
```

### Step 3: Invoke Specialist Creator Sub-Agent

Use the Task tool to invoke the Specialist Creator agent:

```
Task(
  subagent_type="general-purpose",
  description="Create specialist sub-agent for [library_name]",
  prompt="""
  You are the Specialist Creator agent. Create a comprehensive specialist sub-agent for: '$ARGUMENTS'

  Follow the Specialist Creator agent definition in .claude/subagents/specialist-creator.md

  ## Your Task

  Create a specialist sub-agent file at .claude/subagents/[library-name]-specialist.md with:

  1. **Load TEMPLATE.md** as structural scaffold
  2. **Research auto-population** using Archon RAG → WebSearch → User input cascade:
     - Query Archon (if available): "[library] tools patterns best practices"
     - Query WebSearch (fallback): "[library] documentation getting started 2025"
     - Extract: common patterns, tools, gotchas, integration points
  3. **Populate specialist sections**:
     - Name: [Library] Specialist
     - Description: Domain expert for [library] (1 sentence)
     - Tools: Archon RAG, WebSearch, Read, Write (library-specific if applicable)
     - Primary Objective: What this specialist accomplishes
     - Core Responsibilities: 3-5 key areas of expertise
     - Simplicity Principles: 5 guiding principles from research
     - Common Patterns: Library-specific patterns from docs
     - Known Gotchas: Pitfalls and workarounds
     - Integration Points: How to use with other tools
  4. **Generate kebab-case filename**:
     - "Supabase" → "supabase-specialist.md"
     - "PydanticAI" → "pydantic-ai-specialist.md"
     - "Next.js" → "next-js-specialist.md"
  5. **Complete in <2 minutes total**:
     - Template load: <10 seconds
     - Research: <90 seconds (Archon <30s, WebSearch <60s)
     - Population: <20 seconds
     - File write: <5 seconds

  ## Context
  - Library/Framework: $ARGUMENTS (first arg)
  - Scope: [narrow/broad] (second arg or default narrow)
  - Existing specialists: [list from Glob search]

  ## Templates and Agents
  @.claude/subagents/TEMPLATE.md
  @.claude/subagents/specialist-creator.md

  ## Success Criteria
  - File created at .claude/subagents/[library-name]-specialist.md
  - Valid YAML frontmatter with all required fields
  - Comprehensive auto-populated content from research
  - Sources documented (Archon RAG / WebSearch / User)
  - Total time <120 seconds
  """
)
```

### Step 4: Validate Specialist File

After Specialist Creator completes:

```
1. Read created file: .claude/subagents/[library-name]-specialist.md
2. Validate structure:
   - YAML frontmatter present with required fields
   - All template sections populated (not just placeholders)
   - Sources documented for auto-populated content
3. Check file size:
   - Should be comprehensive (>500 words)
   - Not excessive (<2000 words)
4. Verify filename follows kebab-case convention
```

### Step 5: Update Documentation Index

Invoke Documenter agent to add specialist to index:

```
Task(
  subagent_type="general-purpose",
  description="Update documentation for new specialist",
  prompt="""
  You are the Documenter agent. Update the documentation index for a new specialist sub-agent.

  Follow the Documenter agent definition in .claude/subagents/documenter.md

  1. Update docs/README.md:
     - Add new "Specialist Sub-Agents" section (if not exists)
     - List specialist: "[Library] Specialist - [Description]"
     - Include file path: .claude/subagents/[library-name]-specialist.md

  2. Update CHANGELOG.md:
     - Append entry: "Added [Library] Specialist sub-agent for domain expertise"

  3. Create .claude/subagents/README.md (if not exists):
     - Index of all sub-agents (core + specialists)
     - Usage instructions for invoking specialists

  Specialist details:
  - Name: [Library] Specialist
  - File: .claude/subagents/[library-name]-specialist.md
  - Scope: [narrow/broad]
  - Created: [current date]

  @.claude/subagents/documenter.md
  """
)
```

### Step 6: Present Specialist Summary

Show the user:

```
✅ Specialist Created: [Library] Specialist

## Details
- **File:** .claude/subagents/[library-name]-specialist.md
- **Scope:** [Narrow: library-specific / Broad: category-wide]
- **Created:** [timestamp]
- **Research Sources:**
  - Archon RAG: [source names if used]
  - WebSearch: [URLs if used]
  - User Input: [if manual input provided]

## Capabilities
- Provides domain-specific expertise for [library]
- Can be invoked by Explorer and Researcher agents
- Uses Archon RAG → WebSearch → User cascade for knowledge
- Stateless design (each invocation independent)

## How to Use

Specialists are automatically invoked when relevant:
- **During /explore:** Explorer can call specialist for library-specific questions
- **During research:** Researcher can call specialist for targeted knowledge

Manual invocation example:
```
Task(
  subagent_type="general-purpose",
  description="Get [library] expertise",
  prompt="""
  You are the [Library] Specialist. Answer this question: [question]

  @.claude/subagents/[library-name]-specialist.md
  """
)
```

## Next Steps
- Specialist is active and ready for use
- Explorer and Researcher will detect and invoke when appropriate
- Documentation index updated with specialist listing
- You can manually edit the specialist file to refine expertise

**Specialist ready for use in your workflows!**
```

## Important Notes

- **Creation Time:** Target <2 minutes total (template load + research + population)
- **Scope Choice:** Narrow (library-specific) recommended for better performance
- **Reusability:** Specialists persist across features in this project
- **Archon Optional:** Works with WebSearch if Archon MCP unavailable
- **Stateless Design:** Each invocation independent (no knowledge accumulation in Phase 1)

## Error Handling

### If Library Name Missing
```
❌ Error: Library name required

Usage: /create-specialist [library-name] [scope]

Examples:
  /create-specialist Supabase
  /create-specialist PydanticAI narrow
  /create-specialist Database broad
```

### If Specialist Already Exists
```
⚠️ Warning: Specialist already exists

File: .claude/subagents/[library-name]-specialist.md
Created: [date]

Options:
1. Update existing specialist with new research
2. Create new specialist with different scope
3. Skip creation

Choose: [1/2/3]
```

### If Research Fails
```
⚠️ Warning: Research auto-population incomplete

Archon RAG: [Unavailable / Incomplete coverage]
WebSearch: [Failed / Limited results]

Created specialist with basic template structure.
Please manually edit to add:
- Core Responsibilities
- Common Patterns
- Known Gotchas

File: .claude/subagents/[library-name]-specialist.md
```

## Example Invocations

### Create Narrow Specialist (Default)
```
User: /create-specialist Supabase

→ Specialist Creator researches Supabase specifically
→ Creates: .claude/subagents/supabase-specialist.md
→ Scope: Narrow (Supabase only)
→ Time: ~90 seconds (Archon + WebSearch)
→ Result: Comprehensive Supabase expertise
```

### Create Broad Specialist
```
User: /create-specialist Database broad

→ User prompted: "Cover which databases? (e.g., Postgres, Supabase, MySQL)"
→ User: "Postgres, Supabase"
→ Specialist Creator researches both
→ Creates: .claude/subagents/database-specialist.md
→ Scope: Broad (multiple databases)
→ Time: ~120 seconds (broader research)
→ Result: Multi-database expertise
```

### Update Existing Specialist
```
User: /create-specialist FastAPI

→ Detects existing: .claude/subagents/fastapi-specialist.md
→ Asks: "Update existing or create new?"
→ User: "Update"
→ Specialist Creator merges new research with existing
→ Updates: .claude/subagents/fastapi-specialist.md
→ Time: ~60 seconds (incremental research)
→ Result: Enhanced FastAPI expertise
```

## Success Criteria

✅ Specialist file created at correct location
✅ Valid YAML frontmatter structure
✅ Comprehensive auto-populated content
✅ Research sources documented
✅ Creation time <2 minutes
✅ Documentation index updated
✅ Specialist ready for invocation

## Related Commands

- `/explore [topic]` - Automatically suggests specialists during exploration
- `/plan FEAT-XXX` - Uses specialists for architecture research
- `/update-docs` - Regenerates specialist index

## Related Documentation

- [Specialist Creator Agent](./../subagents/specialist-creator.md)
- [Explorer Agent Enhancements](./../subagents/explorer.md)
- [Researcher Agent Enhancements](./../subagents/researcher.md)
- [Template](../subagents/TEMPLATE.md)

---

**Note:** Specialists are permanent per project and can be reused across multiple features. They provide focused, domain-specific expertise that complements the general-purpose agent system.
