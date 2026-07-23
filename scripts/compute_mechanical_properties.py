"""Pull mechanical properties (elastic moduli) for MP entries via MP API.

For entries from Materials Project, this script queries the MP API for
elastic tensor data (bulk modulus, shear modulus, Young's modulus, Poisson ratio).
For non-MP entries, it attempts a geometric proxy based on bond density.

Fills the ssb_screening block with:
  - bulk_modulus_GPa
  - shear_modulus_GPa
  - youngs_modulus_GPa
  - poisson_ratio
  - elastic_source: "MP_API" | "geometric_proxy" | null
  - dendrite_suppression_flag: shear_modulus > 6 GPa (Monroe-Newman criterion)

Usage:
    python scripts/compute_mechanical_properties.py
    python scripts/compute_mechanical_properties.py --api-key YOUR_KEY
    python scripts/compute_mechanical_properties.py --mp-only
    python scripts/compute_mechanical_properties.py --proxy-only
    python scripts/compute_mechanical_properties.py --dry-run
"""
import json, os, sys, time, argparse, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")

WIDTH = 60

# Monroe-Newman criterion: G_solid > ~2x G_Li for dendrite suppression
LI_SHEAR_MODULUS = 4.25  # GPa at room temp (varies 3.4-4.8)
DENDRITE_THRESHOLD = 6.0  # GPa conservative threshold


def compute_density_proxy(structure):
    """Compute geometric proxy for elastic moduli from structure.
    
    Based on bond density and packing fraction correlations.
    Returns approximate bulk_modulus and shear_modulus in GPa.
    """
    try:
        density = structure.density
        n_atoms = len(structure)
        volume = structure.volume
        
        if volume <= 0 or n_atoms < 2:
            return None, None, "insufficient_data"
        
        # Atomic packing density proxy
        # Sum of approximate atomic volumes (using covalent radii)
        atomic_vol = 0.0
        for site in structure:
            el = site.specie.symbol
            r_cov = {
                "Li": 1.28, "Na": 1.66, "Mg": 1.41, "Al": 1.21, "Si": 1.11,
                "P": 1.07, "S": 1.05, "Cl": 1.02, "K": 2.03, "Ca": 1.76,
                "Ti": 1.47, "V": 1.34, "Cr": 1.27, "Mn": 1.26, "Fe": 1.25,
                "Co": 1.24, "Ni": 1.21, "Cu": 1.22, "Zn": 1.20, "Ga": 1.22,
                "Ge": 1.21, "As": 1.21, "Se": 1.17, "Br": 1.14, "Y": 1.78,
                "Zr": 1.57, "Nb": 1.45, "Mo": 1.38, "Ru": 1.33, "Rh": 1.31,
                "Pd": 1.30, "Ag": 1.34, "Cd": 1.36, "In": 1.42, "Sn": 1.40,
                "Sb": 1.40, "Te": 1.37, "I": 1.33, "La": 1.87, "Ce": 1.82,
                "Pr": 1.82, "Nd": 1.81, "Sm": 1.80, "Eu": 1.80, "Gd": 1.79,
                "Tb": 1.76, "Dy": 1.75, "Ho": 1.74, "Er": 1.73, "Tm": 1.72,
                "Yb": 1.71, "Lu": 1.70, "Ta": 1.45, "W": 1.39, "Pb": 1.44,
                "Bi": 1.50, "O": 0.66, "N": 0.71, "F": 0.64, "H": 0.31,
            }.get(el, 1.5)
            atomic_vol += (4.0/3.0) * np.pi * (r_cov ** 3)
        
        packing_fraction = atomic_vol / volume if volume > 0 else 0.3
        
        # Correlation: denser packing -> higher moduli
        # Bulk modulus roughly scales with cohesive energy density
        coh_energy_density = density * 100  # rough proxy in GPa-like units
        
        bulk_modulus = coh_energy_density * (packing_fraction ** 1.5)
        shear_modulus = bulk_modulus * (packing_fraction ** 0.5) * 0.5
        
        # Clamp to realistic ranges
        bulk_modulus = max(5.0, min(400.0, bulk_modulus))
        shear_modulus = max(2.0, min(300.0, shear_modulus))
        
        return round(bulk_modulus, 2), round(shear_modulus, 2), "geometric_proxy"
    except Exception:
        return None, None, "error"


def main():
    parser = argparse.ArgumentParser(description="Compute mechanical properties")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Materials Project API key (optional, for live API queries)")
    parser.add_argument("--mp-only", action="store_true",
                        help="Only process MP entries (skip geometric proxy)")
    parser.add_argument("--proxy-only", action="store_true",
                        help="Only use geometric proxy (skip MP API)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"
    
    print("=" * WIDTH)
    print("  MECHANICAL PROPERTIES — ELASTIC MODULI")
    print(f"  Dendrite suppression threshold: G > {DENDRITE_THRESHOLD} GPa")
    print("=" * WIDTH)
    
    print("\nLoading entries...")
    t0 = time.time()
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        all_entries = json.load(f)
    print(f"  {len(all_entries):,} entries ({time.time()-t0:.1f}s)")
    
    if args.limit:
        all_entries = all_entries[:args.limit]
        print(f"  Limited to {args.limit} entries")
    
    # Try MP API for MP entries
    mp_elastic_data = {}
    if args.api_key and not args.proxy_only:
        print("\n  Querying MP API for elastic data...")
        try:
            from mp_api.client import MPRester
            with MPRester(args.api_key) as mpr:
                mp_ids = [e.get("source_id") for e in all_entries 
                         if e.get("source") == "mp" and e.get("source_id")]
                print(f"  MP entries with source_ids: {len(mp_ids):,}")
                for i in range(0, len(mp_ids), 50):
                    batch = mp_ids[i:i+50]
                    try:
                        results = mpr.elasticity.search(material_ids=batch)
                        for doc in results:
                            if doc.material_id in batch:
                                mp_elastic_data[doc.material_id] = {
                                    "bulk_modulus": doc.bulk_modulus,
                                    "shear_modulus": doc.shear_modulus,
                                    "youngs_modulus": doc.youngs_modulus,
                                    "poisson_ratio": doc.poisson_ratio,
                                }
                    except Exception:
                        pass
                    if (i+1) % 500 == 0:
                        print(f"    Queried {i+1}/{len(mp_ids)} MP IDs")
            print(f"  Retrieved elastic data for {len(mp_elastic_data):,} MP entries")
        except ImportError:
            print("  mp-api not installed. Skipping MP API query.")
        except Exception as exc:
            print(f"  MP API error: {exc}")
    
    # Process entries
    print(f"\n{'─' * WIDTH}")
    print("  Computing mechanical properties...")
    print(f"{'─' * WIDTH}")
    
    processed = 0
    mp_api_found = 0
    proxy_computed = 0
    errors = 0
    dendrite_suppression = 0
    from pymatgen.core import Structure
    import json as _json
    
    for idx, e in enumerate(all_entries):
        if "ssb_screening" not in e:
            e["ssb_screening"] = {}
        
        ss = e["ssb_screening"]
        source = e.get("source", "")
        source_id = e.get("source_id", "")
        
        # Try MP API data first
        if source == "mp" and source_id in mp_elastic_data:
            mp_data = mp_elastic_data[source_id]
            ss["bulk_modulus_GPa"] = mp_data.get("bulk_modulus")
            ss["shear_modulus_GPa"] = mp_data.get("shear_modulus")
            ss["youngs_modulus_GPa"] = mp_data.get("youngs_modulus")
            ss["poisson_ratio"] = mp_data.get("poisson_ratio")
            ss["elastic_source"] = "MP_API"
            mp_api_found += 1
        elif not args.mp_only and e.get("structure_json"):
            # Use geometric proxy
            try:
                struct_dict = _json.loads(e["structure_json"])
                structure = Structure.from_dict(struct_dict)
                K, G, proxy_source = compute_density_proxy(structure)
                if K is not None and G is not None:
                    ss["bulk_modulus_GPa"] = K
                    ss["shear_modulus_GPa"] = G
                    ss["youngs_modulus_GPa"] = round(9 * K * G / (3 * K + G), 2) if (3*K+G) > 0 else None
                    ss["poisson_ratio"] = round((3*K - 2*G) / (2*(3*K + G)), 3) if (3*K+G) > 0 else None
                    ss["elastic_source"] = proxy_source
                    proxy_computed += 1
            except Exception:
                errors += 1
        
        # Set dendrite suppression flag
        shear_mod = ss.get("shear_modulus_GPa")
        if shear_mod is not None:
            ss["dendrite_suppression_flag"] = bool(shear_mod >= DENDRITE_THRESHOLD)
            if ss["dendrite_suppression_flag"]:
                dendrite_suppression += 1
        
        processed += 1
        if (idx + 1) % 5000 == 0:
            print(f"  {idx+1}/{len(all_entries)} | MP_API:{mp_api_found} Proxy:{proxy_computed} Dendrite:{dendrite_suppression}")
    
    print(f"\n{'─' * WIDTH}")
    print(f"  Complete: {processed} processed")
    print(f"    MP API data: {mp_api_found:,}")
    print(f"    Geometric proxy: {proxy_computed:,}")
    print(f"    Errors: {errors:,}")
    print(f"    Dendrite suppression (G > {DENDRITE_THRESHOLD} GPa): {dendrite_suppression:,}")
    
    # Save
    if args.dry_run:
        print(f"\n  (dry-run — not saved)")
    else:
        output_path = DATASET_PATH / "entries_final_v3.json"
        print(f"\n  Writing to {output_path}...")
        t_write = time.time()
        with open(args.output or output_path, "w") as f:
            json.dump(all_entries, f)
        print(f"  Done ({time.time()-t_write:.1f}s)")
    
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
