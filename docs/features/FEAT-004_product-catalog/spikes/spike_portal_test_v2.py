#!/usr/bin/env python3
"""
Spike 2 V2: Portal Reconnaissance - Fixed URL filtering
Filters out /products/add/* URLs and tests actual product detail pages.
"""

import asyncio
import re
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

PORTAL_URL = "https://portal.evi360.nl/products"

async def inspect_portal_v2():
    print("=" * 70)
    print("SPIKE 2 V2: PORTAL RECONNAISSANCE (FIXED)")
    print("=" * 70)

    async with AsyncWebCrawler(verbose=False) as crawler:
        # Fetch listing page
        print(f"\n⏳ Fetching product listing...")
        result = await crawler.arun(PORTAL_URL)

        if not result.success:
            print(f"❌ Failed to fetch portal")
            return

        print(f"✅ Listing fetched ({len(result.html)} chars)")

        soup = BeautifulSoup(result.html, "html.parser")

        # Find all product links
        all_links = soup.select("a[href*='/products/']")
        all_hrefs = [link.get('href') for link in all_links if link.get('href')]

        # Filter: only /products/\d+ (exclude /products/add/*)
        product_detail_pattern = re.compile(r'^/products/\d+$')
        detail_urls = list(dict.fromkeys([
            href for href in all_hrefs
            if product_detail_pattern.match(href)
        ]))

        print(f"\n📊 URL Analysis:")
        print(f"   Total links with '/products/': {len(all_hrefs)}")
        print(f"   Filtered detail URLs (/products/\d+): {len(detail_urls)}")
        print(f"   Filtered out (add to cart, etc): {len(all_hrefs) - len(detail_urls)}")

        if not detail_urls:
            print("\n❌ No product detail URLs found!")
            return

        # Show first 5
        print(f"\n📋 Sample Product Detail URLs:")
        for i, href in enumerate(detail_urls[:5], 1):
            print(f"   {i}. https://portal.evi360.nl{href}")

        # Test first product detail page
        test_url = f"https://portal.evi360.nl{detail_urls[0]}"
        print(f"\n⏳ Testing product detail page: {test_url}")

        product_result = await crawler.arun(test_url)

        if not product_result.success:
            print(f"❌ Failed to fetch product")
            return

        print(f"✅ Product fetched ({len(product_result.html)} chars)")

        # Parse and extract
        product_soup = BeautifulSoup(product_result.html, "html.parser")

        # Save for inspection
        with open("spike_product_detail.html", "w", encoding="utf-8") as f:
            f.write(product_result.html)

        # Try multiple selector strategies
        print(f"\n🎯 Testing Selectors:")

        # Name selectors
        name_selectors = [
            ("h1", product_soup.find("h1")),
            ("h2", product_soup.find("h2")),
            (".product-title", product_soup.select_one(".product-title")),
            ("title", product_soup.find("title")),
            (".page-header h1", product_soup.select_one(".page-header h1")),
            (".content h1", product_soup.select_one(".content h1"))
        ]

        print(f"\n   NAME:")
        found_name = None
        for selector, element in name_selectors:
            if element and element.text.strip() and element.text.strip() != "EVI360":
                content = element.text.strip()[:80]
                print(f"      ✅ '{selector}': \"{content}\"")
                if not found_name:
                    found_name = (selector, element.text.strip())
            else:
                print(f"      ❌ '{selector}'")

        # Description selectors
        desc_selectors = [
            (".product-description", product_soup.select_one(".product-description")),
            (".description", product_soup.select_one(".description")),
            (".content p", product_soup.select_one(".content p")),
            ("article", product_soup.find("article")),
            (".page-content", product_soup.select_one(".page-content"))
        ]

        print(f"\n   DESCRIPTION:")
        found_desc = None
        for selector, element in desc_selectors:
            if element:
                content = element.text.strip()[:80]
                if len(content) > 20:  # Meaningful description
                    print(f"      ✅ '{selector}': \"{content}...\"")
                    if not found_desc:
                        found_desc = (selector, element.text.strip()[:200])
                else:
                    print(f"      ⚠️  '{selector}': Too short ({len(content)} chars)")
            else:
                print(f"      ❌ '{selector}'")

        # Price selectors
        price_selectors = [
            (".price", product_soup.select_one(".price")),
            (".product-price", product_soup.select_one(".product-price")),
            ("[class*='price']", product_soup.select_one("[class*='price']")),
            ("span.price", product_soup.select_one("span.price"))
        ]

        print(f"\n   PRICE:")
        found_price = None
        for selector, element in price_selectors:
            if element:
                content = element.text.strip()
                print(f"      ✅ '{selector}': \"{content}\"")
                if not found_price:
                    found_price = (selector, element.text.strip())
            else:
                print(f"      ❌ '{selector}'")

        # Category selectors
        category_selectors = [
            (".category", product_soup.select_one(".category")),
            (".product-category", product_soup.select_one(".product-category")),
            (".breadcrumb", product_soup.select_one(".breadcrumb")),
            ("nav.breadcrumb", product_soup.select_one("nav.breadcrumb"))
        ]

        print(f"\n   CATEGORY:")
        found_category = None
        for selector, element in category_selectors:
            if element:
                content = element.text.strip()[:50]
                print(f"      ✅ '{selector}': \"{content}\"")
                if not found_category:
                    found_category = (selector, element.text.strip())
            else:
                print(f"      ❌ '{selector}'")

        # Summary
        print(f"\n" + "=" * 70)
        print(f"FINAL SELECTOR RECOMMENDATIONS")
        print("=" * 70)
        if found_name:
            print(f"   ✅ Name: '{found_name[0]}' → \"{found_name[1][:60]}...\"")
        else:
            print(f"   ❌ Name: NO SUITABLE SELECTOR FOUND")

        if found_desc:
            print(f"   ✅ Description: '{found_desc[0]}' → \"{found_desc[1][:60]}...\"")
        else:
            print(f"   ❌ Description: NO SUITABLE SELECTOR FOUND")

        if found_price:
            print(f"   ✅ Price: '{found_price[0]}' → \"{found_price[1]}\"")
        else:
            print(f"   ⚠️  Price: NO SELECTOR (May not be on product pages)")

        if found_category:
            print(f"   ✅ Category: '{found_category[0]}' → \"{found_category[1][:50]}...\"")
        else:
            print(f"   ⚠️  Category: NO SELECTOR (May not be on product pages)")

        print(f"\n📊 Summary:")
        print(f"   Total product detail pages: ~{len(detail_urls)}")
        print(f"   Authentication required: NO")
        print(f"   JavaScript rendering: YES (Crawl4AI handles it)")
        print(f"\n💾 Saved sample HTML to: spike_product_detail.html")
        print(f"\n✅ SPIKE 2 V2 COMPLETE")

if __name__ == "__main__":
    asyncio.run(inspect_portal_v2())
