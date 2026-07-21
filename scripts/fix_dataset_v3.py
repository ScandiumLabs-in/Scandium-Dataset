"""Fix all remaining data quality issues: stale flags, structured_formula, etc."""
import json, time, hashlib
from pathlib import Path
from collections import Counter

AUDIT_DIR = Path.cwd() if Path.cwd().name == "Scandium-Dataset" else Path("/home/shamique/Scandium Labs SSB/Scandium-Dataset")
DATASET = "dataset/entries_final_v3.json"

def reduced_formula(formula):
    """Basic formula reducer — no pymatgen dependency."""
    from collections import OrderedDict
    import re
    parts = re.findall(r'([A-Z][a-z]*)(\d*)', formula)
    elems = OrderedDict()
    for el, cnt in parts:
        elems[el] = elems.get(el, 0) + (int(cnt) if cnt else 1)
    # Sort: electronegativity-like ordering (anion last, cation first)
    # Simple: sort alphabetically, but put O, S, F, Cl, Br, I, N, P last
    anions = {'O', 'S', 'F', 'Cl', 'Br', 'I', 'N', 'P', 'Se', 'Te', 'As', 'Sb'}
    cations = {k: v for k, v in elems.items() if k not in anions}
    anion_list = {k: v for k, v in elems.items() if k in anions}
    sorted_elems = sorted(cations.items()) + sorted(anion_list.items())
    return ''.join(f'{el}{cnt if cnt > 1 else ""}' for el, cnt in sorted_elems)

def main():
    print("=" * 60)
    print("  FIX DATASET v0.0")
    print("=" * 60)

    with open(AUDIT_DIR / DATASET) as f:
        entries = json.load(f)
    N = len(entries)
    print(f"  Loaded {N:,} entries")

    changes = {}

    # 1. Fix stale quality_flags: remove missing_spacegroup from OQMD with SG
    stale_fixed = 0
    for e in entries:
        if e.get("source") == "oqmd" and e.get("space_group") is not None:
            flags = e.get("quality_flags", [])
            if "missing_spacegroup" in flags:
                flags.remove("missing_spacegroup")
                e["quality_flags"] = flags
                stale_fixed += 1
    changes["stale_flags_fixed"] = stale_fixed
    print(f"  Fixed stale quality_flags: {stale_fixed:,}")

    # 2. Add structured_formula using reduced formula (no pymatgen dependency)
    sf_added = 0
    for e in entries:
        if not e.get("structured_formula"):
            raw_f = e.get("formula", "")
            try:
                e["structured_formula"] = reduced_formula(raw_f)
                sf_added += 1
            except Exception:
                e["structured_formula"] = raw_f
                sf_added += 1
    changes["structured_formula_added"] = sf_added
    print(f"  Added structured_formula: {sf_added:,}")

    # 3. Ensure all entries have provenance fields complete
    prov_fixed = 0
    for e in entries:
        prov = e.get("provenance", {})
        if not prov.get("version"):
            prov["version"] = "v0.0.0"
            prov_fixed += 1
        if not prov.get("processed_at"):
            prov["processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            prov_fixed += 1
        e["provenance"] = prov
    changes["provenance_fixed"] = prov_fixed
    print(f"  Fixed provenance completeness: {prov_fixed:,}")

    # 4. Write back
    print("\n  Writing fixed dataset...")
    with open(AUDIT_DIR / DATASET, "w") as f:
        json.dump(entries, f, indent=2)

    # 5. Compute new SHA256
    sha256 = hashlib.sha256()
    with open(AUDIT_DIR / DATASET, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    changes["new_sha256"] = sha256.hexdigest()

    # 6. Update manifest
    manifest_path = AUDIT_DIR / "dataset/manifests/MANIFEST_v3.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        manifest["entries_final_v3.json"] = {
            "sha256": sha256.hexdigest(),
            "size": (AUDIT_DIR / DATASET).stat().st_size,
            "entries": len(entries),
            "updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        changes["manifest_updated"] = True

    # Summary
    print(f"\n{'=' * 60}")
    print("  FIXES APPLIED")
    for k, v in changes.items():
        print(f"    {k}: {v}")
    print(f"{'=' * 60}")

    # Verify
    print("\n  Verification:")
    with open(AUDIT_DIR / DATASET) as f:
        entries2 = json.load(f)
    sf_count = sum(1 for e in entries2 if e.get("structured_formula"))
    stale_remaining = sum(1 for e in entries2 
                          if e.get("source") == "oqmd" and e.get("space_group") is not None
                          and "missing_spacegroup" in e.get("quality_flags", []))
    print(f"    structured_formula: {sf_count}/{len(entries2)}")
    print(f"    stale flags remaining: {stale_remaining}")
    print(f"  Done.")

if __name__ == "__main__":
    main()
