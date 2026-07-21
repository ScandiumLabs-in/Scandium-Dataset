"""Phase 6: Quality Audit — calibration, bias, per-source/family."""
import json, time
from pathlib import Path
from collections import Counter
import numpy as np
from scipy import stats

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
    print("  PHASE 6: QUALITY AUDIT")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)

    scores = np.array([e.get("quality_score", 0) for e in entries])
    sub_scores = {k: np.array([e.get("quality_sub_scores", {}).get(k, 0) for e in entries])
                  for k in ["geometry", "dft", "metadata", "novelty", "chemical"]}

    print(f"\n--- Score Distribution ---")
    print(f"  Mean: {np.mean(scores):.2f}, Median: {np.median(scores):.2f}, Std: {np.std(scores):.2f}")
    print(f"  Min: {np.min(scores):.1f}, Max: {np.max(scores):.1f}")

    # Score bins histogram
    bins = np.arange(0, 101, 10)
    bin_labels = [f"{b}-{b+9}" for b in bins[:-1]]
    bin_counts = np.histogram(scores, bins=bins)[0]
    print(f"\n  Score Distribution:")
    for label, count in zip(bin_labels, bin_counts):
        bar = "█" * max(1, int(40 * count / max(bin_counts)))
        print(f"    {label:>6s}: {count:>7,} {bar}")

    # Check monotonicity of score → calibration
    # Group scores into bins and check each bin's valid%, SG%, etc.
    score_bins = np.digitize(scores, bins=[50, 60, 70, 80, 90])
    bin_ranges = ["<50", "50-60", "60-70", "70-80", "80-90", "≥90"]

    calib_metrics = []
    print(f"\n--- Calibration Check ---")
    for bi in range(1, 6):
        mask = score_bins == bi
        n = int(np.sum(mask))
        if n < 10:
            continue
        subset = [entries[i] for i in range(N) if score_bins[i] == bi]
        
        valid_pct = 100 * sum(1 for e in subset if e.get("tier") in ("gold", "validated")) / len(subset)
        sg_pct = 100 * sum(1 for e in subset if e.get("space_group") is not None) / len(subset)
        complete_pct = 100 * sum(1 for e in subset if all(e.get(f) is not None for f in ["space_group", "density", "elements"])) / len(subset)
        
        calib_metrics.append({
            "bin": bin_ranges[bi],
            "n": len(subset),
            "valid_pct": round(valid_pct, 1),
            "sg_pct": round(sg_pct, 1),
            "complete_pct": round(complete_pct, 1),
        })
        print(f"    {bin_ranges[bi]:>6s}: n={len(subset):,}  valid={valid_pct:.1f}%  SG={sg_pct:.1f}%")

    # Test monotonicity: each successive bin should have higher or equal valid%
    valid_pcts = [m["valid_pct"] for m in calib_metrics]
    is_monotonic = all(valid_pcts[i] <= valid_pcts[i+1] for i in range(len(valid_pcts)-1))
    if is_monotonic:
        finding("PASS", "calibration", "monotonic_valid_pct", "valid% increases with score", "")
    else:
        finding("HIGH", "calibration", "non_monotonic_valid_pct", "score NOT monotonically related to quality", "")

    sg_pcts = [m["sg_pct"] for m in calib_metrics]
    is_sg_monotonic = all(sg_pcts[i] <= sg_pcts[i+1] for i in range(len(sg_pcts)-1))
    if is_sg_monotonic:
        finding("PASS", "calibration", "monotonic_sg_pct", "SG% increases with score", "")
    else:
        finding("HIGH", "calibration", "non_monotonic_sg_pct", "", "")

    # Per-source quality bias
    print(f"\n--- Per-Source Quality Bias ---")
    for src in ["mp", "oqmd", "jarvis"]:
        src_scores = [e.get("quality_score", 0) for e in entries if e.get("source") == src]
        src_mean = np.mean(src_scores)
        print(f"    {src:8s}: mean={src_mean:.2f}, median={np.median(src_scores):.2f}, N={len(src_scores):,}")

    # Check if quality score is fair across sources
    mp_scores = [e.get("quality_score", 0) for e in entries if e.get("source") == "mp"]
    oqmd_scores = [e.get("quality_score", 0) for e in entries if e.get("source") == "oqmd"]
    jv_scores = [e.get("quality_score", 0) for e in entries if e.get("source") == "jarvis"]
    
    t_stat, p_val = stats.ttest_ind(mp_scores, oqmd_scores)
    if p_val > 0.01:
        finding("PASS", "source_bias", "mp_oqmd_score_fair", f"t-test p={p_val:.4f}", "")
    else:
        mean_diff = np.mean(mp_scores) - np.mean(oqmd_scores)
        finding("MEDIUM" if abs(mean_diff) < 10 else "HIGH", "source_bias", "mp_oqmd_score_diff",
                f"p={p_val:.4f}, diff={mean_diff:.1f}", "")

    # Sub-score analysis
    print(f"\n--- Sub-Score Analysis ---")
    for k, vals in sub_scores.items():
        mean_v = np.mean(vals)
        max_v = np.max(vals)
        pct = 100 * mean_v / max_v if max_v > 0 else 0
        print(f"    {k:10s}: mean={mean_v:.1f}/{max_v:.0f} ({pct:.0f}%)")

    # Score ≥ 90 exists?
    n_ge90 = int(np.sum(scores >= 90))
    if n_ge90 > 0:
        finding("PASS", "score_range", "scores_ge90", f"{n_ge90:,} entries ≥ 90", "")
    else:
        finding("MEDIUM", "score_range", "no_scores_ge90", "0 entries ≥ 90 — scoring is conservative", "")

    # Quality flags distribution
    print(f"\n--- Quality Flags ---")
    all_flags = Counter()
    for e in entries:
        for f in e.get("quality_flags", []):
            all_flags[f] += 1
    print(f"    Total unique flag types: {len(all_flags)}")
    for flag, count in all_flags.most_common(10):
        print(f"      {flag:40s}: {count:>7,}")

    print(f"\n{'=' * 60}")
    print(f"  PHASE 6 SUMMARY")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH:     {severity_counts['HIGH']}")
    print(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    print(f"  LOW:      {severity_counts['LOW']}")
    print(f"  PASS:     {severity_counts['PASS']}")
    print(f"{'=' * 60}")

    report = {
        "phase": "Phase 6: Quality Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "score_distribution": {
            "mean": float(np.mean(scores)), "median": float(np.median(scores)),
            "std": float(np.std(scores)), "min": float(np.min(scores)), "max": float(np.max(scores)),
        },
        "calibration": calib_metrics,
        "monotonic_valid_pct": is_monotonic,
        "monotonic_sg_pct": is_sg_monotonic,
        "per_source_scores": {
            src: {"mean": float(np.mean([e.get("quality_score", 0) for e in entries if e.get("source") == src]))}
            for src in ["mp", "oqmd", "jarvis"]
        },
        "sub_scores": {k: {"mean": float(np.mean(v)), "max": int(np.max(v))} for k, v in sub_scores.items()},
        "findings": findings,
        "summary": dict(severity_counts),
    }
    with open(OUT / "phase6_quality_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'phase6_quality_audit.json'}")

if __name__ == "__main__":
    main()
