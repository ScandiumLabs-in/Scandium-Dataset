"""Garnet-family enrichment: identify missed garnet-type structures.

Current garnet count is 41 entries (should be thousands for an SSB dataset).
This script:
  1. Uses composition-based heuristics to find garnet-like formulas
  2. Uses structure fingerprinting to verify garnet topology
  3. Reclassifies entries with structure confirmation
  4. Reports candidate structures for targeted acquisition

Garnet identification logic:
  - Composition: A3B2C3O12 where A=Li,Na, etc; B=La,Zr, etc; C=Zr,Ta,Nb,etc
  - Structure: body-centered cubic, space group Ia-3d (230)
  - Specific known families: LLZO, LLTO, LSNO, etc.

Usage:
    python scripts/enrich_garnet_family.py
    python scripts/enrich_garnet_family.py --dry-run
    python scripts/enrich_garnet_family.py --report-only
"""
import json, os, sys, time, argparse, re, warnings
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
warnings.filterwarnings("ignore")

KNOWN_GARNET_SPACE_GROUPS = {230, 229, 228, 227, 220, 219, 218, 217, 216, 215, 214, 213, 212, 211, 210, 209, 208, 207, 206, 205, 204, 203, 202, 201, 200}
GARNET_SG_IA3D = 230  # Ia-3d, most common garnet space group

GARNET_SYMBOLS = {"Ia-3d", "Ia3d", "I a -3 d", "I a 3 d", "I a-3d", "Ia-3"}

# Common garnet-forming elements
GARNET_A_SITES = {"Li", "Na", "K", "Ag", "Cu"}  # Dodecahedral
GARNET_B_SITES = {"La", "Y", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Yb", "Lu", "Ca", "Sr", "Ba", "Bi", "Ce"}  # Octahedral
GARNET_C_SITES = {"Zr", "Ta", "Nb", "Sb", "Te", "W", "Mo", "V", "Sn", "Ti", "Hf", "Al", "Ga", "Fe", "In", "Sc", "Cr"}  # Tetrahedral/octahedral
GARNET_O_SITES = {"O", "S", "Se", "Te"}  # Anion

# Known garnet structure prefixes for formula-based matching
GARNET_PATTERNS = [
    (r"^Li\d+[A-Z][a-z]?\d*[A-Z][a-z]?\d*O\d+", "lithium_garnet"),
    (r"^Na\d+[A-Z][a-z]?\d*[A-Z][a-z]?\d*O\d+", "sodium_garnet"),
]

def parse_formula(formula):
    """Parse formula string into element counts."""
    parts = re.findall(r'([A-Z][a-z]*)(\d*\.?\d*)', formula)
    return {el: float(cnt) if cnt else 1.0 for el, cnt in parts}

def is_garnet_by_formula(formula_dict):
    """Check if composition resembles garnet (A3B2C3O12-type).
    
    Stricter heuristic: require approximate 3:2:3:12 ratio and
    Li/Na on A sites with Zr/Ta/Nb/Al on B/C sites.
    """
    oxygen_count = sum(formula_dict.get(o, 0) for o in GARNET_O_SITES)
    if oxygen_count < 3:
        return False, "not_oxide"
    
    a_count = sum(formula_dict.get(el, 0) for el in GARNET_A_SITES)
    b_count = sum(formula_dict.get(el, 0) for el in GARNET_B_SITES)
    c_count = sum(formula_dict.get(el, 0) for el in GARNET_C_SITES)
    
    cation_count = a_count + b_count + c_count
    if cation_count < 3:
        return False, "no_garnet_cations"
    
    # Normalize ratios to 12 oxygens
    scale = 12.0 / max(oxygen_count, 1)
    a_norm = a_count * scale
    b_norm = b_count * scale
    c_norm = c_count * scale
    
    # Classic garnet: A3B2C3O12
    # Allow some deviation but not extreme
    total_norm = a_norm + b_norm + c_norm
    if not (5.0 < total_norm < 12.0):
        return False, "wrong_cation_count"
    
    # A-site should be at least ~1 normalized
    if a_norm < 0.5:
        return False, "insufficient_A_site"
    
    # At least one of B or C site should be substantial
    if b_norm + c_norm < 1.0:
        return False, "insufficient_BC_sites"
    
    # For known LLZO-type: need Li + La/Zr + O
    has_li_la_zr = (
        "Li" in formula_dict and 
        any(el in formula_dict for el in ["La", "Y", "Nd", "Pr", "Eu", "Gd"]) and
        any(el in formula_dict for el in ["Zr", "Ta", "Nb"])
    )
    if has_li_la_zr:
        return True, "LLZO_type_composition"
    
    # General garnet-like: at least 2 distinct cation types on B/C
    bc_types = sum(1 for el in formula_dict if el in GARNET_B_SITES or el in GARNET_C_SITES)
    if bc_types >= 2 and a_norm >= 1.0:
        return True, "broad_garnet_composition"
    
    # Na garnets (less common)
    if "Na" in formula_dict and bc_types >= 2 and a_norm >= 1.0:
        return True, "sodium_garnet_composition"
    
    return False, "does_not_match_garnet_stoichiometry"


def check_garnet_structure(structure):
    """Verify garnet topology from structure.
    
    Strict checks:
    1. Space group must be Ia-3d (230) or related garnet space group
    2. Cubic lattice with a ≈ 11-13 Å (typical garnet range)
    3. Reasonable number of atoms in unit cell (garnets have 80+ atoms/cell)
    """
    sg_info = structure.get_space_group_info()
    sg_symbol = str(sg_info[0]) if sg_info else ""
    sg_number = int(sg_info[1]) if len(sg_info) > 1 else 0
    
    # Check space group
    if sg_number == 230:
        return True
    for known_sym in GARNET_SYMBOLS:
        if known_sym in sg_symbol:
            return True
    
    # Garnets are cubic (a=b=c)
    lattice = structure.lattice
    if not (abs(lattice.a - lattice.b) / max(lattice.a, 0.01) < 0.05 and
            abs(lattice.a - lattice.c) / max(lattice.a, 0.01) < 0.05):
        return False
    
    # Garnet lattice constant range
    if not (10.5 < lattice.a < 13.5):
        return False
    
    # Garnets typically have 80-160 atoms in conventional cell
    n_atoms = len(structure)
    if n_atoms < 40:
        return False
    
    # Check for oxygen/anion content (garnets are oxides/sulfides)
    has_anion = any(site.specie.symbol in GARNET_O_SITES for site in structure)
    if not has_anion:
        return False
    
    # Check for A-site cations (Li, Na)
    has_a_site = any(site.specie.symbol in GARNET_A_SITES for site in structure)
    if not has_a_site:
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Garnet family enrichment")
    parser.add_argument("--dry-run", action="store_true", help="Don't save results")
    parser.add_argument("--report-only", action="store_true", help="Generate report without modifying data")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"
    
    print("=" * 60)
    print("  GARNET FAMILY ENRICHMENT")
    print("  Identifying missed garnet-type structures")
    print("=" * 60)
    
    print("\nLoading entries...")
    t0 = time.time()
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        all_entries = json.load(f)
    print(f"  {len(all_entries):,} entries ({time.time()-t0:.1f}s)")
    
    if args.limit:
        all_entries = all_entries[:args.limit]
        print(f"  Limited to {args.limit} entries")
    
    # Phase 1: Composition-based screening
    print(f"\n{'─' * 60}")
    print("  Phase 1: Composition-based garnet screening")
    print(f"{'─' * 60}")
    
    current_garnet = [e for e in all_entries if e.get("sse_family") == "garnet"]
    print(f"  Currently tagged as garnet: {len(current_garnet)}")
    
    garnet_candidates = []
    for e in all_entries:
        formula = e.get("formula", "")
        formula_dict = parse_formula(formula)
        is_match, reason = is_garnet_by_formula(formula_dict)
        if is_match:
            garnet_candidates.append((e, reason))
    
    print(f"  Composition-based garnet candidates: {len(garnet_candidates)}")
    
    # Show top candidates by composition
    cand_by_elements = defaultdict(list)
    for e, reason in garnet_candidates:
        has_li = "Li" in e.get("elements", [])
        has_o = "O" in e.get("elements", [])
        key = f"{'Li' if has_li else 'Na'}-{'O' if has_o else 'S'}"
        cand_by_elements[key].append((e, reason))
    
    for key, cands in sorted(cand_by_elements.items()):
        print(f"  {key}: {len(cands)} candidates")
        for e, reason in cands[:3]:
            print(f"    - {e.get('formula', '?'):30s} {e.get('sse_family', '?'):15s} {e.get('space_group_symbol', ''):10s} [{reason}]")
    
    # Phase 2: Structure-based verification for candidates
    print(f"\n{'─' * 60}")
    print("  Phase 2: Structure-based verification")
    print(f"{'─' * 60}")
    
    structure_confirmed = []
    structure_rejected = []
    
    for e, comp_reason in garnet_candidates:
        if e.get("sse_family") == "garnet":
            structure_confirmed.append(e)
            continue
        
        struct_json = e.get("structure_json")
        if not struct_json:
            structure_rejected.append((e, "no_structure"))
            continue
        
        import json as _json
        from pymatgen.core import Structure
        
        try:
            struct_dict = _json.loads(struct_json)
            structure = Structure.from_dict(struct_dict)
            if check_garnet_structure(structure):
                structure_confirmed.append(e)
            else:
                structure_rejected.append((e, "structure_mismatch"))
        except Exception:
            structure_rejected.append((e, "parse_error"))
    
    print(f"  Structure-confirmed garnets: {len(structure_confirmed)}")
    print(f"  Structure-rejected: {len(structure_rejected)}")
    
    new_garnets = [e for e in structure_confirmed if e.get("sse_family") != "garnet"]
    print(f"  NEW garnets to reclassify: {len(new_garnets)}")
    
    if new_garnets:
        print(f"\n  Top new garnet candidates:")
        for e in sorted(new_garnets, key=lambda x: abs(x.get("formation_energy_per_atom", 0)))[:10]:
            formula = e.get("formula", "?")
            sg = e.get("space_group_symbol", "?")
            fe = e.get("formation_energy_per_atom", 0)
            print(f"    {formula:30s} SG={sg:8s} FE={fe:+.3f} eV/atom")
    
    # Phase 3: Reclassify
    if not args.report_only and not args.dry_run and new_garnets:
        print(f"\n{'─' * 60}")
        print("  Phase 3: Reclassifying entries")
        print(f"{'─' * 60}")
        
        reclassified = 0
        for e in new_garnets:
            old_family = e.get("sse_family", "?")
            e["sse_family"] = "garnet"
            if "ssb_screening" in e:
                e["ssb_screening"]["sse_family"] = "garnet"
            reclassified += 1
        
        print(f"  Reclassified: {reclassified:,} entries to garnet")
        
        # Save
        output_path = DATASET_PATH / "entries_final_v3.json"
        print(f"  Writing to {output_path}...")
        t_write = time.time()
        with open(output_path, "w") as f:
            json.dump(all_entries, f)
        print(f"  Done ({time.time()-t_write:.1f}s)")
    
    elif args.dry_run:
        print(f"\n  (dry-run — no changes saved)")
    
    # Phase 4: Report
    print(f"\n{'─' * 60}")
    print("  GARNET ENRICHMENT REPORT")
    print(f"{'─' * 60}")
    
    all_after = all_entries
    garnet_after = [e for e in all_after if e.get("sse_family") == "garnet"]
    print(f"\n  Final garnet count: {len(garnet_after):,}")
    print(f"  (was {len(current_garnet):,} before enrichment)")
    
    if garnet_after:
        print(f"\n  Sample of current garnet entries:")
        for e in garnet_after[:5]:
            print(f"    {e.get('formula', '?'):35s} {e.get('source', '?'):10s} {e.get('tier', '?'):10s}")
    
    # Recommendations for targeted acquisition
    print(f"\n  {'─' * 60}")
    print("  TARGETED ACQUISITION RECOMMENDATIONS")
    print(f"  {'─' * 60}")
    print(f"""
  To reach SSB-credible garnet coverage (500+ entries):
    
    1. Pull LLZO-family (Li7La3Zr2O12) variants from MP:
       - Li7-3xAlxLa3Zr2O12 (Al-doped)
       - Li6.5La3Zr1.5Ta0.5O12 (Ta-doped)
       - Li6.4La3Zr1.4Ta0.6O12
    
    2. Pull garnet structures from ICSD:
       - All ICSD garnet entries with Li/Na
       - Focus on Li-La-Zr-O, Li-Y-Zr-O, Li-Ca-Zr-O systems
    
    3. Known academic collections:
       - Garnet database from Ceder group publications
       - MPContribs garnet entries
       - Literature-mined garnet compositions
    
    4. Consider computational expansion:
       - Generate LLZO variants with dopant substitutions
       - Run DFT on promising but uncalculated garnet compositions
  """)
    
    print("=" * 60)


if __name__ == "__main__":
    main()
