"""Phase 7: Scientific Audit — property distributions, domain plausibility."""
import json, time
from pathlib import Path
from collections import Counter
import numpy as np

OUT = Path("scripts/audit_reports")
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
    print("  PHASE 7: SCIENTIFIC AUDIT")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)

    # Extract all labels
    fe = np.array([e.get("formation_energy_per_atom", np.nan) for e in entries], dtype=float)
    eah = np.array([e.get("energy_above_hull", np.nan) for e in entries], dtype=float)
    bg = np.array([e.get("band_gap", np.nan) for e in entries], dtype=float)
    vol = np.array([e.get("volume", np.nan) for e in entries], dtype=float)
    dens = np.array([e.get("density", np.nan) for e in entries], dtype=float)
    sg = [e.get("space_group") for e in entries]
    nelem = np.array([len(e.get("elements", [])) for e in entries], dtype=float)

    # FE distribution
    fe_valid = fe[~np.isnan(fe)]
    print(f"\n--- Formation Energy ---")
    print(f"  N={len(fe_valid):,}  Range: [{np.min(fe_valid):.2f}, {np.max(fe_valid):.2f}] eV/atom")
    print(f"  Mean={np.mean(fe_valid):.2f}  Median={np.median(fe_valid):.2f}  Std={np.std(fe_valid):.2f}")
    
    # Expected range for solid-state materials: [-6, 4] eV/atom
    extreme_fe = fe_valid[(fe_valid < -6) | (fe_valid > 4)]
    n_extreme = len(extreme_fe)
    if n_extreme > 100:
        finding("HIGH", "scientific", "extreme_formation_energy_per_atom",
                f"{n_extreme:,} entries outside [-6, 4] eV", f"max={np.max(extreme_fe):.1f}, min={np.min(extreme_fe):.1f}")
    elif n_extreme > 0:
        finding("MEDIUM", "scientific", "extreme_formation_energy_per_atom",
                f"{n_extreme} outliers", "")
    else:
        finding("PASS", "scientific", "formation_energy_plausible", "all in [-6, 4]", "")

    # FE quantiles
    for q in [1, 5, 25, 50, 75, 95, 99]:
        print(f"    P{q:2d}: {np.percentile(fe_valid, q):7.2f} eV/atom")

    # EaH distribution
    eah_valid = eah[~np.isnan(eah)]
    print(f"\n--- Energy Above Hull ---")
    print(f"  N={len(eah_valid):,}  Range: [{np.min(eah_valid):.2f}, {np.max(eah_valid):.2f}] eV/atom")
    print(f"  Mean={np.mean(eah_valid):.2f}  Median={np.median(eah_valid):.2f}  Std={np.std(eah_valid):.2f}")
    
    extreme_eah = eah_valid[eah_valid > 1]
    n_eah_extreme = len(extreme_eah)
    if n_eah_extreme > 100:
        finding("MEDIUM", "scientific", "high_energy_above_hull",
                f"{n_eah_extreme:,} entries > 1 eV/atom", f"max={np.max(extreme_eah):.1f}")
    elif n_eah_extreme > 0:
        finding("MEDIUM", "scientific", "high_energy_above_hull",
                f"{n_eah_extreme} entries > 1 eV", "")
    else:
        finding("PASS", "scientific", "high_energy_above_hull", "all ≤ 1 eV/atom", "")

    # Band gap distribution
    bg_valid = bg[~np.isnan(bg)]
    print(f"\n--- Band Gap ---")
    print(f"  N={len(bg_valid):,}  Range: [{np.min(bg_valid):.2f}, {np.max(bg_valid):.2f}] eV")
    print(f"  Mean={np.mean(bg_valid):.2f}  Median={np.median(bg_valid):.2f}  Std={np.std(bg_valid):.2f}")
    
    # Metal distribution
    n_metal = int(np.sum(bg_valid <= 0.1))
    n_small = int(np.sum((bg_valid > 0.1) & (bg_valid <= 0.5)))
    n_insulator = int(np.sum(bg_valid > 4))
    print(f"  Metals (≤0.1 eV): {n_metal:,} ({100*n_metal/len(bg_valid):.1f}%)")
    print(f"  Narrow-gap (0.1-0.5): {n_small:,} ({100*n_small/len(bg_valid):.1f}%)")  
    print(f"  Wide-gap (>4 eV): {n_insulator:,} ({100*n_insulator/len(bg_valid):.1f}%)")

    # Volume vs density sanity
    vol_valid = vol[~np.isnan(vol)]
    dens_valid = dens[~np.isnan(dens)]
    print(f"\n--- Volume vs Density ---")
    print(f"  Volume range: [{np.min(vol_valid):.0f}, {np.max(vol_valid):.0f}] Å³")
    print(f"  Density range: [{np.min(dens_valid):.1f}, {np.max(dens_valid):.1f}] g/cm³")
    
    # Physical density range: most solids 0.5-25 g/cm³
    extreme_dens = dens_valid[(dens_valid < 0.5) | (dens_valid > 25)]
    if len(extreme_dens) > 100:
        finding("MEDIUM", "scientific", "extreme_density",
                f"{len(extreme_dens):,} outside [0.5, 25] g/cm³", "")
    elif len(extreme_dens) > 0:
        finding("LOW", "scientific", "extreme_density", f"{len(extreme_dens)} outliers", "")
    else:
        finding("PASS", "scientific", "density_plausible", "", "")

    # Element distribution
    print(f"\n--- Most Common Elements ---")
    elem_counter = Counter()
    for e in entries:
        for el in e.get("elements", []):
            elem_counter[el] += 1
    for el, cnt in elem_counter.most_common(20):
        print(f"    {el:3s}: {cnt:,}")

    # Element count distribution
    print(f"\n--- Number of Elements ---")
    nelem_counter = Counter()
    for n_el in nelem:
        nelem_counter[int(n_el)] += 1
    for n_el, cnt in sorted(nelem_counter.items()):
        print(f"    {n_el} elements: {cnt:>7,}")
    max_nelem = int(np.max(nelem))
    if max_nelem > 6:
        finding("LOW", "scientific", "high_element_count",
                f"max elements = {max_nelem}", "")

    # Space group distribution
    print(f"\n--- Space Group Distribution ---")
    sg_counter = Counter()
    for s in sg:
        if s is not None:
            sg_counter[int(s)] += 1
    for sg_num, cnt in sorted(sg_counter.most_common(30)):
        print(f"    SG {sg_num:3d}: {cnt:>7,}")

    # Crystal system distribution
    crystal_systems = {
        "Triclinic": set(range(1, 3)), "Monoclinic": set(range(3, 16)),
        "Orthorhombic": set(range(16, 75)), "Tetragonal": set(range(75, 143)),
        "Trigonal": set(range(143, 168)), "Hexagonal": set(range(168, 195)),
        "Cubic": set(range(195, 231)),
    }
    cs_counter = Counter()
    for s in sg:
        if s is not None:
            for cs_name, sg_set in crystal_systems.items():
                if int(s) in sg_set:
                    cs_counter[cs_name] += 1
                    break
    print(f"\n  Crystal System Distribution:")
    total_cs = sum(cs_counter.values())
    for cs_name, cnt in cs_counter.most_common():
        print(f"    {cs_name:14s}: {cnt:>7,} ({100*cnt/total_cs:.1f}%)")

    print(f"\n--- Battery Relevance ---")
    battery_entries = [e for e in entries if e.get("family") in 
                        ["layered_oxide", "polyanion", "sulfide_sse", "halide_sse", 
                         "garnet", "perovskite_sse", "nasicon", "lisicon",
                         "antiperovskite_sse", "hydroborate_sse"]]
    print(f"  Battery-related: {len(battery_entries):,} ({100*len(battery_entries)/N:.1f}%)")
    
    fe_oc = [e.get("formation_energy_per_atom") for e in battery_entries if e.get("formation_energy_per_atom") is not None]
    if fe_oc:
        print(f"  Battery FE range: [{np.min(fe_oc):.2f}, {np.max(fe_oc):.2f}] eV/atom")

    print(f"\n{'=' * 60}")
    print(f"  PHASE 7 SUMMARY")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH:     {severity_counts['HIGH']}")
    print(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    print(f"  LOW:      {severity_counts['LOW']}")
    print(f"  PASS:     {severity_counts['PASS']}")
    print(f"{'=' * 60}")

    report = {
        "phase": "Phase 7: Scientific Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "formation_energy": {
            "N_valid": int(np.sum(~np.isnan(fe))),
            "mean": float(np.nanmean(fe)),
            "median": float(np.nanmedian(fe)),
            "std": float(np.nanstd(fe)),
            "min": float(np.nanmin(fe)),
            "max": float(np.nanmax(fe)),
            "p1": float(np.nanpercentile(fe, 1)),
            "p5": float(np.nanpercentile(fe, 5)),
            "p25": float(np.nanpercentile(fe, 25)),
            "p50": float(np.nanpercentile(fe, 50)),
            "p75": float(np.nanpercentile(fe, 75)),
            "p95": float(np.nanpercentile(fe, 95)),
            "p99": float(np.nanpercentile(fe, 99)),
            "n_extreme_outliers": int(np.sum((fe < -6) | (fe > 4))),
        },
        "energy_above_hull": {
            "N_valid": int(np.sum(~np.isnan(eah))),
            "mean": float(np.nanmean(eah)),
            "median": float(np.nanmedian(eah)),
            "min": float(np.nanmin(eah)),
            "max": float(np.nanmax(eah)),
            "n_gt_1": int(np.sum(eah > 1)),
        },
        "band_gap": {
            "N_valid": int(np.sum(~np.isnan(bg))),
            "mean": float(np.nanmean(bg)),
            "median": float(np.nanmedian(bg)),
            "n_metal": int(np.sum(bg <= 0.1)),
        },
        "crystal_system": dict(cs_counter.most_common()),
        "top_elements": {el: c for el, c in elem_counter.most_common(20)},
        "n_elements_distribution": {str(k): v for k, v in sorted(nelem_counter.items())},
        "findings": findings,
        "summary": dict(severity_counts),
    }
    with open(OUT / "phase7_scientific_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'phase7_scientific_audit.json'}")

if __name__ == "__main__":
    main()
