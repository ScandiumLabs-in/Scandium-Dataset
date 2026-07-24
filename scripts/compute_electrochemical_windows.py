"""Compute electrochemical stability windows from dataset's own formation energies.

Self-contained — no MP API needed. Uses pymatgen PhaseDiagram built from the
266k entries already in the dataset. Fills the ssb_screening block with:
  - stability_window_low_V
  - stability_window_high_V
  - interfacial_reaction_energy_vs_Li_eV_atom
  - passivating_interphase

Algorithm per entry:
  1. Group entries by chemical system (sorted element tuple).
  2. Build a local convex hull from *all* entries in that system.
  3. Compute decomposition energy (E_above_hull) from the local hull.
  4. For the grand potential window against Li/Na:
     a. Add the reservoir element to the chemical system.
     b. Build a GrandPotentialPhaseDiagram at varying μ.
     c. Find the voltage range where E_hull(μ) ≈ 0.

Usage:
    python scripts/compute_electrochemical_windows.py                    # full dataset
    python scripts/compute_electrochemical_windows.py --subset battery   # battery only
    python scripts/compute_electrochemical_windows.py --subset gold      # gold tier only
    python scripts/compute_electrochemical_windows.py --limit 1000      # first 1000 entries
"""

import json, os, sys, time, argparse, itertools, warnings, math
from pathlib import Path
from collections import defaultdict
warnings.filterwarnings("ignore")

WIDTH = 60

def main():
    parser = argparse.ArgumentParser(description="Compute electrochemical stability windows")
    parser.add_argument("--subset", choices=["battery", "electrolyte", "gold", "full"], default="full")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-system-size", type=int, default=3,
                        help="Minimum entries in a chemical system to build a hull (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Don't save results, just print stats")
    parser.add_argument("--output", type=str, default=None,
                        help="Custom output path (default: dataset/entries_final_v3.json)")
    args = parser.parse_args()
    
    # SAFETY: refuse to save a limited run back to the dataset
    if args.limit and not args.dry_run and args.output is None:
        print("ERROR: Refusing to save limited runs. Use --dry-run or --output to specify a safe path.")
        print("  python scripts/compute_electrochemical_windows.py --limit 100 --dry-run")
        sys.exit(1)

    try:
        from pymatgen.analysis.phase_diagram import PhaseDiagram, GrandPotentialPhaseDiagram, PDEntry
        from pymatgen.core import Composition, Element
    except ImportError as e:
        print(f"ERROR: pymatgen not available: {e}")
        print("Install: pip install pymatgen")
        sys.exit(1)

    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"

    print("=" * WIDTH)
    print("  ELECTROCHEMICAL WINDOWS — SELF-CONTAINED")
    print("  Using dataset's own formation energies (no MP API)")
    print("=" * WIDTH)

    # Load source dataset
    print("\nLoading entries...")
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        all_entries = json.load(f)
    print(f"  {len(all_entries):,} total entries")

    # Select working subset
    if args.subset == "battery":
        with open(DATASET_PATH / "battery_candidate_subset_v1.json") as f:
            entries = json.load(f)
        entries = [e for e in entries if any(el in e.get("elements", []) for el in ["Li", "Na"])]
    elif args.subset == "electrolyte":
        with open(DATASET_PATH / "solid_electrolyte_candidate_subset_v1.json") as f:
            entries = json.load(f)
        entries = [e for e in entries if any(el in e.get("elements", []) for el in ["Li", "Na"])]
    elif args.subset == "gold":
        entries = [e for e in all_entries if e.get("tier") == "gold" and any(el in e.get("elements", []) for el in ["Li", "Na"])]
    else:
        entries = all_entries

    if args.limit:
        entries = entries[:args.limit]
    print(f"  Working subset: {len(entries):,} entries")

    # Reference energies for terminal (pure element) entries
    # Standard PBE reference energies from pymatgen/MP
    # Solid elements: 0 eV/atom (elemental ground state)
    # Gaseous elements: corrected to match PBE formation energies
    TERMINAL_REF_ENERGIES = {
        "O": -4.935,   # O2 gas correction (standard PBE)
        "N": -8.100,   # N2 gas correction
        "F": -1.500,   # F2 gas correction (approx)
        "Cl": -1.700,  # Cl2 gas correction (approx)
        "Br": -0.500,  # Br2 liquid correction (approx)
        "H": -3.300,   # H2 gas correction
    }
    
    def make_terminal_entries(system):
        """Create PDEntry objects for pure elements in the system."""
        entries = []
        for el_symbol in system:
            el = Element(el_symbol)
            comp = Composition({el: 1})
            ref_energy = TERMINAL_REF_ENERGIES.get(el_symbol, 0.0)
            entries.append(PDEntry(comp, ref_energy, name=f"{el_symbol}(ref)"))
        return entries

    # Build hulls from ALL entries (full 266k) for maximum coverage
    print("\nBuilding convex hulls from ALL entries (full dataset)...")
    all_systems = defaultdict(list)
    for e in all_entries:
        fe = e.get("formation_energy_per_atom") or e.get("formation_energy")
        if fe is None:
            continue
        system = tuple(sorted(e.get("elements", [])))
        all_systems[system].append((e, fe))
    
    hulls = {}
    hull_built = 0
    hull_failed = 0
    for system, entries_in_system in all_systems.items():
        if len(entries_in_system) < args.min_system_size:
            continue
        
        # Build compound entries
        compound_entries = []
        for e, fe in entries_in_system:
            try:
                formula = e.get("formula", "")
                comp = Composition(formula)
                total_energy = fe * comp.num_atoms
                compound_entries.append(PDEntry(comp, total_energy))
            except Exception:
                pass
        
        if len(compound_entries) < args.min_system_size:
            continue
        
        # Add terminal entries (pure elements) — required for PhaseDiagram
        terminal_entries = make_terminal_entries(system)
        all_pd_entries = terminal_entries + compound_entries
        
        try:
            hulls[system] = PhaseDiagram(all_pd_entries)
            hull_built += 1
        except Exception as exc:
            hull_failed += 1
            if hull_failed <= 5:
                print(f"  Hull failed for {system}: {str(exc)[:80]}")

    print(f"  Built {hull_built:,} hulls, {hull_failed:,} failed ({len(all_systems):,} systems total)")
    
    # Now select the working subset for computation
    # Only entries with Li or Na as mobile ion, hull-covered, and with formation energy
    valid = []
    for e in entries:
        elements = e.get("elements", [])
        if not any(el in elements for el in ["Li", "Na"]):
            continue
        fe = e.get("formation_energy_per_atom") or e.get("formation_energy")
        if fe is None:
            continue
        system = tuple(sorted(elements))
        if system in hulls:
            e["_fe"] = fe
            e["_system"] = system
            valid.append(e)
    print(f"  Li/Na entries in hull-covered systems: {len(valid):,}")

    if not valid:
        print("No entries in hull-covered systems. Try reducing --min-system-size.")
        return

    # Pre-build PhaseDiagrams INCLUDING the mobile element for each system
    # so we don't rebuild for every entry
    print("\nBuilding combined hulls with Li/Na...")
    combined_hulls = {}  # (system, mobile_el_str) -> PhaseDiagram
    for system, pd in hulls.items():
        for mobile in ("Li", "Na"):
            if mobile in system:
                # Mobile element is already in the system — use the same Pd
                combined_hulls[(system, mobile)] = pd
            else:
                # Build a new Pd including the mobile element
                extended_system = tuple(sorted(set(system + (mobile,))))
                
                # Add existing terminal entries + mobile terminal + compound entries
                mobile_terminal = PDEntry(Composition({mobile: 1}), 0.0, name=f"{mobile}(ref)")
                try:
                    grand_pd = PhaseDiagram(list(pd.all_entries) + [mobile_terminal])
                    combined_hulls[(system, mobile)] = grand_pd
                except Exception:
                    pass
    print(f"  Combined hulls built: {len(combined_hulls):,}")

    LI_METAL_ENERGY = 0.0
    NA_METAL_ENERGY = 0.0

    def compute_stability_window(pd, entry_pd, mobile_element, combined_pd):
        """Compute the electrochemical stability window using grand potential scan.
        
        pd: PhaseDiagram for the chemical system (without mobile element reservoir)
        entry_pd: PDEntry for the target material
        mobile_element: "Li" or "Na"
        combined_pd: PhaseDiagram including the mobile element as a terminal
        
        Returns dict with window_V, decomp_energy, passivating_flag.
        """
        try:
            # Check formation energy relative to base hull
            decomp = pd.get_decomp_and_e_above_hull(entry_pd)
            if decomp is None:
                return None
            _, e_above_hull = decomp
            if e_above_hull > 0.5:
                return None
            
            mobile_el = Element(mobile_element)
            n_mobile = entry_pd.composition.get(mobile_el, 0)
            
            # Scan μ from 0V (pure metal) to -5V vs M/M+
            # Compute grand potential of the entry vs competing phases at each μ
            stable_range = [None, None]
            prev_stable = None
            
            for mu_V in [x * 0.1 for x in range(0, 51)]:
                mu = -mu_V
                gp_entry = entry_pd.energy - mu * n_mobile
                
                # Minimum grand potential among competing phases
                gp_comp = float('inf')
                for other in combined_pd.all_entries:
                    if id(other) == id(entry_pd):
                        continue
                    n_other = other.composition.get(mobile_el, 0) if mobile_el in other.composition.elements else 0
                    gp_other = other.energy - mu * n_other
                    if gp_other < gp_comp:
                        gp_comp = gp_other
                
                is_stable = gp_entry <= gp_comp + 1e-4
                
                if prev_stable is None:
                    prev_stable = is_stable
                elif is_stable != prev_stable:
                    mid_V = mu_V - 0.05
                    if prev_stable and not is_stable:
                        stable_range[1] = mid_V
                    elif not prev_stable and is_stable:
                        stable_range[0] = mid_V
                    prev_stable = is_stable
            
            if prev_stable:
                if stable_range[0] is None:
                    stable_range[0] = 0.0
                if stable_range[1] is None:
                    stable_range[1] = 5.0
            
            # Passivating interphase heuristic
            passivating = False
            if stable_range[0] is not None and stable_range[0] > 0.1:
                mu = 0.0
                gp_products = []
                for other in combined_pd.all_entries:
                    if id(other) == id(entry_pd):
                        continue
                    n_other = other.composition.get(mobile_el, 0) if mobile_el in other.composition.elements else 0
                    gp = other.energy - mu * n_other
                    gp_products.append((gp, other))
                
                if gp_products:
                    gp_products.sort(key=lambda x: x[0])
                    best_decomp = gp_products[0][1]
                    solid_elements = [el.symbol for el in best_decomp.composition.elements 
                                    if el.symbol not in ("O2", "N2", "Cl2", "F2", "S")]
                    if len(solid_elements) >= 2:
                        passivating = True
            
            result = {
                "stability_window_low_V": round(stable_range[0], 3) if stable_range[0] is not None else None,
                "stability_window_high_V": round(stable_range[1], 3) if stable_range[1] is not None else None,
                "decomp_energy_eV_per_atom": round(e_above_hull, 4),
                "passivating_interphase": passivating,
                "method": "grand_potential_scan"
            }
            
            if stable_range[0] is not None and stable_range[1] is not None:
                result["window_width_V"] = round(stable_range[1] - stable_range[0], 3)
            
            return result
        
        except Exception as exc:
            return {"error": str(exc)[:100]}

    # Process entries
    print(f"\n{'─' * WIDTH}")
    print("  Computing stability windows...")
    print(f"{'─' * WIDTH}")

    processed = 0
    errors = 0
    skipped = 0
    windows_found = 0
    t_start = time.time()

    for idx, e in enumerate(valid):
        system = e["_system"]
        pd = hulls[system]
        
        # Create PDEntry for this specific entry
        try:
            formula = e.get("formula", "")
            fe = e.get("_fe")
            comp = Composition(formula)
            total_energy = fe * comp.num_atoms
            entry_pd = PDEntry(comp, total_energy)
        except Exception:
            errors += 1
            continue
        
        # Determine mobile element (preferred: Li > Na)
        elements_set = e.get("elements", [])
        mobile_el = "Li" if "Li" in elements_set else "Na"
        
        # Get the combined hull (with mobile element as terminal)
        combined_key = (system, mobile_el)
        combined_pd = combined_hulls.get(combined_key, pd)
        
        # Compute window
        result = compute_stability_window(pd, entry_pd, mobile_el, combined_pd)
        
        # Fill ssb_screening block
        if "ssb_screening" not in e:
            e["ssb_screening"] = {}
        
        if result and "error" not in result:
            e["ssb_screening"]["stability_window_low_V"] = result["stability_window_low_V"]
            e["ssb_screening"]["stability_window_high_V"] = result["stability_window_high_V"]
            e["ssb_screening"]["window_width_V"] = result.get("window_width_V")
            e["ssb_screening"]["interfacial_reaction_energy_vs_Li_eV_atom"] = result["decomp_energy_eV_per_atom"]
            e["ssb_screening"]["passivating_interphase"] = result["passivating_interphase"]
            windows_found += 1
        elif result:
            errors += 1
        
        processed += 1
        
        if processed % 100 == 0:
            elapsed = time.time() - t_start
            rate = processed / elapsed if elapsed > 0 else 0
            pct = processed / len(valid) * 100
            eta = (len(valid) - processed) / rate if rate > 0 else 0
            print(f"  {processed}/{len(valid)} ({pct:.0f}%) "
                  f"| {windows_found} windows | {rate:.1f} ent/s | ETA {eta/60:.0f}min")

    elapsed = time.time() - t_start
    print(f"\n{'─' * WIDTH}")
    print(f"  Complete: {processed} processed, {windows_found} windows, {errors} errors, {skipped} skipped")
    print(f"  Time: {elapsed/60:.1f} min ({processed/elapsed:.1f} entries/s)")

    # Determine output path — NEVER overwrite the main dataset when running on a subset
    if args.subset == "battery":
        output_path = DATASET_PATH / "battery_candidate_subset_v1.json"
        save_data = entries
    elif args.subset == "electrolyte":
        output_path = DATASET_PATH / "solid_electrolyte_candidate_subset_v1.json"
        save_data = entries
    elif args.subset == "gold":
        output_path = DATASET_PATH / "gold_subset_v1.json"
        save_data = entries
    else:
        output_path = DATASET_PATH / "entries_final_v3.json"
        save_data = all_entries

    if args.dry_run:
        print("  (dry-run — not saved)")
    else:
        with open(output_path, "w") as f:
            json.dump(save_data, f)
        print(f"  Saved to {output_path}")
    
    # Stats
    with_window = 0
    for entry_batch in [all_entries if args.subset == "full" else entries]:
        for entry in entry_batch:
            ss = entry.get("ssb_screening", {})
            if ss.get("stability_window_low_V") is not None:
                with_window += 1
    
    print(f"\n  Entries with stability windows: {with_window:,}")
    
    # Distribution
    windows = []
    for entry_batch in [all_entries if args.subset == "full" else entries]:
        for entry in entry_batch:
            ss = entry.get("ssb_screening", {})
            low = ss.get("stability_window_low_V")
            high = ss.get("stability_window_high_V")
            if low is not None and high is not None:
                windows.append(high - low)
    
    if windows:
        print(f"  Window width distribution (V):")
        for threshold in [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]:
            count = sum(1 for w in windows if w >= threshold)
            print(f"    ≥{threshold:.1f} V: {count:,} ({count/len(windows)*100:.1f}%)")
    
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
