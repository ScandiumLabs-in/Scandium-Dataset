# Provenance

## Every Entry Has a History

Since v0.0, every entry in the Scandium Dataset carries a `provenance` field
that records its complete history:

```python
{
    "provenance": {
        "source": "oqmd",
        "source_id": "472978",
        "checksum": "a1b2c3d4e5f6...",          # SHA256 of canonical fields
        "repairs_applied": [
            {
                "repair_id": "coordinate_artifact",
                "description": "OQMD coords_are_cartesian=True → False fix",
                "date": "2026-07-21"
            }
        ],
        "dedup_resolution": null,                 # null = unique, else group info
        "tier_assignment": {
            "tier": "gold",
            "tier_gates": {
                "raw": true,
                "validated": true,
                "gold": true
            }
        },
        "version": "3.0",
        "created_at": "2026-07-21T..."
    }
}
```

## What It Tracks

| Field | Description |
|-------|-------------|
| `source` | Original database (mp, oqmd, jarvis) |
| `source_id` | ID in the original database |
| `checksum` | SHA256 of canonical fields (source, formula, properties) |
| `repairs_applied` | List of all repairs with IDs and dates |
| `dedup_resolution` | If in a duplicate group, how it was resolved |
| `tier_assignment` | Current tier and all gate results |
| `version` | Dataset version when provenance was assigned |

## Why Provenance Matters

1. **Reproducibility**: Trace every entry back to its source
2. **Auditability**: Know exactly what repairs were applied
3. **Trust**: Evidence that data was not silently modified
4. **Debugging**: If a model fails on an entry, you can investigate its history
5. **Citation**: You can cite the original source entry, not just the aggregate

## Checksum Algorithm

The checksum is computed from these canonical fields in sorted order:

- source
- source_id
- formula
- nsites
- volume
- formation_energy_per_atom
- energy_above_hull
- band_gap
- space_group

This means any change to fundamental properties invalidates the checksum,
providing an integrity check for the entry.
