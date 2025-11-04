# Spike 6: Fuzzy Matching Test

**Date:** 2025-11-04
**Duration:** 15 minutes
**Status:** ⚠️ Complete with Critical Findings

## Objective
Test fuzzy matching between CSV products (23) and portal products to validate ≥80% match rate assumption.

## Test Data
- **CSV products:** 23 unique products
- **Portal products (sample):** 16 products (10% of full 60)
- **Algorithm:** `fuzz.token_sort_ratio()` (best for word order variations)
- **Threshold:** 0.9 (90% similarity)

## Results ⚠️

### Match Rate: **26% (6/23)** ❌
- **Matched (≥90%):** 6 products
- **Unmatched (<90%):** 17 products
- **Target:** ≥80% (≥19 of 23)
- **Status:** **FAILED** - Far below target!

### Matched Products (6)
1. "Inzet vertrouwenspersoon" → "Inzet vertrouwenspersoon" (1.00)
2. "Vroegconsult Arbeidsdeskundige" → "Vroegconsult Arbeidsdeskundige" (1.00)
3. "Inzet bedrijfsmaatschappelijk werk" → "Inzet bedrijfsmaatschappelijk werk" (1.00)
4. "Werkplekonderzoek op locatie" → "Werkplekonderzoek op locatie" (1.00)
5. "Multidisciplinaire burnout aanpak" → "Multidisciplinaire Burnout Aanpak" (1.00)
6. "Loopbaanbegeleiding" → "Loopbaanbegeleiding" (1.00)

### Near-Misses (85-89%)
- "Arbeidsdeskundig Onderzoek 1e spoor" → "Arbeidsdeskundig Onderzoek" (0.85)

### Problem Cases
- Many CSV products have qualifiers: "bv. gericht op...", "1e spoor", "(Bv. bij...)"
- CSV uses longer descriptive names vs. portal's concise names
- Some CSV products don't exist on portal (e.g., "Verslavingszorg interventie")

## Critical Discovery ⚠️

**THE PRD ASSUMPTION IS WRONG:**
- PRD assumes fuzzy matching will work at ≥80% success rate
- **Reality:** Only 26% match with 0.9 threshold on sample data
- **Root cause:** CSV product names are **descriptive/verbose**, portal names are **concise/marketing**

### Example Mismatches:
```
CSV: "Adviesgesprek P&O Adviseur (Bv. bij een vaststellings-overeenkomst...)"
Portal: "Adviesgesprek P&O Adviseur"
Score: 0.44 (❌ threshold 0.9)

CSV: "Vroegconsult Arbeidsdeskundige bv. gericht op aanpassingen eigen taken"
Portal: "Vroegconsult Arbeidsdeskundige"
Score: 0.61 (❌)

CSV: "Inzet van een mediator"
Portal: "Inzet mediator"
Score: 0.78 (❌)
```

## Revised Strategy Options

### Option A: Lower Threshold to 0.7-0.75 ⚠️
- **Pros:** Will match more products
- **Cons:** Higher false positive risk (wrong matches)
- **Recommendation:** Test with full 60 portal products first

### Option B: Manual Mapping Fallback ✅ RECOMMENDED
- **Approach:**
  1. Run fuzzy matching at 0.85 threshold
  2. Log all unmatched products
  3. Create `manual_product_mappings.json` for edge cases
  4. Combine automated + manual matches

**Example manual_product_mappings.json:**
```json
{
  "Adviesgesprek P&O Adviseur (Bv. bij een vaststellings-overeenkomst...)": "Adviesgesprek P&O Adviseur",
  "Inzet van een mediator": "Inzet mediator",
  "Vroegconsult Arbeidsdeskundige bv. gericht op aanpassingen eigen taken": "Vroegconsult Arbeidsdeskundige"
}
```

### Option C: Normalize Product Names Before Matching ✅ RECOMMENDED
```python
def normalize_for_matching(name):
    # Remove qualifiers and parentheticals
    name = re.sub(r'\(.*?\)', '', name)  # Remove (...)
    name = re.sub(r'bv\..*$', '', name, flags=re.IGNORECASE)  # Remove "bv. ..."
    name = re.sub(r'\d+e spoor', '', name)  # Remove "1e spoor", "2e spoor"
    name = name.strip()
    return name
```

**With normalization:**
- "Arbeidsdeskundig Onderzoek 1e spoor" → "Arbeidsdeskundig Onderzoek" (EXACT MATCH!)

## Updated Acceptance Criteria

### AC-004-003: CSV Fuzzy Matching Success Rate (REVISED)
- **Original:** ≥80% (≥19 of 23) at 0.9 threshold
- **Updated:** ≥80% (≥19 of 23) at **0.85 threshold + normalization + manual fallback**

**New approach:**
1. Normalize both CSV and portal names (remove qualifiers)
2. Use token_sort_ratio at 0.85 threshold
3. Manual mapping for remaining unmatched products
4. Target: ≥19 products enriched (automated + manual)

## Implementation Recommendations

### 1. Normalization Function
```python
import re

def normalize_product_name(name: str) -> str:
    """Normalize product name for fuzzy matching."""
    # Remove parentheticals
    name = re.sub(r'\([^)]*\)', '', name)
    # Remove "bv." qualifiers
    name = re.sub(r'\s+bv\..*$', '', name, flags=re.IGNORECASE)
    # Remove spoor indicators
    name = re.sub(r'\s+\d+e\s+spoor', '', name)
    # Normalize whitespace
    name = ' '.join(name.split())
    return name.strip()
```

### 2. Fuzzy Matching with Fallback
```python
def fuzzy_match_with_fallback(csv_products, portal_products, manual_mappings=None):
    matches = []
    unmatched = []

    for csv_prod in csv_products:
        # Check manual mapping first
        if manual_mappings and csv_prod in manual_mappings:
            portal_match = manual_mappings[csv_prod]
            matches.append((csv_prod, portal_match, 1.0, "manual"))
            continue

        # Normalize names
        csv_norm = normalize_product_name(csv_prod)

        best_match = None
        best_score = 0

        for portal_prod in portal_products:
            portal_norm = normalize_product_name(portal_prod)
            score = fuzz.token_sort_ratio(csv_norm, portal_norm) / 100.0

            if score > best_score:
                best_score = score
                best_match = portal_prod

        # Lower threshold to 0.85 with normalization
        if best_score >= 0.85:
            matches.append((csv_prod, best_match, best_score, "automated"))
        else:
            unmatched.append((csv_prod, best_match, best_score))

    return matches, unmatched
```

### 3. Update PRD and Architecture
- Document that fuzzy matching uses **0.85 threshold + normalization**
- Accept that some products require manual mapping
- Log all unmatched products for review during implementation

## Next Steps

1. **Re-test with full 60 portal products** (not just sample 16)
2. **Implement normalization function** in `ingestion/fuzzy_matcher.py`
3. **Create manual mapping file** for unmatched products
4. **Update AC-004-003** to reflect revised approach

---

**Status:** ⚠️ COMPLETE with CRITICAL FINDINGS
**Blockers:** Fuzzy matching approach needs revision
**Key Finding:** 0.9 threshold is too strict - use 0.85 + normalization + manual fallback
**Ready for:** Implementation with revised strategy
