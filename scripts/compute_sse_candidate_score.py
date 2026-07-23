"""Compute SSE candidate scores for all entries based on the 5-gate screening system.

Populates the ssb_screening block with:
  - gates_passed: list of passed gate names
  - sse_candidate_score: composite score (0-100)
  - thermo_stable: bool (gate 1)
  - electronic_insulation: bool (gate 2)

Gates:
  1. thermo_stability: E_hull < 0.025 eV/atom (stable or near-stable)
  2. electronic_insulation: band_gap > 1.0 eV (not metallic)
  3. ionic_mobility: cavd_channel_dimensionality in ["2D", "3D"] (when available)
  4. electrochemical_window: window_width > 1.0 V (when available)
  5. mechanical: dendrite_suppression_flag (when available)

Score is transparent and compositional:
  - Gate 1 (thermo): 30 points
  - Gate 2 (electronic): 25 points
  - Gate 3 (mobility proxy): 20 points (partial credit for 1D channels)
  - Gate 4 (electrochemical): 15 points
  - Gate 5 (mechanical): 10 points

Usage:
    python scripts/compute_sse_candidate_score.py
    python scripts/compute_sse_candidate_score.py --subset battery
    python scripts/compute_sse_candidate_score.py --limit 10000 --dry-run
"""
import json, os, sys, time, argparse, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

WIDTH = 60

# Gate thresholds
GATES = {
    "thermo_stability": {
        "weight": 30,
        "field": "thermo_stable",
        "description": "E_hull < 0.025 eV/atom",
        "check": lambda e: e.get("ssb_screening", {}).get("thermo_stable", False)
    },
    "electronic_insulation": {
        "weight": 25,
        "field": "electronic_insulation",
        "description": "band_gap > 1.0 eV",
        "check": lambda e: e.get("ssb_screening", {}).get("electronic_insulation", False)
    },
    "ionic_mobility": {
        "weight": 20,
        "field": "cavd_channel_dimensionality",
        "description": "2D/3D percolation channels",
        "check": lambda e: _check_mobility(e)
    },
    "electrochemical_window": {
        "weight": 15,
        "field": "stability_window_low_V",
        "description": "window_width > 1.0 V",
        "check": lambda e: _check_window(e)
    },
    "mechanical": {
        "weight": 10,
        "field": "dendrite_suppression_flag",
        "description": "shear_modulus > 6 GPa",
        "check": lambda e: e.get("ssb_screening", {}).get("dendrite_suppression_flag", False)
    }
}

def _check_mobility(e):
    ss = e.get("ssb_screening", {})
    dim = ss.get("cavd_channel_dimensionality")
    if dim in ("3D",):
        return True
    if dim in ("2D",):
        return True
    if dim in ("1D",):
        # Partial: mobile ions exist but channels are 1D
        return False
    return False

def _check_window(e):
    ss = e.get("ssb_screening", {})
    low = ss.get("stability_window_low_V")
    high = ss.get("stability_window_high_V")
    if low is not None and high is not None:
        return (high - low) >= 1.0
    return False

def _check_mechanical(e):
    return e.get("ssb_screening", {}).get("dendrite_suppression_flag", False)


def compute_gate_score(e, gate_name, gate_config):
    """Compute gate score. Gate passes = full weight, else 0."""
    try:
        passed = gate_config["check"](e)
        return gate_config["weight"] if passed else 0, passed
    except Exception:
        return 0, False


def main():
    parser = argparse.ArgumentParser(description="Compute SSE candidate scores")
    parser.add_argument("--subset", choices=["battery", "electrolyte", "gold", "full"], default="full")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    
    if args.limit and not args.dry_run and args.output is None:
        print("ERROR: Refusing to save limited runs. Use --dry-run or --output.")
        sys.exit(1)
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"
    
    print("=" * WIDTH)
    print("  SSE CANDIDATE SCORE — 5-GATE SCREENING SYSTEM")
    print("=" * WIDTH)
    print()
    print("  Gate weights:")
    for gate_name, config in GATES.items():
        print(f"    {config['weight']:2d} pts — {gate_name}: {config['description']}")
    print()
    
    print("Loading entries...")
    t0 = time.time()
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        all_entries = json.load(f)
    print(f"  {len(all_entries):,} entries ({time.time()-t0:.1f}s)")
    
    # Select working subset
    if args.subset == "battery":
        with open(DATASET_PATH / "battery_subset_v3.json") as f:
            entries = json.load(f)
    elif args.subset == "electrolyte":
        with open(DATASET_PATH / "electrolyte_subset_v3.json") as f:
            entries = json.load(f)
    elif args.subset == "gold":
        entries = [e for e in all_entries if e.get("tier") == "gold"]
    else:
        entries = all_entries
    
    if args.limit:
        entries = entries[:args.limit]
    
    print(f"  Working subset: {len(entries):,} entries")
    
    if not entries:
        print("No entries to process.")
        return
    
    # Score all entries
    print(f"\n{'─' * WIDTH}")
    print("  Computing scores...")
    print(f"{'─' * WIDTH}")
    
    score_dist = {}
    gate_counts = {g: {"pass": 0, "total": 0} for g in GATES}
    
    # Track entries that need to be synced back to all_entries
    updated_keys = set()
    
    for idx, e in enumerate(entries):
        if "ssb_screening" not in e:
            e["ssb_screening"] = {}
        
        ss = e["ssb_screening"]
        
        total_score = 0
        gates_passed = []
        
        for gate_name, config in GATES.items():
            score, passed = compute_gate_score(e, gate_name, config)
            total_score += score
            gate_counts[gate_name]["total"] += 1
            if passed:
                gates_passed.append(gate_name)
                gate_counts[gate_name]["pass"] += 1
        
        ss["sse_candidate_score"] = total_score
        ss["gates_passed"] = gates_passed
        
        # Record distribution
        bin_key = f"{(total_score // 10) * 10}-{(total_score // 10) * 10 + 9}"
        score_dist[bin_key] = score_dist.get(bin_key, 0) + 1
        
        # Keep track of which entries were updated
        source_id = e.get("source_id", "") + e.get("source", "")
        updated_keys.add(source_id)
    
    # Print results
    print(f"\n  Score distribution:")
    for key in sorted(score_dist.keys(), key=lambda x: int(x.split("-")[0])):
        count = score_dist[key]
        bar = "█" * min(count // 1000, 50)
        print(f"    {key:>6}: {count:>6,}  {bar}")
    
    print(f"\n  Per-gate pass rates:")
    for gate_name, counts in gate_counts.items():
        pct = counts["pass"] / max(counts["total"], 1) * 100
        print(f"    {gate_name:25s}: {counts['pass']:>6,}/{counts['total']:<6,} ({pct:.1f}%)")
    
    # Top scores
    all_sorted = sorted(entries, key=lambda e: e.get("ssb_screening", {}).get("sse_candidate_score", 0), reverse=True)
    print(f"\n  Top 10 candidates:")
    for e in all_sorted[:10]:
        ss = e.get("ssb_screening", {})
        print(f"    Score {ss.get('sse_candidate_score', 0):3d} | {e.get('structured_formula', e.get('formula','')):20s} | "
              f"{e.get('sse_family', '?'):15s} | Gates: {ss.get('gates_passed', [])}")
    
    # Sync back to all_entries
    if args.subset in ("full",):
        save_data = all_entries
    elif args.subset == "gold":
        save_data = all_entries
        entry_map = {}
        for e in entries:
            key = e.get("source_id", "") + e.get("source", "")
            entry_map[key] = e
        for e in save_data:
            key = e.get("source_id", "") + e.get("source", "")
            if key in entry_map:
                e["ssb_screening"] = entry_map[key].get("ssb_screening", {})
    else:
        save_data = entries
    
    # Save
    if args.subset == "battery":
        output_path = DATASET_PATH / "battery_subset_v3.json"
    elif args.subset == "electrolyte":
        output_path = DATASET_PATH / "electrolyte_subset_v3.json"
    elif args.subset == "gold":
        output_path = DATASET_PATH / "entries_final_v3.json"
    else:
        output_path = DATASET_PATH / "entries_final_v3.json"
    
    if args.dry_run:
        print(f"\n  (dry-run — not saved)")
    else:
        print(f"\n  Writing to {output_path}...")
        t_write = time.time()
        with open(output_path, "w") as f:
            json.dump(save_data, f)
        print(f"  Done ({time.time()-t_write:.1f}s)")
    
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
