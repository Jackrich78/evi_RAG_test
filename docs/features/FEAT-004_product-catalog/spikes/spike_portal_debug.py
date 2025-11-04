#!/usr/bin/env python3
"""Debug script to inspect actual URL patterns from portal"""

import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

async def debug_urls():
    print("Debugging portal URL structure...")

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun("https://portal.evi360.nl/products")

        soup = BeautifulSoup(result.html, "html.parser")
        all_links = soup.find_all("a", href=True)

        # Get all unique hrefs
        all_hrefs = list(dict.fromkeys([link['href'] for link in all_links]))

        # Filter for product-related URLs
        product_hrefs = [h for h in all_hrefs if 'product' in h.lower()]

        print(f"\nTotal links: {len(all_hrefs)}")
        print(f"Product-related: {len(product_hrefs)}")
        print(f"\nFirst 20 product URLs:")
        for i, href in enumerate(product_hrefs[:20], 1):
            print(f"   {i}. {href}")

asyncio.run(debug_urls())
