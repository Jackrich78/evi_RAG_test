#!/usr/bin/env python3
"""
Validate portal selectors on 5 different products
Tests if h1, p, .product-price selectors work reliably across different product types
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup


# Test 5 different product IDs (spread across different categories based on spike findings)
TEST_PRODUCTS = [
    24,  # Arbeidsdeskundig Onderzoek (tested in spike)
    7,   # Different product
    33,  # Different product
    50,  # Different product
    55,  # Different product
]


async def test_selector_on_product(crawler, product_id: int):
    """Test selectors on a single product"""
    url = f"https://portal.evi360.nl/products/{product_id}"

    try:
        result = await crawler.arun(url)
        soup = BeautifulSoup(result.html, "html.parser")

        # Test selectors
        name_elem = soup.find("h1")
        price_elem = soup.select_one(".product-price")

        # Description: Try multiple strategies
        # Strategy 1: Look for div.platform-product-description (product-specific content)
        desc_container = soup.select_one("div.platform-product-description")
        if desc_container:
            # Get all paragraphs inside the product description div
            paragraphs = desc_container.find_all("p")
            # Filter out empty paragraphs and join
            desc_texts = [p.text.strip() for p in paragraphs if p.text.strip()]
            description = " ".join(desc_texts) if desc_texts else None
        else:
            # Fallback to first <p>
            desc_elem = soup.find("p")
            description = desc_elem.text.strip() if desc_elem else None

        # Extract values
        name = name_elem.text.strip() if name_elem else None
        price = price_elem.text.strip() if price_elem else None

        # Validate
        success = True
        issues = []

        if not name:
            success = False
            issues.append("❌ NAME MISSING (h1 selector failed)")
        else:
            print(f"  ✅ Name: {name[:60]}...")

        if not description:
            success = False
            issues.append("❌ DESCRIPTION MISSING (p selector failed)")
        elif len(description) < 50:
            issues.append(f"⚠️ DESCRIPTION TOO SHORT ({len(description)} chars) - may be wrong element")
        else:
            print(f"  ✅ Description: {description[:60]}... ({len(description)} chars)")

        if not price:
            print(f"  ⚠️ Price: None (acceptable per AC-004-103)")
        else:
            print(f"  ✅ Price: {price}")

        return {
            "product_id": product_id,
            "url": url,
            "success": success,
            "name": name,
            "description": description,
            "description_length": len(description) if description else 0,
            "price": price,
            "issues": issues
        }

    except Exception as e:
        return {
            "product_id": product_id,
            "url": url,
            "success": False,
            "name": None,
            "description": None,
            "description_length": 0,
            "price": None,
            "issues": [f"❌ EXCEPTION: {str(e)}"]
        }


async def main():
    """Test selectors on 5 products"""
    print("=" * 80)
    print("SELECTOR VALIDATION TEST")
    print("=" * 80)
    print(f"\nTesting selectors on {len(TEST_PRODUCTS)} products...")
    print(f"Selectors: h1 (name), p (description), .product-price (price)\n")

    results = []

    async with AsyncWebCrawler(verbose=False) as crawler:
        for product_id in TEST_PRODUCTS:
            print(f"\n[Product {product_id}] https://portal.evi360.nl/products/{product_id}")
            result = await test_selector_on_product(crawler, product_id)
            results.append(result)

            # Print issues if any
            if result["issues"]:
                for issue in result["issues"]:
                    print(f"  {issue}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    successful = sum(1 for r in results if r["success"])

    print(f"\n✅ Successful: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"❌ Failed: {total - successful}/{total}")

    # Description length analysis
    desc_lengths = [r["description_length"] for r in results if r["description_length"] > 0]
    if desc_lengths:
        avg_length = sum(desc_lengths) / len(desc_lengths)
        min_length = min(desc_lengths)
        max_length = max(desc_lengths)
        print(f"\n📝 Description lengths: min={min_length}, max={max_length}, avg={avg_length:.0f}")

    # Failed products
    failed = [r for r in results if not r["success"]]
    if failed:
        print("\n⚠️ FAILED PRODUCTS:")
        for r in failed:
            print(f"  - Product {r['product_id']}: {', '.join(r['issues'])}")

    # Products with short descriptions
    short_desc = [r for r in results if r["description_length"] > 0 and r["description_length"] < 50]
    if short_desc:
        print("\n⚠️ PRODUCTS WITH SHORT DESCRIPTIONS (<50 chars):")
        for r in short_desc:
            print(f"  - Product {r['product_id']}: {r['description_length']} chars - \"{r['description'][:50]}\"")

    # Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    if successful == total and not short_desc:
        print("✅ ALL SELECTORS WORKING RELIABLY")
        print("✅ Ready to proceed with implementation")
    elif successful == total:
        print("⚠️ SELECTORS WORK BUT SOME DESCRIPTIONS ARE SHORT")
        print("→ Add validation: description length >50 chars")
        print("→ Fallback: use product name as description if <50 chars")
    else:
        print("❌ SELECTORS NOT RELIABLE")
        print("→ Must fix selectors before implementation")

    print("\n")

    # Return success rate for automation
    return successful / total


if __name__ == "__main__":
    success_rate = asyncio.run(main())
    sys.exit(0 if success_rate >= 0.8 else 1)  # 80% threshold for pass
