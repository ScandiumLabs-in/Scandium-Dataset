"""Phase 8: Metadata Audit — completeness, consistency, correctness."""
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

REQUIRED_FIELDS = ["source_id", "formula", "elements", "source",
                   "space_group", "volume", "density", "structure_json",
                   "quality_score", "quality_sub_scores", "quality_flags",
                   "tier", "provenance", "nsites", "band_gap", "formation_energy_per_atom",
                   "families"]

def main():
    print("=" * 60)
    print("  PHASE 8: METADATA AUDIT")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)

    # Field completeness
    print(f"\n--- Field Completeness ---")
    field_missing = Counter()
    for field in REQUIRED_FIELDS:
        for e in entries:
            if field not in e or e[field] is None:
                field_missing[field] += 1
    
    for field, count in sorted(field_missing.items()):
        bad = count > 0
        sev = "PASS"
        if bad and count > N * 0.01:
            sev = "HIGH" if count > N * 0.1 else "MEDIUM"
        elif bad and count > 10:
            sev = "LOW"
        elif bad:
            sev = "PASS"
        finding(sev, "completeness", f"missing_{field}", f"{count:,} ({100*count/N:.1f}%)", "")

    # Check tier distribution
    print(f"\n--- Tier Distribution ---")
    tier_counts = Counter(e.get("tier") for e in entries)
    for tier, cnt in sorted(tier_counts.items()):
        print(f"    {tier:12s}: {cnt:>7,}")
    if tier_counts.get("raw") is None:
        finding("LOW", "tiers", "no_raw_tier", "raw tier missing from frozen set", "")
    
    # Source distribution
    print(f"\n--- Source Distribution ---")
    src_counts = Counter(e.get("source") for e in entries)
    for src, cnt in sorted(src_counts.items()):
        print(f"    {src:8s}: {cnt:>7,} ({100*cnt/N:.1f}%)")
    
    # Family distribution
    print(f"\n--- Family Distribution ---")
    family_counts = Counter()
    for e in entries:
        for fam in e.get("families", []):
            family_counts[fam] += 1
    for fam, cnt in sorted(family_counts.most_common(20)):
        print(f"    {fam:20s}: {cnt:>7,}")

    # Provenance completeness
    print(f"\n--- Provenance ---")
    prov_fields = 0
    for e in entries:
        if e.get("provenance"):
            prov_fields += 1
    print(f"  Entries with provenance: {prov_fields:,} ({100*prov_fields/N:.1f}%)")
    if prov_fields < N:
        finding("HIGH", "provenance", "missing_provenance",
                f"{N - prov_fields:,} entries ({100*(N-prov_fields)/N:.1f}%) missing", "")
    else:
        finding("PASS", "provenance", "all_have_provenance", "", "")

    # Check duplicate_group metadata
    dg_cnt = sum(1 for e in entries if e.get("duplicate_group") is not None)
    print(f"\n  Entries with duplicate_group: {dg_cnt:,} ({100*dg_cnt/N:.1f}%)")

    # Check that all entries have structure_json
    no_struct = sum(1 for e in entries if not e.get("structure_json"))
    if no_struct > 0:
        finding("CRITICAL", "structure", "missing_structure",
                f"{no_struct:,} ({100*no_struct/N:.1f}%)", "")
    else:
        finding("PASS", "structure", "all_have_structure", "", "")

    # Check structured_formula parity
    sf_missing = sum(1 for e in entries if not e.get("structured_formula"))
    if sf_missing > 0:
        finding("MEDIUM", "metadata", "missing_structured_formula",
                f"{sf_missing:,} entries", "")
    
    # ID format consistency
    print(f"\n--- ID Consistency ---")
    id_formats = Counter()
    for e in entries:
        mid = e.get("source_id", "")
        if mid.startswith("mp-"):
            id_formats["mp-"] += 1
        elif mid.startswith("oqmd-"):
            id_formats["oqmd-"] += 1
        elif mid.startswith("jv-") or mid.startswith("jarvis-"):
            id_formats["jarvis"] += 1
        else:
            id_formats["other"] += 1
    for fmt, cnt in sorted(id_formats.items()):
        print(f"    {fmt:12s}: {cnt:>7,}")

    if id_formats.get("other", 0) > 0:
        finding("MEDIUM", "metadata", "nonstandard_ids",
                f"{id_formats['other']:,} nonstandard IDs", "")

    # Quality flags staleness (OQMD space_group flag vs actual space_group)
    stale_flags = 0
    for e in entries:
        if e.get("source") == "oqmd" and e.get("space_group") is not None:
            flags = e.get("quality_flags", [])
            if "missing_spacegroup" in flags:
                stale_flags += 1
    if stale_flags > 100:
        finding("MEDIUM", "metadata", "stale_quality_flags",
                f"{stale_flags:,} OQMD entries flagged missing_spacegroup but SG now populated", "flags need recalculation")
    elif stale_flags > 0:
        finding("LOW", "metadata", "stale_quality_flags", f"{stale_flags} entries", "")
    else:
        finding("PASS", "metadata", "flags_current", "", "")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  PHASE 8 SUMMARY")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH:     {severity_counts['HIGH']}")
    print(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    print(f"  LOW:      {severity_counts['LOW']}")
    print(f"  PASS:     {severity_counts['PASS']}")
    print(f"{'=' * 60}")

    report = {
        "phase": "Phase 8: Metadata Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "field_completeness": dict(field_missing),
        "tier_distribution": dict(tier_counts),
        "source_distribution": dict(src_counts),
        "family_distribution": dict(family_counts),
        "id_formats": dict(id_formats),
        "stale_quality_flags": stale_flags,
        "findings": findings,
        "summary": dict(severity_counts),
    }
    with open(OUT / "phase8_metadata_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'phase8_metadata_audit.json'}")

if __name__ == "__main__":
    main()
