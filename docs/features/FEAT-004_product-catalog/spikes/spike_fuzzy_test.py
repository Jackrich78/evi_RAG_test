#!/usr/bin/env python3
"""
Spike 6: Fuzzy Matching Test
Tests fuzzywuzzy matching between CSV products (23) and portal products (60).
"""

from fuzzywuzzy import fuzz
import csv
from pathlib import Path

# CSV products (from Spike 3)
csv_path = Path(__file__).parent.parent / "Intervention_matrix.csv"

# Sample portal product names (from Spike 2 + realistic extrapolation)
portal_products = [
    "Arbeidsdeskundig Onderzoek",
    "Herstelcoaching (6-9 maanden)",
    "Multidisciplinaire Burnout Aanpak",
    "Bedrijfsfysiotherapie",
    "Vroegconsult Arbeidsdeskundige",
    "Inzet bedrijfsmaatschappelijk werk",
    "Werkplekonderzoek op locatie",
    "Adviesgesprek P&O Adviseur",
    "Inzet vertrouwenspersoon",
    "Mediation",
    "Inzet mediator",
    "Re-integratietraject",
    "Loopbaanbegeleiding",
    "Coaching",
    "Leefstijlprogramma",
    "Psychologische ondersteuning",
]

print("=" * 70)
print("SPIKE 6: FUZZY MATCHING TEST")
print("=" * 70)

# Parse CSV
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Extract unique CSV products
csv_products = list(dict.fromkeys([row["Soort interventie"].strip() for row in rows]))

print(f"\n📊 Data Overview:")
print(f"   CSV products: {len(csv_products)}")
print(f"   Portal products (sample): {len(portal_products)}")

def normalize(text):
    """Normalize product name for matching."""
    return text.lower().strip()

print(f"\n🔍 Testing Fuzzy Matching (threshold ≥ 0.9 = 90%):\n")

matches = []
unmatched = []

for csv_prod in csv_products:
    csv_norm = normalize(csv_prod)
    best_match = None
    best_score = 0

    for portal_prod in portal_products:
        portal_norm = normalize(portal_prod)

        # Test different fuzzy algorithms
        ratio_score = fuzz.ratio(csv_norm, portal_norm) / 100.0
        partial_score = fuzz.partial_ratio(csv_norm, portal_norm) / 100.0
        token_sort_score = fuzz.token_sort_ratio(csv_norm, portal_norm) / 100.0

        # Use token_sort_ratio (best for word order variations)
        score = token_sort_score

        if score > best_score:
            best_score = score
            best_match = portal_prod

    status = "✅ MATCH" if best_score >= 0.9 else "❌ NO MATCH"
    print(f"{status} {best_score:.2f} | {csv_prod}")
    print(f"         → {best_match}\n")

    if best_score >= 0.9:
        matches.append((csv_prod, best_match, best_score))
    else:
        unmatched.append((csv_prod, best_match, best_score))

print("=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)
print(f"✅ Matched (≥90%): {len(matches)}/{len(csv_products)} ({len(matches)/len(csv_products)*100:.0f}%)")
print(f"❌ Unmatched (<90%): {len(unmatched)}/{len(csv_products)} ({len(unmatched)/len(csv_products)*100:.0f}%)")

if unmatched:
    print(f"\n⚠️  Unmatched Products:")
    for csv_prod, best_match, score in unmatched:
        print(f"   {csv_prod[:50]} (best: {score:.2f} → {best_match[:40]})")

print(f"\n💡 Recommendation:")
if len(matches) / len(csv_products) >= 0.8:
    print(f"   ✅ Threshold 0.9 achieves ≥80% match rate - USE IT")
else:
    print(f"   ⚠️  Try threshold 0.85 or use token_sort_ratio algorithm")

print(f"\n📝 Note:")
print(f"   This uses SAMPLE portal products. Actual portal has 60 products.")
print(f"   Re-run with full portal data after scraping for final validation.")
