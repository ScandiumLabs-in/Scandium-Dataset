"""Example: Filter entries by tier and family."""
import json
from collections import Counter

with open("dataset/entries_final_v3.json") as f:
    entries = json.load(f)

# Filter by tier
gold = [e for e in entries if e.get("tier") == "gold"]
strict_gold = [e for e in entries
               if e.get("strict_gold", {}).get("is_strict_gold", False)]
validated = [e for e in entries if e.get("tier") == "validated"]

print(f"Gold:        {len(gold):>8,}")
print(f"Strict Gold: {len(strict_gold):>8,}")
print(f"Validated:   {len(validated):>8,}")

# Filter by battery family
battery_families = {"layered_oxide", "sulfide_sse", "halide_sse",
                    "polyanion", "nasicon", "garnet", "borohydride"}
battery = [e for e in entries
           if set(e.get("families", [])) & battery_families]

print(f"\nBattery subset: {len(battery):,}")

# Filter by source
for src in ["mp", "oqmd", "jarvis"]:
    subset = [e for e in entries if e.get("source") == src]
    print(f"  {src}: {len(subset):,} entries")

# Combine filters
battery_gold = [e for e in gold
                if set(e.get("families", [])) & battery_families]
print(f"\nBattery + Gold: {len(battery_gold):,}")

# Quality score distribution
scores = Counter()
for e in gold:
    scores[(e.get("quality_score", 0) // 10) * 10] += 1
print(f"\nGold quality score distribution:")
for k in sorted(scores.keys()):
    print(f"  {k}-{k+9}: {scores[k]:,}")
