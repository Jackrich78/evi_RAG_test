#!/usr/bin/env python3
"""
Spike 3: CSV Structure Validation Script
Validates Intervention_matrix.csv structure and problem-product mappings.
"""

import csv
from collections import Counter
from pathlib import Path

csv_path = Path(__file__).parent.parent / "Intervention_matrix.csv"

print("=" * 60)
print("SPIKE 3: CSV STRUCTURE VALIDATION")
print("=" * 60)

# Parse CSV
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"\n✅ CSV loaded successfully")
print(f"   Path: {csv_path}")
print(f"   Encoding: UTF-8-with-BOM")

# Basic stats
print(f"\n📊 Basic Statistics:")
print(f"   Total rows: {len(rows)}")
print(f"   Columns: {list(rows[0].keys())}")

# Extract products and problems
products = [row["Soort interventie"].strip() for row in rows]
problems = [row["Probleem"].strip() for row in rows]
categories = [row["Category"].strip() for row in rows]

unique_products = list(dict.fromkeys(products))  # Preserve order
unique_categories = set(categories)

print(f"\n🔍 Data Analysis:")
print(f"   Unique products: {len(unique_products)}")
print(f"   Duplicate mappings: {len(products) - len(unique_products)}")
print(f"   Unique categories: {len(unique_categories)}")
print(f"   Categories: {sorted(unique_categories)}")

# Count problem mappings per product
product_counts = Counter(products)
multi_problem_products = {k: v for k, v in product_counts.items() if v > 1}

print(f"\n🔗 Many-to-One Relationships:")
print(f"   Products with multiple problems: {len(multi_problem_products)}")
print(f"   Products with single problem: {len(unique_products) - len(multi_problem_products)}")

# Show aggregation examples
print(f"\n📝 Sample Problem Aggregations:")
for i, (product, count) in enumerate(list(multi_problem_products.items())[:5], 1):
    print(f"\n   {i}. {product} ({count} problems):")
    sample_problems = [row["Probleem"] for row in rows if row["Soort interventie"].strip() == product]
    for j, prob in enumerate(sample_problems, 1):
        print(f"      {j}. {prob[:80]}{'...' if len(prob) > 80 else ''}")

# Show single-problem examples
single_problem_products = [k for k, v in product_counts.items() if v == 1]
print(f"\n📝 Sample Single-Problem Products:")
for i, product in enumerate(single_problem_products[:3], 1):
    problem = [row["Probleem"] for row in rows if row["Soort interventie"].strip() == product][0]
    print(f"   {i}. {product}")
    print(f"      → {problem[:80]}{'...' if len(problem) > 80 else ''}")

# Validate all products
print(f"\n✅ Validation Checks:")
print(f"   All rows have 'Probleem': {all('Probleem' in row and row['Probleem'].strip() for row in rows)}")
print(f"   All rows have 'Soort interventie': {all('Soort interventie' in row and row['Soort interventie'].strip() for row in rows)}")
print(f"   All rows have 'Category': {all('Category' in row and row['Category'].strip() for row in rows)}")
print(f"   No empty product names: {all(prod.strip() for prod in products)}")

# Expected structure for metadata
print(f"\n🎯 Expected Metadata Structure:")
print("""
   product["metadata"] = {
       "problem_mappings": ["Problem 1", "Problem 2", ...],
       "csv_category": "Category name"
   }
""")

# Sample product with aggregated structure
sample_product = list(multi_problem_products.keys())[0]
sample_problems_list = [row["Probleem"] for row in rows if row["Soort interventie"].strip() == sample_product]
sample_category = [row["Category"] for row in rows if row["Soort interventie"].strip() == sample_product][0]

print(f"📦 Example Aggregated Product:")
print(f'   Product name: "{sample_product}"')
print(f'   Category: "{sample_category}"')
print(f'   Problem mappings ({len(sample_problems_list)} total):')
for i, prob in enumerate(sample_problems_list, 1):
    print(f'      {i}. "{prob[:70]}..."')

print(f"\n" + "=" * 60)
print("SPIKE 3 COMPLETE")
print("=" * 60)
