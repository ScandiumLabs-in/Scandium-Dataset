"""Compute energy above hull for JARVIS entries via internal convex hull.

JARVIS-DFT entries (25,673) currently have no energy_above_hull values because
they come from a different DFT methodology (optPBE + TBmBJ). This script builds
internal convex hulls within the JARVIS subset and computes EaH relative to those.

This is an approximate correction — the true hull for JARVIS entries is the
Materials Project convex hull (PAW-PBE). The internal hull gives a first-pass
stability estimate until a proper cross-method correction is developed.

Usage:
    python scripts/compute_jarvis_hull_energy.py
    python scripts/compute_jarvis_hull_energy.py --dry-run
    python scripts/compute_jarvis_hull_energy.py --limit 5000
"""
import json, os, sys, time, argparse, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
import pyarrow as pa
warnings.filterwarnings("ignore")

WIDTH = 60


def main():
    parser = argparse.ArgumentParser(description="Compute EaH for JARVIS entries via internal hull")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"
    
    print("=" * WIDTH)
    print("  JARVIS ENERGY ABOVE HULL")
    print("  Internal convex hull within JARVIS subset")
    print("=" * WIDTH)
    
    print("\nLoading entries from typed Parquet...")
    t0 = time.time()
    sys.path.insert(0, str(BASE_DIR))
    from dataset.dataset_store import DatasetStore
    store = DatasetStore.open()
    print(f"  {store.num_entries:,} entries ({time.time()-t0:.1f}s)")
    
    # Load all JARVIS entries in one batch (reduced columns)
    print(f"\n  Loading JARVIS entries...")
    jarvis_entries = [
        e for e in store.scan(columns=[
            "source_id", "source", "formula", "elements",
            "energy_above_hull", "formation_energy_per_atom",
        ])
        if e.get("source") == "jarvis"
    ]
    print(f"  {len(jarvis_entries):,} JARVIS entries loaded")
    
    if args.limit:
        jarvis_entries = jarvis_entries[:args.limit]
    
    jarvis_with_eah = sum(1 for e in jarvis_entries if e.get("energy_above_hull") is not None)
    print(f"  JARVIS with EaH already: {jarvis_with_eah}")
    
    from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
    from pymatgen.core import Composition
    
    print(f"\n  Building JARVIS internal convex hulls...")
    
    systems = defaultdict(list)
    for e in jarvis_entries:
        elements = tuple(sorted(set(e.get("elements", []))))
        fe = e.get("formation_energy_per_atom")
        if fe is None:
            continue
        systems[elements].append((e, fe))
    
    print(f"  Chemical systems in JARVIS: {len(systems)}")
    
    TERMINAL_ENERGIES = {
        "O": -4.935, "N": -8.100, "F": -1.500, "Cl": -1.700, 
        "Br": -0.500, "H": -3.300,
    }
    
    hulls = {}
    hull_systems = 0
    hull_failed = 0
    
    for system, entries_in_system in systems.items():
        if len(entries_in_system) < 3:
            continue
        
        compound_entries = []
        for e, fe in entries_in_system:
            try:
                formula = e.get("formula", "")
                comp = Composition(formula)
                total_energy = fe * comp.num_atoms
                compound_entries.append(PDEntry(comp, total_energy, name=e.get("source_id", "")))
            except Exception:
                pass
        
        if len(compound_entries) < 3:
            continue
        
        terminal_entries = []
        for el_symbol in system:
            ref_energy = TERMINAL_ENERGIES.get(el_symbol, 0.0)
            terminal_entries.append(PDEntry(Composition({el_symbol: 1}), ref_energy, name=f"{el_symbol}(ref)"))
        
        all_pd_entries = terminal_entries + compound_entries
        
        try:
            hulls[system] = PhaseDiagram(all_pd_entries)
            hull_systems += 1
        except Exception:
            hull_failed += 1
    
    print(f"  Hulls built: {hull_systems}, failed: {hull_failed}")
    
    print(f"\n  Computing EaH for JARVIS entries...")
    
    computed = 0
    errors = 0
    already_have = 0
    hull_missing = 0
    
    # Batch updates: collect row_idx → new value, then apply once
    col_idx = store._table.schema.get_field_index("energy_above_hull")
    old_col = store._table.column("energy_above_hull")
    new_values = old_col.to_pylist()
    
    t_start = time.time()
    for idx, e in enumerate(jarvis_entries):
        elements = tuple(sorted(set(e.get("elements", []))))
        fe = e.get("formation_energy_per_atom")
        
        if fe is None:
            continue
        
        row_idx = store._index.get(e["source_id"])
        if row_idx is None:
            continue
        
        if new_values[row_idx] is not None:
            already_have += 1
            continue
        
        pd = hulls.get(elements)
        if pd is None:
            hull_missing += 1
            continue
        
        try:
            formula = e.get("formula", "")
            comp = Composition(formula)
            total_energy = fe * comp.num_atoms
            entry = PDEntry(comp, total_energy)
            
            decomp = pd.get_decomp_and_e_above_hull(entry)
            if decomp is not None:
                _, e_above_hull = decomp
                new_values[row_idx] = round(float(e_above_hull), 6)
                computed += 1
            else:
                hull_missing += 1
        except Exception:
            errors += 1
        
        if (idx + 1) % 5000 == 0:
            elapsed = time.time() - t_start
            print(f"  {idx+1}/{len(jarvis_entries)} computed={computed} hull_missing={hull_missing} ({elapsed:.0f}s)")
    
    # Apply batch update to the table
    print(f"  Applying {computed} batch updates to Parquet table...")
    new_col = pa.chunked_array([pa.array(new_values, type=old_col.type)])
    store._table = store._table.set_column(col_idx, "energy_above_hull", new_col)
    store._dirty = True
    
    print(f"\n  JARVIS EaH results:")
    print(f"    Already had EaH: {already_have:,}")
    print(f"    Computed (new): {computed:,}")
    print(f"    No hull available: {hull_missing:,}")
    print(f"    Errors: {errors:,}")
    
    # Print examples
    print(f"\n  Sample JARVIS entries with computed EaH:")
    shown = 0
    for e in jarvis_entries:
        row_idx = store._index.get(e["source_id"])
        if row_idx is None:
            continue
        eah = new_values[row_idx]
        if eah is not None:
            if shown < 5:
                formula = e.get("formula", "")
                fe = e.get("formation_energy_per_atom", 0)
                print(f"    {formula:30s} FE={fe:+.4f} EaH={eah:.4f}")
                shown += 1
    
    total_eah = sum(1 for v in new_values if v is not None)
    print(f"\n  Overall EaH coverage after update: {total_eah:,}/{store.num_entries:,} ({total_eah/store.num_entries*100:.1f}%)")
    
    if args.dry_run:
        print(f"\n  (dry-run — not saved)")
        store._dirty = False
        store.close()
    else:
        output_path = DATASET_PATH / "entries_v4_typed.parquet"
        print(f"\n  Writing to {output_path}...")
        t_write = time.time()
        store.checkpoint()
        print(f"  Done ({time.time()-t_write:.1f}s)")
    
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
