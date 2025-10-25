# Task Management - EVI 360 RAG System

This project uses **Archon MCP** for task tracking and management.

**Archon Project**: EVI RAG System for Workplace Safety
**Project ID**: `c5b0366e-d3a8-45cc-8044-997366030473`

---

## 🎯 Quick Commands

Ask Claude Code:
- *"Show me all tasks in the EVI RAG project"*
- *"What's the status of Phase 3 tasks?"*
- *"What tasks are assigned to me?"*
- *"Mark task [id] as done"*
- *"Create a new task for [description]"*

---

## 📊 Current Phase

**Phase 1-2**: ✅ Complete (Infrastructure + Data Models)
**Phase 3**: ⏳ Next (Notion Integration - 3 tasks)

### Phase 3 Tasks (Next Up)

1. **Create Notion API client wrapper** (`ingestion/notion_client.py`)
   - Fetch guidelines from Notion database
   - Extract 3-tier content structure
   - Convert Notion blocks to markdown

2. **Implement tier-aware chunking** (`ingestion/tier_chunker.py`)
   - Detect tier markers in content
   - Apply different chunking strategies per tier
   - Add tier metadata to chunks

3. **Build guideline ingestion pipeline** (`ingestion/ingest_guidelines.py`)
   - End-to-end automation: Notion → Database
   - Embedding generation
   - Knowledge graph building

---

## 📋 Detailed Tracking

For comprehensive progress tracking and phase breakdowns, see:
- **[docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md)** - Detailed phase breakdown with completion criteria
- **[archive/2025-10-19_supabase_migration/STATUS_REPORT.md](archive/2025-10-19_supabase_migration/STATUS_REPORT.md)** - Project snapshot at migration time

---

## 🔧 Working with Archon

### Viewing Tasks

```bash
# In Claude Code, ask:
"Show me all tasks in the EVI RAG project"

# Or filter by status:
"What tasks are in todo status?"
"Show me tasks currently in progress"
"What tasks have I completed?"
```

### Creating Tasks

```bash
# In Claude Code, ask:
"Create a new task: Implement Dutch response templates"

# With details:
"Create a task for Phase 4:
 Title: Build EVI 360 product scraper
 Description: Scrape product pages from EVI 360 website with rate limiting
 Feature: Product Scraping
 Assignee: Coding Agent"
```

### Updating Tasks

```bash
# In Claude Code, ask:
"Mark task [task-id] as done"
"Update task [task-id] status to in progress"
"Assign task [task-id] to User"
```

---

## 📁 Task Organization

Tasks in Archon are organized by:
- **Feature**: Phase grouping (e.g., "Notion Integration", "Product Scraping")
- **Status**: todo, doing, review, done
- **Assignee**: User, Coding Agent, or specific agent names
- **Priority**: Set via task_order field (higher = more urgent)

---

## 🎯 Task Granularity Guidelines

### For Feature-Specific Projects
Create detailed implementation tasks:
- "Set up Notion API client"
- "Implement tier detection logic"
- "Add Dutch language validation"
- "Write unit tests for chunker"

### For Codebase-Wide Projects
Create feature-level tasks:
- "Implement Notion integration"
- "Add product scraping system"
- "Build multi-agent architecture"

### General Rule
Each task should represent **30 minutes to 4 hours** of work.

---

## 🔄 Task Workflow

```
todo → doing → review → done
```

**Best Practices**:
- Only ONE task in 'doing' status at a time
- Mark tasks 'review' when code is written but needs validation
- Mark tasks 'done' only after testing/verification
- Update Archon immediately after completing work

---

## 📊 Progress Overview

**Total Phases**: 8
**Completed Phases**: 2 (Phase 1-2)
**Current Phase**: Phase 3 (Notion Integration)

### Phase Breakdown

- ✅ **Phase 1**: Infrastructure Setup (4 tasks) - Complete
- ✅ **Phase 2**: Data Models & Schema (2 tasks) - Complete
- ⏳ **Phase 3**: Notion Integration (3 tasks) - Next
- 📝 **Phase 4**: Product Scraping (3 tasks)
- 📝 **Phase 5**: Multi-Agent System (6 tasks)
- 📝 **Phase 6**: Dutch Language Support (2 tasks)
- 📝 **Phase 7**: CLI & Testing (3 tasks)
- 📝 **Phase 8**: Documentation (3 tasks)

**Total**: 26 tasks across 8 phases

---

## 🎓 Tips for Effective Task Management

1. **Keep tasks focused**: One clear objective per task
2. **Write clear descriptions**: Include acceptance criteria
3. **Update status promptly**: Mark progress immediately
4. **Use features for grouping**: Makes filtering easier
5. **Set realistic priorities**: Use task_order for sequencing

---

## 📚 Related Documentation

- **Project Overview**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
- **Setup Guide**: [LOCAL_SETUP_COMPLETE.md](LOCAL_SETUP_COMPLETE.md)
- **Progress Tracking**: [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md)
- **Development Guidelines**: [CLAUDE.md](CLAUDE.md)

---

**Task Management Tool**: Archon MCP
**Integration**: Claude Code with Archon MCP server
**Project**: EVI 360 RAG System for Workplace Safety
