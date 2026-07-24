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
    frac_coords = np.array([s.frac_coords for s in mobile_sites])
    
    n_mobile = len(mobile_sites)
    if n_mobile < 2:
        return {"dimensionality": "none", "coordination": 0, "site_volume": 0.0, "percolation": False}
    
    lattice = structure.lattice
    
    from scipy.spatial import KDTree
    
    all_coords = []
    for i, site in enumerate(mobile_sites):
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
    
    coordination_counts = []
    
    for i in range(n_mobile):
        point = lattice.get_cartesian_coords(mobile_sites[i].frac_coords)
        nn = tree.query_ball_point(point, r=5.0)
        nn_indices = indices[nn]
        nn_self = sum(1 for j in nn_indices if j == i)
        nn_count = len(nn_indices) - nn_self
        coordination_counts.append(nn_count)
    
    mean_coordination = np.mean(coordination_counts) if coordination_counts else 0
    
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
    
    try:
        site_volumes = []
        for site in mobile_sites:
            from scipy.spatial import Voronoi as ScipyVoronoi
            
            neighbors = structure.get_neighbors(site, r=cutoff)
            if len(neighbors) < 4:
                site_volumes.append(0.0)
                continue
            
            points = [site.coords]
            for n_site, dist, _, _ in neighbors:
                points.append(n_site.coords)
            
            if len(points) < 4:
                site_volumes.append(0.0)
                continue
            
            try:
                vor = ScipyVoronoi(np.array(points))
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
    
    print("\nLoading entries from typed Parquet...")
    t0 = time.time()
    sys.path.insert(0, str(BASE_DIR))
    from dataset.dataset_store import DatasetStore
    store = DatasetStore.open()
    print(f"  {store.num_entries:,} total entries ({time.time()-t0:.1f}s)")
    
    mobile_elements = {"Li", "Na"}
    
    # Load subset IDs if filtering
    subset_ids = None
    if args.subset == "battery":
        with open(DATASET_PATH / "battery_candidate_subset_v1.json") as f:
            battery = json.load(f)
        subset_ids = {e.get("source_id", "") + e.get("source", "") for e in battery}
    elif args.subset == "electrolyte":
        with open(DATASET_PATH / "solid_electrolyte_candidate_subset_v1.json") as f:
            electrolyte = json.load(f)
        subset_ids = {e.get("source_id", "") + e.get("source", "") for e in electrolyte}
    
    # Collect target entries
    skipped_no_mobile = 0
    skipped_no_structure = 0
    target_ids = []
    
    for e in store.scan(columns=["source_id", "source", "mobile_ion", "structure_json"]):
        mobile_ion = e.get("mobile_ion", "")
        if mobile_ion not in mobile_elements:
            skipped_no_mobile += 1
            continue
        if not e.get("structure_json"):
            skipped_no_structure += 1
            continue
        key = e.get("source_id", "") + e.get("source", "")
        if subset_ids is not None and key not in subset_ids:
            continue
        target_ids.append(e["source_id"])
    
    print(f"  Li/Na mobile ion entries with structures: {len(target_ids):,}")
    print(f"  Skipped (no mobile ion): {skipped_no_mobile:,}")
    print(f"  Skipped (no structure): {skipped_no_structure:,}")
    
    if args.subset == "gold":
        gold_ids = set()
        for e in store.scan(columns=["source_id", "tier"]):
            if e.get("tier") == "gold":
                gold_ids.add(e["source_id"])
        target_ids = [sid for sid in target_ids if sid in gold_ids]
        print(f"  Subset (gold): {len(target_ids):,} entries")
    elif args.subset != "full":
        print(f"  Subset ({args.subset}): {len(target_ids):,} entries")
    
    if args.limit:
        target_ids = target_ids[:args.limit]
        print(f"  Limited to {args.limit} entries")
    
    if not target_ids:
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
    
    for idx, source_id in enumerate(target_ids):
        entry = store.lookup(source_id)
        if entry is None:
            continue
        
        mobile_ion = entry.get("mobile_ion", "Li")
        
        try:
            structure = parse_structure(entry["structure_json"])
            result = compute_voronoi_connectivity(structure, mobile_element=mobile_ion)
            
            store.update_field(source_id, "ssb_screening",
                result["dimensionality"], nested_path="cavd_channel_dimensionality")
            store.update_field(source_id, "ssb_screening",
                result["coordination"], nested_path="mobile_ion_connectivity")
            store.update_field(source_id, "ssb_screening",
                result["site_volume"], nested_path="mobile_ion_site_volume")
            
            dims[result["dimensionality"]] += 1
            processed += 1
            
        except Exception as exc:
            errors += 1
            if errors <= 5:
                print(f"  Error [{source_id}]: {str(exc)[:80]}")
            store.update_field(source_id, "ssb_screening",
                "error", nested_path="cavd_channel_dimensionality")
        
        if (idx + 1) % 500 == 0:
            elapsed = time.time() - t_start
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            pct = (idx + 1) / len(target_ids) * 100
            print(f"  {idx+1}/{len(target_ids)} ({pct:.0f}%) | "
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
    
    if args.dry_run:
        print("\n  (dry-run — not saved)")
        store._dirty = False
        store.close()
    else:
        print(f"\n  Writing to Parquet...")
        t_write = time.time()
        store.checkpoint()
        print(f"  Done ({time.time()-t_write:.1f}s)")
    
    print("=" * WIDTH)


if __name__ == "__main__":
    main()
