"""Example: Load and explore the Scandium Dataset."""
import json
from collections import Counter

# Load the full dataset
with open("dataset/entries_final_v3.json") as f:
    entries = json.load(f)

print(f"Loaded {len(entries):,} entries")

# Quick statistics
tiers = Counter(e.get("tier", "unknown") for e in entries)
sources = Counter(e.get("source", "unknown") for e in entries)
formulas = len(set(e.get("formula", "") for e in entries))

print(f"\nStatistics:")
print(f"  Sources: {dict(sources)}")
print(f"  Tiers: {dict(tiers)}")
print(f"  Unique formulas: {formulas:,}")
print(f"  Families: {len(set(f for e in entries for f in e.get('families', [])))}")

# Sample entries
print(f"\nSample entries:")
for i in range(3):
    e = entries[i]
    print(f"  {e['formula']:20s} | source={e['source']:6s} | "
          f"FE={e.get('formation_energy_per_atom', 0):.3f} | "
          f"tier={e.get('tier', '?')}")
