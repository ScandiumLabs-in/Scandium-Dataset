"""Integrate experimental Li solid-electrolyte conductivity data.

Two separate, independently curated databases are supported:

1. **Hargreaves et al. 2023** — npj Computational Materials
   ~820 entries, 403 compositions, 214 sources
   https://doi.org/10.1038/s41524-023-01137-3

2. **OBELiX (Therrien et al. 2025, NRC-Mila)**
   ~599 entries, curated with leakage-resistant splits
   pip install obelix-data
   https://github.com/nrc-mila/OBELiX

These are complementary — not duplicates — and are tracked as two separate
provenance sources with distinct citations.

Usage:
    # Hargreaves 2023
    python scripts/integrate_experimental_data.py --ransom-path path/to/ransom2023.csv

    # OBELiX via pip package
    python scripts/integrate_experimental_data.py --obelix

    # Both
    python scripts/integrate_experimental_data.py --ransom-path ... --obelix

    # Dry run
    python scripts/integrate_experimental_data.py --dry-run
"""
import json, os, sys, time, argparse, csv, io, re, subprocess
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

WIDTH = 60

RANSOM_URLS = [
    "https://raw.githubusercontent.com/nrc-cnrc/ransom2023-conductivity/main/data/conductivity_database.csv",
]

HARGREAVES_DOI = "https://doi.org/10.1038/s41524-022-00951-z"
OBELIX_DOI = "https://github.com/nrc-mila/OBELiX"


def parse_formula(formula):
    parts = re.findall(r'([A-Z][a-z]*)(\d*\.?\d*)', formula)
    return {el: float(cnt) if cnt else 1.0 for el, cnt in parts}


def formula_similarity(f1, f2):
    d1 = parse_formula(f1)
    d2 = parse_formula(f2)
    if set(d1.keys()) != set(d2.keys()):
        return False
    total1, total2 = sum(d1.values()), sum(d2.values())
    for el in d1:
        r1 = d1[el] / total1
        r2 = d2[el] / total2
        if abs(r1 - r2) > 0.05:
            return False
    return True


def try_fetch_ransom():
    """Try to download Hargreaves 2023 database."""
    import urllib.request
    for url in RANSOM_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Scandium-Labs/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode("utf-8")
                print(f"  Downloaded {len(data):,} bytes")
                return data
        except Exception as e:
            print(f"  Failed: {str(e)[:80]}")
    return None


def try_fetch_obelix_package():
    """Try to install obelix-data package and load data."""
    try:
        import obelix
        ob = obelix.OBELiX(data_path="/tmp/obelix_rawdata", no_cifs=True)
        n = len(ob.dataframe)
        print(f"  OBELiX package loaded: {n} entries")
        return ob
    except ImportError:
        print("  obelix-data not installed. Attempting pip install...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "obelix-data"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            try:
                import obelix
                ob = obelix.OBELiX(data_path="/tmp/obelix_rawdata", no_cifs=True)
                n = len(ob.dataframe)
                print(f"  OBELiX installed and loaded: {n} entries")
                return ob
            except Exception as e:
                print(f"  Load failed after install: {e}")
                return None
        else:
            print(f"  Install failed: {result.stderr[-200:]}")
            return None


def parse_ransom_csv(csv_data):
    """Parse Hargreaves 2023 CSV into entry dicts."""
    reader = csv.DictReader(io.StringIO(csv_data))
    entries = []
    for i, row in enumerate(reader):
        entry = {
            "source": "Hargreaves2023",
            "source_id": f"Hargreaves2023-{i:04d}",
            "is_experimental": True,
            "experimental_database": "Hargreaves2023",
            "provenance": {
                "source": "Hargreaves2023",
                "source_id": f"Hargreaves2023-{i:04d}",
                "doi": HARGREAVES_DOI,
                "integrated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        }
        formula = row.get("Formula", row.get("formula", "")).strip()
        if formula:
            entry["formula"] = formula
            entry["structured_formula"] = formula
            entry["elements"] = list(parse_formula(formula).keys())
            entry["carrier_elements"] = ["Li"]

        for field in ["Conductivity_S_cm", "conductivity_S_cm", "Conductivity (S/cm)"]:
            val = row.get(field, "").strip()
            if val:
                try:
                    entry["conductivity_S_cm"] = float(val)
                except ValueError:
                    pass

        for field in ["Ea_eV", "activation_energy_eV", "Activation energy (eV)"]:
            val = row.get(field, "").strip()
            if val:
                try:
                    entry["activation_energy_eV"] = float(val)
                except ValueError:
                    pass

        for field in ["Temperature_K", "temperature_K", "Temperature (K)"]:
            val = row.get(field, "").strip()
            if val:
                try:
                    entry["temperature_K"] = float(val)
                except ValueError:
                    pass

        ref = row.get("Reference", row.get("reference", "")).strip()
        if ref:
            entry["reference"] = ref
            entry["provenance"]["experimental_reference"] = ref

        entries.append(entry)

    return entries


def parse_obelix_via_package(obelix_obj):
    """Parse OBELiX data via pandas DataFrame."""
    entries = []
    try:
        df = obelix_obj.dataframe
        for idx, row in df.iterrows():
            formula = str(row.get("Reduced Composition", ""))
            true_comp = str(row.get("True Composition", ""))
            conductivity = row.get("Ionic conductivity (S cm-1)")
            doi = str(row.get("DOI", ""))
            family = str(row.get("Family", ""))
            icsd = row.get("ICSD ID")
            sg = str(row.get("Space group", ""))

            entry = {
                "source": "OBELiX",
                "source_id": f"OBELiX-{idx}",
                "is_experimental": True,
                "experimental_database": "OBELiX_Therrien2025",
                "formula": formula,
                "structured_formula": true_comp if (true_comp and true_comp != "nan") else formula,
                "elements": list(parse_formula(formula).keys()) if formula else [],
                "carrier_elements": ["Li"],
                "conductivity_S_cm": float(conductivity) if pd.notna(conductivity) else None,
                "space_group": sg if sg != "nan" else "",
                "sse_family": family if family != "nan" else "",
                "reference": doi if doi != "nan" else "",
                "provenance": {
                    "source": "OBELiX_Therrien2025",
                    "source_id": f"OBELiX-{idx}",
                    "doi": "https://github.com/nrc-mila/OBELiX",
                    "icsd_id": str(icsd) if pd.notna(icsd) else "",
                    "integrated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
            }
            entries.append(entry)
    except Exception as e:
        print(f"  OBELiX DataFrame parse error: {e}")

    return entries


def cross_reference_and_add(exp_entries, all_dataset_entries):
    """Cross-reference experimental entries with the existing dataset."""
    formula_index = defaultdict(list)
    for e in all_dataset_entries:
        sf = e.get("structured_formula", e.get("formula", ""))
        formula_index[sf].append(e)

    matched = 0
    unmatched = 0
    conductivity_added = 0
    new_entries = []

    for exp_e in exp_entries:
        exp_formula = exp_e.get("formula", "")
        matched_entries = formula_index.get(exp_formula, [])

        if not matched_entries:
            for sf, existing in formula_index.items():
                if formula_similarity(exp_formula, sf):
                    matched_entries = existing
                    break

        db_name = exp_e.get("experimental_database", "unknown")

        if matched_entries:
            matched += 1
            for existing_e in matched_entries:
                if "ssb_screening" not in existing_e:
                    existing_e["ssb_screening"] = {}

                cond = exp_e.get("conductivity_S_cm")
                ea = exp_e.get("activation_energy_eV")

                if cond is not None:
                    existing_e["ssb_screening"]["estimated_ionic_conductivity_S_cm"] = cond
                    existing_e["ssb_screening"]["conductivity_source"] = f"experimental_{db_name}"
                    conductivity_added += 1

                if ea is not None:
                    existing_e["ssb_screening"]["experimental_activation_energy_eV"] = ea

                existing_e["is_experimental"] = True
                if "provenance" not in existing_e:
                    existing_e["provenance"] = {}
                existing_e["provenance"]["experimental_confirmed"] = True
                existing_e["provenance"]["experimental_database"] = db_name
                existing_e["provenance"]["experimental_reference"] = exp_e.get("reference", "")
        else:
            unmatched += 1
            new_entry = {
                "source": exp_e.get("source", "experimental"),
                "source_id": exp_e.get("source_id", f"exp-{unmatched}"),
                "formula": exp_formula,
                "structured_formula": exp_formula,
                "elements": exp_e.get("elements", []),
                "nsites": len(exp_e.get("elements", [])),
                "band_gap": None,
                "formation_energy_per_atom": None,
                "energy_above_hull": None,
                "is_experimental": True,
                "families": ["experimental_SSE"],
                "sse_family": "experimental",
                "mobile_ion": "Li",
                "carrier_elements": ["Li"],
                "tier": "experimental_gold",
                "quality_score": 95,
                "quality_flags": ["experimental_data", "has_conductivity"],
                "ssb_screening": {
                    "estimated_ionic_conductivity_S_cm": exp_e.get("conductivity_S_cm"),
                    "conductivity_source": f"experimental_{db_name}",
                    "experimental_activation_energy_eV": exp_e.get("activation_energy_eV"),
                    "measurement_temperature_K": exp_e.get("temperature_K"),
                    "mobile_ion": "Li",
                    "sse_family": "experimental",
                    "gates_passed": ["experimental"],
                    "sse_candidate_score": 100,
                },
                "provenance": exp_e.get("provenance", {}),
                "license": "CC-BY-4.0",
            }
            new_entries.append(new_entry)

    return matched, unmatched, conductivity_added, new_entries


def main():
    parser = argparse.ArgumentParser(description="Integrate experimental conductivity data")
    parser.add_argument("--ransom-path", type=str, default=None,
                        help="Path to Hargreaves 2023 CSV file")
    parser.add_argument("--obelix", action="store_true",
                        help="Try to load OBELiX via obelix-data package")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--cross-ref-only", action="store_true")
    args = parser.parse_args()

    if not args.ransom_path and not args.obelix:
        print("Specify at least one data source:")
        print("  --ransom-path <file.csv>  Hargreaves et al. 2023 database")
        print("  --obelix                  OBELiX via obelix-data package")
        sys.exit(1)

    BASE_DIR = Path(__file__).resolve().parent.parent
    DATASET_PATH = BASE_DIR / "dataset"

    print("=" * WIDTH)
    print("  EXPERIMENTAL DATA INTEGRATION")
    print("=" * WIDTH)

    all_experimental = []

    # --- Hargreaves 2023 ---
    if args.ransom_path:
        source_label = "Hargreaves et al. 2023 (npj Comput. Mater.)"
        print(f"\n  [{source_label}]")

        ransom_data = None
        path = Path(args.ransom_path)
        if path.exists():
            with open(path) as f:
                ransom_data = f.read()
            print(f"  Loaded from {path}")
        else:
            print(f"  File not found: {path}")
            print("  Attempting download...")
            ransom_data = try_fetch_ransom()

        if ransom_data:
            entries = parse_ransom_csv(ransom_data)
            print(f"  Parsed {len(entries):,} entries")
            for e in entries:
                e["experimental_database"] = "Hargreaves2023"
            all_experimental.extend(entries)
            with_cond = sum(1 for e in entries if e.get("conductivity_S_cm") is not None)
            with_ea = sum(1 for e in entries if e.get("activation_energy_eV") is not None)
            print(f"    With conductivity: {with_cond}")
            print(f"    With activation energy: {with_ea}")
        else:
            print(f"  Could not load Hargreaves 2023 data.")
            print(f"  Download manually from: {HARGREAVES_DOI}")

    # --- OBELiX Therrien 2025 ---
    if args.obelix:
        source_label = "OBELiX (Therrien et al. 2025, NRC-Mila)"
        print(f"\n  [{source_label}]")
        print("  Attempting obelix-data package...")
        ob_data = try_fetch_obelix_package()
        if ob_data is not None:
            entries = parse_obelix_via_package(ob_data)
            print(f"  Parsed {len(entries):,} entries")
            for e in entries:
                e["experimental_database"] = "OBELiX_Therrien2025"
            all_experimental.extend(entries)
            with_cond = sum(1 for e in entries if e.get("conductivity_S_cm") is not None)
            with_ea = sum(1 for e in entries if e.get("activation_energy_eV") is not None)
            print(f"    With conductivity: {with_cond}")
            print(f"    With activation energy: {with_ea}")
        else:
            print(f"  Could not load OBELiX via package.")
            print(f"  Try: pip install obelix-data")
            print(f"  Or:  https://github.com/nrc-mila/OBELiX")

    if not all_experimental:
        print("\n  No experimental data loaded. Nothing to integrate.")
        sys.exit(1)

    # --- Cross-reference with existing dataset ---
    print(f"\n  Loading Scandium-Dataset...")
    t0 = time.time()
    with open(DATASET_PATH / "entries_final_v3.json") as f:
        all_entries = json.load(f)
    print(f"  {len(all_entries):,} entries ({time.time()-t0:.1f}s)")

    print(f"\n{'─' * WIDTH}")
    print("  Cross-referencing...")
    print(f"{'─' * WIDTH}")

    matched, unmatched, conductivity_added, new_entries = cross_reference_and_add(
        all_experimental, all_entries
    )

    print(f"\n  Results:")
    print(f"    Matched existing entries: {matched}")
    print(f"    Unmatched (new compositions): {unmatched}")
    print(f"    Conductivity labels added: {conductivity_added}")
    print(f"    New experimental entries: {len(new_entries)}")

    if new_entries:
        cond_entries = [(e.get("formula", "?"),
                         e.get("ssb_screening", {}).get("estimated_ionic_conductivity_S_cm"))
                        for e in new_entries
                        if e.get("ssb_screening", {}).get("estimated_ionic_conductivity_S_cm")]
        for formula, cond in sorted(cond_entries, key=lambda x: -abs(x[1] or 0))[:5]:
            if cond:
                print(f"    {formula:30s} σ={cond:.2e} S/cm")

    if not args.dry_run:
        if new_entries:
            all_entries.extend(new_entries)
            print(f"\n  Added {len(new_entries):,} experimental entries")

        output_path = DATASET_PATH / "entries_final_v3.json"
        print(f"  Writing to {output_path}...")
        t_write = time.time()
        with open(output_path, "w") as f:
            json.dump(all_entries, f)
        print(f"  Done ({time.time()-t_write:.1f}s)")

        experimental_count = sum(1 for e in all_entries if e.get("is_experimental"))
        with_conductivity_total = sum(
            1 for e in all_entries
            if e.get("ssb_screening", {}).get("estimated_ionic_conductivity_S_cm")
        )

        print(f"\n{'─' * WIDTH}")
        print("  INTEGRATION SUMMARY")
        print(f"{'─' * WIDTH}")
        db_sources = set(e.get("experimental_database", "unknown") for e in all_experimental)
        for db in sorted(db_sources):
            count = sum(1 for e in all_experimental if e.get("experimental_database") == db)
            print(f"  {db}: {count} entries")
        print(f"  Total experimental entries in dataset: {experimental_count}")
        print(f"  Entries with conductivity labels: {with_conductivity_total}")
    else:
        print(f"\n  (dry-run)")

    print("=" * WIDTH)


if __name__ == "__main__":
    main()
