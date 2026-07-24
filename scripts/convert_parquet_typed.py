"""Convert the encoded-string Parquet to proper typed columns for HF viewer compat."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dataset.dataset_store import _decode_value

import pyarrow as pa
import pyarrow.parquet as pq

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"
SRC = DATASET_DIR / "entries_v3.parquet"
DST = DATASET_DIR / "entries_v4_typed.parquet"


def infer_type(col_name, prefixes):
    if 'b' in prefixes:
        return pa.bool_()
    elif 'i' in prefixes:
        return pa.int64()
    elif 'f' in prefixes:
        return pa.float64()
    return pa.string()


def safe(v, pa_type):
    if v is None:
        return None
    d = _decode_value(v)
    if d is None or d == '':
        return None
    try:
        if isinstance(d, (dict, list)):
            return json.dumps(d)
        if pa_type == pa.int64():
            return int(d)
        if pa_type == pa.float64():
            return float(d)
        if pa_type == pa.bool_():
            return bool(d)
        return str(d)
    except (ValueError, TypeError):
        return None


def main():
    print("Reading source Parquet...")
    t0 = time.time()
    src = pq.read_table(SRC)
    print(f"  {src.num_rows:,} rows, {src.num_columns} columns ({time.time()-t0:.1f}s)")

    pcols = {col: set() for col in src.column_names}
    for i in range(min(5000, src.num_rows)):
        for col in src.column_names:
            raw = src.column(col)[i].as_py()
            pcols[col].add(raw.split(':')[0] if raw and ':' in raw else None)

    print("Decoding and converting...")
    t0 = time.time()
    arrays = {}
    for col in src.column_names:
        raw_col = src.column(col)
        tgt = infer_type(col, pcols[col])
        vals = [safe(raw_col[i].as_py(), tgt) for i in range(raw_col.length())]
        arr = pa.array(vals, type=tgt)
        arrays[col] = arr
        print(f"  {col:40s} → {str(tgt):10s}  ({time.time()-t0:.1f}s)")

    print("Building typed table...")
    schema = pa.schema([pa.field(c, arrays[c].type) for c in src.column_names])
    table = pa.table(arrays, schema=schema)

    print("Writing typed Parquet...")
    pq.write_table(table, DST, compression="zstd", compression_level=9)
    sz = DST.stat().st_size
    print(f"  {DST.name}: {sz/1e6:.1f} MB")

    verify = pq.read_table(DST)
    assert verify.num_rows == src.num_rows
    print(f"Verified: {verify.num_rows:,} rows × {verify.num_columns} cols")
    for f in verify.schema:
        print(f"  {f.name:40s} {f.type}")


if __name__ == "__main__":
    main()
