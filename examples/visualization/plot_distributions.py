"""Example: Visualize dataset distributions.

Requires: matplotlib, numpy
"""
import json, numpy as np
from collections import Counter

with open("dataset/entries_final_v3.json") as f:
    entries = json.load(f)

# FE histogram
fe_vals = np.array([e.get("formation_energy_per_atom", 0)
                    for e in entries if e.get("formation_energy_per_atom") is not None])

print("FE Distribution (eV/atom):")
fe_range = (-5, 3)
bins = np.linspace(fe_range[0], fe_range[1], 40)
hist, edges = np.histogram(fe_vals, bins=bins)
max_bar = max(hist)
for i in range(len(hist)):
    if hist[i] < max_bar * 0.01:
        continue
    bar_len = int(60 * hist[i] / max_bar)
    print(f"  {edges[i]:+5.2f}: {'█' * bar_len} ({hist[i]:,})")

# BG histogram
bg_vals = np.array([e.get("band_gap", 0)
                    for e in entries if e.get("band_gap") is not None])
bg_nonzero = bg_vals[bg_vals > 0.01]
print(f"\nBand Gap Distribution:")
print(f"  Zero gap (metals): {np.sum(bg_vals <= 0.01):,} "
      f"({100*np.sum(bg_vals <= 0.01)/len(bg_vals):.0f}%)")
print(f"  Non-zero mean: {np.mean(bg_nonzero):.3f} eV")
print(f"  Non-zero median: {np.median(bg_nonzero):.3f} eV")
print(f"  Max: {np.max(bg_vals):.2f} eV")

# Tier pie
tiers = Counter(e.get("tier", "unknown") for e in entries)
print(f"\nTier Distribution:")
for tier, count in tiers.most_common():
    print(f"  {tier:12s}: {count:>7,} ({100*count/len(entries):.1f}%)")
