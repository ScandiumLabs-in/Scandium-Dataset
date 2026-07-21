"""Example: Compute per-family and per-source statistics."""
import json
import numpy as np
from collections import Counter

with open("dataset/entries_final_v3.json") as f:
    entries = json.load(f)

# Per-family statistics
families = Counter(f for e in entries for f in e.get("families", ["unknown"]))
print("Family Distribution:")
for fam, count in families.most_common():
    pct = 100 * count / len(entries)
    print(f"  {fam:25s}: {count:>7,} ({pct:.1f}%)")

# Per-source FE distribution
print("\nFE Distribution by Source:")
for src in ["mp", "oqmd", "jarvis"]:
    subset = [e for e in entries if e.get("source") == src]
    fe_vals = [e.get("formation_energy_per_atom", 0) for e in subset
               if e.get("formation_energy_per_atom") is not None]
    print(f"  {src:8s}: mean={np.mean(fe_vals):.3f}  "
          f"median={np.median(fe_vals):.3f}  "
          f"std={np.std(fe_vals):.3f}  "
          f"N={len(fe_vals):,}")

# Coverage analysis
print("\nProperty Coverage:")
for prop in ["formation_energy_per_atom", "energy_above_hull", "band_gap"]:
    present = sum(1 for e in entries if e.get(prop) is not None)
    print(f"  {prop:35s}: {present:>7,} / {len(entries):,} "
          f"({100*present/len(entries):.1f}%)")
