# Validate Completed Tasks

You are running the validation workflow for completed implementation tasks. Your goal is to systematically test all tasks currently in "review" status in Archon to ensure they are working correctly before marking them as "done".

## Instructions

### Step 1: Identify Tasks to Validate

Use Archon to get all tasks in "review" status:

```
Find all tasks with status="review" in the EVI RAG project (project_id: c5b0366e-d3a8-45cc-8044-997366030473)
```

### Step 2: Launch Validator Agent for Each Feature Group

For each group of related tasks (grouped by feature), launch the validator agent with SPECIFIC details about what was built:

**Example for "Data Models & Schema" feature**:
```
Launch validator agent with prompt:

"Validate the EVI-specific Pydantic models that were added to agent/models.py.

What was built:
- TieredGuideline model with tier 1/2/3 content fields and validation
- EVIProduct model with name, description, url, category, compliance_tags, embedding
- GuidelineSearchResult model with tier, score, similarity fields
- ProductRecommendation model with product, relevance_score, reasoning
- ProductSearchResult model for database results
- ResearchAgentResponse model with guidelines and products lists
- SpecialistAgentResponse model with Dutch message and citations

Test requirements:
1. Import all new models successfully
2. Test model validation (valid data passes, invalid data raises errors)
3. Test field validators (tier must be 1-3, URLs must start with http, etc.)
4. Test with sample data that matches EVI use cases
5. Ensure compliance_tags are formatted correctly (uppercase, underscores)

Files to test: agent/models.py (lines 255-436)
"
```

**Example for "Infrastructure Setup" feature**:
```
Launch validator agent with prompt:

"Validate the PostgreSQL schema extensions and configuration files for EVI RAG system.

What was built:
1. sql/evi_schema_additions.sql:
   - Added tier column to chunks table
   - Created products table with embeddings and compliance_tags
   - Updated hybrid_search to use Dutch language
   - Created search_guidelines_by_tier() function
   - Created search_products() function
   - Created guideline_tier_stats and product_catalog_summary views

2. config/notion_config.py:
   - NotionConfig dataclass with validation
   - Environment variable loading
   - HTTP headers generation

3. docker-compose.yml:
   - Neo4j 5.26.1 setup with proper memory settings

Test requirements:
1. Validate SQL syntax is correct (no parse errors)
2. Test NotionConfig can be imported and instantiated
3. Test NotionConfig.from_env() raises errors when env vars missing
4. Verify docker-compose.yml is valid YAML
5. Test that test_supabase_connection.py can import and run without syntax errors

Files to test:
- sql/evi_schema_additions.sql
- config/notion_config.py
- docker-compose.yml
- tests/test_supabase_connection.py
"
```

### Step 3: Validation Criteria

For each task, the validator should:

✅ **Code Quality Checks**:
- All files can be imported without syntax errors
- No obvious bugs or typos
- Follows Python best practices (PEP8 for Python)
- Type hints are correct
- Validation logic works as expected

✅ **Functionality Tests**:
- Models can be instantiated with valid data
- Validators reject invalid data appropriately
- Configuration classes work as documented
- SQL files have correct syntax
- YAML files are valid

✅ **Integration Tests** (if possible):
- Models integrate with existing codebase
- No import conflicts or circular dependencies
- Type compatibility with existing code

### Step 4: Report Results

After validator completes, create a summary:

```markdown
# Validation Report - [Feature Name]

## Tasks Validated
- Task ID: [id] - [title]
- Task ID: [id] - [title]

## Test Results
✅ Passed: X tests
❌ Failed: Y tests

## What Was Tested
- ✅ [Specific test]: Working correctly
- ✅ [Specific test]: Handles edge cases
- ⚠️ [Specific test]: [Issue found]

## Recommendations
- [ ] Mark as done (if all pass)
- [ ] Fix issues before marking done (if failures)

## Files Tested
- file1.py: X tests
- file2.sql: Syntax validation
- etc.
```

### Step 5: Update Task Status

Based on validation results:

**If all tests pass**:
```
Update task status from "review" to "done" in Archon
```

**If tests fail**:
```
Keep task in "review" status and create follow-up task to fix issues
```

## Feature Groups to Validate

Based on current implementation, validate these feature groups:

### 1. Data Models & Schema
**Tasks**:
- "Create Pydantic models for EVI data structures"
- "Extend PostgreSQL schema for EVI-specific needs"

**Validator Focus**: Model validation, SQL syntax, type checking

### 2. Infrastructure Setup
**Tasks**:
- "Configure Neo4j in Docker for local development"
- "Set up Notion API integration"
- "Create Supabase project with PGVector and Dutch language support" (documentation only)

**Validator Focus**: Configuration validation, import tests, YAML validation

## Important Notes

1. **Don't require database connection**: Tests should validate code/syntax without needing actual DB connection
2. **Use mocking**: Mock external dependencies (database, APIs) for unit tests
3. **Focus on what was built**: Only test the newly implemented code, not the entire system
4. **Keep tests simple**: 3-5 tests per component is sufficient
5. **Document clearly**: Make it clear what passed/failed and why

## Example Validation Command

To run this validation workflow:

```bash
# In Claude Code chat
/validate-tasks
```

This will:
1. Query Archon for tasks in "review" status
2. Group tasks by feature
3. Launch validator agent for each feature group
4. Collect results
5. Update task statuses in Archon
6. Generate summary report

---

**Remember**: The validator agent needs SPECIFIC details about what was built to create meaningful tests. Don't just say "test the models" - tell it exactly which models, what fields, what validators, and what the expected behavior is.
