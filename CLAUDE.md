### 🔄 Project Awareness & Context

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

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).

### 🧪 Testing & Reliability
- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case
- When testing, always activate the virtual environment in venv_linux and run python commands with 'python3'

### 🔌 MCP Server Usage

#### Crawl4AI RAG MCP Server
- **Use for external documentation**: Get docs for Pydantic AI
- **Always check available sources first**: Use `get_available_sources` to see what's crawled.
- **Code examples**: Use `search_code_examples` when looking for implementation patterns.

#### Neon MCP Server  
- **Database project management**: Use `create_project` to create new Neon database projects.
- **Execute SQL**: Use `run_sql` to execute schema and data operations.
- **Table management**: Use `get_database_tables` and `describe_table_schema` for inspection.
- **Always specify project ID**: Pass the project ID to all database operations.
- **Example workflow**:
  1. `create_project` - create new database project
  2. `run_sql` with schema SQL - set up tables
  3. `get_database_tables` - verify schema creation
  4. Use returned connection string for application config


### ✅ Task Completion
- **Use Archon MCP** for task management - see `TASKS.md` for how to use it
- **Mark completed tasks** immediately after finishing them using Archon MCP tools
- **Update `docs/IMPLEMENTATION_PROGRESS.md`** when completing major milestones or phases

### 📎 Style & Conventions
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

### 📚 Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 🧠 AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.