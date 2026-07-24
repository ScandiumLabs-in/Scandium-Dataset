"""Indexed Parquet-backed dataset store for the Scandium-Dataset.

Replaces the 1.6 GB JSON singleton file with a columnar store that:
- Loads only the columns you need (no more parsing 1.6 GB for a formula lookup)
- Supports O(1) lookups by source_id via built-in index
- Writes incrementally (no full-rewrite for a single-entry update)
- Is natively viewable on HuggingFace Hub

Schema:
  - Each entry is a row in a PyArrow Table
  - Nested fields (ssb_screening, provenance, structure_json) are stored as
    top-level struct columns or serialized JSON strings
  - Index on source_id

Usage:
    store = DatasetStore.open()                    # load existing
    entry = store.lookup("mp-12345")               # O(1) by source_id
    store.update_field("mp-12345", "band_gap", 4.2)  # in-place update
    store.append(new_entries)                      # batch append
    store.checkpoint()                             # save to disk
"""
import json, time, os, shutil
from pathlib import Path
from typing import Optional
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.ipc as ipc
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
MASTER_PARQUET = DATASET_DIR / "entries_v4_typed.parquet"
MASTER_JSON = DATASET_DIR / "entries_final_v3.json"

# Columns that are simple scalars — stored directly in Parquet
SCALAR_COLUMNS = [
    "source", "source_id", "formula", "structured_formula",
    "band_gap", "formation_energy_per_atom", "energy_above_hull",
    "nsites", "nelements", "volume", "density",
    "mobile_ion", "tier", "quality_score",
    "is_experimental", "is_stable", "is_metal",
    "space_group", "space_group_number", "crystal_system",
    "sse_family", "license",
    # Newly added — were silently dropped in original conversion
    "duplicate_group", "source_weight",
    "total_magnetization", "fe_per_carrier",
    "volume_per_carrier", "carrier_fraction",
    "electronic_insulation", "space_group_symbol",
    "magnetic_ordering",
]

# Nested fields stored as JSON strings
JSON_STRING_FIELDS = [
    "structure_json", "ssb_screening", "provenance",
    "elements", "families", "carrier_elements",
    "quality_flags", "tags", "notes",
    # Newly added — were silently dropped in original conversion
    "anions", "strict_gold", "tier_detail", "tier_gates",
    "quality_sub_scores", "references", "merged_sources",
]


def _encode_value(val):
    """Encode a value for consistent storage.

    All values stored as strings. Nested objects (dicts, lists) use
    JSON encoding. Simple values are stringified with type prefixes
    so they can be decoded back to the correct type.
    """
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return "json:" + json.dumps(val)
    if isinstance(val, bool):
        return "b:" + ("1" if val else "0")
    if isinstance(val, int):
        return "i:" + str(val)
    if isinstance(val, float):
        return "f:" + str(val)
    if isinstance(val, str):
        return "s:" + val
    return "s:" + str(val)


def _decode_value(encoded):
    """Reverse of _encode_value."""
    if encoded is None:
        return None
    if not isinstance(encoded, str):
        return encoded
    if encoded.startswith("json:"):
        return json.loads(encoded[5:])
    if encoded.startswith("b:"):
        return encoded[2:] == "1"
    if encoded.startswith("i:"):
        return int(encoded[2:])
    if encoded.startswith("f:"):
        return float(encoded[2:])
    if encoded.startswith("s:"):
        return encoded[2:]
    # Typed Parquet stores JSON string columns without prefixes;
    # detect raw JSON objects/arrays and parse them.
    stripped = encoded.strip()
    if stripped and stripped[0] in ("{", "["):
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass
    return encoded


def _pyarrow_type(val):
    """Map a Python value to its best PyArrow type."""
    if val is None:
        return pa.null()
    if isinstance(val, bool):
        return pa.bool_()
    if isinstance(val, int):
        return pa.int64()
    if isinstance(val, float):
        return pa.float64()
    return pa.string()


def _first_pass_extract(entry, fields):
    """Extract fields with type-safe encoding."""
    result = {}
    for f in fields:
        result[f] = _encode_value(entry.get(f))
    return result


def _json_to_table_batch(entries, batch_size=50000):
    """Convert entries to PyArrow Table in batches."""
    rows = []
    for entry in entries:
        row = _first_pass_extract(entry, SCALAR_COLUMNS + JSON_STRING_FIELDS)
        rows.append(row)
        if len(rows) >= batch_size:
            yield pa.Table.from_pylist(rows)
            rows.clear()
    if rows:
        yield pa.Table.from_pylist(rows)


def convert_json_to_parquet(json_path=None, parquet_path=None, force=False):
    """Convert the master JSON file to Parquet format."""
    if json_path is None:
        json_path = MASTER_JSON
    else:
        json_path = Path(json_path)

    if parquet_path is None:
        parquet_path = MASTER_PARQUET
    else:
        parquet_path = Path(parquet_path)

    if parquet_path.exists() and not force:
        print(f"  Parquet already exists at {parquet_path}")
        print(f"  Use force=True to re-convert")
        return False

    print(f"  Loading JSON from {json_path}...")
    t0 = time.time()
    with open(json_path) as f:
        entries = json.load(f)
    print(f"  {len(entries):,} entries loaded ({time.time()-t0:.1f}s)")

    print(f"  Converting to Parquet...")
    t1 = time.time()
    tables = list(_json_to_table_batch(entries))
    if len(tables) == 1:
        table = tables[0]
    else:
        table = pa.concat_tables(tables)

    print(f"  Table rows: {table.num_rows}, columns: {table.num_columns}")
    print(f"  Writing to {parquet_path}...")
    pq.write_table(table, parquet_path, compression="zstd")
    file_size = os.path.getsize(parquet_path)
    print(f"  Done ({time.time()-t1:.1f}s), {file_size/1e9:.2f} GB")

    # Write a sidecar index (using decoded source_ids, not encoded)
    index_path = parquet_path.with_suffix(".index.json")
    source_ids_raw = table.column("source_id").to_pylist()
    source_ids_decoded = [_decode_value(s) for s in source_ids_raw]
    # Verify uniqueness
    unique_sids = set(source_ids_decoded)
    if len(unique_sids) < len(source_ids_decoded):
        dupes = len(source_ids_decoded) - len(unique_sids)
        print(f"  Warning: {dupes} duplicate source_ids found")
    index_data = {sid: i for i, sid in enumerate(source_ids_decoded)}
    with open(index_path, "w") as f:
        json.dump(index_data, f)
    print(f"  Index: {len(index_data)} entries")

    return True


class DatasetStore:
    """Indexed Parquet-backed store for the Scandium-Dataset.

    Provides O(1) lookup by source_id and incremental update without
    full-file rewrites.
    """
    _table: Optional[pa.Table] = None
    _index: Optional[dict] = None
    _dirty: bool = False
    _parquet_path: Path = MASTER_PARQUET
    _index_path: Path = MASTER_PARQUET.with_suffix(".index.json")

    def __init__(self, parquet_path=None):
        if parquet_path:
            self._parquet_path = Path(parquet_path)
            self._index_path = self._parquet_path.with_suffix(".index.json")

    @classmethod
    def open(cls, parquet_path=None):
        """Open existing store or convert from JSON if needed."""
        store = cls(parquet_path)
        p = store._parquet_path
        ip = store._index_path

        if not p.exists():
            print(f"  Parquet not found at {p}")
            print(f"  Converting from JSON...")
            convert_json_to_parquet(parquet_path=p)
            if not p.exists():
                raise FileNotFoundError(f"Could not create {p}")

        print(f"  Loading Parquet from {p}...")
        t0 = time.time()
        store._table = pq.read_table(p)
        print(f"  {store._table.num_rows:,} rows loaded ({time.time()-t0:.1f}s)")

        if ip.exists():
            with open(ip) as f:
                store._index = json.load(f)
            print(f"  Index: {len(store._index)} entries")
        else:
            print(f"  Rebuilding index...")
            t1 = time.time()
            sids_raw = store._table.column("source_id").to_pylist()
            sids_decoded = [_decode_value(s) for s in sids_raw]
            store._index = {sid: i for i, sid in enumerate(sids_decoded)}
            with open(ip, "w") as f:
                json.dump(store._index, f)
            print(f"  Index rebuilt ({time.time()-t1:.1f}s)")

        store._dirty = False
        return store

    def lookup(self, source_id: str) -> Optional[dict]:
        """Lookup an entry by source_id. O(1). Values decoded back to original types."""
        row_idx = self._index.get(source_id)
        if row_idx is None:
            return None
        row = self._table.slice(row_idx, 1).to_pylist()[0]
        return {k: _decode_value(v) for k, v in row.items()}

    def lookup_many(self, source_ids):
        """Lookup multiple entries by source_id."""
        result = []
        missing = []
        for sid in source_ids:
            e = self.lookup(sid)
            if e:
                result.append(e)
            else:
                missing.append(sid)
        return result, missing

    def scan(self, columns=None, filter_fn=None):
        """Iterate over entries, optionally filtered.

        Args:
            columns: list of column names to load (None = all)
            filter_fn: callable(entry) -> bool to filter rows

        Yields:
            dict per matching entry
        """
        table = self._table
        if columns:
            available = [c for c in columns if c in table.column_names]
            table = table.select(available)

        for row in table.to_pylist():
            decoded = {k: _decode_value(v) for k, v in row.items()}
            if filter_fn is None or filter_fn(decoded):
                yield decoded

    def count(self, filter_fn=None):
        """Count entries, optionally filtered."""
        if filter_fn is None:
            return self._table.num_rows
        return sum(1 for _ in self.scan(filter_fn=filter_fn))

    @staticmethod
    def _is_encoded_table(table: pa.Table) -> bool:
        """Check if the table uses the old all-string encoded format."""
        return all(
            table.schema.field(i).type == pa.string()
            for i in range(table.num_columns)
        )

    def update_field(self, source_id: str, field: str, value, nested_path: Optional[str] = None):
        """Update a single field for an entry. In-memory only until checkpoint().

        Args:
            source_id: entry identifier
            field: column/field name to update
            value: new value
            nested_path: if set, field is treated as a JSON-encoded dict column
                         and value is set at field[nested_path] within it
        """
        row_idx = self._index.get(source_id)
        if row_idx is None:
            raise KeyError(f"Entry not found: {source_id}")

        encoded_format = self._is_encoded_table(self._table)

        if nested_path:
            col_idx = self._table.schema.get_field_index(field)
            if col_idx < 0:
                raise KeyError(f"Nested field column not found: {field}")
            old_col = self._table.column(field)
            cur_values = old_col.to_pylist()
            cur_raw = cur_values[row_idx]
            cur_dict = _decode_value(cur_raw) if cur_raw is not None else {}
            if not isinstance(cur_dict, dict):
                cur_dict = {}
            cur_dict[nested_path] = value
            # Write back as plain JSON (no prefix) for typed format;
            # use encoded prefix for legacy format
            if encoded_format:
                cur_values[row_idx] = _encode_value(cur_dict)
            else:
                cur_values[row_idx] = json.dumps(cur_dict)
            new_col = pa.chunked_array([pa.array(cur_values, type=old_col.type)])
            self._table = self._table.set_column(col_idx, field, new_col)
        else:
            col_idx = self._table.schema.get_field_index(field)
            if encoded_format:
                write_val = _encode_value(value)
            else:
                write_val = value

            if col_idx >= 0:
                old_col = self._table.column(field)
                new_values = old_col.to_pylist()
                new_values[row_idx] = write_val
                new_col = pa.chunked_array([pa.array(new_values, type=old_col.type)])
                self._table = self._table.set_column(col_idx, field, new_col)
            else:
                n = self._table.num_rows
                new_values = [None] * n
                new_values[row_idx] = write_val
                pa_type = pa.string() if encoded_format else _pyarrow_type(value)
                new_col = pa.array(new_values, type=pa_type)
                self._table = self._table.append_column(
                    pa.field(field, pa_type), pa.chunked_array([new_col])
                )

        self._dirty = True

    def update_entry(self, source_id: str, updates: dict):
        """Apply multiple field updates to an entry."""
        for field, value in updates.items():
            self.update_field(source_id, field, value)

    def append(self, entries: list):
        """Append new entries (as dicts). Raises on duplicate source_id."""
        new_sids = [e.get("source_id") for e in entries]
        existing = [sid for sid in new_sids if sid in self._index]
        if existing:
            raise ValueError(f"Duplicate source_ids: {existing[:5]}")

        encoded_format = self._is_encoded_table(self._table)
        if encoded_format:
            batch = pa.Table.from_pylist([
                _first_pass_extract(e, SCALAR_COLUMNS + JSON_STRING_FIELDS)
                for e in entries
            ])
        else:
            batch = pa.Table.from_pylist(entries)

        # Ensure batch schema matches table schema — add missing columns as null
        for col_name in self._table.column_names:
            if col_name not in batch.column_names:
                col_type = self._table.schema.field(col_name).type
                null_arr = pa.nulls(len(entries), type=col_type)
                batch = batch.append_column(col_name, null_arr)

        self._table = pa.concat_tables([self._table, batch])

        start = len(self._index)
        for i, e in enumerate(entries):
            self._index[e["source_id"]] = start + i

        self._dirty = True

    def checkpoint(self):
        """Write in-memory state to disk."""
        if not self._dirty:
            return

        print(f"  Checkpointing to {self._parquet_path}...")
        t0 = time.time()
        pq.write_table(self._table, self._parquet_path, compression="zstd")
        print(f"  Done ({time.time()-t0:.1f}s)")

        # Update index file
        with open(self._index_path, "w") as f:
            json.dump(self._index, f)

        self._dirty = False

    def close(self):
        """Checkpoint and release memory."""
        if self._dirty:
            self.checkpoint()
        self._table = None
        self._index = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def num_entries(self):
        return self._table.num_rows if self._table else 0


if __name__ == "__main__":
    # Conversion entry point
    import argparse
    parser = argparse.ArgumentParser(description="Manage the Parquet dataset store")
    parser.add_argument("--convert", action="store_true", help="Convert JSON to Parquet")
    parser.add_argument("--force", action="store_true", help="Force re-conversion")
    args = parser.parse_args()

    if args.convert:
        convert_json_to_parquet(force=args.force)
    else:
        print("Usage: python dataset/dataset_store.py --convert")
