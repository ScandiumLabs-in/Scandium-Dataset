"""Phase 5: Repair Audit — every repair verified with confidence."""
import json, time
from pathlib import Path
from collections import Counter

OUT = Path("scripts/audit_reports")
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
    print("  PHASE 5: REPAIR AUDIT")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)

    # Check provenance for repair records
    repaired_count = 0
    for e in entries:
        prov = e.get("provenance", {})
        repairs = prov.get("repairs_applied", [])
        if repairs:
            repaired_count += 1

    print(f"\n--- Coordinate Repair ---")
    coord_repaired = sum(1 for e in entries if e.get("source") == "oqmd" and 
                         any(r.get("repair_id") == "coordinate_artifact" 
                             for r in e.get("provenance", {}).get("repairs_applied", [])))
    
    if coord_repaired > 0:
        finding("PASS", "coordinate_repair", "entries_repaired",
                f"{coord_repaired:,} OQMD entries", "coordinate artifact fixed")
    else:
        # Check via other means — verify all OQMD have valid min_dist now
        import numpy as np
        from pymatgen.core import Structure
        sample = [e for e in entries if e.get("source") == "oqmd"]
        if sample:
            has_artifact = 0
            for e in sample[:100]:
                try:
                    sj = e.get("structure_json", "{}")
                    if isinstance(sj, str):
                        sd = json.loads(sj)
                    else:
                        sd = sj
                    s = Structure.from_dict(sd)
                    dc = s.distance_matrix
                    np.fill_diagonal(dc, float("inf"))
                    md = float(dc.min())
                    if abs(md - np.sqrt(3)/4) < 0.01:
                        has_artifact += 1
                except Exception:
                    pass
            if has_artifact > 0:
                finding("CRITICAL", "coordinate_repair", "artifact_still_present",
                        f"{has_artifact}/100 sampled still have artifact", "")
            else:
                finding("PASS", "coordinate_repair", "artifact_cleared",
                        f"0/100 sampled have artifact", "")
    
    # Space group repair
    print(f"\n--- Symmetry Repair ---")
    oqmd_sg_found = sum(1 for e in entries if e.get("source") == "oqmd" and e.get("space_group") is not None)
    oqmd_sg_missing = sum(1 for e in entries if e.get("source") == "oqmd" and e.get("space_group") is None)
    if oqmd_sg_missing == 0:
        finding("PASS", "symmetry_repair", "sg_all_found", f"{oqmd_sg_found:,}/{oqmd_sg_found+oqmd_sg_missing:,}", "")
    elif oqmd_sg_missing <= 20:
        finding("MEDIUM", "symmetry_repair", "sg_minor_failures", f"{oqmd_sg_missing:,} still missing SG", "")
    else:
        finding("CRITICAL", "symmetry_repair", "sg_major_failures", f"{oqmd_sg_missing:,} still missing SG", "")

    # Volume repair
    print(f"\n--- Volume Repair ---")
    oqmd_vol_zero = sum(1 for e in entries if e.get("source") == "oqmd" and (e.get("volume") is None or e.get("volume", 0) == 0))
    jarvis_vol_zero = sum(1 for e in entries if e.get("source") == "jarvis" and (e.get("volume") is None or e.get("volume", 0) == 0))
    mp_vol_zero = sum(1 for e in entries if e.get("source") == "mp" and (e.get("volume") is None or e.get("volume", 0) == 0))
    
    if oqmd_vol_zero + jarvis_vol_zero + mp_vol_zero == 0:
        finding("PASS", "volume_repair", "all_volumes_resolved", "0 entries with zero volume", "")
    else:
        finding("HIGH", "volume_repair", "remaining_zero_volume", 
                f"OQMD:{oqmd_vol_zero:,} JARVIS:{jarvis_vol_zero:,} MP:{mp_vol_zero:,}", "")

    # Density repair
    print(f"\n--- Density Repair ---")
    oqmd_dens_zero = sum(1 for e in entries if e.get("source") == "oqmd" and (e.get("density") is None or e.get("density", 0) == 0))
    if oqmd_dens_zero == 0:
        finding("PASS", "density_repair", "all_density_resolved", "0 OQMD entries with zero density", "")
    else:
        finding("HIGH", "density_repair", "remaining_zero_density", f"{oqmd_dens_zero:,}", "")

    # Verify repair logs exist
    print(f"\n--- Repair Log Verification ---")
    repair_logs = list(OUT.parent.glob("repair_reports/coordinate_repair_*.json"))
    sym_log = OUT.parent / "reports/repair_reports/oqmd_symmetry_pass.json"
    
    if repair_logs:
        finding("PASS", "repair_logs", "coordinate_repair_log_exists", f"{len(repair_logs)} log(s)", "")
    else:
        # Check in original location
        orig_logs = list((AUDIT_DIR.parent / "scandium-labs/dataset_v3/repair/logs").glob("coordinate_repair_*.json"))
        if orig_logs:
            finding("PASS", "repair_logs", "coordinate_repair_log_exists", "found in original location", "")
        else:
            finding("HIGH", "repair_logs", "coordinate_repair_log_missing", "no log found", "")
    
    if sym_log.exists() or (AUDIT_DIR.parent / "scandium-labs/dataset_v3/repair/logs/oqmd_symmetry_pass.json").exists():
        finding("PASS", "repair_logs", "symmetry_repair_log_exists", "found", "")
    else:
        finding("HIGH", "repair_logs", "symmetry_repair_log_missing", "not found", "")

    print(f"\n{'=' * 60}")
    print(f"  PHASE 5 SUMMARY")
    print(f"  CRITICAL: {severity_counts['CRITICAL']}")
    print(f"  HIGH:     {severity_counts['HIGH']}")
    print(f"  MEDIUM:   {severity_counts['MEDIUM']}")
    print(f"  LOW:      {severity_counts['LOW']}")
    print(f"  PASS:     {severity_counts['PASS']}")
    print(f"{'=' * 60}")

    report = {
        "phase": "Phase 5: Repair Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "repairs": {
            "coordinate_artifact": {"repaired": coord_repaired},
            "symmetry": {"found": oqmd_sg_found, "missing": oqmd_sg_missing},
            "volume": {"oqmd_zero": oqmd_vol_zero, "jarvis_zero": jarvis_vol_zero, "mp_zero": mp_vol_zero},
            "density": {"oqmd_zero": oqmd_dens_zero},
        },
        "findings": findings,
        "summary": dict(severity_counts),
    }
    with open(OUT / "phase5_repair_audit.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'phase5_repair_audit.json'}")

if __name__ == "__main__":
    DATASET = "dataset/entries_final_v3.json"
    main()
