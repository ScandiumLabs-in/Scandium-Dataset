"""BVSE-based Li/Na migration barrier proxy using bvlain (softBV method).

Uses the established bvlain package (Chen & Adams, softBV methodology) for
bond-valence site energy percolation analysis. This is orders of magnitude
cheaper than DFT-NEB and is the standard first-pass screening proxy.

Method:
  1. Load structure and assign oxidation states via BVAnalyzer
  2. Compute BVSE grid on a 0.3 Å resolution mesh
  3. Find percolation barrier (minimum energy for a connected migration network)
  4. Classify: Ea < 0.25 eV = superionic, 0.25-0.50 eV = good,
     0.50-0.75 eV = moderate, > 0.75 eV = poor conductor

Reference:
  - Chen & Adams. "softBV" package for bond-valence methods.
  - Adams. Acta Cryst. B, 2001. Bond valence parameters.
  - Rong et al. Chem. Mater. 2020. SPSE platform BVSE methodology.

Fills ssb_screening block with:
  - bvse_migration_barrier_eV: float or null
  - bvse_mobility_class: str
  - bvse_percolation_dimensionality: str ("3D", "2D", "1D", "none")

Usage:
    python scripts/compute_bvse_barriers.py                           # full Li/Na subset
    python scripts/compute_bvse_barriers.py --limit 1000 --dry-run     # test run
    python scripts/compute_bvse_barriers.py --batch-size 2000          # incremental save
"""
import json, os, sys, time, argparse, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
warnings.filterwarnings("ignore")

WIDTH = 60

MOBILITY_THRESHOLDS = [
    ("superionic", 0.25),
    ("good", 0.50),
    ("moderate", 0.75),
    ("poor", float('inf')),
]


def parse_structure_json(struct_str):
    import json as _json
    from pymatgen.core import Structure
    return Structure.from_dict(_json.loads(struct_str))


def compute_bvse_barrier(structure, mobile_element="Li", resolution=0.3, n_jobs=1):
    """Compute BVSE migration barrier using bvlain.

    Returns:
        dict with migration_barrier_eV, mobility_class, percolation_dim
    """
    from bvlain import Lain

    lain = Lain(verbose=False)

    # Assign oxidation states (required by bvlain's BV parameter lookup)
    from pymatgen.analysis.bond_valence import BVAnalyzer
    try:
        bva = BVAnalyzer()
        st_oxi = bva.get_oxi_state_decorated_structure(structure)
    except Exception:
        return _null_result("oxidation state assignment failed")

    try:
        lain.read_structure(st_oxi, oxi_check=False)
    except Exception as exc:
        return _null_result(f"read_structure: {str(exc)[:60]}")

    mobile_ion_str = f"{mobile_element}1+"

    try:
        lain.bvse_distribution(mobile_ion=mobile_ion_str, resolution=resolution)
    except Exception as exc:
        err = str(exc)
        if "No BVSE data for a given combination" in err:
            return _null_result("no BV params for this composition")
        return _null_result(f"bvse_distribution: {err[:60]}")

    try:
        barriers = lain.percolation_barriers(encut=10.0, n_jobs=n_jobs)
    except Exception as exc:
        err = str(exc)
        if "min() iterable argument is empty" in err:
            return _null_result("no percolation path found")
        return _null_result(f"percolation: {err[:60]}")

    min_barrier = min(v for v in barriers.values())
    if min_barrier == float('inf') or min_barrier < 0:
        return _null_result("no connected pathway")

    # Determine percolation dimensionality
    eps = 0.05
    dim_map = {1: "1D", 2: "2D", 3: "3D"}
    dims = []
    for d in [1, 2, 3]:
        if barriers[f"E_{d}D"] <= min_barrier + eps:
            dims.append(d)
    percolation_dim = dim_map.get(max(dims), "3D") if dims else "none"

    # Classify
    mobility_class = "poor"
    for cls_name, threshold in MOBILITY_THRESHOLDS:
        if min_barrier < threshold:
            mobility_class = cls_name
            break

    return {
        "migration_barrier_eV": round(float(min_barrier), 4),
        "mobility_class": mobility_class,
        "percolation_dimensionality": percolation_dim,
        "bvse_grid_resolution": resolution,
    }


def _null_result(reason=""):
    return {
        "migration_barrier_eV": None,
        "mobility_class": "none",
        "percolation_dimensionality": "none",
        "_skip_reason": reason,
    }


def main():
    parser = argparse.ArgumentParser(description="BVSE migration barrier proxy (bvlain)")
    parser.add_argument("--subset", choices=["battery", "electrolyte", "gold", "full"], default="full")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=500,
                        help="Entries per batch before checkpoint (default: 500)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--resolution", type=float, default=0.5,
                        help="BVSE grid resolution in Å (default: 0.5, range 0.3-0.6)")
    parser.add_argument("--jobs", type=int, default=1,
                        help="Number of parallel workers for percolation search (default: 1)")
    parser.add_argument("--max-sites", type=int, default=100,
                        help="Skip structures with more than this many sites (default: 100)")
    args = parser.parse_args()

    if args.limit and not args.dry_run and args.output is None:
        print("ERROR: Refusing to save limited runs. Use --dry-run or --output.")
        sys.exit(1)

    BASE_DIR = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(BASE_DIR / "dataset"))
    from dataset_store import DatasetStore

    print("=" * WIDTH)
    print("  BVSE MIGRATION BARRIER PROXY  (bvlain engine)")
    print("  softBV percolation analysis for Li/Na conductors")
    print("=" * WIDTH)

    print("\nOpening dataset store...")
    t0 = time.time()
    store = DatasetStore.open()
    print(f"  {store.num_entries:,} entries ({time.time()-t0:.1f}s)")

    # Filter to Li/Na entries with structures (and not too large)
    entries = list(store.scan(
        filter_fn=lambda e: (
            e.get("mobile_ion") in ("Li", "Na")
            and e.get("structure_json") is not None
            and isinstance(e.get("nsites"), (int, float))
            and e.get("nsites", 0) <= args.max_sites
        )
    ))
    print(f"  Li/Na entries with structures (≤{args.max_sites} sites): {len(entries):,}")

    if args.limit:
        entries = entries[:args.limit]
        print(f"  Limited to {args.limit} entries")

    if not entries:
        print("No entries to process.")
        return

    print(f"\n{'─' * WIDTH}")
    print("  Computing BVSE percolation barriers...")
    print(f"{'─' * WIDTH}")

    processed = 0
    errors = 0
    skipped_oxi = 0
    skipped_no_path = 0
    class_counts = defaultdict(int)
    barrier_vals = []
    t_start = time.time()
    last_checkpoint = 0

    for idx, e in enumerate(entries):
        mobile_ion = e.get("mobile_ion", "Li")
        sid = e.get("source_id", "?")

        try:
            structure = parse_structure_json(e["structure_json"])
            result = compute_bvse_barrier(structure, mobile_element=mobile_ion,
                                          resolution=args.resolution, n_jobs=args.jobs)

            updates = {
                "bvse_migration_barrier_eV": result["migration_barrier_eV"],
                "bvse_mobility_class": result["mobility_class"],
                "bvse_percolation_dimensionality": result.get("percolation_dimensionality"),
            }

            if not args.dry_run:
                for field, value in updates.items():
                    store.update_field(sid, "ssb_screening", value, nested_path=field)

            reason = result.get("_skip_reason", "")
            if result["migration_barrier_eV"] is not None:
                barrier_vals.append(result["migration_barrier_eV"])
            elif "oxidation state" in reason:
                skipped_oxi += 1
            elif "percolation" in reason or "path" in reason or "connected" in reason:
                skipped_no_path += 1
            else:
                errors += 1

            class_counts[result["mobility_class"]] += 1

        except Exception as exc:
            errors += 1
            if errors <= 5:
                print(f"  Error [{sid}]: {str(exc)[:60]}")

        processed += 1

        if (idx + 1) % 200 == 0:
            elapsed = time.time() - t_start
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            pct = (idx + 1) / len(entries) * 100
            eta = (len(entries) - (idx + 1)) / rate if rate > 0 else 0
            mean_bar = np.mean(barrier_vals) if barrier_vals else 0
            print(f"  {idx+1}/{len(entries)} ({pct:.0f}%) | "
                  f"rate:{rate:.1f} ent/s | ETA:{eta/60:.0f}min | "
                  f"mean:{mean_bar:.3f} eV | "
                  f"ok:{len(barrier_vals)} oxi:{skipped_oxi} nopath:{skipped_no_path} err:{errors}")

        # Checkpoint every batch-size entries
        if not args.dry_run and (processed - last_checkpoint) >= args.batch_size:
            store.checkpoint()
            last_checkpoint = processed

    elapsed = time.time() - t_start
    print(f"\n{'─' * WIDTH}")
    print(f"  Complete: {processed} entries processed")
    print(f"  Time: {elapsed/60:.1f} min ({processed/elapsed:.1f} ent/s)")
    print(f"  Barriers computed: {len(barrier_vals)}")
    print(f"  Skipped (no oxi states): {skipped_oxi}")
    print(f"  Skipped (no pathway): {skipped_no_path}")
    print(f"  Errors: {errors}")

    print(f"\n  BVSE mobility class distribution:")
    for cls_name in ["superionic", "good", "moderate", "poor", "none"]:
        count = class_counts.get(cls_name, 0)
        pct = count / max(processed, 1) * 100
        print(f"    {cls_name:15s}: {count:,} ({pct:.1f}%)")

    if barrier_vals:
        print(f"\n  Migration barrier statistics (eV):")
        print(f"    Min: {min(barrier_vals):.3f}")
        print(f"    Max: {max(barrier_vals):.3f}")
        print(f"    Mean: {np.mean(barrier_vals):.3f}")
        print(f"    Median: {np.median(barrier_vals):.3f}")
        for threshold in [0.15, 0.25, 0.50, 0.75]:
            count = sum(1 for b in barrier_vals if b <= threshold)
            print(f"    ≤{threshold:.2f} eV: {count:,} ({count/len(barrier_vals)*100:.1f}%)")

    if not args.dry_run:
        store.checkpoint()
        print(f"\n  Parquet store checkpointed to entries_v3.parquet")
    else:
        print(f"\n  (dry-run — not saved)")

    print("=" * WIDTH)
    store.close()


if __name__ == "__main__":
    main()
