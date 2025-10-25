---
description: Update documentation index and validate cross-references
argument-hint: [scope]
---

# Documentation Update Workflow

You are updating project documentation to ensure consistency and maintainability.

**Scope:** ${ARGUMENTS:-all}

## Your Mission

Invoke the Documenter agent to regenerate the documentation index, validate cross-references, and append CHANGELOG entries.

## Workflow Steps

### Step 1: Determine Scope

Parse the scope argument (defaults to "all"):
- **all** - Full documentation scan and index regeneration
- **feature** - Update only features section
- **system** - Update only system documentation
- **sop** - Update only SOPs
- **[FEAT-ID]** - Update specific feature only

### Step 2: Invoke Documenter Agent

Use the Task tool to invoke the Documenter agent:
```
Task(
  subagent_type="general-purpose",
  description="Update documentation index",
  prompt="""
  You are the Documenter agent. Update project documentation with scope: '${ARGUMENTS:-all}'

  Follow the Documenter agent definition in .claude/subagents/documenter.md

  ## Your Tasks

  ### 1. Scan Documentation
  - Use Glob to find all markdown files in docs/
  - Categorize by type: features, system, sop, templates
  - Read each feature folder to determine status
  - Check last-modified dates

  ### 2. Regenerate docs/README.md
  - Create organized index by category
  - List all features with status and links
  - List all system docs
  - List all SOPs
  - Note templates directory
  - Include last-updated timestamp

  ### 3. Validate Cross-References
  - Search for all markdown links [text](path)
  - Verify target files exist
  - Report broken links
  - Suggest fixes for typos or moved files

  ### 4. Update CHANGELOG (if requested)
  If scope includes new features or significant changes:
  - Append entry to CHANGELOG.md
  - Use conventional format: Added/Changed/Fixed
  - Single line per change
  - Link to documentation

  ## Index Format
  Follow this structure for docs/README.md:
  - Header with last-updated timestamp
  - Features section (organized by status)
  - System Documentation section (alphabetical)
  - Standard Operating Procedures section (alphabetical)
  - Templates section (note location)

  ## Agent Definition
  @.claude/subagents/documenter.md

  ## Context
  @docs/
  """
)
```

### Step 3: Review Results

After Documenter completes:
1. Show updated docs/README.md
2. Report any broken links found
3. Show CHANGELOG entries if added
4. Confirm index is current

### Step 4: Handle Broken Links

If broken links were found:
```
⚠️ Broken Links Detected

The following links need attention:
- [file:line] → [link] (target not found)

Suggestions:
- [Specific fix suggestions from Documenter]

Would you like me to:
1. Fix automatically (rename/move files)
2. Update links to correct paths
3. Remove broken links

Or you can fix manually and re-run /update-docs
```

### Step 5: Confirm Completion

Show summary:
```
✅ Documentation Updated

## Changes
- docs/README.md regenerated (X features, Y system docs, Z SOPs)
- CHANGELOG.md updated with [entries]
- Cross-references validated: [X valid, Y broken]

## Statistics
- Features: X total (A exploring, B ready, C in progress, D complete)
- System Docs: Y files
- SOPs: Z files
- Last updated: [timestamp]

## Next Steps
- Review docs/README.md for accuracy
- Fix any broken links reported
- Commit documentation updates
```

## Use Cases

### After Feature Planning
```
User: /plan FEAT-001
[Planning completes]
User: /update-docs

→ Documenter adds FEAT-001 to index with status "Ready"
→ Appends CHANGELOG entry
→ Validates all links still work
```

### After Manual Documentation Changes
```
User: [Edits docs/system/architecture.md manually]
User: /update-docs system

→ Documenter updates system docs section
→ Validates architecture.md links
→ Updates last-modified date
```

### Full Documentation Audit
```
User: /update-docs all

→ Documenter scans all documentation
→ Regenerates complete index
→ Validates all cross-references
→ Reports statistics and broken links
```

### Specific Feature Update
```
User: /update-docs FEAT-001

→ Documenter updates only FEAT-001 entry
→ Checks status (exploring → ready → in progress → complete)
→ Updates links to FEAT-001 docs
```

## Automation Hooks (Phase 2)

In Phase 2, this workflow will be triggered automatically:
- **PostToolUse Hook:** After any doc file written/edited
- **Lightweight:** Only adds new files to index
- **Manual Trigger:** Full regeneration via /update-docs command

## Important Notes

- **Regeneration:** docs/README.md is completely regenerated each time
- **Append Only:** CHANGELOG.md is append-only (never edits existing entries)
- **No Content Changes:** Documenter never modifies feature or system docs, only indexes them
- **Fast Operation:** Should complete in <1 minute for typical projects

## Example Output

```
✅ Documentation Index Updated

## Summary
- 5 features indexed
  - FEAT-001: Authentication (Ready for Implementation)
  - FEAT-002: Dashboard (Exploring)
  - FEAT-003: Billing (Ready for Implementation)
  - FEAT-004: Analytics (In Progress - Phase 2)
  - FEAT-005: Admin Panel (Complete)

- 5 system documents
  - architecture.md (last modified: 2025-10-24)
  - database.md (last modified: 2025-10-23)
  - api.md (last modified: 2025-10-24)
  - integrations.md (last modified: 2025-10-22)
  - stack.md (last modified: 2025-10-21)

- 6 SOPs
  - git-workflow.md
  - testing-strategy.md
  - code-style.md
  - mistakes.md
  - github-setup.md
  - sop-template.md

## Cross-Reference Validation
✅ 47 links validated
⚠️ 2 broken links found:
  - docs/features/FEAT-001_authentication/architecture.md:23
    → Link to [database schema](../system/db-schema.md)
    → Suggestion: Should be database.md?

  - docs/system/integrations.md:15
    → Link to [Auth0 setup](../sop/auth0-config.md)
    → Suggestion: File not found, create or remove link?

## CHANGELOG
Added entry:
- Documentation index regenerated with 5 features

## Next Steps
1. Review docs/README.md
2. Fix 2 broken links identified above
3. Run /update-docs again to confirm
```

## Success Criteria

✅ docs/README.md regenerated with complete index
✅ All features listed with correct status
✅ All system docs and SOPs indexed
✅ Cross-references validated
✅ Broken links reported (if any)
✅ CHANGELOG updated (if changes made)
✅ Last-updated timestamp current

## Future Enhancements (Phase 3)

- Detect orphaned documents (not linked from anywhere)
- Generate dependency graph of features
- Track documentation coverage metrics
- Validate word counts against limits
- Flag outdated content (>90 days old)
- Auto-fix common link issues
