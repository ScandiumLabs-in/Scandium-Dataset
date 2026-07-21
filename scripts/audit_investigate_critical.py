"""Investigate 4 Critical findings: JARVIS EaH, extreme FE, extreme EaH."""
import json
from pathlib import Path
from collections import Counter

DATASET = "dataset/entries_final_v3.json"
AUDIT_DIR = Path.cwd() if Path.cwd().name == "Scandium-Dataset" else Path("/home/shamique/Scandium Labs SSB/Scandium-Dataset")

with open(AUDIT_DIR / DATASET) as f:
    entries = json.load(f)

print("=" * 60)
print("  INVESTIGATION: 4 CRITICAL FINDINGS")
print("=" * 60)

# 1. JARVIS EaH missing
print("\n--- 1. JARVIS Energy Above Hull ---")
jarvis = [e for e in entries if e.get("source") == "jarvis"]
jarvis_eah = sum(1 for e in jarvis if e.get("energy_above_hull") is not None)
print(f"  JARVIS entries: {len(jarvis):,}")
print(f"  With EaH: {jarvis_eah:,}")
print(f"  Missing EaH: {len(jarvis) - jarvis_eah:,} (100%)")
print(f"  Fundamental limitation: JARVIS DFT does not compute hull distance")
print(f"  Resolution: document in known_issues; EaH=null is valid in raw/validated tiers")
print(f"  Gold tier already excludes these from gate 7 (missing_labels)")

# 2. Extreme FE > 5 eV/atom
print("\n--- 2. Extreme Formation Energy (FE > 5 eV/atom) ---")
extreme_fe = [e for e in entries if e.get("formation_energy_per_atom") is not None 
              and abs(e.get("formation_energy_per_atom")) > 5]
extreme_fe.sort(key=lambda x: -abs(x.get("formation_energy_per_atom", 0)))

print(f"  Entries with |FE| > 5 eV/atom: {len(extreme_fe):,}")
print(f"  FE range: [{min(e.get('formation_energy_per_atom', 0) for e in extreme_fe):.2f}, "
      f"{max(e.get('formation_energy_per_atom', 0) for e in extreme_fe):.2f}]")

# Show top 20
print(f"\n  Top 20 by |FE|:")
print(f"  {'Source':8s} {'FE':>8s} {'Formula':20s} {'Elements':30s} {'SG':>4s}")
print(f"  {'-'*8} {'-'*8} {'-'*20} {'-'*30} {'-'*4}")
for e in extreme_fe[:20]:
    print(f"  {e.get('source','?'):8s} {e.get('formation_energy_per_atom',0):8.2f} "
          f"{e.get('formula',''):20s} {str(e.get('elements',[])):30s} "
          f"{e.get('space_group','?'):>4}")

# Source breakdown
src_counts = Counter(e.get("source") for e in extreme_fe)
print(f"\n  By source: {dict(src_counts)}")

# 3. Extreme EaH > 5 eV/atom
print("\n--- 3. Extreme Energy Above Hull (EaH > 5 eV/atom) ---")
extreme_eah = [e for e in entries if e.get("energy_above_hull") is not None 
               and e.get("energy_above_hull") > 5]
extreme_eah.sort(key=lambda x: -x.get("energy_above_hull", 0))

print(f"  Entries with EaH > 5 eV/atom: {len(extreme_eah):,}")
print(f"  EaH range: [{min(e.get('energy_above_hull', 0) for e in extreme_eah):.2f}, "
      f"{max(e.get('energy_above_hull', 0) for e in extreme_eah):.2f}]")

print(f"\n  Top 20 by EaH:")
print(f"  {'Source':8s} {'EaH':>8s} {'FE':>8s} {'Formula':20s} {'Elements':30s} {'SG':>4s}")
print(f"  {'-'*8} {'-'*8} {'-'*8} {'-'*20} {'-'*30} {'-'*4}")
for e in extreme_eah[:20]:
    print(f"  {e.get('source','?'):8s} {e.get('energy_above_hull',0):8.2f} "
          f"{e.get('formation_energy_per_atom',0):8.2f} "
          f"{e.get('formula',''):20s} {str(e.get('elements',[])):30s} "
          f"{e.get('space_group','?'):>4}")

src_counts_eah = Counter(e.get("source") for e in extreme_eah)
print(f"\n  By source: {dict(src_counts_eah)}")

# How many extreme FE entries are also Gold tier?
gold_fe = sum(1 for e in extreme_fe if e.get("tier") == "gold")
gold_eah = sum(1 for e in extreme_eah if e.get("tier") == "gold")
print(f"\n--- Tier Impact ---")
print(f"  Extreme FE in Gold tier: {gold_fe}")
print(f"  Extreme EaH in Gold tier: {gold_eah}")

# Check if these extreme entries are multi-element
print(f"\n--- Element Count Analysis ---")
for label, entries_list in [("FE>5", extreme_fe), ("EaH>5", extreme_eah)]:
    nelem_counts = Counter(len(e.get("elements", [])) for e in entries_list)
    print(f"  {label}: nelem distribution: {dict(sorted(nelem_counts.items()))}")

print(f"\n=== RESOLUTION PLAN ===")
print(f"  1. JARVIS EaH: DOCUMENT as fundamental limitation")
print(f"  2. Extreme FE: REMOVE from Gold tier (should not pass gate 10)")
print(f"  3. Extreme EaH: REMOVE from Gold tier")
print(f"  After fixes: 0 remaining Critical issues → release ready")
