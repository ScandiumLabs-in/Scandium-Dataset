# Getting Started

## Installation

The Scandium Dataset is distributed as JSON files. No installation required
for basic use. For benchmark evaluation, clone the repository:

```bash
git clone https://github.com/Scandium-Labs/Scandium-Dataset
cd Scandium-Dataset
```

Python 3.9+ is recommended.

## Loading the Dataset

```python
import json

# Load the full dataset
with open("dataset/entries_final_v3.json") as f:
    entries = json.load(f)

print(f"Loaded {len(entries):,} entries")
```

## Basic Operations

### Filter by tier

```python
gold = [e for e in entries if e.get("tier") == "gold"]
strict_gold = [e for e in entries
               if e.get("strict_gold", {}).get("is_strict_gold")]
validated = [e for e in entries if e.get("tier") == "validated"]
```

### Filter by family

```python
battery_families = {"layered_oxide", "sulfide_sse", "halide_sse",
                    "polyanion", "nasicon", "garnet", "borohydride"}

battery = [e for e in entries
           if set(e.get("families", [])) & battery_families]
```

### Filter by source

```python
mp = [e for e in entries if e.get("source") == "mp"]
oqmd = [e for e in entries if e.get("source") == "oqmd"]
jarvis = [e for e in entries if e.get("source") == "jarvis"]
```

### Access properties

```python
for e in entries[:5]:
    print(f"{e['formula']:20s}  "
          f"FE={e.get('formation_energy_per_atom', 'N/A'):>8.4f}  "
          f"EaH={e.get('energy_above_hull', 'N/A'):>8.4f}  "
          f"BG={e.get('band_gap', 'N/A'):>8.4f}")
```

### Check provenance

```python
e = entries[0]
prov = e.get("provenance", {})
print(f"Source: {prov.get('source')} ({prov.get('source_id')})")
print(f"Checksum: {prov.get('checksum')}")
print(f"Repairs: {prov.get('repairs_applied')}")
print(f"Tier: {prov.get('tier_assignment', {}).get('tier')}")
```

## Using Editions

```python
# Battery subset
with open("dataset/battery_subset_v3.json") as f:
    battery = json.load(f)

# Electrolyte subset (strict Gold only)
with open("dataset/electrolyte_subset_v3.json") as f:
    electrolyte = json.load(f)
```

## Using the Benchmark Splits

```python
import json

with open("dataset/splits/random_80_10_10.json") as f:
    split = json.load(f)

train_entries = [entries[i] for i in split["train"]]
val_entries = [entries[i] for i in split["val"]]
test_entries = [entries[i] for i in split["test"]]
```

See [examples/](../examples/) for complete scripts.
