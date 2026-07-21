"""Phase 2: Structure Audit — geometry, crystal systems, outliers.

Every structure is validated for physical reasonableness.
"""
import json, os, sys, time
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path.cwd()))
import numpy as np

OUT = Path("scripts/audit_reports")
OUT.mkdir(parents=True, exist_ok=True)
DATASET = "dataset/entries_final_v3.json"
AUDIT_DIR = Path.cwd() if Path.cwd().name == "Scandium-Dataset" else Path("/home/shamique/Scandium Labs SSB/Scandium-Dataset")

severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "PASS": 0}
findings = []

def finding(severity, phase, check, status, detail):
    severity_counts[severity] += 1
    findings.append({"severity": severity, "phase": phase, "check": check, "status": status, "detail": str(detail)[:200]})
    s = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🔵" if severity == "LOW" else "✅"
    print(f"  {s} [{severity:8s}] {check}: {str(detail)[:120]}")

def main():
    print("=" * 60)
    print("  PHASE 2: STRUCTURE AUDIT")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)
    print(f"  Loaded {N:,} entries\n")

    # Collect geometry stats
    volumes = []
    densities = []
    nsites_list = []
    min_dists = []
    sgs = Counter()
    crystal_systems = Counter()
    sg_failures = []

    for i, e in enumerate(entries):
        if i % 50000 == 0:
            print(f"  [{i}/{N}]", flush=True)

        vol = e.get("volume", 0)
        if vol and vol > 0:
            volumes.append(vol)
        dens = e.get("density", 0)
        if dens and dens > 0:
            densities.append(dens)
        ns = e.get("nsites", 0)
        if ns > 0:
            nsites_list.append(ns)
        sg = e.get("space_group")
        if sg is not None:
            try:
                sgs[int(sg)] += 1
                # Crystal system from space group number
                sg_num = int(sg)
                if 1 <= sg_num <= 2: crystal_systems["Triclinic"] += 1
                elif sg_num <= 15: crystal_systems["Monoclinic"] += 1
                elif sg_num <= 74: crystal_systems["Orthorhombic"] += 1
                elif sg_num <= 142: crystal_systems["Tetragonal"] += 1
                elif sg_num <= 167: crystal_systems["Trigonal"] += 1
                elif sg_num <= 194: crystal_systems["Hexagonal"] += 1
                elif sg_num <= 230: crystal_systems["Cubic"] += 1
                else: crystal_systems["Unknown"] += 1
            except (ValueError, TypeError):
                sg_failures.append(i)
        else:
            sg_failures.append(i)

    volumes = np.array(volumes)
    densities = np.array(densities)
    nsites_arr = np.array(nsites_list)

    # --- Geometry Validation ---
    print("\n--- Geometry Validation ---")

    # Zero volume
    zero_vol = sum(1 for e in entries if e.get("volume") is None or e.get("volume", 0) <= 0)
    if zero_vol:
        finding("CRITICAL", "geometry", "zero_volume", f"{zero_vol:,} entries", "")
    else:
        finding("PASS", "geometry", "zero_volume", "0 entries", "all have volume > 0")

    # Negative volume
    neg_vol = sum(1 for e in entries if e.get("volume", 0) < 0)
    if neg_vol:
        finding("CRITICAL", "geometry", "negative_volume", f"{neg_vol:,} entries", "")
    else:
        finding("PASS", "geometry", "negative_volume", "0 entries", "")

    # NaN coordinates — check structure_json for NaN
    nan_coords = 0
    for i, e in enumerate(entries):
        sj = e.get("structure_json", "")
        if isinstance(sj, str) and ("NaN" in sj or "nan" in sj or "Infinity" in sj):
            nan_coords += 1
    if nan_coords:
        finding("CRITICAL", "geometry", "nan_coordinates", f"{nan_coords:,} entries with NaN in structure", "")
    else:
        finding("PASS", "geometry", "nan_coordinates", "0 entries", "")

    # Nsites ≥ 2 (single atoms)
    single_atom = sum(1 for n in nsites_arr if n < 2)
    if single_atom:
        finding("HIGH", "geometry", "single_atom_entries", f"{single_atom:,} entries", "")
    else:
        finding("PASS", "geometry", "single_atom_entries", "0 entries", "")

    # --- Crystal Validation ---
    print("\n--- Crystal Validation ---")

    if sgs:
        most_common_sg = sgs.most_common(5)
        finding("PASS", "crystal", "space_groups", f"{len(sgs)} unique SGs", 
                f"top: {dict(most_common_sg)}")

    if crystal_systems:
        finding("PASS", "crystal", "crystal_systems", 
                f"{dict(crystal_systems.most_common())}", "")

    # SG failures
    if sg_failures:
        pct = 100 * len(sg_failures) / N
        finding("HIGH" if pct > 1 else "MEDIUM", "crystal", "space_group_failures",
                f"{len(sg_failures):,} / {N:,} ({pct:.2f}%)", "")
    else:
        finding("PASS", "crystal", "space_group_failures", "0", "")

    # Volume stats
    print(f"\n  Volume stats (n={len(volumes):,}):")
    print(f"    mean={np.mean(volumes):.1f}  median={np.median(volumes):.1f}  "
          f"min={np.min(volumes):.1f}  max={np.max(volumes):.1f}")

    # Density stats
    print(f"\n  Density stats (n={len(densities):,}):")
    print(f"    mean={np.mean(densities):.2f}  median={np.median(densities):.2f}  "
          f"min={np.min(densities):.2f}  max={np.max(densities):.2f}")

    # --- Structural Outliers ---
    print("\n--- Structural Outliers ---")

    # Largest volumes
    vol_sorted = sorted(enumerate(entries), key=lambda x: x[1].get("volume", 0) or 0, reverse=True)
    largest_vol = [(i, e.get("volume", 0), e.get("formula", "")) for i, e in vol_sorted[:5]]
    finding("LOW", "outliers", "largest_volume", f"top: {largest_vol[0][2]} ({largest_vol[0][1]:.0f} Å³)", "")

    # Smallest volumes
    smallest_vol = [(i, e.get("volume", 0) or float("inf"), e.get("formula", "")) for i, e in enumerate(entries) if e.get("volume", 0) > 0]
    smallest_vol.sort(key=lambda x: x[1])
    finding("LOW", "outliers", "smallest_volume", 
            f"top: {smallest_vol[0][2]} ({smallest_vol[0][1]:.1f} Å³)", "")

    # Highest density
    dens_sorted = sorted(enumerate(entries), key=lambda x: x[1].get("density", 0) or 0, reverse=True)
    finding("LOW", "outliers", "highest_density", 
            f"top: {dens_sorted[0][1].get('formula','?')} ({dens_sorted[0][1].get('density',0):.1f} g/cm³)", "")

    # Most atoms
    ns_sorted = sorted(enumerate(entries), key=lambda x: x[1].get("nsites", 0) or 0, reverse=True)
    max_ns = ns_sorted[0][1].get("nsites", 0) if ns_sorted else 0
    finding("LOW", "outliers", "most_atoms", f"max nsites = {max_ns}", "")

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print(f"  PHASE 2 SUMMARY")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH:     {severity_counts['HIGH']}")
    print(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    print(f"  LOW:      {severity_counts['LOW']}")
    print(f"  PASS:     {severity_counts['PASS']}")
    print(f"{'=' * 60}")

    # Crystal system report
    total_cs = sum(crystal_systems.values())
    print(f"\n  Crystal System Distribution:")
    for cs, cnt in crystal_systems.most_common():
        print(f"    {cs:15s}: {cnt:>7,} ({100*cnt/total_cs:.1f}%)")

    report = {
        "phase": "Phase 2: Structure Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": N,
        "geometry": {
            "volume_mean": float(np.mean(volumes)),
            "volume_median": float(np.median(volumes)),
            "volume_min": float(np.min(volumes)),
            "volume_max": float(np.max(volumes)),
            "density_mean": float(np.mean(densities)),
            "density_median": float(np.median(densities)),
            "nsites_mean": float(np.mean(nsites_arr)),
            "nsites_median": float(np.median(nsites_arr)),
        },
        "crystal_systems": dict(crystal_systems.most_common()),
        "unique_space_groups": len(sgs),
        "top_space_groups": dict(sgs.most_common(10)),
        "findings": findings,
        "summary": dict(severity_counts),
    }
    with open(OUT / "phase2_structure_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'phase2_structure_audit.json'}")

if __name__ == "__main__":
    main()
