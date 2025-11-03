# FEAT-002 Human Validation Guide

**Feature:** Notion Integration
**Status:** ✅ Complete (2025-10-26)
**Purpose:** Validate that 87 Dutch guidelines are searchable in the RAG knowledge base
**Time:** 10-15 minutes

---

## Quick Start ⭐

1. Ensure Docker containers are running
2. Connect to PostgreSQL
3. Run the validation queries below
4. Check that Dutch search returns relevant results

---

## Prerequisites

- Docker containers running: `docker-compose ps` (both should show "healthy")
- PostgreSQL accessible at `localhost:5432`
- `psql` command-line tool installed

**Start Docker if needed:**
```bash
cd /Users/builder/dev/evi_rag_test
docker-compose up -d
docker-compose ps  # Verify both containers healthy
```

---

## Step 1: Connect to Database

```bash
psql postgresql://postgres:postgres@localhost:5432/evi_rag
```

You should see:
```
psql (14.x, server 15.x)
Type "help" for help.

evi_rag=#
```

---

## Step 2: Validate Database Contains All Data

### ✅ Query 1: Check Total Chunk Count

```sql
SELECT COUNT(*) as total_chunks FROM chunks;
```

**Expected Result:**
```
 total_chunks
--------------
        10833
(1 row)
```

✅ **Pass:** 10,833 chunks found
❌ **Fail:** Different number (indicates incomplete ingestion)

---

### ✅ Query 2: Check Embeddings Coverage

```sql
SELECT
  COUNT(*) as total_chunks,
  COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as embedded_chunks,
  ROUND(100.0 * COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) / COUNT(*), 2) as coverage_percent
FROM chunks;
```

**Expected Result:**
```
 total_chunks | embedded_chunks | coverage_percent
--------------+-----------------+------------------
        10833 |           10833 |           100.00
(1 row)
```

✅ **Pass:** 100% coverage
❌ **Fail:** Less than 100% (indicates embedding generation issues)

---

### ✅ Query 3: Verify Tier Deferral

Per AC-002-302, all tier values should be NULL (tier parsing deferred).

```sql
SELECT COUNT(*) as non_null_tiers
FROM chunks
WHERE tier IS NOT NULL;
```

**Expected Result:**
```
 non_null_tiers
----------------
              0
(1 row)
```

✅ **Pass:** 0 non-null tiers
❌ **Fail:** Any non-zero number

---

### ✅ Query 4: Check Document Count

```sql
SELECT COUNT(*) as total_documents FROM documents;
```

**Expected Result:**
```
 total_documents
-----------------
              87
(1 row)
```

✅ **Pass:** 87 documents
❌ **Fail:** Different number

---

## Step 3: Test Dutch Full-Text Search

### ✅ Test Query 1: "veiligheid" (safety)

```sql
SELECT
  LEFT(content, 150) as preview,
  ts_rank(to_tsvector('dutch', content), plainto_tsquery('dutch', 'veiligheid')) as rank
FROM chunks
WHERE to_tsvector('dutch', content) @@ plainto_tsquery('dutch', 'veiligheid')
ORDER BY rank DESC
LIMIT 3;
```

**Expected:** 3 results with Dutch text containing "veiligheid"

**Example output:**
```
                                     preview                                    |   rank
--------------------------------------------------------------------------------+-----------
 ...veiligheid op de werkplek is een belangrijk onderwerp...                  | 0.3326
 ...werkplek veiligheid begint met risicoanalyse...                            | 0.3030
 ...persoonlijke veiligheid en werkplekgezondheid...                           | 0.2869
(3 rows)
```

✅ **Pass:** 3+ results returned, Dutch text readable, rank > 0
❌ **Fail:** 0 results or garbled Dutch characters

---

### ✅ Test Query 2: "zwangerschap" (pregnancy)

```sql
SELECT
  LEFT(content, 150) as preview,
  ts_rank(to_tsvector('dutch', content), plainto_tsquery('dutch', 'zwangerschap')) as rank
FROM chunks
WHERE to_tsvector('dutch', content) @@ plainto_tsquery('dutch', 'zwangerschap')
ORDER BY rank DESC
LIMIT 3;
```

**Expected:** 3 results about pregnancy

✅ **Pass:** Results contain "zwangerschap" or related pregnancy terms
❌ **Fail:** 0 results or irrelevant content

---

### ✅ Test Query 3: "rugklachten" (back complaints)

```sql
SELECT
  LEFT(content, 150) as preview,
  ts_rank(to_tsvector('dutch', content), plainto_tsquery('dutch', 'rugklachten')) as rank
FROM chunks
WHERE to_tsvector('dutch', content) @@ plainto_tsquery('dutch', 'rugklachten')
ORDER BY rank DESC
LIMIT 3;
```

**Expected:** 3 results about back problems

✅ **Pass:** Results contain "rug" (back) related terms
❌ **Fail:** 0 results

---

### ✅ Test Query 4: "beschermingsmiddelen" (protective equipment)

```sql
SELECT
  LEFT(content, 150) as preview,
  ts_rank(to_tsvector('dutch', content), plainto_tsquery('dutch', 'beschermingsmiddelen')) as rank
FROM chunks
WHERE to_tsvector('dutch', content) @@ plainto_tsquery('dutch', 'beschermingsmiddelen')
ORDER BY rank DESC
LIMIT 3;
```

**Expected:** 3 results about protective equipment

✅ **Pass:** Results contain "bescherming" or "middelen" (protection or equipment) terms
❌ **Fail:** 0 results

---

## Step 4: Inspect Sample Content Quality

### ✅ Check Content Samples

```sql
SELECT
  d.title,
  LEFT(c.content, 200) as content_preview,
  LENGTH(c.content) as content_length
FROM chunks c
JOIN documents d ON c.document_id = d.id
ORDER BY RANDOM()
LIMIT 5;
```

**What to look for:**
- ✅ Dutch text is readable (no garbled characters like �� or mojibake)
- ✅ Content makes sense (not just URLs or metadata)
- ✅ Content lengths reasonable (typically 500-2000 characters)
- ✅ Special Dutch characters (é, ë, ï, ö, ü) display correctly

---

### ✅ Check for Empty or Suspicious Chunks

```sql
SELECT COUNT(*) as suspicious_chunks
FROM chunks
WHERE content IS NULL OR LENGTH(TRIM(content)) < 50;
```

**Expected:** 0 or very few (< 10)

✅ **Pass:** 0-10 suspicious chunks
⚠️ **Warning:** 10-100 suspicious chunks (acceptable but investigate)
❌ **Fail:** > 100 suspicious chunks (indicates data quality issue)

---

## Step 5: Exit and Summary

### Exit psql

```sql
\q
```

---

## ✅ Validation Checklist

Copy this and check off as you validate:

```markdown
## FEAT-002 Validation Results

**Date:** [Your date]
**Tester:** [Your name]

### Step 1: Database Verification
- [ ] 10,833 chunks found ✅ / ❌
- [ ] 100% embeddings coverage ✅ / ❌
- [ ] All tier values NULL ✅ / ❌
- [ ] 87 documents found ✅ / ❌

### Step 2: Dutch Search Queries
- [ ] Query 1 (veiligheid) returned 3+ results ✅ / ❌
- [ ] Query 2 (zwangerschap) returned 3+ results ✅ / ❌
- [ ] Query 3 (rugklachten) returned 3+ results ✅ / ❌
- [ ] Query 4 (beschermingsmiddelen) returned 3+ results ✅ / ❌

### Step 3: Content Quality
- [ ] Sample chunks readable ✅ / ❌
- [ ] No encoding issues (Dutch characters display correctly) ✅ / ❌
- [ ] Content lengths reasonable ✅ / ❌
- [ ] Suspicious chunks < 10 ✅ / ❌

## Overall Result
- [ ] ✅ **PASS** - FEAT-002 validated, RAG knowledge base working correctly
- [ ] ⚠️ **PASS WITH WARNINGS** - Minor issues found (notes below)
- [ ] ❌ **FAIL** - Blocking issues found (notes below)

## Issues Found
[List any issues here, or write "None"]

## Notes
[Any additional observations]
```

---

## Success Criteria Summary

FEAT-002 is considered **validated** if ALL of these pass:

1. ✅ Database contains 10,833 chunks
2. ✅ 100% embeddings coverage
3. ✅ All tier values NULL (per AC-002-302)
4. ✅ 87 documents in database
5. ✅ All 4 Dutch search queries return relevant results
6. ✅ Dutch special characters display correctly
7. ✅ Content quality acceptable (< 10 suspicious chunks)

**If all criteria pass:** 🎉 FEAT-002 is validated! The EVI 360 RAG knowledge base is working correctly with 87 Dutch workplace safety guidelines.

---

## Troubleshooting

### Issue: Connection refused

**Problem:** `psql: could not connect to server: Connection refused`

**Solution:**
```bash
docker-compose up -d
docker-compose ps  # Wait until postgres shows (healthy)
# Try again after 30 seconds
```

---

### Issue: No chunks found (count = 0)

**Problem:** Query returns 0 chunks

**Solution:**

1. Check if files exist:
   ```bash
   ls documents/notion_guidelines/*.md | wc -l
   # Should show 87
   ```

2. Check if ingestion ran:
   ```sql
   SELECT COUNT(*) FROM documents;
   # Should be 87
   ```

3. If 0 documents, the ingestion didn't run. Check the logs:
   ```bash
   tail -100 /tmp/feat002_full_ingestion.log
   ```

---

### Issue: Dutch characters garbled

**Problem:** Dutch text shows as `������` or similar

**Solution:**
- Check your terminal encoding:
  ```bash
  echo $LANG
  # Should be something like: en_US.UTF-8
  ```

- If not UTF-8, set it:
  ```bash
  export LANG=en_US.UTF-8
  export LC_ALL=en_US.UTF-8
  ```

- Reconnect to psql and try again

---

## Next Steps After Validation

Once FEAT-002 is validated:

1. ✅ Sign off on FEAT-002 completion
2. ✅ Proceed to FEAT-003 (Query & Retrieval) to build user-facing search interface
3. ✅ Archive this validation report

---

**Last Updated:** 2025-10-26
**See Also:**
- [VALIDATION_REPORT.md](VALIDATION_REPORT.md) - Automated validation results
- [COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md) - Feature completion summary
- [STATUS.md](STATUS.md) - Current status and next steps
