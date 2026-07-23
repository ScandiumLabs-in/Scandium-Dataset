"""Fast OBELiX merge using direct PyArrow table manipulation.

Avoids the scan() bottleneck by building a formula index from the
Parquet columns directly and applying all updates at once.
"""
import json, sys, time
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "dataset"))
from dataset_store import _encode_value, _decode_value, SCALAR_COLUMNS, JSON_STRING_FIELDS

import pyarrow.parquet as pq
import pyarrow as pa
import pandas as pd

PARQUET_PATH = BASE_DIR / "dataset" / "entries_v3.parquet"
INDEX_PATH = BASE_DIR / "dataset" / "entries_v3.index.json"
OBELIX_DATA_PATH = "/tmp/obelix_rawdata"

WIDTH = 60


def load_obelix():
    import obelix
    ob = obelix.OBELiX(data_path=OBELIX_DATA_PATH, no_cifs=True)
    df = ob.dataframe
    return df


def format_obelix_entry(row, seq_id=0):
    """Convert OBELiX DataFrame row to a dataset entry dict."""
    formula = str(row.get("Reduced Composition", ""))
    true_comp = str(row.get("True Composition", ""))
    conductivity = row.get("Ionic conductivity (S cm-1)")
    if pd.notna(conductivity):
        conductivity = float(conductivity)
    else:
        conductivity = None
    doi = str(row.get("DOI", ""))
    family = str(row.get("Family", ""))
    sg = str(row.get("Space group", ""))
    icsd = row.get("ICSD ID")

    entry = {
        "source": "OBELiX",
        "source_id": f"OBELiX-{seq_id:04d}",
        "formula": formula,
        "structured_formula": true_comp if true_comp and true_comp != "nan" else formula,
        "nsites": 0, "band_gap": None,
        "formation_energy_per_atom": None, "energy_above_hull": None,
        "is_experimental": True,
        "families": [f"experimental_{family}"] if family and family != "nan" else ["experimental_SSE"],
        "sse_family": family if family and family != "nan" else "experimental",
        "mobile_ion": "Li", "carrier_elements": ["Li"],
        "tier": "experimental_gold", "quality_score": 100,
        "quality_flags": ["experimental_data", "has_conductivity"],
        "space_group": sg if sg != "nan" else "",
        "elements": list(set(c for c in formula if c.isalpha())),
        "ssb_screening": {
            "estimated_ionic_conductivity_S_cm": conductivity,
            "conductivity_source": "experimental_OBELiX_Therrien2025",
            "mobile_ion": "Li",
            "sse_family": family if family and family != "nan" else "experimental",
            "gates_passed": ["experimental"],
            "sse_candidate_score": 100,
        },
        "provenance": {
            "source": "OBELiX_Therrien2025", "source_id": f"OBELiX-{seq_id:04d}",
            "doi": "https://github.com/nrc-mila/OBELiX",
            "icsd_id": str(icsd) if pd.notna(icsd) else "",
            "experimental_confirmed": True,
            "experimental_database": "OBELiX_Therrien2025",
            "experimental_reference": doi if doi != "nan" else "",
        },
        "license": "CC-BY-4.0",
    }
    return entry


def main():
    print("=" * WIDTH)
    print("  OBELiX FAST MERGE")
    print("=" * WIDTH)

    print("\nLoading OBELiX data...")
    t0 = time.time()
    df = load_obelix()
    print(f"  {len(df):,} entries, {df['Reduced Composition'].nunique()} unique comps ({time.time()-t0:.1f}s)")

    print("\nBuilding formula index from Parquet store...")
    t1 = time.time()
    table = pq.read_table(PARQUET_PATH)

    # Cast null-type columns to string so concat_tables works later
    from pyarrow import types
    null_cols = [f.name for f in table.schema if types.is_null(f.type)]
    if null_cols:
        new_fields = []
        for f in table.schema:
            if f.name in null_cols:
                new_fields.append(pa.field(f.name, pa.string()))
            else:
                new_fields.append(f)
        table = table.cast(pa.schema(new_fields))
    print(f"  {table.num_rows:,} rows loaded ({time.time()-t1:.1f}s)")

    # Build formula -> row index map
    formula_to_rows = defaultdict(list)
    for i in range(table.num_rows):
        for col_name in ["formula", "structured_formula"]:
            raw = table.column(col_name)[i].as_py()
            if raw:
                decoded = _decode_value(raw)
                if decoded:
                    formula_to_rows[str(decoded).lower()].append(i)
    print(f"  Index: {len(formula_to_rows):,} unique formulas -> {sum(len(v) for v in formula_to_rows.values()):,} references")

    # Match OBELiX entries
    print("\nCross-referencing...")
    matched_rows = set()
    unmatched_df_rows = []
    matched_df = []
    for idx, row in df.iterrows():
        formula = str(row.get("Reduced Composition", "")).lower()
        matching = formula_to_rows.get(formula, [])
        if matching:
            matched_rows.update(matching)
            matched_df.append(row)
        else:
            unmatched_df_rows.append(row)

    print(f"  Matched: {len(matched_df)} OBELiX entries → {len(matched_rows)} dataset rows")
    print(f"  Unmatched: {len(unmatched_df_rows)} OBELiX entries")

    # Save unmatched list
    unmatched_formulas = sorted(set(
        str(r.get("Reduced Composition", "")) for r in unmatched_df_rows
    ))
    with open(BASE_DIR / "dataset" / "obelix_unmatched_formulas.json", "w") as f:
        json.dump(unmatched_formulas, f, indent=2)
    print(f"  Unmatched formulas saved: {len(unmatched_formulas)}")

    # Count by family
    from collections import Counter
    fam_counts = Counter(str(r.get("Family", "")) for r in unmatched_df_rows)
    print(f"\n  Unmatched by family:")
    for fam, cnt in sorted(fam_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {fam if fam != 'nan' else 'unspecified':30s}: {cnt}")

    # --- Apply updates to matched entries ---
    print(f"\n{'─' * WIDTH}")
    print("  Applying updates to matched entries...")
    t2 = time.time()

    # For each matched row, read current ssb_screening, append conductivity info
    ssb_col = table.column("ssb_screening").to_pylist()
    prov_col = table.column("provenance").to_pylist()
    exp_col = table.column("is_experimental").to_pylist()
    sid_col = table.column("source_id").to_pylist()

    # Group matched OBELiX entries by formula for efficient update
    formula_updates = defaultdict(list)
    for r in matched_df:
        f = str(r.get("Reduced Composition", "")).lower()
        conductivity = float(r.get("Ionic conductivity (S cm-1)")) if pd.notna(r.get("Ionic conductivity (S cm-1)")) else None
        doi = str(r.get("DOI", ""))
        formula_updates[f].append({"conductivity": conductivity, "doi": doi})

    updates_applied = 0
    for row_i in matched_rows:
        sid_raw = sid_col[row_i]
        sid = _decode_value(sid_raw) if sid_raw else None

        # Decode current ssb_screening
        ssb_raw = ssb_col[row_i]
        ssb = _decode_value(ssb_raw) if ssb_raw else {}
        if not isinstance(ssb, dict):
            ssb = {}

        # Find matching OBELiX data for this entry's formula
        for col_name in ["formula", "structured_formula"]:
            raw = table.column(col_name)[row_i].as_py()
            if raw:
                formula_decoded = _decode_value(raw)
                if formula_decoded:
                    updates = formula_updates.get(str(formula_decoded).lower(), [])
                    if updates:
                        # Take the first OBELiX measurement for this formula
                        upd = updates[0]
                        if upd["conductivity"] is not None:
                            ssb["estimated_ionic_conductivity_S_cm"] = upd["conductivity"]
                            ssb["conductivity_source"] = "experimental_OBELiX_Therrien2025"
                        if upd["doi"] and upd["doi"] != "nan":
                            ssb["experimental_reference"] = upd["doi"]
                    break

        ssb_col[row_i] = _encode_value(ssb)

        # Update provenance
        prov_raw = prov_col[row_i]
        prov = _decode_value(prov_raw) if prov_raw else {}
        if not isinstance(prov, dict):
            prov = {}
        prov["experimental_confirmed"] = True
        prov["experimental_database"] = "OBELiX_Therrien2025"
        prov_col[row_i] = _encode_value(prov)

        # Mark as experimental
        exp_col[row_i] = _encode_value(True)

        updates_applied += 1

    # Write updated columns back to table
    table = table.set_column(
        table.schema.get_field_index("ssb_screening"), "ssb_screening",
        pa.chunked_array([pa.array(ssb_col)])
    )
    table = table.set_column(
        table.schema.get_field_index("provenance"), "provenance",
        pa.chunked_array([pa.array(prov_col)])
    )
    table = table.set_column(
        table.schema.get_field_index("is_experimental"), "is_experimental",
        pa.chunked_array([pa.array(exp_col)])
    )
    print(f"  {updates_applied} rows updated ({time.time()-t2:.1f}s)")

    # --- Append unmatched as new entries ---
    print(f"\nAppending {len(unmatched_df_rows)} unmatched OBELiX entries...")
    t3 = time.time()

    # Import the standardized extraction from dataset_store
    ALL_FIELDS = SCALAR_COLUMNS + JSON_STRING_FIELDS
    ALL_FIELDS_SET = set(ALL_FIELDS)

    new_entry_dicts = []
    for i, row in enumerate(unmatched_df_rows):
        entry = format_obelix_entry(row, i)
        encoded = {}
        for f in ALL_FIELDS:
            val = _encode_value(entry.get(f))
            encoded[f] = val if val is not None else ""
        new_entry_dicts.append(encoded)

    new_batch = pa.Table.from_pylist(new_entry_dicts)

    # Add any columns from existing table schema that are missing in new_batch
    missing_from_new = [f for f in table.schema.names if f not in new_batch.schema.names]
    for f in missing_from_new:
        # Need string type to match existing schema — insert empty strings
        arr = pa.array([""] * new_batch.num_rows, type=pa.string())
        new_batch = new_batch.append_column(pa.field(f, pa.string()), arr)

    # Remove columns from new_batch not in existing schema
    cols_to_drop = [f for f in new_batch.schema.names if f not in table.schema.names]
    for f in cols_to_drop:
        col_idx = new_batch.schema.get_field_index(f)
        new_batch = new_batch.remove_column(col_idx)

    # Reorder columns to match
    new_batch = new_batch.select(table.schema.names)

    table = pa.concat_tables([table, new_batch])
    print(f"  Appended {new_batch.num_rows} rows ({time.time()-t3:.1f}s)")
    print(f"  Total rows: {table.num_rows:,}")

    # --- Rewrite Parquet + index ---
    print(f"\n{'─' * WIDTH}")
    print("  Checkpointing...")
    t4 = time.time()
    pq.write_table(table, PARQUET_PATH, compression="zstd")

    # Rebuild index
    sids_raw = table.column("source_id").to_pylist()
    sids_decoded = [_decode_value(s) for s in sids_raw]
    index = {sid: i for i, sid in enumerate(sids_decoded)}
    with open(INDEX_PATH, "w") as f:
        json.dump(index, f)
    print(f"  Parquet + index written ({time.time()-t4:.1f}s)")

    # Summary
    with_cond = sum(
        1 for i in range(table.num_rows)
        if table.column("ssb_screening")[i].as_py()
        and "estimated_ionic_conductivity" in str(table.column("ssb_screening")[i].as_py())
    )
    exp_new = sum(
        1 for i in range(table.num_rows)
        if table.column("tier")[i].as_py()
        and "experimental" in str(table.column("tier")[i].as_py())
    )

    print(f"\n{'─' * WIDTH}")
    print("  MERGE COMPLETE")
    print(f"{'─' * WIDTH}")
    print(f"  OBELiX entries integrated: {len(df)}")
    print(f"  Matched + tagged: {len(matched_df)}")
    print(f"  New entries appended: {len(unmatched_df_rows)}")
    print(f"  Unmatched formulas (acquisition target): {len(unmatched_formulas)}")
    print(f"  Total entries in dataset: {table.num_rows:,}")
    print("=" * WIDTH)

    return 0


if __name__ == "__main__":
    sys.exit(main())
