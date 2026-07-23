"""Generate conductivity-stratified benchmark splits for SSE screening tasks.

Extends the existing frozen splits with conductivity-aware splits:
  1. Conductivity held-out: hold out top 10% conductors by BVSE barrier
  2. Composition held-out + conducitivity-aware: no formula overlap 
  3. Family-stratified: balanced by SSE family

Usage:
    python scripts/generate_conductivity_splits.py                          # from existing splits + BVSE
    python scripts/generate_conductivity_splits.py --min-barrier 0.0        # include all
    python scripts/generate_conductivity_splits.py --dry-run                # stats only
"""
import json, os, sys, time, argparse, random
from pathlib import Path
from collections import defaultdict
import numpy as np

SEED = 42
SPLIT_DIR = "dataset/splits"


def main():
    parser = argparse.ArgumentParser(description="Generate conductivity-stratified splits")
    parser.add_argument("--min-barrier", type=float, default=0.0,
                        help="Minimum BVSE barrier to filter by (default: 0.0 = all)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"
    
    print("=" * 60)
    print("  CONDUCTIVITY BENCHMARK SPLITS")
    print("  Extending splits for SSE screening tasks")
    print("=" * 60)
    
    print("\nLoading entries...")
    t0 = time.time()
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        entries = json.load(f)
    print(f"  {len(entries):,} entries ({time.time()-t0:.1f}s)")
    
    # Filter to entries with BVSE barrier data
    ssb_entries = [e for e in entries if e.get("ssb_screening", {}).get("bvse_migration_barrier_eV") is not None]
    print(f"\n  Entries with BVSE barriers: {len(ssb_entries):,}")
    
    if args.min_barrier > 0:
        ssb_entries = [e for e in ssb_entries 
                      if e["ssb_screening"]["bvse_migration_barrier_eV"] >= args.min_barrier]
        print(f"  After min-barrier {args.min_barrier:.1f} eV: {len(ssb_entries):,}")
    
    if not ssb_entries:
        print("  No entries with BVSE barriers found. Run compute_bvse_barriers.py first.")
        return
    
    random.seed(SEED)
    np.random.seed(SEED)
    
    splits = {}
    
    # 1. Conductivity-stratified split (stratified by BVSE barrier percentile)
    print(f"\n{'─' * 60}")
    print("  1. Conductivity-stratified split")
    print(f"{'─' * 60}")
    
    barriers = np.array([e["ssb_screening"]["bvse_migration_barrier_eV"] for e in ssb_entries])
    percentiles = np.percentile(barriers, [33, 67])
    
    low = [e for e in ssb_entries if e["ssb_screening"]["bvse_migration_barrier_eV"] <= percentiles[0]]
    mid = [e for e in ssb_entries if percentiles[0] < e["ssb_screening"]["bvse_migration_barrier_eV"] <= percentiles[1]]
    high = [e for e in ssb_entries if e["ssb_screening"]["bvse_migration_barrier_eV"] > percentiles[1]]
    
    print(f"    Low barrier (≤{percentiles[0]:.3f} eV): {len(low):,}")
    print(f"    Mid barrier ({percentiles[0]:.3f}-{percentiles[1]:.3f} eV): {len(mid):,}")
    print(f"    High barrier (≥{percentiles[1]:.3f} eV): {len(high):,}")
    
    stratified_train, stratified_val, stratified_test = [], [], []
    for pool in [low, mid, high]:
        np.random.shuffle(pool)
        n = len(pool)
        n_train = int(n * args.train_ratio)
        n_val = int(n * args.val_ratio)
        stratified_train.extend(pool[:n_train])
        stratified_val.extend(pool[n_train:n_train+n_val])
        stratified_test.extend(pool[n_train+n_val:])
    
    sorted_train = sorted(stratified_train, key=lambda e: e["ssb_screening"]["bvse_migration_barrier_eV"])
    sorted_val = sorted(stratified_val, key=lambda e: e["ssb_screening"]["bvse_migration_barrier_eV"])
    sorted_test = sorted(stratified_test, key=lambda e: e["ssb_screening"]["bvse_migration_barrier_eV"])
    
    splits["conductivity_stratified"] = {
        "train": [e["source_id"] + e.get("source", "") for e in sorted_train],
        "val": [e["source_id"] + e.get("source", "") for e in sorted_val],
        "test": [e["source_id"] + e.get("source", "") for e in sorted_test],
    }
    print(f"    Train: {len(splits['conductivity_stratified']['train']):,}")
    print(f"    Val: {len(splits['conductivity_stratified']['val']):,}")
    print(f"    Test: {len(splits['conductivity_stratified']['test']):,}")
    
    # 2. Family-stratified split (balanced by SSE family)
    print(f"\n{'─' * 60}")
    print("  2. Family-stratified split")
    print(f"{'─' * 60}")
    
    families = defaultdict(list)
    for e in ssb_entries:
        fam = e.get("ssb_screening", {}).get("sse_family") or e.get("sse_family", "unknown")
        families[fam].append(e)
    
    family_counts = {fam: len(entries) for fam, entries in sorted(families.items(), key=lambda x: -len(x[1]))}
    print(f"    Families: {len(families)}")
    for fam, count in list(family_counts.items())[:10]:
        print(f"      {fam:20s}: {count:,}")
    
    family_train, family_val, family_test = [], [], []
    for fam, pool in families.items():
        np.random.shuffle(pool)
        n = len(pool)
        n_train = max(1, int(n * args.train_ratio))
        n_val = max(1, int(n * args.val_ratio))
        family_train.extend(pool[:n_train])
        family_val.extend(pool[n_train:n_train+n_val])
        family_test.extend(pool[n_train+n_val:])
    
    splits["family_stratified_ssb"] = {
        "train": [e["source_id"] + e.get("source", "") for e in family_train],
        "val": [e["source_id"] + e.get("source", "") for e in family_val],
        "test": [e["source_id"] + e.get("source", "") for e in family_test],
    }
    print(f"    Train: {len(splits['family_stratified_ssb']['train']):,}")
    print(f"    Val: {len(splits['family_stratified_ssb']['val']):,}")
    print(f"    Test: {len(splits['family_stratified_ssb']['test']):,}")
    
    # 3. Best-candidate held-out (hold out top-100 lowest-barrier entries for testing)
    print(f"\n{'─' * 60}")
    print("  3. Best-candidate held-out split")
    print(f"{'─' * 60}")
    
    sorted_by_barrier = sorted(ssb_entries, key=lambda e: e["ssb_screening"]["bvse_migration_barrier_eV"])
    top_k = min(500, len(sorted_by_barrier))
    best_test = sorted_by_barrier[:top_k]
    best_pool = sorted_by_barrier[top_k:]
    
    np.random.shuffle(best_pool)
    n_best_train = int(len(best_pool) * args.train_ratio)
    n_best_val = int(len(best_pool) * args.val_ratio)
    best_train = best_pool[:n_best_train]
    best_val = best_pool[n_best_train:n_best_train+n_best_val]
    
    splits["best_conductors_held_out"] = {
        "train": [e["source_id"] + e.get("source", "") for e in best_train],
        "val": [e["source_id"] + e.get("source", "") for e in best_val],
        "test": [e["source_id"] + e.get("source", "") for e in best_test],
    }
    print(f"    Test (top {top_k} conductors): {len(splits['best_conductors_held_out']['test']):,}")
    print(f"    Train: {len(splits['best_conductors_held_out']['train']):,}")
    print(f"    Val: {len(splits['best_conductors_held_out']['val']):,}")
    
    # 4. Mobility class held-out (hold out entire mobility classes)
    print(f"\n{'─' * 60}")
    print("  4. Mobility-class held-out split")
    print(f"{'─' * 60}")
    
    classes = defaultdict(list)
    for e in ssb_entries:
        cls = e["ssb_screening"].get("bvse_mobility_class", "unknown")
        classes[cls].append(e)
    
    for cls, pool in classes.items():
        print(f"    {cls:15s}: {len(pool):,}")
    
    # Hold out superionic as test set (hardest generalization task)
    if "superionic" in classes:
        mob_test = classes["superionic"]
        mob_pool = []
        for cls, pool in classes.items():
            if cls != "superionic":
                mob_pool.extend(pool)
        np.random.shuffle(mob_pool)
        n_mob_train = int(len(mob_pool) * args.train_ratio)
        n_mob_val = int(len(mob_pool) * args.val_ratio)
        mob_train = mob_pool[:n_mob_train]
        mob_val = mob_pool[n_mob_train:n_mob_train+n_mob_val]
        
        splits["mobility_class_held_out"] = {
            "train": [e["source_id"] + e.get("source", "") for e in mob_train],
            "val": [e["source_id"] + e.get("source", "") for e in mob_val],
            "test": [e["source_id"] + e.get("source", "") for e in mob_test],
        }
        print(f"\n    Hold-out class: superionic ({len(mob_test):,} entries)")
        print(f"    Train: {len(mob_train):,}, Val: {len(mob_val):,}")
    else:
        print("    No superionic entries found for held-out split.")
    
    # Save splits
    if not args.dry_run:
        output_dir = BASE_DIR / SPLIT_DIR / "ssb"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for split_name, split_data in splits.items():
            output_path = output_dir / f"{split_name}.json"
            
            # Convert to index-based splits
            entry_indices = {}
            for i, e in enumerate(entries):
                key = e["source_id"] + e.get("source", "")
                entry_indices[key] = i
            
            index_split = {
                "train": [entry_indices[k] for k in split_data["train"] if k in entry_indices],
                "val": [entry_indices[k] for k in split_data["val"] if k in entry_indices],
                "test": [entry_indices[k] for k in split_data["test"] if k in entry_indices],
            }
            
            with open(output_path, "w") as f:
                json.dump(index_split, f, indent=2)
            print(f"\n  Saved: {output_path}")
            print(f"    Train: {len(index_split['train']):,}")
            print(f"    Val: {len(index_split['val']):,}")
            print(f"    Test: {len(index_split['test']):,}")
        
        # Summary
        print(f"\n{'─' * 60}")
        print("  SPLIT SUMMARY")
        print(f"{'─' * 60}")
        for split_name in splits:
            data = splits[split_name]
            print(f"  {split_name:35s}: train={len(data['train']):,} val={len(data['val']):,} test={len(data['test']):,}")
    
    else:
        print(f"\n  (dry-run — no files written)")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
