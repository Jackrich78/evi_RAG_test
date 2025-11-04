#!/usr/bin/env python3
"""
Validate fuzzy matching on FULL 60-product dataset with normalization
Tests if 0.85 threshold + normalization achieves ≥80% match rate
"""

import asyncio
import re
import csv
import sys
import json
from pathlib import Path
from fuzzywuzzy import fuzz

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup


CSV_PATH = project_root / "docs" / "features" / "FEAT-004_product-catalog" / "Intervention_matrix.csv"


def normalize_product_name(name: str) -> str:
    """Normalize product name for fuzzy matching (from Spike 6)."""
    # Remove parentheticals
    name = re.sub(r'\([^)]*\)', '', name)
    # Remove "bv." qualifiers
    name = re.sub(r'\s+bv\..*$', '', name, flags=re.IGNORECASE)
    # Remove spoor indicators
    name = re.sub(r'\s+\d+e\s+spoor', '', name)
    # Normalize whitespace
    name = ' '.join(name.split())
    return name.strip()


def load_csv_products():
    """Load unique product names from CSV."""
    products = set()
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Column name is "Soort interventie" in Intervention_matrix.csv
            product = row.get("Soort interventie") or row.get("Product") or row.get("product")
            if product:
                products.add(product.strip())
    return sorted(products)


async def scrape_all_portal_products():
    """Scrape all 60 portal product names."""
    print("Scraping all portal products...")

    async with AsyncWebCrawler(verbose=False) as crawler:
        # Get listing page
        result = await crawler.arun("https://portal.evi360.nl/products")
        soup = BeautifulSoup(result.html, "html.parser")

        # Extract product URLs
        all_links = soup.find_all("a", href=True)
        product_urls = [
            link['href'] for link in all_links
            if re.match(r'https://portal\.evi360\.nl/products/\d+$', link['href'])
        ]

        print(f"Found {len(product_urls)} portal products")

        # Scrape each product for name
        portal_products = []
        for i, url in enumerate(product_urls, 1):
            try:
                result = await crawler.arun(url)
                product_soup = BeautifulSoup(result.html, "html.parser")
                name_elem = product_soup.find("h1")
                if name_elem:
                    name = name_elem.text.strip()
                    portal_products.append({"name": name, "url": url})
                    print(f"  [{i}/{len(product_urls)}] {name[:50]}...")
                else:
                    print(f"  [{i}/{len(product_urls)}] ⚠️ No name found: {url}")
            except Exception as e:
                print(f"  [{i}/{len(product_urls)}] ❌ Error: {e}")

    return portal_products


def fuzzy_match_with_normalization(csv_products, portal_products, threshold=0.85):
    """
    Fuzzy match CSV products to portal products with normalization.
    Returns matches and unmatched products.
    """
    matches = []
    unmatched = []

    portal_names = [p["name"] for p in portal_products]

    for csv_prod in csv_products:
        # Normalize CSV product name
        csv_norm = normalize_product_name(csv_prod)

        best_match = None
        best_match_url = None
        best_score = 0

        # Compare with all portal products
        for portal in portal_products:
            portal_name = portal["name"]
            portal_norm = normalize_product_name(portal_name)

            # Use token_sort_ratio (best for word order variations)
            score = fuzz.token_sort_ratio(csv_norm, portal_norm) / 100.0

            if score > best_score:
                best_score = score
                best_match = portal_name
                best_match_url = portal["url"]

        # Check if match meets threshold
        if best_score >= threshold:
            matches.append({
                "csv_name": csv_prod,
                "csv_normalized": csv_norm,
                "portal_name": best_match,
                "portal_url": best_match_url,
                "score": best_score,
                "type": "automated"
            })
        else:
            unmatched.append({
                "csv_name": csv_prod,
                "csv_normalized": csv_norm,
                "best_portal_match": best_match,
                "best_score": best_score
            })

    return matches, unmatched


async def main():
    """Run full fuzzy matching validation."""
    print("=" * 80)
    print("FULL FUZZY MATCHING VALIDATION")
    print("=" * 80)
    print(f"\nThreshold: 0.85 (with normalization)")
    print(f"Target: ≥80% (≥19 of 23 CSV products)\n")

    # Load CSV products
    print("Loading CSV products...")
    csv_products = load_csv_products()
    print(f"✅ Loaded {len(csv_products)} unique CSV products\n")

    # Scrape portal products
    portal_products = await scrape_all_portal_products()
    print(f"✅ Scraped {len(portal_products)} portal products\n")

    # Fuzzy match
    print("=" * 80)
    print("FUZZY MATCHING WITH NORMALIZATION")
    print("=" * 80 + "\n")

    matches, unmatched = fuzzy_match_with_normalization(
        csv_products, portal_products, threshold=0.85
    )

    # Print matches
    print(f"✅ MATCHED: {len(matches)}/{len(csv_products)} ({len(matches)/len(csv_products)*100:.1f}%)\n")
    for m in matches:
        print(f"  {m['score']:.2f} | \"{m['csv_name'][:40]}...\" → \"{m['portal_name'][:40]}...\"")

    # Print unmatched
    print(f"\n❌ UNMATCHED: {len(unmatched)}/{len(csv_products)} ({len(unmatched)/len(csv_products)*100:.1f}%)\n")
    for u in unmatched:
        print(f"  {u['best_score']:.2f} | \"{u['csv_name'][:40]}...\" (best: \"{u['best_portal_match'][:40]}...\")")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    match_rate = len(matches) / len(csv_products)
    target_matches = int(len(csv_products) * 0.8)

    print(f"\n📊 Match Rate: {match_rate*100:.1f}% ({len(matches)}/{len(csv_products)})")
    print(f"🎯 Target: ≥80% (≥{target_matches}/{len(csv_products)})")

    if len(matches) >= target_matches:
        print(f"✅ SUCCESS: Target met!")
    else:
        print(f"❌ FAILED: Need {target_matches - len(matches)} more matches")

    print(f"\n📝 Manual mapping needed: {len(unmatched)} products")

    # Save results
    results = {
        "csv_product_count": len(csv_products),
        "portal_product_count": len(portal_products),
        "threshold": 0.85,
        "matched": len(matches),
        "unmatched": len(unmatched),
        "match_rate": match_rate,
        "target_met": len(matches) >= target_matches,
        "matches": matches,
        "unmatched": unmatched
    }

    results_file = Path(__file__).parent / "fuzzy_matching_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved to: {results_file}")

    # Generate manual mapping template
    if unmatched:
        manual_mapping = {u["csv_name"]: u["best_portal_match"] for u in unmatched}
        mapping_file = Path(__file__).parent / "manual_product_mappings_template.json"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(manual_mapping, f, indent=2, ensure_ascii=False)
        print(f"📋 Manual mapping template: {mapping_file}")

    print("\n")

    # Return success
    return len(matches) >= target_matches


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
