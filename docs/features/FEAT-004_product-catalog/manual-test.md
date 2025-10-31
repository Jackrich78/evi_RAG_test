# Manual Testing Guide: Product Catalog Integration

## Feature ID
FEAT-004

## Feature Name
Product Catalog Integration

## Purpose
This guide provides step-by-step instructions for manually testing the product catalog ingestion and search functionality. These tests should be performed by QA testers or domain experts to validate functionality beyond automated tests.

---

## Prerequisites

### Environment Setup
- [ ] Python virtual environment activated (venv_linux)
- [ ] PostgreSQL database running with products schema
- [ ] Notion API key configured in environment variables
- [ ] Notion product database ID configured in `config/notion_config.py`
- [ ] Test products available in Notion database (minimum 10 products)

### Required Access
- [ ] Admin access to Notion workspace with product database
- [ ] Database connection credentials for test environment
- [ ] Command line access to run ingestion scripts

### Sample Test Data in Notion
Ensure the following product types exist:
- At least 1 product with all fields complete
- At least 1 product with missing optional fields (price_range)
- At least 3 products with CE compliance tag
- At least 2 products in "PPE" category
- At least 1 product with Dutch description

---

## Test Scenarios

### Scenario 1: Product Ingestion - Happy Path

**Objective:** Verify complete product ingestion from Notion to PostgreSQL

**Steps:**
1. Open terminal and activate virtual environment:
   ```bash
   source venv_linux/bin/activate
   ```

2. Run product ingestion command:
   ```bash
   python3 -m ingestion.ingest --type products
   ```

3. Observe console output for ingestion progress

4. Verify success message shows number of products ingested

5. Connect to PostgreSQL and query products table:
   ```sql
   SELECT COUNT(*) FROM products;
   ```

6. Verify count matches Notion product database count

7. Query sample product to verify all fields:
   ```sql
   SELECT * FROM products LIMIT 1;
   ```

**Expected Results:**
- ✅ Ingestion completes without errors
- ✅ Console logs show "Ingested N products successfully"
- ✅ Database contains all products from Notion
- ✅ All fields populated correctly (name, description, category, supplier, compliance_tags, use_cases, price_range, embedding)
- ✅ No NULL values for required fields (name, description)

**Acceptance Criteria Validated:** AC-FEAT-004-001, AC-FEAT-004-003, AC-FEAT-004-020

---

### Scenario 2: Product Search - Semantic Query

**Objective:** Verify semantic search returns relevant products

**Steps:**
1. Open Python REPL or create test script:
   ```bash
   python3
   ```

2. Import product search function:
   ```python
   from agent.product_queries import search_products
   ```

3. Execute Dutch language search query:
   ```python
   results = search_products(query="veiligheidshelm voor bouwplaats", limit=10)
   ```

4. Print results and inspect relevance:
   ```python
   for product in results:
       print(f"Name: {product['name']}")
       print(f"Category: {product['category']}")
       print(f"Score: {product['similarity_score']}")
       print("---")
   ```

5. Verify products are related to "safety helmets" or "construction"

6. Note response time in console

**Expected Results:**
- ✅ Query returns 1-10 products (depending on catalog size)
- ✅ Top results are semantically relevant (helmets, head protection)
- ✅ Results include all required fields (name, description, category, supplier, compliance_tags)
- ✅ Results ranked by similarity (highest score first)
- ✅ Query completes in <500ms
- ✅ Dutch language query understood correctly

**Acceptance Criteria Validated:** AC-FEAT-004-006, AC-FEAT-004-007, AC-FEAT-004-008, AC-FEAT-004-009

---

### Scenario 3: Compliance Filtering

**Objective:** Verify products can be filtered by compliance tags

**Steps:**
1. Search with single compliance filter:
   ```python
   results = search_products(
       query="veiligheidsbril",
       filters={"compliance_tags": ["CE"]},
       limit=10
   )
   ```

2. Verify all results have "CE" in compliance_tags

3. Search with multiple compliance filters:
   ```python
   results = search_products(
       query="bescherming",
       filters={"compliance_tags": ["CE", "EN 397"]},
       limit=10
   )
   ```

4. Verify all results have BOTH "CE" AND "EN 397" tags

5. Search with non-existent compliance tag:
   ```python
   results = search_products(
       query="helm",
       filters={"compliance_tags": ["INVALID_TAG"]},
       limit=10
   )
   ```

6. Verify empty results returned without error

**Expected Results:**
- ✅ Single filter returns only matching products
- ✅ Multiple filters use AND logic (all tags must match)
- ✅ Compliance tags are normalized (case-insensitive)
- ✅ Invalid filter returns empty list gracefully
- ✅ Combined semantic + filter search works correctly

**Acceptance Criteria Validated:** AC-FEAT-004-011, AC-FEAT-004-012, AC-FEAT-004-013, AC-FEAT-004-014, AC-FEAT-004-015

---

### Scenario 4: Product-Guideline Linking

**Objective:** Verify products are linked to relevant guidelines

**Steps:**
1. Query for a guideline topic that has related products:
   ```python
   from agent.specialist import search_with_products
   results = search_with_products(query="hoofdbescherming op de bouwplaats")
   ```

2. Inspect results for "Related Products" section

3. Verify related products match guideline topic (head protection)

4. Check that product categories align with guideline categories

5. Query a different guideline topic:
   ```python
   results = search_with_products(query="gehoorbescherming")
   ```

6. Verify different related products appear (hearing protection)

**Expected Results:**
- ✅ Guideline results include "Related Products" section
- ✅ Related products are relevant to guideline topic
- ✅ Products linked by category or use_case keywords
- ✅ Product recommendations change based on guideline query
- ✅ Linkage is maintained across ingestion updates

**Acceptance Criteria Validated:** AC-FEAT-004-016, AC-FEAT-004-017, AC-FEAT-004-018, AC-FEAT-004-019

---

### Scenario 5: Data Quality Validation

**Objective:** Verify data quality and edge case handling

**Steps:**
1. Query products table for missing optional fields:
   ```sql
   SELECT name, supplier, price_range
   FROM products
   WHERE supplier IS NULL OR price_range IS NULL;
   ```

2. Verify products with NULL optional fields are still present

3. Query for products with special characters:
   ```sql
   SELECT name FROM products WHERE name LIKE '%™%' OR name LIKE '%®%';
   ```

4. Verify special characters preserved correctly

5. Check ingestion logs for warnings about missing data:
   ```bash
   cat logs/ingestion.log | grep "WARNING"
   ```

6. Verify warnings logged for missing optional fields

7. Query for longest product description:
   ```sql
   SELECT name, LENGTH(description) as desc_length
   FROM products
   ORDER BY desc_length DESC
   LIMIT 1;
   ```

8. Verify very long descriptions are handled (truncated if >5000 chars)

**Expected Results:**
- ✅ Products with missing optional fields are ingested
- ✅ NULL values used for missing optional fields
- ✅ Special characters preserved (™, ®, #, etc.)
- ✅ Warnings logged for data quality issues
- ✅ Long descriptions truncated with warning
- ✅ No products skipped due to minor issues

**Acceptance Criteria Validated:** AC-FEAT-004-021, AC-FEAT-004-022, AC-FEAT-004-032, AC-FEAT-004-033

---

### Scenario 6: Update Existing Products

**Objective:** Verify product updates work correctly (no duplicates)

**Steps:**
1. Note initial product count:
   ```sql
   SELECT COUNT(*) FROM products;
   ```

2. Update a product in Notion (change description or add compliance tag)

3. Wait 30 seconds for Notion to sync

4. Re-run ingestion:
   ```bash
   python3 -m ingestion.ingest --type products
   ```

5. Verify product count unchanged (no duplicates):
   ```sql
   SELECT COUNT(*) FROM products;
   ```

6. Query the updated product to verify changes:
   ```sql
   SELECT * FROM products WHERE notion_page_id = 'updated-product-id';
   ```

7. Verify description or compliance_tags reflect Notion changes

**Expected Results:**
- ✅ Product count remains the same (no duplicates created)
- ✅ Updated product reflects latest Notion data
- ✅ Other products unchanged
- ✅ Ingestion log shows "Updated N products"
- ✅ Updated_at timestamp changed for updated product

**Acceptance Criteria Validated:** AC-FEAT-004-004, AC-FEAT-004-019

---

### Scenario 7: Performance Testing

**Objective:** Verify search performance meets requirements

**Steps:**
1. Create Python script to measure search time:
   ```python
   import time
   from agent.product_queries import search_products

   queries = [
       "veiligheidshelm",
       "gehoorbescherming",
       "veiligheidsbril",
       "werkhandschoenen",
       "harnas"
   ]

   times = []
   for query in queries:
       start = time.time()
       results = search_products(query=query, limit=10)
       end = time.time()
       elapsed = (end - start) * 1000  # Convert to ms
       times.append(elapsed)
       print(f"{query}: {elapsed:.2f}ms")

   avg_time = sum(times) / len(times)
   print(f"Average: {avg_time:.2f}ms")
   ```

2. Run script and note average search time

3. Verify average is below 500ms

4. Run with larger result set (limit=50) and measure

**Expected Results:**
- ✅ Average search time <500ms for top 10 results
- ✅ Search time scales linearly with result count
- ✅ No performance degradation with multiple queries
- ✅ Database uses pgvector index (check EXPLAIN output)

**Acceptance Criteria Validated:** AC-FEAT-004-008, AC-FEAT-004-024, AC-FEAT-004-025

---

## Edge Cases to Test

### Empty Catalog
- [ ] Run ingestion with empty Notion database
- [ ] Verify "0 products processed" message
- [ ] Search returns empty results without error

### Concurrent Ingestion
- [ ] Start ingestion process
- [ ] Immediately start second ingestion
- [ ] Verify second process exits with lock warning
- [ ] Verify data integrity (no corruption)

### API Failures
- [ ] Temporarily disable network connection
- [ ] Run ingestion
- [ ] Verify retry logic and error messages
- [ ] Restore connection and verify recovery

---

## Acceptance Checklist

After completing all scenarios, verify:
- [ ] All products ingested successfully (Scenario 1)
- [ ] Semantic search returns relevant results (Scenario 2)
- [ ] Compliance filtering works correctly (Scenario 3)
- [ ] Products linked to guidelines (Scenario 4)
- [ ] Data quality validated (Scenario 5)
- [ ] Product updates don't create duplicates (Scenario 6)
- [ ] Performance requirements met (Scenario 7)
- [ ] Edge cases handled gracefully
- [ ] No errors or warnings in application logs
- [ ] Database schema correct (no missing tables/columns)

---

## Troubleshooting

### Common Issues

**Issue:** Ingestion fails with "Notion API key not found"
- **Solution:** Set `NOTION_API_KEY` environment variable

**Issue:** Database connection error
- **Solution:** Verify PostgreSQL running and credentials correct

**Issue:** Search returns no results
- **Solution:** Verify products ingested and embeddings generated

**Issue:** Performance slower than 500ms
- **Solution:** Check pgvector index exists: `CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops);`

---

## Test Report Template

```
Test Date: [DATE]
Tester: [NAME]
Environment: [TEST/STAGING]

Scenario 1: [PASS/FAIL] - [Notes]
Scenario 2: [PASS/FAIL] - [Notes]
Scenario 3: [PASS/FAIL] - [Notes]
Scenario 4: [PASS/FAIL] - [Notes]
Scenario 5: [PASS/FAIL] - [Notes]
Scenario 6: [PASS/FAIL] - [Notes]
Scenario 7: [PASS/FAIL] - [Notes]

Issues Found:
1. [Issue description]
2. [Issue description]

Overall Status: [PASS/FAIL]
Ready for Production: [YES/NO]
```

---

**Word Count:** 796 words (under 800-word limit)
