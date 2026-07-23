"""Predict oxidation states for all entries using bond valence analysis.

Fills each entry with:
  - oxidation_states: dict of {element: average_oxidation_state}
  - predicted_oxidation_states_valid: bool

Usage:
    python scripts/compute_oxidation_states.py
    python scripts/compute_oxidation_states.py --limit 10000
    python scripts/compute_oxidation_states.py --dry-run
"""
import json, os, sys, time, argparse, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
warnings.filterwarnings("ignore")

WIDTH = 60

COMMON_OXIDATION = {
    "Li": [1], "Na": [1], "K": [1], "Rb": [1], "Cs": [1],
    "Mg": [2], "Ca": [2], "Sr": [2], "Ba": [2],
    "Al": [3], "Ga": [3], "In": [3],
    "Si": [4], "Ge": [4], "Sn": [2, 4], "Pb": [2, 4],
    "P": [5], "As": [3, 5], "Sb": [3, 5], "Bi": [3, 5],
    "O": [-2], "S": [-2, 4, 6], "Se": [-2, 4, 6], "Te": [-2, 4, 6],
    "F": [-1], "Cl": [-1], "Br": [-1], "I": [-1],
    "N": [-3], "H": [1],
    "Ti": [4], "V": [3, 5], "Cr": [3, 6], "Mn": [2, 4, 7],
    "Fe": [2, 3], "Co": [2, 3], "Ni": [2], "Cu": [1, 2],
    "Zn": [2], "Y": [3], "Zr": [4], "Nb": [5], "Mo": [4, 6],
    "La": [3], "Ce": [3, 4], "Pr": [3], "Nd": [3], "Sm": [3],
    "Eu": [2, 3], "Gd": [3], "Tb": [3, 4], "Dy": [3], "Ho": [3],
    "Er": [3], "Tm": [3], "Yb": [2, 3], "Lu": [3],
    "Ta": [5], "W": [6], "B": [3], "C": [4], "Sc": [3],
    "Hg": [1, 2],
}


def parse_formula(formula):
    import re
    parts = re.findall(r'([A-Z][a-z]*)(\d*\.?\d*)', formula)
    return {el: float(cnt) if cnt else 1.0 for el, cnt in parts}


def heuristic_oxidation_states(formula_dict):
    elements = list(formula_dict.keys())
    anions = {"O", "S", "Se", "Te", "F", "Cl", "Br", "I", "N", "P", "As", "Sb"}
    cation_els = [el for el in elements if el not in anions]
    anion_els = [el for el in elements if el in anions]
    if not anion_els:
        return {el: 0.0 for el in elements}
    result = {}
    assigned_anions = 0.0
    for el in elements:
        states = COMMON_OXIDATION.get(el, [0])
        if el in anions:
            result[el] = float(min(states))
            assigned_anions += result[el] * formula_dict[el]
        else:
            result[el] = float(max(states))
    total_charge = sum(result[el] * formula_dict[el] for el in elements)
    if abs(total_charge) > 0.5 and cation_els:
        scale = -assigned_anions / max(abs(total_charge - assigned_anions), 0.01)
        for el in cation_els:
            result[el] = round(result[el] * scale, 1)
    return result


def main():
    parser = argparse.ArgumentParser(description="Predict oxidation states")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"
    
    print("=" * WIDTH)
    print("  OXIDATION STATE PREDICTION")
    print("=" * WIDTH)
    
    print("\nLoading entries...")
    t0 = time.time()
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        all_entries = json.load(f)
    print(f"  {len(all_entries):,} entries ({time.time()-t0:.1f}s)")
    
    if args.limit:
        all_entries = all_entries[:args.limit]
        print(f"  Limited to {args.limit} entries")
    
    try:
        from pymatgen.analysis.bond_valence import BVAnalyzer
        from pymatgen.core import Structure
        bva = BVAnalyzer()
        bva_available = True
        print("  BVAnalyzer available")
    except Exception:
        bva_available = False
        print("  BVAnalyzer not available, heuristic only")
    
    import json as _json
    
    print(f"\n{'─' * WIDTH}")
    print("  Assigning oxidation states...")
    
    bva_success = 0
    heuristic_assigned = 0
    errors = 0
    
    for idx, e in enumerate(all_entries):
        formula = e.get("formula", "")
        formula_dict = parse_formula(formula)
        e["oxidation_states"] = {}
        assigned = False
        
        if bva_available and e.get("structure_json"):
            try:
                struct_dict = _json.loads(e["structure_json"])
                structure = Structure.from_dict(struct_dict)
                oxi_states = bva.get_valences(structure)
                if oxi_states:
                    element_oxi = defaultdict(list)
                    for site, oxi in zip(structure, oxi_states):
                        element_oxi[site.specie.symbol].append(float(oxi))
                    e["oxidation_states"] = {el: round(sum(vals)/len(vals), 2) for el, vals in element_oxi.items()}
                    e["predicted_oxidation_states_valid"] = True
                    bva_success += 1
                    assigned = True
            except Exception:
                pass
        
        if not assigned:
            oxi = heuristic_oxidation_states(formula_dict)
            e["oxidation_states"] = oxi
            e["predicted_oxidation_states_valid"] = False
            heuristic_assigned += 1
        
        if (idx + 1) % 10000 == 0:
            print(f"  {idx+1}/{len(all_entries)} | BVA:{bva_success} Heuristic:{heuristic_assigned}")
    
    print(f"\n  BVA: {bva_success:,}, Heuristic: {heuristic_assigned:,}, Total: {bva_success+heuristic_assigned:,}/{len(all_entries):,}")
    
    if args.dry_run:
        print(f"\n  (dry-run)")
    else:
        output_path = DATASET_PATH / "entries_final_v3.json"
        print(f"\n  Writing...")
        t_write = time.time()
        with open(output_path, "w") as f:
            json.dump(all_entries, f)
        print(f"  Done ({time.time()-t_write:.1f}s)")
    
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
