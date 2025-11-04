#!/usr/bin/env python3
"""
Spike 2 Final: Portal Reconnaissance
Complete portal scraping test with correct URL filtering.
"""

import asyncio
import re
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

PORTAL_URL = "https://portal.evi360.nl/products"

async def spike_portal_final():
    print("=" * 70)
    print("SPIKE 2: PORTAL RECONNAISSANCE - FINAL")
    print("=" * 70)

    async with AsyncWebCrawler(verbose=False) as crawler:
        # Step 1: Fetch listing page
        print(f"\n⏳ Step 1: Fetching product listing...")
        result = await crawler.arun(PORTAL_URL)

        if not result.success:
            print(f"❌ FAILED")
            return

        print(f"✅ SUCCESS ({len(result.html)} chars)")

        soup = BeautifulSoup(result.html, "html.parser")
        all_links = soup.find_all("a", href=True)
        all_hrefs = [link['href'] for link in all_links]

        # Step 2: Filter for product detail URLs
        # Pattern: https://portal.evi360.nl/products/\d+ (NOT /products/add/*)
        product_detail_urls = []
        for href in all_hrefs:
            # Match full URLs with numeric ID only
            if re.match(r'https://portal\.evi360\.nl/products/\d+$', href):
                product_detail_urls.append(href)

        # Deduplicate
        product_detail_urls = list(dict.fromkeys(product_detail_urls))

        print(f"\n📊 Step 2: URL Filtering")
        print(f"   Total <a> tags: {len(all_links)}")
        print(f"   Product detail URLs (products/\\d+): {len(product_detail_urls)}")

        if not product_detail_urls:
            print(f"\n❌ No product detail URLs found!")
            return

        # Show samples
        print(f"\n📋 Sample URLs (first 5):")
        for i, url in enumerate(product_detail_urls[:5], 1):
            print(f"   {i}. {url}")

        # Step 3: Test first product page
        test_url = product_detail_urls[0]
        print(f"\n⏳ Step 3: Testing product detail page")
        print(f"   URL: {test_url}")

        product_result = await crawler.arun(test_url)

        if not product_result.success:
            print(f"   ❌ FAILED to fetch")
            return

        print(f"   ✅ SUCCESS ({len(product_result.html)} chars)")

        # Parse product page
        product_soup = BeautifulSoup(product_result.html, "html.parser")

        # Save HTML for manual inspection
        with open("spike_product_final.html", "w", encoding="utf-8") as f:
            f.write(product_result.html)
        print(f"   💾 Saved to spike_product_final.html")

        # Step 4: Test selectors
        print(f"\n🎯 Step 4: Testing Selectors\n")

        # NAME
        print("   NAME:")
        name_tests = [
            ("h1", product_soup.find("h1")),
            ("h1.title", product_soup.select_one("h1.title")),
            ("h1.product-title", product_soup.select_one("h1.product-title")),
            (".page-title", product_soup.select_one(".page-title")),
            ("h2", product_soup.find("h2")),
        ]

        best_name = None
        for selector, elem in name_tests:
            if elem and elem.text.strip():
                text = elem.text.strip()
                # Filter out generic site names
                if text not in ["EVI360", "Products", "Producten"]:
                    status = "✅ GOOD"
                    if not best_name:
                        best_name = (selector, text)
                else:
                    status = "⚠️  GENERIC"
                print(f"      {status} '{selector}': \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
            else:
                print(f"      ❌ NONE '{selector}'")

        # DESCRIPTION
        print("\n   DESCRIPTION:")
        desc_tests = [
            (".description", product_soup.select_one(".description")),
            (".product-description", product_soup.select_one(".product-description")),
            ("article p", product_soup.select_one("article p")),
            (".content p", product_soup.select_one(".content p")),
            ("div.wysiwyg", product_soup.select_one("div.wysiwyg")),
            ("p", product_soup.find("p")),
        ]

        best_desc = None
        for selector, elem in desc_tests:
            if elem and elem.text.strip():
                text = elem.text.strip()
                length = len(text)
                if length > 50:  # Meaningful description
                    status = "✅ GOOD"
                    if not best_desc:
                        best_desc = (selector, text[:200])
                elif length > 10:
                    status = "⚠️  SHORT"
                else:
                    status = "❌ TOO SHORT"
                print(f"      {status} '{selector}': {length} chars - \"{text[:40]}...\"")
            else:
                print(f"      ❌ NONE '{selector}'")

        # PRICE
        print("\n   PRICE:")
        price_tests = [
            (".price", product_soup.select_one(".price")),
            (".product-price", product_soup.select_one(".product-price")),
            ("span.price", product_soup.select_one("span.price")),
            ("[class*='price']", product_soup.select_one("[class*='price']")),
        ]

        best_price = None
        for selector, elem in price_tests:
            if elem and elem.text.strip():
                text = elem.text.strip()
                print(f"      ✅ FOUND '{selector}': \"{text}\"")
                if not best_price:
                    best_price = (selector, text)
            else:
                print(f"      ❌ NONE '{selector}'")

        # CATEGORY
        print("\n   CATEGORY:")
        category_tests = [
            (".category", product_soup.select_one(".category")),
            (".breadcrumb", product_soup.select_one(".breadcrumb")),
            ("nav.breadcrumb a", product_soup.select("nav.breadcrumb a")),
            (".product-category", product_soup.select_one(".product-category")),
        ]

        best_category = None
        for selector, elem in category_tests:
            if selector == "nav.breadcrumb a":  # Multiple elements
                if elem:
                    texts = [e.text.strip() for e in elem]
                    print(f"      ✅ FOUND '{selector}': {texts}")
                    if not best_category and len(texts) > 0:
                        best_category = (selector, texts[-1])  # Last breadcrumb
                else:
                    print(f"      ❌ NONE '{selector}'")
            else:
                if elem and elem.text.strip():
                    text = elem.text.strip()
                    print(f"      ✅ FOUND '{selector}': \"{text[:50]}\"")
                    if not best_category:
                        best_category = (selector, text)
                else:
                    print(f"      ❌ NONE '{selector}'")

        # FINAL RECOMMENDATIONS
        print(f"\n" + "=" * 70)
        print("IMPLEMENTATION SELECTORS")
        print("=" * 70)

        if best_name:
            print(f"✅ NAME: '{best_name[0]}'")
            print(f"   Example: \"{best_name[1][:60]}...\"")
        else:
            print(f"❌ NAME: NO SUITABLE SELECTOR - MANUAL INSPECTION REQUIRED")

        if best_desc:
            print(f"\n✅ DESCRIPTION: '{best_desc[0]}'")
            print(f"   Example: \"{best_desc[1][:60]}...\"")
        else:
            print(f"\n❌ DESCRIPTION: NO SUITABLE SELECTOR - MANUAL INSPECTION REQUIRED")

        if best_price:
            print(f"\n✅ PRICE: '{best_price[0]}'")
            print(f"   Example: \"{best_price[1]}\"")
        else:
            print(f"\n⚠️  PRICE: Not found (may be optional field)")

        if best_category:
            print(f"\n✅ CATEGORY: '{best_category[0]}'")
            print(f"   Example: \"{best_category[1][:50]}\"")
        else:
            print(f"\n⚠️  CATEGORY: Not found (may be optional field)")

        print(f"\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"✅ Total products found: ~{len(product_detail_urls)}")
        print(f"✅ Portal publicly accessible: YES")
        print(f"✅ JavaScript rendering: YES (Crawl4AI handles it)")
        print(f"✅ Sample HTML saved: spike_product_final.html")
        print(f"\n⚠️  ACTION REQUIRED:")
        print(f"   1. Manually inspect spike_product_final.html")
        print(f"   2. Verify selectors work on multiple products")
        print(f"   3. Document in 02_portal_reconnaissance.md")

if __name__ == "__main__":
    asyncio.run(spike_portal_final())
