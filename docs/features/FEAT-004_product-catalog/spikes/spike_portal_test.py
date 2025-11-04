#!/usr/bin/env python3
"""
Spike 2: Portal Reconnaissance Script
Tests Crawl4AI on portal.evi360.nl and documents actual HTML selectors.
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import sys

PORTAL_URL = "https://portal.evi360.nl/products"

async def inspect_portal():
    print("=" * 70)
    print("SPIKE 2: PORTAL RECONNAISSANCE")
    print("=" * 70)

    try:
        print(f"\n🔍 Testing Crawl4AI on: {PORTAL_URL}")

        async with AsyncWebCrawler(verbose=False) as crawler:
            # Test product listing page
            print("\n⏳ Fetching product listing page...")
            result = await crawler.arun(PORTAL_URL)

            if not result.success:
                print(f"❌ ERROR: Failed to fetch portal")
                print(f"   Status: {result.status_code}")
                print(f"   Error: {result.error_message}")
                return

            print(f"✅ Portal fetch successful")
            print(f"   HTML length: {len(result.html)} chars")
            print(f"   Status code: {result.status_code if hasattr(result, 'status_code') else 'N/A'}")

            # Parse HTML
            soup = BeautifulSoup(result.html, "html.parser")

            # Find main content
            main_elements = soup.select("main")
            print(f"\n📄 Page Structure:")
            print(f"   Found {len(main_elements)} <main> elements")

            # Find product links (try multiple patterns)
            patterns = [
                "a[href*='/products/']",
                "a[href*='product']",
                ".product-card a",
                ".product-item a",
                "article a",
                "div[class*='product'] a"
            ]

            print(f"\n🔗 Searching for product links (trying {len(patterns)} patterns)...")
            all_links = []

            for pattern in patterns:
                links = soup.select(pattern)
                if links:
                    print(f"   ✅ Pattern '{pattern}': {len(links)} links found")
                    all_links.extend(links)
                else:
                    print(f"   ❌ Pattern '{pattern}': No links")

            # Deduplicate links
            unique_hrefs = list(dict.fromkeys([link.get('href') for link in all_links if link.get('href')]))
            print(f"\n   Total unique product URLs: {len(unique_hrefs)}")

            if not unique_hrefs:
                print("\n⚠️  WARNING: No product links found!")
                print("   This could mean:")
                print("   1. Portal requires authentication")
                print("   2. Products are loaded via JavaScript after page load")
                print("   3. URL structure is different")
                print("\n   Saving HTML to spike_portal_output.html for manual inspection...")
                with open("spike_portal_output.html", "w", encoding="utf-8") as f:
                    f.write(result.html)
                return

            # Show first 5 product URLs
            print(f"\n📋 Sample Product URLs:")
            for i, href in enumerate(unique_hrefs[:5], 1):
                # Make absolute URL if needed
                if href.startswith('/'):
                    full_url = f"https://portal.evi360.nl{href}"
                elif not href.startswith('http'):
                    full_url = f"https://portal.evi360.nl/{href}"
                else:
                    full_url = href

                # Get link text
                link_element = [l for l in all_links if l.get('href') == href][0]
                link_text = link_element.text.strip()[:50]
                print(f"   {i}. {full_url}")
                print(f"      Text: \"{link_text}{'...' if len(link_element.text.strip()) > 50 else ''}\"")

            # Test clicking into first product
            if unique_hrefs:
                print(f"\n⏳ Testing product detail page extraction...")
                first_href = unique_hrefs[0]

                # Make absolute URL
                if first_href.startswith('/'):
                    product_url = f"https://portal.evi360.nl{first_href}"
                elif not first_href.startswith('http'):
                    product_url = f"https://portal.evi360.nl/{first_href}"
                else:
                    product_url = first_href

                print(f"   URL: {product_url}")

                product_result = await crawler.arun(product_url)

                if not product_result.success:
                    print(f"   ❌ Failed to fetch product page")
                    return

                print(f"   ✅ Product page fetched ({len(product_result.html)} chars)")

                # Parse product page
                product_soup = BeautifulSoup(product_result.html, "html.parser")

                # Test PRD selectors
                prd_selectors = {
                    "name": ["h1.product-title", "h1", "title", ".product-name"],
                    "description": [".product-description", ".description", "p", "article p"],
                    "price": [".product-price", ".price", "[class*='price']"],
                    "category": [".product-category", ".category", "[class*='category']"]
                }

                print(f"\n🎯 Testing Selectors on Sample Product:")
                found_selectors = {}

                for field, selectors in prd_selectors.items():
                    print(f"\n   {field.upper()}:")
                    found = False
                    for selector in selectors:
                        element = product_soup.select_one(selector)
                        if element:
                            content = element.text.strip()[:100]
                            print(f"      ✅ Selector '{selector}' FOUND")
                            print(f"         Content: \"{content}{'...' if len(element.text.strip()) > 100 else ''}\"")
                            if not found:  # Record first working selector
                                found_selectors[field] = selector
                            found = True
                        else:
                            print(f"      ❌ Selector '{selector}' NOT FOUND")

                    if not found:
                        print(f"      ⚠️  No working selector found for {field}")

                # Summary
                print(f"\n" + "=" * 70)
                print(f"SELECTOR SUMMARY (Use these in implementation!)")
                print("=" * 70)
                for field, selector in found_selectors.items():
                    print(f"   {field}: '{selector}'")

                # Save sample product HTML for manual inspection
                print(f"\n💾 Saving sample product HTML to spike_product_sample.html...")
                with open("spike_product_sample.html", "w", encoding="utf-8") as f:
                    f.write(product_result.html)

                print(f"\n✅ SPIKE 2 COMPLETE")
                print(f"\nRECOMMENDATION:")
                print(f"   - Use selectors from SELECTOR SUMMARY above")
                print(f"   - Total products: ~{len(unique_hrefs)}")
                print(f"   - Portal is publicly accessible (no auth required)")

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print(f"\n   This could indicate:")
        print(f"   1. Network connectivity issue")
        print(f"   2. Portal is down or blocking automated access")
        print(f"   3. Crawl4AI configuration issue")
        import traceback
        print(f"\n   Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("\nℹ️  This spike will:")
    print("   1. Test Crawl4AI on portal.evi360.nl")
    print("   2. Extract product listing URLs")
    print("   3. Test selectors on a sample product page")
    print("   4. Document actual selectors for implementation\n")

    asyncio.run(inspect_portal())
