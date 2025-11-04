# Spike 1: Dependencies Validation

**Date:** 2025-11-04
**Duration:** 15 minutes
**Status:** ✅ Complete

## Objective
Validate and install all required Python dependencies for FEAT-004 portal scraping and fuzzy matching.

## Environment
- **Venv path:** `/Users/builder/dev/evi_rag_test/venv`
- **Python version:** 3.13.5
- **Activation:** `source venv/bin/activate`

## Existing Dependencies (Before Spike)
```
asyncpg==0.30.0
beautifulsoup4==4.12.3
openai==1.90.0 (upgraded to 2.7.1 by crawl4ai)
```

## Required New Dependencies
```
crawl4ai         - JavaScript-capable web scraping
fuzzywuzzy       - Fuzzy string matching (CSV → portal products)
python-Levenshtein - Speedup for fuzzywuzzy
```

## Installation Results

### Installation Command
```bash
source venv/bin/activate
pip3 install crawl4ai fuzzywuzzy python-Levenshtein
```

### Installed Versions
```
crawl4ai==0.7.6
fuzzywuzzy==0.18.0
python-Levenshtein==0.27.3
```

### Additional Dependencies (Auto-installed)
**Core scraping:**
- playwright==1.55.0
- patchright==1.55.2
- lxml==5.4.0
- aiofiles==25.1.0

**Fuzzy matching:**
- rapidfuzz==3.14.3 (Levenshtein speedup)

**HTTP/Network:**
- h2==4.3.0 (HTTP/2 support)
- brotli==1.1.0 (compression)

**AI/LLM:**
- litellm==1.79.1
- tiktoken==0.12.0
- openai upgraded from 1.90.0 → 2.7.1 ⚠️

**NLP:**
- nltk==3.9.2
- snowballstemmer==2.2.0

**Utilities:**
- psutil==7.1.3
- humanize==4.14.0
- joblib==1.5.2

### Import Test Results
```python
from crawl4ai import AsyncWebCrawler  # ✅
from fuzzywuzzy import fuzz            # ✅
from Levenshtein import distance       # ✅
import asyncpg                         # ✅
import openai                          # ✅ (version 2.7.1)
from bs4 import BeautifulSoup          # ✅
```

**Result:** ✅ All imports successful

## Potential Issues Identified

### Issue 1: OpenAI Version Upgrade
- **From:** 1.90.0
- **To:** 2.7.1
- **Cause:** crawl4ai → litellm dependency chain
- **Impact:** May have API changes, need to verify embedding generation still works
- **Mitigation:** Test embedding generation in Spike 7 (E2E)

### Issue 2: Large Dependency Footprint
- **Total new packages:** ~50+ (including transitive dependencies)
- **Notable:** playwright (38.7 MB), patchright (38.7 MB), scipy (20.9 MB)
- **Impact:** Larger venv size, slower cold starts
- **Mitigation:** Acceptable for local development

## Requirements.txt Updates

**Add these to requirements.txt:**
```txt
# FEAT-004: Product Catalog Dependencies
crawl4ai==0.7.6
fuzzywuzzy==0.18.0
python-Levenshtein==0.27.3
```

**Note:** Transitive dependencies will be auto-installed

## Validation Checklist

- [x] crawl4ai installed (version 0.7.6)
- [x] fuzzywuzzy installed (version 0.18.0)
- [x] python-Levenshtein installed (version 0.27.3)
- [x] All imports successful
- [x] No installation errors
- [ ] OpenAI 2.7.1 compatibility verified (deferred to Spike 7)

## Next Steps

1. **Spike 2 (Portal):** Use AsyncWebCrawler to test portal.evi360.nl
2. **Spike 6 (Fuzzy):** Use fuzz.ratio() for CSV matching tests
3. **Spike 7 (E2E):** Verify openai 2.7.1 embedding generation works

## Recommendations for Implementation

1. **Venv activation:** Always use `source venv/bin/activate` (not venv_linux)
2. **Import pattern:**
   ```python
   from crawl4ai import AsyncWebCrawler
   from fuzzywuzzy import fuzz
   ```
3. **Fuzzy matching:** Use `fuzz.ratio()` for 0-100 scale scoring
4. **Playwright install:** May need `playwright install` for browser binaries (test in Spike 2)

---

**Status:** ✅ COMPLETE
**Blockers:** None
**Ready for:** Spike 2 (Portal Reconnaissance)
