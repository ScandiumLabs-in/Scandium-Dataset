"""Extract a Commercial-Safe edition of the dataset (MP + JARVIS only).

OQMD is non-commercial only, limiting use for commercial ML training.
This script creates a clearly-labeled subset containing only entries with
CC BY 4.0 (MP) and CC0 1.0 (JARVIS) licenses.

Outputs:
  - dataset/commercial_safe_subset_v3.json: ~94,952 entries
  - dataset/manifests/manifest_commercial_safe.json: checksums

Usage:
    python scripts/extract_commercial_safe_edition.py
    python scripts/extract_commercial_safe_edition.py --stats-only
    python scripts/extract_commercial_safe_edition.py --output-dir /tmp
"""
import json, os, sys, hashlib, time, argparse
from pathlib import Path

COMMERCIAL_LICENSES = {"CC-BY-4.0", "CC0-1.0"}
COMMERCIAL_SOURCES = {"mp", "jarvis"}


def main():
    parser = argparse.ArgumentParser(description="Extract Commercial-Safe dataset edition")
    parser.add_argument("--stats-only", action="store_true", help="Print stats only, no output")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom output directory")
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"
    
    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
    else:
        OUTPUT_DIR = DATASET_PATH
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("  COMMERCIAL-SAFE EDITION EXTRACTION")
    print("  Filtering entries by license: CC-BY-4.0 (MP), CC0-1.0 (JARVIS)")
    print("=" * 60)
    
    print("\nLoading entries...")
    t0 = time.time()
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        all_entries = json.load(f)
    print(f"  {len(all_entries):,} entries ({time.time()-t0:.1f}s)")
    
    # Filter by license
    commercial = []
    oqmd_entries = []
    for e in all_entries:
        lic = e.get("license", "")
        if lic in COMMERCIAL_LICENSES:
            commercial.append(e)
        else:
            oqmd_entries.append(e)
    
    print(f"\n  Commercial-safe: {len(commercial):,} entries")
    print(f"  OQMD (non-commercial): {len(oqmd_entries):,} entries")
    print(f"  Commercial fraction: {len(commercial)/len(all_entries)*100:.1f}%")
    
    # Stats by source
    source_counts = {}
    for e in commercial:
        src = e.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1
    
    print(f"\n  Commercial-safe source breakdown:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count:,}")
    
    # Stats by tier
    tier_counts = {}
    for e in commercial:
        t = e.get("tier", "unknown")
        tier_counts[t] = tier_counts.get(t, 0) + 1
    
    print(f"\n  Commercial-safe tier breakdown:")
    for t, count in sorted(tier_counts.items(), key=lambda x: -x[1]):
        print(f"    {t}: {count:,}")
    
    # Stats by SSE family
    family_counts = {}
    for e in commercial:
        fam = e.get("sse_family", "unknown")
        family_counts[fam] = family_counts.get(fam, 0) + 1
    
    print(f"\n  Commercial-safe SSE family breakdown:")
    for fam, count in sorted(family_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"    {fam}: {count:,}")
    
    # Stats for OQMD battery/electrolyte entries (what users lose)
    oqmd_battery = sum(1 for e in oqmd_entries if any(f in e.get("families", []) for f in 
                       ["sulfide_sse", "halide_sse", "layered_oxide"]))
    oqmd_electrolyte = sum(1 for e in oqmd_entries if e.get("sse_family") not in ("none", "oxide"))
    
    print(f"\n  OQMD entries lost (not in commercial-safe):")
    print(f"    Battery-relevant families: {oqmd_battery:,}")
    print(f"    SSE-family tagged: {oqmd_electrolyte:,}")
    
    if args.stats_only:
        print(f"\n  (stats only — no file written)")
        return
    
    # Write commercial-safe edition
    output_path = OUTPUT_DIR / "commercial_safe_subset_v3.json"
    print(f"\n  Writing commercial-safe edition ({len(commercial):,} entries)...")
    print(f"    -> {output_path}")
    
    t_write = time.time()
    with open(output_path, "w") as f:
        json.dump(commercial, f)
    print(f"    Done ({time.time()-t_write:.1f}s)")
    
    # Compute SHA256
    sha256 = hashlib.sha256()
    with open(output_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    file_size = output_path.stat().st_size
    
    print(f"    SHA256: {sha256.hexdigest()}")
    print(f"    Size: {file_size/1024/1024:.1f} MB")
    
    # Write manifest
    manifest = {
        "edition": "commercial_safe",
        "description": "MP (CC-BY-4.0) + JARVIS (CC0-1.0) entries only. No OQMD.",
        "total_entries": len(commercial),
        "file": "commercial_safe_subset_v3.json",
        "sha256": sha256.hexdigest(),
        "size_bytes": file_size,
        "sources": {src: count for src, count in source_counts.items()},
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    manifest_path = OUTPUT_DIR / "manifests" / "manifest_commercial_safe.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"    Manifest: {manifest_path}")
    
    # Also generate battery and electrolyte subsets from commercial-safe
    battery_edition = [e for e in commercial if any(
        f in e.get("families", []) for f in 
        ["sulfide_sse", "halide_sse", "layered_oxide", "garnet", "nasicon", 
         "perovskite", "anti_perovskite", "lisicon", "lGPS_type", "argyrodite",
         "borohydride", "battery", "oxide"]) or e.get("sse_family") not in ("none",)]
    
    battery_output = OUTPUT_DIR / "commercial_safe_battery_subset_v3.json"
    print(f"\n  Writing commercial-safe battery edition ({len(battery_edition):,} entries)...")
    with open(battery_output, "w") as f:
        json.dump(battery_edition, f)
    print(f"    -> {battery_output} ({time.time()-t_write:.1f}s)")
    
    print(f"\n  Manual filtering by license field is also supported:")
    print(f'    entries = [e for e in data if e["license"] in ("CC-BY-4.0", "CC0-1.0")]')
    print("=" * 60)


if __name__ == "__main__":
    main()
