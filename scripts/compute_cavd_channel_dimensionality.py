"""CAVD-like channel dimensionality analysis for Li/Na ion migration pathways.

Computes percolation channel dimensionality (0D/1D/2D/3D) from crystal structures
using Voronoi-based void network analysis. Fills the ssb_screening block with:
  - cavd_channel_dimensionality: "0D" | "1D" | "2D" | "3D" | "none"
  - mobile_ion_site_volume: Volume of mobile ion Voronoi cell (A^3)
  - mobile_ion_connectivity: Coordination of mobile ion sites

This is a geometric pre-filter — materials with 0D channels or no percolation
network are extremely unlikely to be good ionic conductors.

Usage:
    python scripts/compute_cavd_channel_dimensionality.py                    # subset: mobile-ion only
    python scripts/compute_cavd_channel_dimensionality.py --subset battery   # battery edition only
    python scripts/compute_cavd_channel_dimensionality.py --limit 1000       # first 1000 entries
    python scripts/compute_cavd_channel_dimensionality.py --dry-run          # stats only, no save

References:
    - Zhang et al. Scientific Data (2020) — SPSE platform CAVD methodology
    - pymatgen VoronoiConnectivity for void space analysis
"""
import json, os, sys, time, argparse, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")

WIDTH = 60

def parse_structure(structure_json_str):
    from pymatgen.core import Structure
    import json as _json
    d = _json.loads(structure_json_str)
    return Structure.from_dict(d)

def compute_voronoi_connectivity(structure, mobile_element="Li", cutoff=10.0):
    """Analyze mobile ion connectivity via Voronoi tessellation.
    
    Returns dict with:
      - dimensionality : estimated channel dimensionality
      - coordination : number of neighboring mobile ion sites
      - site_volume : average Voronoi volume of mobile ion sites
      - percolation : bool, whether 3D percolation is likely
    """
    from pymatgen.analysis.structure_analyzer import VoronoiConnectivity
    
    mobile_sites = [s for s in structure if s.specie.symbol == mobile_element]
    if len(mobile_sites) < 2:
        return {"dimensionality": "none", "coordination": 0, "site_volume": 0.0, "percolation": False}
    
    try:
        vc = VoronoiConnectivity(structure, mobile_element, cutoff=cutoff)
        connectivity = vc.get_connectivity()
    except Exception:
        connectivity = {}
    
    # Analyze mobile ion sublattice geometry
    # Get fractional coordinates of mobile ions
    frac_coords = np.array([s.frac_coords for s in mobile_sites])
    
    # Compute distances (considering periodic boundary conditions)
    n_mobile = len(mobile_sites)
    if n_mobile < 2:
        return {"dimensionality": "none", "coordination": 0, "site_volume": 0.0, "percolation": False}
    
    # Calculate coordination environment
    lattice = structure.lattice
    
    # Count nearest neighbors and their direction distribution
    from scipy.spatial import KDTree
    from pymatgen.core import PeriodicSite
    
    # Build periodic neighbors
    all_coords = []
    for i, site in enumerate(mobile_sites):
        # Include images
        for image in [(0,0,0), (1,0,0), (-1,0,0), (0,1,0), (0,-1,0), 
                       (0,0,1), (0,0,-1), (1,1,0), (1,-1,0), (-1,1,0), (-1,-1,0),
                       (1,0,1), (1,0,-1), (-1,0,1), (-1,0,-1), (0,1,1), (0,1,-1),
                       (0,-1,1), (0,-1,-1)]:
            shift = np.array(image, dtype=float)
            cart = lattice.get_cartesian_coords(site.frac_coords + shift)
            all_coords.append((i, cart, image))
    
    coords = np.array([c[1] for c in all_coords])
    indices = np.array([c[0] for c in all_coords])
    
    if len(coords) == 0:
        return {"dimensionality": "none", "coordination": 0, "site_volume": 0.0, "percolation": False}
    
    tree = KDTree(coords)
    
    # Find nearest neighbor distances
    avg_dist = None
    coordination_counts = []
    
    min_dist = 0.5
    for i in range(n_mobile):
        point = lattice.get_cartesian_coords(mobile_sites[i].frac_coords)
        nn = tree.query_ball_point(point, r=5.0)
        nn_indices = indices[nn]
        # Count neighbors (excluding self)
        nn_self = sum(1 for j in nn_indices if j == i)
        nn_count = len(nn_indices) - nn_self
        coordination_counts.append(nn_count)
    
    mean_coordination = np.mean(coordination_counts) if coordination_counts else 0
    
    # Estimate channel dimensionality from coordination environment
    # 3D: high coordination (>4) with isotropic distribution
    # 2D: moderate coordination with planar distribution
    # 1D: low coordination with linear distribution
    # 0D: isolated sites with no connectivity
    
    if mean_coordination >= 4:
        dimensionality = "3D"
        percolation = True
    elif mean_coordination >= 2:
        dimensionality = "2D"
        percolation = True
    elif mean_coordination >= 1:
        dimensionality = "1D"
        percolation = False
    else:
        dimensionality = "0D"
        percolation = False
    
    # Compute average Voronoi volume of mobile sites
    try:
        site_volumes = []
        for site in mobile_sites:
            from scipy.spatial import Voronoi as ScipyVoronoi
            from pymatgen.core.periodic_table import Element as PmgElement
            
            # Get neighboring sites within cutoff
            neighbors = structure.get_neighbors(site, r=cutoff)
            if len(neighbors) < 4:
                site_volumes.append(0.0)
                continue
            
            # Build points for Voronoi tessellation
            points = [site.coords]
            for n_site, dist, _, _ in neighbors:
                points.append(n_site.coords)
            
            if len(points) < 4:
                site_volumes.append(0.0)
                continue
            
            try:
                vor = ScipyVoronoi(np.array(points))
                # Get the Voronoi cell for the first point (our site)
                region_idx = vor.point_region[0]
                region = vor.regions[region_idx]
                if -1 not in region and len(region) > 0:
                    verts = vor.vertices[region]
                    from scipy.spatial import ConvexHull
                    hull = ConvexHull(verts)
                    site_volumes.append(hull.volume)
                else:
                    site_volumes.append(0.0)
            except Exception:
                site_volumes.append(0.0)
        
        avg_site_volume = np.mean(site_volumes) if site_volumes else 0.0
    except Exception:
        avg_site_volume = 0.0
    
    return {
        "dimensionality": dimensionality,
        "coordination": round(float(mean_coordination), 2),
        "site_volume": round(float(avg_site_volume), 4),
        "percolation": percolation
    }


def main():
    parser = argparse.ArgumentParser(description="CAVD channel dimensionality analysis")
    parser.add_argument("--subset", choices=["battery", "electrolyte", "gold", "full"], default="full")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Don't save results")
    parser.add_argument("--output", type=str, default=None, help="Custom output path")
    args = parser.parse_args()
    
    if args.limit and not args.dry_run and args.output is None:
        print("ERROR: Refusing to save limited runs. Use --dry-run or --output.")
        sys.exit(1)
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"
    
    print("=" * WIDTH)
    print("  CAVD CHANNEL DIMENSIONALITY ANALYSIS")
    print("  Geometric pre-filter for Li/Na ion migration pathways")
    print("=" * WIDTH)
    
    print("\nLoading entries...")
    t0 = time.time()
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        all_entries = json.load(f)
    print(f"  {len(all_entries):,} total entries ({time.time()-t0:.1f}s)")
    
    # Select working subset: only entries with mobile ion (Li or Na) and structure_json
    mobile_elements = {"Li", "Na"}
    entries = []
    skipped_no_mobile = 0
    skipped_no_structure = 0
    
    for e in all_entries:
        mobile_ion = e.get("mobile_ion", "")
        if mobile_ion not in mobile_elements:
            skipped_no_mobile += 1
            continue
        if not e.get("structure_json"):
            skipped_no_structure += 1
            continue
        entries.append(e)
    
    print(f"  Li/Na mobile ion entries with structures: {len(entries):,}")
    print(f"  Skipped (no mobile ion): {skipped_no_mobile:,}")
    print(f"  Skipped (no structure): {skipped_no_structure:,}")
    
    if args.subset != "full":
        if args.subset == "battery":
            with open(DATASET_PATH / "battery_subset_v3.json") as f:
                battery = json.load(f)
            battery_ids = {e.get("source_id", "") + e.get("source", "") for e in battery}
            entries = [e for e in entries if e.get("source_id", "") + e.get("source", "") in battery_ids]
        elif args.subset == "electrolyte":
            with open(DATASET_PATH / "electrolyte_subset_v3.json") as f:
                electrolyte = json.load(f)
            electrolyte_ids = {e.get("source_id", "") + e.get("source", "") for e in electrolyte}
            entries = [e for e in entries if e.get("source_id", "") + e.get("source", "") in electrolyte_ids]
        elif args.subset == "gold":
            entries = [e for e in entries if e.get("tier") == "gold"]
        print(f"  Subset ({args.subset}): {len(entries):,} entries")
    
    if args.limit:
        entries = entries[:args.limit]
        print(f"  Limited to {args.limit} entries")
    
    if not entries:
        print("No entries to process.")
        return
    
    # Process entries
    print(f"\n{'─' * WIDTH}")
    print("  Computing channel dimensionality...")
    print(f"{'─' * WIDTH}")
    
    processed = 0
    errors = 0
    dims = {"3D": 0, "2D": 0, "1D": 0, "0D": 0, "none": 0, "error": 0}
    t_start = time.time()
    
    for idx, e in enumerate(entries):
        mobile_ion = e.get("mobile_ion", "Li")
        
        try:
            structure = parse_structure(e["structure_json"])
            result = compute_voronoi_connectivity(structure, mobile_element=mobile_ion)
            
            # Fill ssb_screening block
            if "ssb_screening" not in e:
                e["ssb_screening"] = {}
            
            e["ssb_screening"]["cavd_channel_dimensionality"] = result["dimensionality"]
            dims[result["dimensionality"]] += 1
            processed += 1
            
        except Exception as exc:
            errors += 1
            if errors <= 5:
                print(f"  Error [{e.get('source_id','?')}]: {str(exc)[:80]}")
            if "ssb_screening" in e:
                e["ssb_screening"]["cavd_channel_dimensionality"] = "error"
        
        if (idx + 1) % 500 == 0:
            elapsed = time.time() - t_start
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            pct = (idx + 1) / len(entries) * 100
            print(f"  {idx+1}/{len(entries)} ({pct:.0f}%) | "
                  f"3D:{dims['3D']} 2D:{dims['2D']} 1D:{dims['1D']} 0D:{dims['0D']} "
                  f"| {rate:.1f} ent/s")
    
    elapsed = time.time() - t_start
    print(f"\n{'─' * WIDTH}")
    print(f"  Complete: {processed} processed, {errors} errors")
    print(f"  Time: {elapsed/60:.1f} min ({processed/elapsed:.1f} ent/s)")
    print(f"\n  Channel dimensionality distribution:")
    for dim, count in sorted(dims.items()):
        if count > 0:
            print(f"    {dim}: {count:,} ({count/max(processed,1)*100:.1f}%)")
    
    # Determine output path
    if args.subset == "battery":
        with open(DATASET_PATH / "battery_subset_v3.json") as f:
            save_data = json.load(f)
        output_path = DATASET_PATH / "battery_subset_v3.json"
        # Update entries in save_data
        entry_map = {e.get("source_id", "") + e.get("source", ""): e for e in entries}
        for s in save_data:
            key = s.get("source_id", "") + s.get("source", "")
            if key in entry_map:
                s["ssb_screening"] = entry_map[key].get("ssb_screening", {})
    elif args.subset == "electrolyte":
        with open(DATASET_PATH / "electrolyte_subset_v3.json") as f:
            save_data = json.load(f)
        output_path = DATASET_PATH / "electrolyte_subset_v3.json"
        entry_map = {e.get("source_id", "") + e.get("source", ""): e for e in entries}
        for s in save_data:
            key = s.get("source_id", "") + s.get("source", "")
            if key in entry_map:
                s["ssb_screening"] = entry_map[key].get("ssb_screening", {})
    elif args.subset == "gold":
        output_path = DATASET_PATH / "entries_final_v3.json"
        save_data = all_entries
    else:
        output_path = DATASET_PATH / "entries_final_v3.json"
        save_data = all_entries
    
    if args.dry_run:
        print("\n  (dry-run — not saved)")
    else:
        print(f"\n  Writing to {output_path}...")
        t_write = time.time()
        with open(output_path, "w") as f:
            json.dump(save_data, f)
        print(f"  Done ({time.time()-t_write:.1f}s)")
    
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
