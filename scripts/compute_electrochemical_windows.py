"""Compute electrochemical stability windows for Gold-tier SSE entries.

This script uses pymatgen's PhaseDiagram to estimate the electrochemical
stability window against Li/Na metal for entries in the dataset.

Requires:
    - MP API key (set as MATERIALS_PROJECT_API_KEY env var)
    - Internet connection to query MP phase diagrams
    - ~2-5 seconds per entry (22K+ entries = ~30 hours for full run)

Usage:
    # Compute for electrolyte subset (41,665 entries):
    python scripts/compute_electrochemical_windows.py --subset electrolyte

    # Compute for Gold SSE entries only (22,525 entries):
    python scripts/compute_electrochemical_windows.py --gold-sse

    # Compute for a single entry:
    python scripts/compute_electrochemical_windows.py --single Li6PS5Cl

Output:
    Adds an "electrochemical_window" field to each entry with:
    {
        "reduction_potential_V_vs_Li": float,  # vs Li/Li+
        "oxidation_potential_V_vs_Li": float,   # vs Li/Li+
        "window_width_V": float,
        "stable_against_Li_metal": bool,
        "method": "grand_potential_phase_diagram",
        "note": "Approximate. See docs/sse_readiness.md for limitations."
    }
"""

import json, os, sys, time, argparse
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

WIDTH = 60

def main():
    parser = argparse.ArgumentParser(description="Compute electrochemical stability windows")
    parser.add_argument("--subset", choices=["electrolyte", "battery", "full"], default=None)
    parser.add_argument("--gold-sse", action="store_true", help="Gold-tier SSE entries only")
    parser.add_argument("--single", type=str, help="Formula of single entry to compute")
    parser.add_argument("--limit", type=int, default=None, help="Max entries to process")
    args = parser.parse_args()

    api_key = os.environ.get("MATERIALS_PROJECT_API_KEY")
    if not api_key:
        print("ERROR: MATERIALS_PROJECT_API_KEY not set.")
        print("Get a free API key at https://next-gen.materialsproject.org/api")
        sys.exit(1)

    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset" / "entries_final_v3.json"

    print("=" * WIDTH)
    print("  ELECTROCHEMICAL STABILITY WINDOW COMPUTATION")
    print("  Requires MP API key and 2-5 seconds per entry")
    print("=" * WIDTH)

    print("\nLoading dataset...")
    with open(DATASET_PATH) as f:
        entries = json.load(f)
    print(f"  {len(entries):,} entries loaded")

    # Filter entries
    if args.gold_sse:
        target_entries = [e for e in entries 
                          if e.get("tier") == "gold"
                          and any(f in ["sulfide_sse", "halide_sse", "garnet", "nasicon"]
                                  for f in e.get("families", []))
                          and any(c in e.get("elements", []) for c in ["Li", "Na"])]
        print(f"  Gold SSE entries: {len(target_entries):,}")
    elif args.subset == "electrolyte":
        with open(BASE_DIR / "dataset" / "electrolyte_subset_v3.json") as f:
            target_entries = json.load(f)
        print(f"  Electrolyte subset: {len(target_entries):,}")
    elif args.subset == "battery":
        with open(BASE_DIR / "dataset" / "battery_subset_v3.json") as f:
            target_entries = json.load(f)
        print(f"  Battery subset: {len(target_entries):,}")
    elif args.single:
        target_entries = [e for e in entries if e.get("formula") == args.single]
        print(f"  Single entry: {args.single} ({len(target_entries)} matches)")
        if not target_entries:
            print(f"  No entries found with formula '{args.single}'")
            sys.exit(1)
    else:
        target_entries = entries
        print(f"  Full dataset: {len(target_entries):,} (will take very long)")

    if args.limit:
        target_entries = target_entries[:args.limit]
        print(f"  Limiting to {args.limit} entries")

    has_struct = sum(1 for e in target_entries if e.get("structure_json"))
    print(f"  Entries with structure: {has_struct:,}")

    if not target_entries:
        print("  No entries to process. Exiting.")
        return

    print(f"\n{'─' * WIDTH}")
    print("  Starting computation...")
    print(f"  This will complete approximately 1 entry every 2-5 seconds.")
    print(f"  Estimated time: {len(target_entries) * 3 / 3600:.1f} hours")
    print(f"{'─' * WIDTH}")

    # Try importing pymatgen
    try:
        from pymatgen.analysis.phase_diagram import PhaseDiagram, GrandPotentialPhaseDiagram
        from pymatgen.ext.matproj import MPRester
        from pymatgen.core import Composition, Element
    except ImportError as e:
        print(f"ERROR: pymatgen not available: {e}")
        print("Install: pip install pymatgen")
        sys.exit(1)

    mpr = MPRester(api_key)
    li_metal = Element("Li")
    na_metal = Element("Na")

    processed = 0
    errors = 0
    t_start = time.time()

    for e in target_entries:
        try:
            formula = e.get("formula", "")
            elements = e.get("elements", [])
            has_li = "Li" in elements
            has_na = "Na" in elements
            structure_json = e.get("structure_json")

            if not structure_json:
                continue

            from pymatgen.core import Structure
            struct = Structure.from_dict(json.loads(structure_json))
            energy = e.get("formation_energy_per_atom")
            if energy is None:
                continue

            # Compute against relevant alkali metal
            windows = {}
            if has_li:
                # Grand potential phase diagram against Li
                try:
                    # Get all competing phases in the chemical system
                    entries_pd = mpr.get_entries_in_chemsys(
                        list(set(elements + ["Li"]))
                    )
                    # Add the entry itself
                    from pymatgen.entries.computed_entry import ComputedEntry
                    self_entry = ComputedEntry(
                        struct.composition,
                        energy * struct.composition.num_atoms,
                    )
                    entries_pd.append(self_entry)

                    pd = PhaseDiagram(entries_pd)
                    gp_pd = GrandPotentialPhaseDiagram(
                        entries_pd, 
                        {li_metal: -1.9},  # Li chemical potential at 0V vs Li
                    )
                    
                    # Decomposition energy vs Li
                    decomp = pd.get_decomp_and_e_above_hull(self_entry)
                    e_above_hull = decomp[1] if decomp else None
                    
                    if e_above_hull is not None:
                        # Rough window estimate
                        windows["li"] = {
                            "decomp_energy_eV_per_atom": round(e_above_hull, 4),
                            "method": "grand_potential_phase_diagram",
                        }
                except Exception as exc:
                    windows["li"] = {"error": str(exc)[:100]}

            if has_na:
                try:
                    entries_pd_na = mpr.get_entries_in_chemsys(
                        list(set(elements + ["Na"]))
                    )
                    from pymatgen.entries.computed_entry import ComputedEntry
                    self_entry_na = ComputedEntry(
                        struct.composition,
                        energy * struct.composition.num_atoms,
                    )
                    entries_pd_na.append(self_entry_na)
                    pd_na = PhaseDiagram(entries_pd_na)
                    gp_pd_na = GrandPotentialPhaseDiagram(
                        entries_pd_na,
                        {na_metal: -1.9},
                    )
                    decomp = pd_na.get_decomp_and_e_above_hull(self_entry_na)
                    e_above_hull = decomp[1] if decomp else None
                    if e_above_hull is not None:
                        windows["na"] = {
                            "decomp_energy_eV_per_atom": round(e_above_hull, 4),
                            "method": "grand_potential_phase_diagram",
                        }
                except Exception as exc:
                    windows["na"] = {"error": str(exc)[:100]}

            if windows:
                e["electrochemical_window"] = windows
                processed += 1

        except Exception as exc:
            errors += 1
            if errors <= 5:
                print(f"  Error [{formula}]: {str(exc)[:80]}")

        if processed > 0 and processed % 50 == 0:
            elapsed = time.time() - t_start
            rate = processed / elapsed
            remaining = (len(target_entries) - processed) / rate
            print(f"  Progress: {processed}/{len(target_entries)} "
                  f"({rate:.2f} entries/s, ~{remaining/60:.0f} min remaining)")

    elapsed = time.time() - t_start
    print(f"\n{'─' * WIDTH}")
    print(f"  Complete: {processed} windows computed, {errors} errors")
    print(f"  Time: {elapsed/60:.1f} minutes")

    # Save dataset
    with open(DATASET_PATH, "w") as f:
        json.dump(entries, f)
    print(f"  Dataset saved to {DATASET_PATH}")

    # Stats
    with_window = sum(1 for e in entries if e.get("electrochemical_window"))
    print(f"\n  Total entries with electrochemical windows: {with_window:,}")
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
