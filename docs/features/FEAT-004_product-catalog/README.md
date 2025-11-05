# FEAT-004: Product Catalog with Interventie Wijzer Integration

**Status:** 🚧 PHASE 1 COMPLETE - Ready for Phase 2
**Planning Complete:** 2025-11-05
**Spike Validation:** 2025-11-04
**Phase 1 Complete:** 2025-11-05 (Portal Scraping ✅)

---

## 📋 Documentation Index

Start here for implementation:

### Primary Documents
1. **[PHASE_1_COMPLETE.md](./PHASE_1_COMPLETE.md)** ⭐ **READ FIRST FOR PHASE 2**
   - Phase 1 completion summary (portal scraping)
   - Key learnings and discoveries (60 products, not 76)
   - Ready for Phase 2 handoff

2. **[IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)** - Full Implementation Plan
   - Complete 4-phase implementation plan
   - Step-by-step instructions with code examples
   - Validation steps and troubleshooting
   - Time estimates: 6-10 hours total

2. **[prd.md](./prd.md)** - Product Requirements
   - Feature scope and goals
   - Success metrics (76 products, 83% match rate)
   - Architecture decisions

3. **[acceptance.md](./acceptance.md)** - Acceptance Criteria
   - 13 functional criteria
   - 5 edge cases
   - 3 non-functional requirements
   - Pass/fail validation steps

4. **[architecture.md](./architecture.md)** - Technical Design
   - System architecture diagrams
   - Validated selectors (h1, div.platform-product-description p, .product-price)
   - Fuzzy matching strategy with normalization
   - Data flow (4 phases)

5. **[testing.md](./testing.md)** - Test Strategy
   - 18 unit tests (stubs in tests/unit/)
   - 6 integration tests (stubs in tests/integration/)
   - 10 manual test queries

### Supporting Files

- **[manual-test.md](./manual-test.md)** - 10 Dutch test queries for manual validation
- **[research.md](./research.md)** - Background research and alternatives considered
- **[SPIKE_FINDINGS_UPDATE.md](./SPIKE_FINDINGS_UPDATE.md)** - Spike execution summary

### Data Files

- **[manual_product_mappings.json](./manual_product_mappings.json)** - 10 validated manual product mappings
- **[unresolved_products.json](./unresolved_products.json)** - 4 products requiring stakeholder review
- **[Intervention_matrix.csv](./Intervention_matrix.csv)** - Source CSV (26 rows, 23 unique products)

### Spike Validation (Reference Only)

- **[spikes/VALIDATION_SUMMARY.md](./spikes/VALIDATION_SUMMARY.md)** - Complete validation report
- **[spikes/](./spikes/)** - 7 spike investigations (all complete)

---

## ✅ Pre-Implementation Checklist

Before starting implementation, verify:

- [ ] Docker services running (`docker-compose up -d`)
- [ ] Database migration 004 applied (products table has `price` column)
- [ ] `.env` configured with `EMBEDDING_MODEL=text-embedding-3-small`
- [ ] Manual mapping files exist (`manual_product_mappings.json`, `unresolved_products.json`)
- [ ] Test stub files exist in `tests/unit/` and `tests/integration/`
- [ ] Read IMPLEMENTATION_GUIDE.md Phase 0 completely

---

## 🎯 Key Validated Numbers

**UPDATED AFTER PHASE 1 SCRAPING:**

| Metric | Validated Value | Old (Planning) Value |
|--------|----------------|----------------------|
| Portal Products | **60** ✅ | 76 (overestimated) |
| CSV Rows | **26** | 33 |
| CSV Unique Products | **23** | 33 |
| Fuzzy Threshold | **0.85** with normalization | ≥0.9 |
| Automated Match Rate | **39%** (9/23) | 80% expected |
| Manual Match Rate | **43%** (10/23) | N/A |
| Total Match Rate | **83%** (19/23) | ≥80% target |
| Unresolved | **4** products | N/A |

---

## 🔧 Implementation Phases

**Updated Time Estimates:**

1. ✅ **Phase 0: Setup** (15 min) - COMPLETE
2. ✅ **Phase 1: Portal Scraping** (15 min actual, 2-3 hrs estimated) - COMPLETE
   - 60 products scraped and inserted
   - 5 unit tests passing
   - Descriptions validated (245-4556 chars)
3. 🔄 **Phase 2: CSV + Fuzzy Match** (1-2 hrs) - **NEXT**
   - Parse CSV (26 rows → 23 unique)
   - Fuzzy match (0.85 threshold + manual mappings)
   - Enrich DB with problem_mappings
4. ⏳ **Phase 3: Embeddings** (30-60 min) - Pending
5. ⏳ **Phase 4: Agent Integration** (1-2 hrs) - Pending

**See PHASE_1_COMPLETE.md for handoff to Phase 2.**

---

## 🚨 Critical Information

### Validated Selectors (DO NOT CHANGE)
```python
# Name
name = soup.select_one("h1").text.strip()

# Description (CRITICAL: use container!)
desc_container = soup.select_one("div.platform-product-description")
paragraphs = desc_container.find_all("p") if desc_container else []
description = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])

# Price (optional)
price_elem = soup.select_one(".product-price")
price = price_elem.text.strip() if price_elem else None
```

### Fuzzy Matching Strategy (Validated)
- **Threshold:** 0.85 (not 0.9 - too strict)
- **Normalization:** lowercase + remove special chars
- **Manual Fallback:** Load `manual_product_mappings.json` (10 products)
- **Unresolved Tracking:** Write to `unresolved_products.json` (4 products)

### Agent Integration
- **Remove restriction:** Line 51 in `agent/specialist_agent.py`
- **Add tool:** `search_products_tool` to agent tools list
- **Update prompt:** Add product recommendation instructions

---

## 📊 Success Criteria

Implementation complete when:
- ✅ 76 products scraped from portal
- ✅ ≥19 products enriched with problem mappings (83% match rate)
- ✅ 100% embedding coverage
- ✅ Agent can search and recommend products
- ✅ All tests passing (18 unit + 6 integration)
- ✅ Manual testing ≥70% relevance (7/10 queries)

---

## 🆘 Troubleshooting

**Issue:** Only getting generic 147-char descriptions  
**Fix:** Use `div.platform-product-description p` selector (not just `p`)

**Issue:** Fuzzy matching <80%  
**Fix:** Check `manual_product_mappings.json` loaded correctly

**Issue:** Agent not calling search_products()  
**Fix:** Verify tool registered and restriction removed from specialist_agent.py:51

**Full troubleshooting guide:** See IMPLEMENTATION_GUIDE.md

---

## 📝 Next Steps

1. **Read:** IMPLEMENTATION_GUIDE.md from top to bottom
2. **Setup:** Run Phase 0 checklist
3. **Implement:** Execute Phases 1-4 sequentially
4. **Test:** Run tests after each phase
5. **Complete:** Update CHANGELOG.md and mark PRD as complete

**Good luck! Everything is ready for you.** 🚀
