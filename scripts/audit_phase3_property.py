"""Phase 3: Property Audit — distributions, outliers, physical constraints."""
import json, time
from pathlib import Path
from collections import Counter
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

def analyze_prop(values, name, unit, phys_min=None, phys_max=None):
    vals = np.array([v for v in values if v is not None])
    n_missing = sum(1 for v in values if v is None)
    
    print(f"\n  {name} ({unit}):")
    print(f"    n={len(vals):,}, missing={n_missing:,}, mean={np.mean(vals):.4f}, "
          f"median={np.median(vals):.4f}, std={np.std(vals):.4f}")
    print(f"    min={np.min(vals):.4f}, max={np.max(vals):.4f}")
    
    # Percentiles
    for p in [1, 5, 25, 50, 75, 95, 99]:
        print(f"    P{p:2d}={np.percentile(vals, p):.4f}", end="")
    print()
    
    # Skewness and kurtosis
    from scipy import stats
    print(f"    skewness={stats.skew(vals):.4f}, kurtosis={stats.kurtosis(vals):.4f}")
    
    return vals, n_missing

def main():
    print("=" * 60)
    print("  PHASE 3: PROPERTY AUDIT")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)
    print(f"  Loaded {N:,} entries")

    FE = [e.get("formation_energy_per_atom") for e in entries]
    EaH = [e.get("energy_above_hull") for e in entries]
    BG = [e.get("band_gap") for e in entries]

    # --- Distribution analysis ---
    print("\n--- Distribution Analysis ---")
    fe_vals, fe_missing = analyze_prop(FE, "Formation Energy", "eV/atom")
    eah_vals, eah_missing = analyze_prop(EaH, "Energy Above Hull", "eV/atom")
    bg_vals, bg_missing = analyze_prop(BG, "Band Gap", "eV")

    # --- Physical constraints ---
    print("\n--- Physical Constraints ---")

    # BG >= 0
    neg_bg = np.sum(bg_vals < -0.01)
    if neg_bg:
        finding("CRITICAL", "physical", "negative_band_gap", f"{neg_bg:,} entries with BG < 0", "")
    else:
        finding("PASS", "physical", "band_gap_non_negative", f"{np.sum(bg_vals < 0)} negative", "")

    # EaH >= 0
    neg_eah = np.sum(eah_vals < -0.01)
    if neg_eah:
        finding("CRITICAL", "physical", "negative_hull_energy", f"{neg_eah:,} entries with EaH < 0", "")
    else:
        finding("PASS", "physical", "hull_non_negative", f"{neg_eah} negative", "")

    # FE within physical range (-5 to +3 eV/atom)
    extreme_fe = np.sum((fe_vals < -6) | (fe_vals > 4))
    if extreme_fe:
        finding("HIGH", "physical", "extreme_formation_energy",
                f"{extreme_fe:,} entries with FE outside [-6, 4]", "")
    else:
        finding("PASS", "physical", "fe_reasonable_range", "all within [-6, 4]", "")

    # --- Outliers ---
    print("\n--- Outliers ---")

    # IQR-based outlier detection
    def iqr_outliers(vals, name, n_iqr=3):
        q1, q3 = np.percentile(vals, [25, 75])
        iqr = q3 - q1
        low = q1 - n_iqr * iqr
        high = q3 + n_iqr * iqr
        outliers = vals[(vals < low) | (vals > high)]
        return outliers, low, high

    fe_out, fe_low, fe_high = iqr_outliers(fe_vals, "FE")
    eah_out, eah_low, eah_high = iqr_outliers(eah_vals, "EaH")
    bg_out, bg_low, bg_high = iqr_outliers(bg_vals, "BG")

    finding("LOW", "outliers", "fe_iqr_outliers", f"{len(fe_out):,} (thresholds: {fe_low:.3f}, {fe_high:.3f})", "")
    finding("LOW", "outliers", "eah_iqr_outliers", f"{len(eah_out):,} (thresholds: {eah_low:.3f}, {eah_high:.3f})", "")
    finding("LOW", "outliers", "bg_iqr_outliers", f"{len(bg_out):,} (thresholds: {bg_low:.3f}, {bg_high:.3f})", "")

    # Extreme values (hard thresholds)
    extreme_fe_hard = fe_vals[(fe_vals < -5) | (fe_vals > 5)]
    max_fe = float(np.max(fe_vals))
    min_fe = float(np.min(fe_vals))
    severity = "CRITICAL" if max_fe > 10 or min_fe < -10 else "HIGH"
    finding(severity, "outliers", "extreme_fe_hard", 
            f"{len(extreme_fe_hard):,} with |FE| > 5 (max={max_fe:.2f}, min={min_fe:.2f})", 
            f"values: {np.sort(extreme_fe_hard)[:10].tolist()}")

    extreme_eah_hard = eah_vals[eah_vals > 5]
    max_eah = float(np.max(eah_vals)) if len(eah_vals) > 0 else 0
    if len(extreme_eah_hard) > 0:
        sev = "CRITICAL" if max_eah > 10 else "HIGH"
        finding(sev, "outliers", "extreme_eah_hard",
                f"{len(extreme_eah_hard):,} with EaH > 5 (max={max_eah:.2f})", "")
    else:
        finding("PASS", "outliers", "extreme_eah_hard", "0", "")

    # --- Correlations ---
    print("\n--- Property Correlations ---")
    from scipy import stats
    
    # Build aligned arrays for correlation
    import pandas as pd
    df = pd.DataFrame({"fe": FE, "eah": EaH, "bg": BG}).dropna()
    fe_aligned = df["fe"].values[:50000]
    eah_aligned = df["eah"].values[:50000]
    bg_aligned = df["bg"].values[:50000]
    
    r1, _ = stats.pearsonr(fe_aligned, eah_aligned)
    print(f"  FE vs EaH: r={r1:.4f} (n={len(fe_aligned):,})")
    r2, _ = stats.pearsonr(fe_aligned, bg_aligned)
    print(f"  FE vs BG:  r={r2:.4f} (n={len(fe_aligned):,})")
    r3, _ = stats.pearsonr(eah_aligned, bg_aligned)
    print(f"  EaH vs BG: r={r3:.4f} (n={len(eah_aligned):,})")

    finding("PASS", "correlations", "fe_eah_correlation", f"r={r1:.4f}", "")
    finding("PASS", "correlations", "fe_bg_correlation", f"r={r2:.4f}", "")

    # --- Missing values per source ---
    print("\n--- Missing Values Per Source ---")
    for src in ["mp", "oqmd", "jarvis"]:
        subset = [e for e in entries if e.get("source") == src]
        for prop in ["formation_energy_per_atom", "energy_above_hull", "band_gap"]:
            missing = sum(1 for e in subset if e.get(prop) is None)
            if missing > 0:
                pct = 100 * missing / len(subset)
                sev = "CRITICAL" if pct > 50 else "HIGH" if pct > 10 else "MEDIUM"
                finding(sev, "missing", f"{src}_{prop}_missing",
                        f"{missing:,}/{len(subset):,} ({pct:.1f}%)", "")

    print(f"\n{'=' * 60}")
    print(f"  PHASE 3 SUMMARY")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH:     {severity_counts['HIGH']}")
    print(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    print(f"  LOW:      {severity_counts['LOW']}")
    print(f"  PASS:     {severity_counts['PASS']}")
    print(f"{'=' * 60}")

    report = {
        "phase": "Phase 3: Property Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": N,
        "properties": {
            "formation_energy": {
                "n": int(len(fe_vals)), "missing": fe_missing,
                "mean": float(np.mean(fe_vals)), "median": float(np.median(fe_vals)),
                "std": float(np.std(fe_vals)), "min": float(np.min(fe_vals)), "max": float(np.max(fe_vals)),
                "skewness": float(stats.skew(fe_vals)), "kurtosis": float(stats.kurtosis(fe_vals)),
                "outliers_iqr": int(len(fe_out)),
            },
            "energy_above_hull": {
                "n": int(len(eah_vals)), "missing": eah_missing,
                "mean": float(np.mean(eah_vals)), "median": float(np.median(eah_vals)),
                "std": float(np.std(eah_vals)), "min": float(np.min(eah_vals)), "max": float(np.max(eah_vals)),
                "outliers_iqr": int(len(eah_out)),
            },
            "band_gap": {
                "n": int(len(bg_vals)), "missing": bg_missing,
                "mean": float(np.mean(bg_vals)), "median": float(np.median(bg_vals)),
                "std": float(np.std(bg_vals)), "min": float(np.min(bg_vals)), "max": float(np.max(bg_vals)),
                "outliers_iqr": int(len(bg_out)),
            },
        },
        "findings": findings,
        "summary": dict(severity_counts),
    }
    with open(OUT / "phase3_property_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'phase3_property_audit.json'}")

if __name__ == "__main__":
    main()
