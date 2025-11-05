# Phase 2 Handoff: Quick Start Guide

**For Next Session:** Read this first, then proceed to Phase 2 implementation.

---

## ⚡ 30-Second Context

**What's Done:**
- ✅ 60 portal products scraped and in database
- ✅ 5 unit tests passing
- ✅ Product descriptions validated (product-specific, not generic)

**What's Next:**
- 🔄 Parse CSV (26 rows → 23 unique products)
- 🔄 Fuzzy match CSV → portal products (0.85 threshold + manual mappings)
- 🔄 Enrich database with `problem_mappings` metadata

**Time Estimate:** 1-2 hours

---

## 🎯 Critical Discovery: Product Count is 60 (not 76)

**Why this matters:**
- Planning docs estimated 76 products
- **Actual scraped count: 60 products** ✅
- This is the correct, validated number

**What happened:**
- Portal listing had 120 URLs (60 view pages + 60 admin `/add/` pages)
- Scraper correctly filtered out admin pages
- Only valid products were inserted

**Action Required:**
- Update any "76 products" references to "60 products" as you encounter them
- No need to re-scrape - 60 is the validated count

---

## 📂 Files Ready for Phase 2

**CSV Data:**
- `docs/features/FEAT-004_product-catalog/Intervention_matrix.csv`
  - 26 rows total
  - 23 unique products (many-to-one: multiple problems → same product)

**Manual Mappings (Pre-validated):**
- `docs/features/FEAT-004_product-catalog/manual_product_mappings.json`
  - 10 manual CSV → portal product mappings
  - Use these FIRST before fuzzy matching

**Unresolved Products Template:**
- `docs/features/FEAT-004_product-catalog/unresolved_products.json`
  - Will contain 4 products that can't be matched
  - For stakeholder review after Phase 2

---

## 🔧 Implementation Strategy

### Step 1: Parse CSV (15 min)
**Create:** `ingestion/parse_interventie_csv.py`

```python
def parse_interventie_csv() -> Dict[str, Dict]:
    """
    Parse CSV and aggregate problems by product name.

    Returns: {
        "Herstelcoaching": {
            "problems": ["Burn-out klachten", "..."],
            "category": "Verbetering belastbaarheid"
        },
        ...
    }
    """
    # 26 rows → 23 unique products
```

### Step 2: Load Manual Mappings (10 min)
```python
with open("manual_product_mappings.json") as f:
    manual_mappings = json.load(f)["mappings"]

# Convert to dict for fast lookup
manual_map = {
    m["csv_product"]: m["portal_product"]
    for m in manual_mappings
}
# 10 mappings ready
```

### Step 3: Fuzzy Match (30 min)
```python
from fuzzywuzzy import fuzz
import re

def normalize_product_name(name: str) -> str:
    """Remove special chars, lowercase."""
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip()

# Fuzzy match with 0.85 threshold
similarity = fuzz.token_sort_ratio(
    normalize_product_name(csv_name),
    normalize_product_name(portal_name)
) / 100.0

if similarity >= 0.85:
    # Match found!
```

### Step 4: Enrich Database (20 min)
```python
metadata = {
    "problem_mappings": ["Problem 1", "Problem 2"],
    "csv_category": "Category"
}

await conn.execute("""
    UPDATE products
    SET metadata = $1, category = $2, updated_at = NOW()
    WHERE id = $3
""", json.dumps(metadata), csv_category, product_id)
```

### Step 5: Unit Tests (30 min)
Implement tests 6-11 in `tests/unit/test_product_ingest.py`:
- CSV parsing
- Fuzzy matching
- Enrichment

---

## 🎯 Success Criteria for Phase 2

**When complete, you should have:**
- ✅ 23 unique CSV products parsed
- ✅ ≥19 products matched (9 automated + 10 manual = 83%)
- ✅ ≥19 products have `problem_mappings` in metadata
- ✅ 4 unresolved products written to JSON
- ✅ Unit tests 6-11 passing

**Validation:**
```sql
-- Check enriched products
SELECT COUNT(*) FROM products
WHERE jsonb_array_length(metadata->'problem_mappings') > 0;
-- Expected: ≥19

-- Sample enriched product
SELECT name, category, metadata->'problem_mappings'
FROM products
WHERE metadata->'problem_mappings' IS NOT NULL
LIMIT 3;
```

---

## 💡 Key Learnings from Phase 1

### 1. Validated Selectors Work Perfectly
- `h1` for name: 100% ✅
- `div.platform-product-description p` for description: 100% ✅
- `.product-price` for price: Works (NULL if missing) ✅

### 2. Upsert by URL is Clean
```python
ON CONFLICT (url) DO UPDATE
```
- No duplicates
- Easy re-scraping with `--refresh`
- Perfect for incremental updates

### 3. Return None for Invalid Data
```python
if not name:
    logger.error(f"No name found for {url}")
    return None
```
- Clean error handling
- Scraper continues
- Easy to log and track

### 4. Description Lengths Confirm Quality
- Min: 245 chars
- Max: 4,556 chars
- Avg: 1,552 chars
- All product-specific (not 147-char generic) ✅

---

## 📝 Quick Checklist Before Starting

- [ ] Read `PHASE_1_COMPLETE.md` completely
- [ ] Verify 60 products in database: `SELECT COUNT(*) FROM products;`
- [ ] Check CSV file exists: `ls docs/features/FEAT-004_product-catalog/Intervention_matrix.csv`
- [ ] Check manual mappings exist: `cat manual_product_mappings.json | jq '.mappings | length'` (should be 10)
- [ ] Activate venv: `source venv/bin/activate`
- [ ] Docker running: `docker-compose ps` (PostgreSQL healthy)

---

## 🚀 Start Phase 2

**Read next:**
1. `IMPLEMENTATION_GUIDE.md` → Phase 2 section (lines ~245-395)
2. Start implementing `ingestion/parse_interventie_csv.py`

**Do NOT:**
- Re-scrape portal (already done)
- Question 60 product count (validated)
- Skip manual mappings (critical for 83% match rate)

**Good luck! Phase 2 should take 1-2 hours.** 🎯
