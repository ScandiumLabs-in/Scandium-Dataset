"""Phase 1 pipeline runner — executes all Phase 1 scripts in sequence.

This script runs the complete Phase 1 pipeline:
  1. Electrochemical stability windows (Li/Na entries)
  2. CAVD channel dimensionality (all Li/Na entries with structures)
  3. SSE candidate score (all entries, 5-gate system)
  4. Mechanical properties (all entries, geometric proxy)
  5. Oxidation states (all entries, BVA + heuristic)
  6. JARVIS EaH (internal convex hull)
  7. Commercial-safe edition extraction
  8. Garnet enrichment (structure-based reclassification)

Usage:
    python scripts/run_phase1_pipeline.py                        # full pipeline
    python scripts/run_phase1_pipeline.py --steps 1,3,5          # specific steps only
    python scripts/run_phase1_pipeline.py --dry-run              # stats only, no writes
    python scripts/run_phase1_pipeline.py --skip-write           # compute but don't save
"""
import sys, time, argparse, subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPTS_DIR.parent

STEPS = {
    1: ("Electrochemical Windows", "compute_electrochemical_windows.py", 
        ["python", "scripts/compute_electrochemical_windows.py", "--subset", "full"]),
    2: ("CAVD Channel Dimensionality", "compute_cavd_channel_dimensionality.py",
        ["python", "scripts/compute_cavd_channel_dimensionality.py", "--subset", "full"]),
    3: ("SSE Candidate Score", "compute_sse_candidate_score.py",
        ["python", "scripts/compute_sse_candidate_score.py", "--subset", "full"]),
    4: ("Mechanical Properties", "compute_mechanical_properties.py",
        ["python", "scripts/compute_mechanical_properties.py"]),
    5: ("Oxidation States", "compute_oxidation_states.py",
        ["python", "scripts/compute_oxidation_states.py"]),
    6: ("JARVIS EaH", "compute_jarvis_hull_energy.py",
        ["python", "scripts/compute_jarvis_hull_energy.py"]),
    7: ("Commercial-Safe Edition", "extract_commercial_safe_edition.py",
        ["python", "scripts/extract_commercial_safe_edition.py"]),
    8: ("Garnet Enrichment", "enrich_garnet_family.py",
        ["python", "scripts/enrich_garnet_family.py"]),
}

STEP_ORDER = [1, 2, 3, 4, 5, 6, 7, 8]


def main():
    parser = argparse.ArgumentParser(description="Phase 1 pipeline runner")
    parser.add_argument("--steps", type=str, default=None,
                        help="Comma-separated step numbers (e.g. 1,3,5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Add --dry-run to all scripts")
    parser.add_argument("--skip-write", action="store_true",
                        help="Add --dry-run to dataset-modifying scripts")
    args = parser.parse_args()
    
    if args.steps:
        selected_steps = [int(s.strip()) for s in args.steps.split(",")]
    else:
        selected_steps = STEP_ORDER
    
    print("=" * 60)
    print("  PHASE 1 PIPELINE")
    print("  8 steps to transform Scandium-Dataset into SSB screening resource")
    print("=" * 60)
    
    total_start = time.time()
    
    for step_num in selected_steps:
        if step_num not in STEPS:
            print(f"\n  [SKIP] Step {step_num}: unknown")
            continue
        
        name, script, base_cmd = STEPS[step_num]
        
        print(f"\n{'─' * 60}")
        print(f"  Step {step_num}/8: {name}")
        print(f"  Script: scripts/{script}")
        print(f"{'─' * 60}")
        
        cmd = list(base_cmd)
        if args.dry_run or args.skip_write:
            cmd.append("--dry-run")
        
        step_start = time.time()
        print(f"  Running: {' '.join(cmd)}")
        print()
        
        result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
        
        # Print stdout
        for line in result.stdout.split("\n"):
            print(f"  {line}")
        
        if result.stderr.strip():
            print(f"\n  stderr:")
            for line in result.stderr.strip().split("\n"):
                print(f"  ! {line}")
        
        if result.returncode != 0:
            print(f"\n  [FAILED] exit code {result.returncode}")
            if not args.dry_run:
                print("  Aborting pipeline.")
                sys.exit(1)
        
        elapsed = time.time() - step_start
        print(f"\n  [{elapsed/60:.1f} min]")
    
    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"  Pipeline complete: {len(selected_steps)} steps in {total_elapsed/60:.1f} min")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
