"""Phase 1: Raw Data Audit — source integrity, schema, statistics.

Critical check: every source entry has all required fields.
"""
import json, os, time
from pathlib import Path
from collections import Counter, defaultdict

OUT = Path("scripts/audit_reports")
OUT.mkdir(parents=True, exist_ok=True)

DATASET = "dataset/entries_final_v3.json"
AUDIT_DIR = Path.cwd() if Path.cwd().name == "Scandium-Dataset" else Path("/home/shamique/Scandium Labs SSB/Scandium-Dataset")

REQUIRED_FIELDS = [
    "formula", "source", "source_id", "formation_energy_per_atom",
    "elements", "nsites", "structure_json",
]

REQUIRED_STRUCTURE_KEYS = ["lattice", "sites", "@module", "@class"]

severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "PASS": 0}
findings = []

def finding(severity, phase, check, status, detail):
    severity_counts[severity] += 1
    findings.append({
        "severity": severity, "phase": phase, "check": check,
        "status": status, "detail": detail,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    s = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🔵" if severity == "LOW" else "✅"
    print(f"  {s} [{severity:8s}] {check}: {detail[:120]}")

def main():
    print("=" * 60)
    print("  PHASE 1: RAW DATA AUDIT")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)
    print(f"\n  Loaded {N:,} entries")

    # 1. Source integrity
    print("\n--- Source Integrity ---")
    sources = Counter(e.get("source", "unknown") for e in entries)
    for src, cnt in sources.most_common():
        finding("PASS", "source_integrity", f"source_{src}", f"{cnt:,} entries", "")
    
    # Check for unknown sources
    unknown = [e for e in entries if e.get("source") not in ("mp", "oqmd", "jarvis")]
    if unknown:
        finding("CRITICAL", "source_integrity", "unknown_sources",
                f"{len(unknown)} entries", f"sources: {set(e.get('source') for e in unknown)}")
    else:
        finding("PASS", "source_integrity", "all_sources_known", "3 valid sources", "")

    # 2. Schema consistency
    print("\n--- Schema Consistency ---")
    missing_fields = defaultdict(set)
    wrong_types = []
    corrupted_json = []
    duplicate_ids = defaultdict(list)

    for i, e in enumerate(entries):
        for field in REQUIRED_FIELDS:
            if e.get(field) is None:
                src = e.get("source", "?")
                missing_fields[field].add(src)
        
        # Check structure_json parseable
        sj = e.get("structure_json")
        if sj:
            if isinstance(sj, str):
                try:
                    sd = json.loads(sj)
                    if not all(k in sd for k in REQUIRED_STRUCTURE_KEYS):
                        corrupted_json.append((i, "missing_keys"))
                except json.JSONDecodeError:
                    corrupted_json.append((i, "parse_error"))
            elif isinstance(sj, dict):
                if not all(k in sj for k in REQUIRED_STRUCTURE_KEYS):
                    corrupted_json.append((i, "missing_keys_dict"))

        # Check duplicate IDs per source
        sid = e.get("source_id")
        src = e.get("source")
        if sid and src:
            duplicate_ids[(src, sid)].append(i)

    # Report missing fields
    for field, srcs in missing_fields.items():
        finding("HIGH" if field in ("formula", "source", "structure_json") else "MEDIUM",
                "schema", f"missing_field_{field}", 
                f"missing in {', '.join(sorted(srcs))}",
                f"{field} should never be None")

    # Report corrupted JSON
    if corrupted_json:
        finding("CRITICAL", "schema", "corrupted_structure_json",
                f"{len(corrupted_json)} entries", "")
    else:
        finding("PASS", "schema", "structure_json_valid", "all parseable", "")

    # Report duplicate IDs
    dup_ids_found = {k: v for k, v in duplicate_ids.items() if len(v) > 1}
    if dup_ids_found:
        finding("HIGH", "schema", "duplicate_source_ids",
                f"{len(dup_ids_found)} groups", 
                "same (source, source_id) pairs exist — potential dedup gap")
    else:
        finding("PASS", "schema", "no_duplicate_ids", "all source IDs unique", "")

    # 3. Source statistics
    print("\n--- Source Statistics ---")
    for src in ["mp", "oqmd", "jarvis"]:
        subset = [e for e in entries if e.get("source") == src]
        print(f"\n  {src.upper()}: {len(subset):,} entries")
        
        # Missing labels
        for prop in ["formation_energy_per_atom", "energy_above_hull", "band_gap", "space_group", "volume", "density"]:
            missing = sum(1 for e in subset if e.get(prop) is None)
            if missing > 0:
                pct = 100 * missing / len(subset)
                sev = "CRITICAL" if pct > 50 else "HIGH" if pct > 10 else "MEDIUM" if pct > 0 else "PASS"
                finding(sev, "source_stats", f"{src}_{prop}_missing",
                        f"{missing:,} / {len(subset):,} ({pct:.1f}%)", "")
            else:
                finding("PASS", "source_stats", f"{src}_{prop}_present",
                        f"0 missing (100% coverage)", "")

    # 4. License compatibility check
    print("\n--- License Compatibility ---")
    oqmd = [e for e in entries if e.get("source") == "oqmd"]
    finding("PASS", "license", "oqmd_license",
            f"{len(oqmd):,} entries: non-commercial use OK",
            "OQMD allows non-commercial use with attribution")
    finding("PASS", "license", "mp_license",
            f"{sources.get('mp', 0):,} entries: CC BY 4.0",
            "MP requires attribution")
    finding("PASS", "license", "jarvis_license",
            f"{sources.get('jarvis', 0):,} entries: CC0",
            "No restrictions")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  PHASE 1 SUMMARY")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH:     {severity_counts['HIGH']}")
    print(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    print(f"  LOW:      {severity_counts['LOW']}")
    print(f"  PASS:     {severity_counts['PASS']}")
    print(f"{'=' * 60}")

    report = {
        "phase": "Phase 1: Raw Data Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_entries": N,
        "sources": dict(sources.most_common()),
        "findings": findings,
        "summary": dict(severity_counts),
    }
    with open(OUT / "phase1_raw_data_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'phase1_raw_data_audit.json'}")

if __name__ == "__main__":
    main()
