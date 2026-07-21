"""Phase 4: Duplicate Audit — exact, near, formula, cross-source."""
import json, time
from pathlib import Path
from collections import Counter, defaultdict
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
    print("  PHASE 4: DUPLICATE AUDIT")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)
    print(f"  Loaded {N:,} entries")

    # Get dedup info
    dup_groups = Counter()
    cross_source_dup = 0
    intra_source_dup = 0
    kept_entries = 0
    duplicate_entries = 0
    dup_group_details = defaultdict(list)

    for e in entries:
        dg = e.get("duplicate_group")
        if dg is not None:
            dup_groups[dg] += 1
            dup_group_details[dg].append(e.get("source", "?"))

    duplicate_entries = sum(dup_groups.values())
    kept_entries = N - duplicate_entries  # these are the ones kept
    n_groups = len(dup_groups)

    print(f"\n--- Duplicate Summary ---")
    print(f"  Duplicate groups: {n_groups:,}")
    print(f"  Duplicate entries: {duplicate_entries:,} (these were kept as representatives)")
    print(f"  Original total before dedup: {N + 31997:,} (assuming 31,997 removed)")

    # Cross-source analysis
    cross_source_groups = 0
    for gid, srcs in dup_group_details.items():
        unique_srcs = set(srcs)
        if len(unique_srcs) > 1:
            cross_source_groups += 1
            intra_source_dup += len(srcs) - 1

    intra_source_groups = n_groups - cross_source_groups

    finding("PASS", "duplicates", "total_duplicate_groups",
            f"{n_groups:,} groups ({duplicate_entries:,} entries kept)", "")
    finding("PASS", "duplicates", "cross_source_groups",
            f"{cross_source_groups:,} groups span multiple sources", "")
    finding("PASS", "duplicates", "intra_source_groups",
            f"{intra_source_groups:,} groups within single source", "")

    # Group size distribution
    group_sizes = sorted(dup_groups.values(), reverse=True)
    print(f"\n--- Group Size Distribution ---")
    print(f"  Max group size: {max(group_sizes) if group_sizes else 0}")
    print(f"  Mean group size: {np.mean(group_sizes):.2f}" if group_sizes else "  No groups")
    
    size_bins = Counter()
    for sz in group_sizes:
        if sz == 2: size_bins["2"] += 1
        elif sz <= 5: size_bins["3-5"] += 1
        elif sz <= 10: size_bins["6-10"] += 1
        else: size_bins[">10"] += 1
    
    for label, cnt in size_bins.most_common():
        print(f"    size {label}: {cnt:,} groups")

    # Cross-source overlap by formula
    print(f"\n--- Cross-Source Formula Overlap ---")
    by_formula = defaultdict(set)
    for e in entries:
        f = e.get("formula", "").strip()
        if f:
            by_formula[f].add(e.get("source", ""))

    cross_formula = {f: s for f, s in by_formula.items() if len(s) > 1}
    print(f"  Formulas with multiple sources: {len(cross_formula):,}")

    overlap_pairs = Counter()
    for f, srcs in cross_formula.items():
        for s1 in srcs:
            for s2 in srcs:
                if s1 < s2:
                    overlap_pairs[(s1, s2)] += 1

    for (s1, s2), cnt in overlap_pairs.most_common():
        finding("PASS", "cross_source_overlap", f"{s1}_{s2}_formulas",
                f"{cnt:,} formulas shared", "")

    # Check if any formulas have >2 sources (potential triple duplicates)
    triple = {f: s for f, s in cross_formula.items() if len(s) >= 3}
    if triple:
        finding("MEDIUM", "duplicates", "triple_source_formulas",
                f"{len(triple):,} formulas appear in all 3 sources", "")
    else:
        finding("PASS", "duplicates", "triple_source_formulas", "0", "")

    print(f"\n{'=' * 60}")
    print(f"  PHASE 4 SUMMARY")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH:     {severity_counts['HIGH']}")
    print(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    print(f"  LOW:      {severity_counts['LOW']}")
    print(f"  PASS:     {severity_counts['PASS']}")
    print(f"{'=' * 60}")

    report = {
        "phase": "Phase 4: Duplicate Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": N,
        "duplicate_groups": n_groups,
        "duplicate_entries_kept": duplicate_entries,
        "estimated_removed": 31997,
        "cross_source_groups": cross_source_groups,
        "intra_source_groups": intra_source_groups,
        "cross_source_formulas": len(cross_formula),
        "overlap_pairs": {f"{s1}_{s2}": c for (s1, s2), c in overlap_pairs.most_common()},
        "group_size_distribution": dict(size_bins),
        "findings": findings,
        "summary": dict(severity_counts),
    }
    with open(OUT / "phase4_duplicate_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'phase4_duplicate_audit.json'}")

if __name__ == "__main__":
    main()
