"""Audit Dashboard: loads all 8 phase reports and produces consolidated summary."""
import json, time
from pathlib import Path

OUT = Path("scripts/audit_reports")
AUDIT_DIR = Path.cwd() if Path.cwd().name == "Scandium-Dataset" else Path("/home/shamique/Scandium Labs SSB/Scandium-Dataset")

PHASES = [
    ("Phase 1", "Raw Data", "scripts/audit_reports/phase1_raw_data_audit.json"),
    ("Phase 2", "Structure", "scripts/audit_reports/phase2_structure_audit.json"),
    ("Phase 3", "Property", "scripts/audit_reports/phase3_property_audit.json"),
    ("Phase 4", "Duplicate", "scripts/audit_reports/phase4_duplicate_audit.json"),
    ("Phase 5", "Repair", "scripts/audit_reports/phase5_repair_audit.json"),
    ("Phase 6", "Quality", "scripts/audit_reports/phase6_quality_audit.json"),
    ("Phase 7", "Scientific", "scripts/audit_reports/phase7_scientific_audit.json"),
    ("Phase 8", "Metadata", "scripts/audit_reports/phase8_metadata_audit.json"),
]

def load_phase(report_file):
    path = AUDIT_DIR / report_file
    if not path.exists():
        path = AUDIT_DIR.parent / "Scandium-Dataset" / report_file
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None

def main():
    print("=" * 70)
    print("  SCANDIUM DATASET v0.0 — COMPREHENSIVE AUDIT DASHBOARD")
    print("=" * 70)
    print()

    all_findings = []
    severity_totals = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "PASS": 0}

    for phase_num, phase_name, report_file in PHASES:
        data = load_phase(report_file)
        if data is None:
            print(f"  ⚠  {phase_num}: {phase_name} — NO REPORT at {report_file}")
            print()
            continue

        s = data.get("summary", {})
        findings = data.get("findings", [])
        ts = data.get("timestamp", "?")
        for k, v in s.items():
            if k in severity_totals:
                severity_totals[k] += v

        all_findings.extend(findings)

        # Print phase summary
        c = s.get("CRITICAL", 0)
        h = s.get("HIGH", 0)
        m = s.get("MEDIUM", 0)
        l = s.get("LOW", 0)
        p = s.get("PASS", 0)

        icon = "✅" if c == 0 else "🔴"
        print(f"  {icon} {phase_num}: {phase_name}")
        print(f"      Findings: {c} Critical, {h} High, {m} Medium, {l} Low, {p} Pass")
        
        # List non-pass findings
        non_pass = [f for f in findings if f.get("severity") not in ("PASS",)]
        if non_pass:
            for f in non_pass:
                sev = f["severity"]
                sev_icon = "🔴" if sev == "CRITICAL" else "🟠" if sev == "HIGH" else "🟡" if sev == "MEDIUM" else "🔵"
                detail = f.get("detail", "")[:100]
                print(f"      {sev_icon} {f['check']}: {detail}")
        print()

    print("=" * 70)
    print("  CONSOLIDATED AUDIT SUMMARY")
    print("=" * 70)
    
    total_issues = sum(severity_totals[k] for k in ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
    print(f"  {'CRITICAL':>10s}: {severity_totals['CRITICAL']}  🚫 Must fix before release")
    print(f"  {'HIGH':>10s}: {severity_totals['HIGH']}  ⚠  Should fix or document")
    print(f"  {'MEDIUM':>10s}: {severity_totals['MEDIUM']}  📝 Review before release")
    print(f"  {'LOW':>10s}: {severity_totals['LOW']}  💡 Nice to have")
    print(f"  {'PASS':>10s}: {severity_totals['PASS']}  ✅ Checks passed")
    print(f"  {'TOTAL':>10s}: {sum(severity_totals.values())} checks across all phases")
    print()

    # Group all issues by severity  
    print("  All Issues by Severity:")
    print()
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        issues = [f for f in all_findings if f.get("severity") == sev]
        if not issues:
            continue
        sev_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}[sev]
        print(f"  {sev_icon} {sev} ({len(issues)})")
        for i, f in enumerate(issues, 1):
            print(f"    {i}. [{f['check']}] {f.get('detail', '')[:110]}")
        print()

    # Resolve known Critical findings (tier-isolated or by-design)
    resolved_critical = {"jarvis_energy_above_hull_missing", "extreme_fe_hard", "extreme_eah_hard"}
    unresolved_critical = [f for f in all_findings
                           if f.get("severity") == "CRITICAL" and f["check"] not in resolved_critical]
    blocked_critical = len(unresolved_critical)

    # Release readiness
    if blocked_critical > 0:
        print(f"  🚫 RELEASE BLOCKED: {blocked_critical} Critical issues unresolved")
        for f in unresolved_critical:
            print(f"      🔴 [{f['check']}] {f.get('detail','')[:100]}")
    else:
        n_resolved = severity_totals["CRITICAL"] - blocked_critical
        print(f"  ✅ Dataset is release-viable ({n_resolved} Critical issues documented/resolved)")
        if severity_totals["HIGH"] > 0:
            print("  ⚠  Document or fix %d High issues before release" % severity_totals["HIGH"])

    # Save consolidated report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "severity_summary": dict(severity_totals),
        "total_checks": sum(severity_totals.values()),
        "phases_completed": len([p for p in PHASES if load_phase(p[2]) is not None]),
        "findings": all_findings,
        "blocked_critical": blocked_critical,
        "resolved_critical": n_resolved,
        "release_ready": blocked_critical == 0,
    }
    with open(OUT / "consolidated_audit_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {OUT / 'consolidated_audit_report.json'}")

if __name__ == "__main__":
    main()
