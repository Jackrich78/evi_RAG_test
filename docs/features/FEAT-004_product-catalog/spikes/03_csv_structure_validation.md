# Spike 3: CSV Structure Validation

**Date:** 2025-11-04
**Duration:** 10 minutes
**Status:** ✅ Complete

## Objective
Validate Intervention_matrix.csv structure and problem-to-product mappings.

## CSV File Details
- **Path:** `docs/features/FEAT-004_product-catalog/Intervention_matrix.csv`
- **Encoding:** UTF-8 with BOM (handled with `encoding='utf-8-sig'`)
- **Columns:** `Probleem`, `Category`, `Link interventie`, `Soort interventie`

## Critical Findings ⚠️

### Row Count Discrepancy
- **PRD Assumption:** 33 rows
- **Actual Count:** **26 rows** (excluding header)
- **Discrepancy:** -7 rows (21% fewer than expected)

### Unique Product Count
- **PRD Assumption:** 33 unique products
- **Actual Count:** **23 unique products**
- **Duplicate mappings:** 3 products (mapped to multiple problems)

**Impact:** Target match rate calculations need adjustment:
- **Old target:** ≥80% of 33 = ≥27 matched
- **New target:** ≥80% of 23 = ≥19 matched

## Data Structure Analysis

### Categories (8 unique)
```
1. Arbeidsinhoud
2. Arbeidsomstandigheden
3. Arbeidsverhoudingen
4. Arbeidsvoorwaarden
5. Preventie
6. Sociale omstandigheden
7. Verbetering belastbaarheid
8. Vitaliteit & Loopbaan
```

### Many-to-One Relationships
**Products with multiple problems (3 products):**
1. **Vroegconsult Arbeidsdeskundige** (2 problems)
2. **Inzet bedrijfsmaatschappelijk werk** (2 problems)
3. **Werkplekonderzoek op locatie** (2 problems)

**Products with single problem:** 20 products

### Sample Product Aggregation

**Example: "Vroegconsult Arbeidsdeskundige"**
```python
{
    "product_name": "Vroegconsult Arbeidsdeskundige",
    "category": "Arbeidsinhoud",
    "problems": [
        "Is mijn zieke werknemer geschikt voor een concrete andere functie in mijn bedrijf?",
        "De werkweek moet worden aangepast zodat deze niet te zwaar is voor mijn zieke werknemer."
    ]
}
```

**Metadata structure:**
```python
product["metadata"] = {
    "problem_mappings": [
        "Is mijn zieke werknemer geschikt...",
        "De werkweek moet worden aangepast..."
    ],
    "csv_category": "Arbeidsinhoud"
}
```

## Sample Products

### Multi-Problem Products (3 total)
1. **Vroegconsult Arbeidsdeskundige** → 2 problems
2. **Inzet bedrijfsmaatschappelijk werk** → 2 problems
3. **Werkplekonderzoek op locatie** → 2 problems

### Single-Problem Products (Examples from 20)
1. **Adviesgesprek P&O Adviseur** → "Mijn werknemer en ik hebben advies nodig wat er gebeurt nadat..."
2. **Inzet vertrouwenspersoon** → "Mijn werknemer voelt zich niet veilig op de werkvloer"
3. **Vroegconsult Arbeidsdeskundige bv. gericht op aanpassingen eigen taken** → "Welke re-integratiemogelijkheden..."

## Validation Checklist
- [x] CSV parses without errors
- [x] All 26 rows processed successfully
- [x] All rows have non-empty 'Probleem' field
- [x] All rows have non-empty 'Soort interventie' field
- [x] All rows have non-empty 'Category' field
- [x] Dutch characters (ë, ü, etc.) handled correctly
- [x] UTF-8 BOM handled correctly

## Implementation Guidance

### 1. CSV Parsing Pattern
```python
import csv

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Aggregate problems by product
product_mappings = {}
for row in rows:
    product_name = row["Soort interventie"].strip()
    problem = row["Probleem"].strip()
    category = row["Category"].strip()

    if product_name not in product_mappings:
        product_mappings[product_name] = {
            "problems": [],
            "category": category
        }

    product_mappings[product_name]["problems"].append(problem)
```

### 2. Expected Output Structure
```python
[
    {
        "product_name": "Vroegconsult Arbeidsdeskundige",
        "problems": ["Problem 1", "Problem 2"],
        "category": "Arbeidsinhoud"
    },
    {
        "product_name": "Inzet vertrouwenspersoon",
        "problems": ["Problem 1"],
        "category": "Arbeidsverhoudingen"
    },
    # ... 21 more products
]
```

### 3. Metadata Enrichment
```python
# For fuzzy-matched portal product
portal_product["metadata"] = {
    "problem_mappings": csv_match["problems"],  # Array of problem strings
    "csv_category": csv_match["category"]       # Category string
}
```

## Updated Acceptance Criteria

### AC-004-003: CSV Fuzzy Matching Success Rate
- **Original:** ≥80% (≥27 of 33)
- **Updated:** ≥80% (≥19 of 23) ⚠️
- **Reason:** CSV has 23 unique products, not 33

### AC-004-004: Problem Mapping Enrichment
- **Original:** ≥25 products with problem_mappings
- **Updated:** ≥19 products with problem_mappings ⚠️
- **Reason:** Only 23 unique CSV products available

## Recommendations

1. **Update PRD:** Change all references from "33 products" to "26 rows / 23 unique products"
2. **Update acceptance criteria:** Adjust targets from 27→19 and 25→19
3. **Update architecture.md:** Document many-to-one relationship (3 products with 2+ problems)
4. **Fuzzy matching threshold:** May need to test 0.85 threshold if 0.9 yields <80% match rate

## Next Steps

1. **Spike 2 (Portal):** Scrape actual product count from portal (expect ~60)
2. **Spike 6 (Fuzzy):** Test if 23 CSV products can match ≥19 portal products at 0.9 threshold
3. **Update planning docs:** Correct all "33" references to "26 rows / 23 unique products"

---

**Status:** ✅ COMPLETE
**Blockers:** None
**Critical Update:** CSV has 26 rows / 23 unique products (NOT 33!)
**Ready for:** Spike 6 (Fuzzy Matching Test)
