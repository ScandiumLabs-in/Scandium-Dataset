"""Parallel BVSE processor — processes Li/Na entries using multiprocessing.
Launched from nohup; checkpoints every N entries per worker.
"""
import json, os, sys, time, argparse, warnings
from pathlib import Path
from collections import defaultdict
from multiprocessing import Pool, cpu_count
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "dataset"))
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
warnings.filterwarnings("ignore")

PARQUET_PATH = BASE_DIR / "dataset" / "entries_v3.parquet"
INDEX_PATH = BASE_DIR / "dataset" / "entries_v3.index.json"
CHECKPOINT_PATH = BASE_DIR / "dataset" / "bvse_checkpoint.json"

MOBILITY_THRESHOLDS = [
    ("superionic", 0.25),
    ("good", 0.50),
    ("moderate", 0.75),
    ("poor", float('inf')),
]


def process_one(args):
    sid, struct_json, mobile_ion = args
    from pymatgen.core import Structure
    from pymatgen.analysis.bond_valence import BVAnalyzer
    from bvlain import Lain
    result = {"sid": sid, "barrier": None, "cls": "none", "dim": "none", "skip": ""}
    try:
        struct = Structure.from_dict(json.loads(struct_json))
        bva = BVAnalyzer()
        st_oxi = bva.get_oxi_state_decorated_structure(struct)
        lain = Lain(verbose=False)
        lain.read_structure(st_oxi, oxi_check=False)
        lain.bvse_distribution(mobile_ion=f"{mobile_ion}1+", resolution=0.5)
        barriers = lain.percolation_barriers(encut=10.0, n_jobs=1)
        min_barrier = min(v for v in barriers.values())
        if min_barrier == float('inf') or min_barrier < 0:
            result["skip"] = "no connected pathway"
            return result
        eps = 0.05
        dim_map = {1: "1D", 2: "2D", 3: "3D"}
        dims = []
        for d in [1, 2, 3]:
            if barriers[f"E_{d}D"] <= min_barrier + eps:
                dims.append(d)
        percolation_dim = dim_map.get(max(dims), "3D") if dims else "none"
        mobility_class = "poor"
        for cls_name, threshold in MOBILITY_THRESHOLDS:
            if min_barrier < threshold:
                mobility_class = cls_name
                break
        result["barrier"] = round(float(min_barrier), 4)
        result["cls"] = mobility_class
        result["dim"] = percolation_dim
    except Exception as exc:
        err = str(exc)
        if "No BVSE data" in err:
            result["skip"] = "no BV params"
        elif "oxidation state" in err.lower():
            result["skip"] = "oxidation failed"
        elif "min() iterable" in err:
            result["skip"] = "no path"
        else:
            result["skip"] = f"error: {err[:80]}"
    return result


def _write_checkpoint(table, updated_rows, all_ssb, sid_to_idx, all_table_rows):
    """Write updated ssb_screening values back to the Parquet table."""
    import pyarrow as pa
    import pyarrow.parquet as pq
    from dataset_store import _encode_value, _decode_value
    ssb_col = table.column("ssb_screening").to_pylist()
    for table_row in updated_rows:
        # Find the corresponding index in all_* arrays
        sid = _decode_value(table.column("source_id")[table_row].as_py())
        if sid in sid_to_idx:
            ssb_col[table_row] = _encode_value(all_ssb[sid_to_idx[sid]])
    table = table.set_column(
        table.schema.get_field_index("ssb_screening"), "ssb_screening",
        pa.chunked_array([pa.array(ssb_col)])
    )
    pq.write_table(table, PARQUET_PATH, compression="zstd")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=max(1, cpu_count() - 1))
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--max-sites", type=int, default=60)
    args = parser.parse_args()

    print(f"Parallel BVSE processor | workers={args.workers} batch={args.batch_size} max_sites={args.max_sites}")
    print(f"Loading Parquet...")
    import pyarrow.parquet as pq
    t0 = time.time()
    table = pq.read_table(PARQUET_PATH)
    # Decode columns
    from dataset_store import _decode_value, _encode_value
    all_sids = []
    all_structs = []
    all_mobiles = []
    all_ssb = []
    all_rows = []
    for i in range(table.num_rows):
        sid = _decode_value(table.column("source_id")[i].as_py())
        mobile = _decode_value(table.column("mobile_ion")[i].as_py())
        nsites_raw = table.column("nsites")[i].as_py()
        nsites = int(_decode_value(nsites_raw)) if nsites_raw else 999
        struct_raw = table.column("structure_json")[i].as_py()
        struct = _decode_value(struct_raw) if struct_raw else None
        ssb_raw = table.column("ssb_screening")[i].as_py()
        ssb = _decode_value(ssb_raw) if ssb_raw else {}
        if mobile in ("Li", "Na") and struct and nsites <= args.max_sites:
            all_sids.append(sid)
            all_structs.append(struct)
            all_mobiles.append(mobile)
            all_ssb.append(ssb)
            all_rows.append(i)
    print(f"  {len(all_sids):,} Li/Na entries (≤{args.max_sites} sites) loaded in {time.time()-t0:.1f}s")

    # Build lookup: source_id -> index in all_* arrays
    sid_to_idx = {sid: i for i, sid in enumerate(all_sids)}
    all_table_rows = all_rows  # table row indices for each entry
    updated_rows = set()

    # Load checkpoint
    completed_sids = set()
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            completed_sids = set(json.load(f))
        print(f"  Resuming from checkpoint: {len(completed_sids):,} already computed")

    # Build worklist (skip already done)
    worklist = []
    for idx in range(len(all_sids)):
        if all_sids[idx] not in completed_sids:
            worklist.append((all_sids[idx], all_structs[idx], all_mobiles[idx]))
    print(f"  Remaining: {len(worklist):,} entries")

    if not worklist:
        print("  All entries already processed.")
        return

    # Process in batches
    total_processed = len(completed_sids)
    total_ok = 0
    total_skip = 0
    total_err = 0
    barriers = []
    class_counts = defaultdict(int)

    batch_num = 0
    checkpoint_counter = 0
    CHECKPOINT_EVERY_N_BATCHES = 50  # checkpoint every 50 batches (every ~2500 entries at batch=50)
    pool = Pool(processes=args.workers)
    t_start = time.time()
    while worklist:
        batch = worklist[:args.batch_size]
        worklist = worklist[args.batch_size:]
        print(f"  Batch {batch_num}: {len(batch)} entries, {len(worklist)} remaining...", flush=True)
        results = pool.map(process_one, batch)
        # Apply results
        for r in results:
            sid = r["sid"]
            if sid in sid_to_idx:
                idx = sid_to_idx[sid]
                ssb = all_ssb[idx]
                if r["barrier"] is not None:
                    ssb["bvse_migration_barrier_eV"] = r["barrier"]
                    ssb["bvse_mobility_class"] = r["cls"]
                    ssb["bvse_percolation_dimensionality"] = r["dim"]
                    barriers.append(r["barrier"])
                    class_counts[r["cls"]] += 1
                    total_ok += 1
                elif r["skip"]:
                    total_skip += 1
                else:
                    total_err += 1
                completed_sids.add(sid)
                updated_rows.add(all_table_rows[idx])
        total_processed += len(batch)
        batch_num += 1

        # Periodic checkpoint to Parquet
        checkpoint_counter += 1
        if checkpoint_counter >= CHECKPOINT_EVERY_N_BATCHES or not worklist:
            _write_checkpoint(table, updated_rows, all_ssb, sid_to_idx, all_table_rows)
            # Save completed SIDs for resume
            with open(CHECKPOINT_PATH, "w") as f:
                json.dump(list(completed_sids), f)
            rate = total_processed / (time.time() - t_start)
            eta = len(worklist) / rate if rate > 0 and worklist else 0
            print(f"    CHECKPOINT: {total_processed:,} done, {len(worklist):,} remain, "
                  f"{rate:.1f} ent/s, ETA {eta/3600:.1f}h", flush=True)
            checkpoint_counter = 0

    pool.close()
    pool.join()

    elapsed = time.time() - t_start
    print(f"\n{'=' * 60}")
    print(f"  BVSE COMPLETE")
    print(f"  Processed: {total_processed:,}")
    print(f"  Barriers computed: {total_ok}")
    print(f"  Skipped: {total_skip}")
    print(f"  Errors: {total_err}")
    print(f"  Time: {elapsed/60:.1f} min ({total_processed/elapsed:.1f} ent/s)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
