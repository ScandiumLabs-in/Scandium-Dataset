# Source Audit

**Date:** 2026-07-21 23:35:39  

## Dataset Overview

The Scandium-Dataset v0.0 aggregates computational materials data from three sources, yielding **266,732 total entries** across three tiers (Gold, Validated, Raw).

### Source Distribution

| Source | Entries | Percentage | License |
|--------|---------|------------|--------|
| Materials Project    |  69,279 |  26.0% | CC BY 4.0 |
| OQMD                 | 171,780 |  64.4% | Non-commercial with attribution |
| JARVIS-DFT           |  25,673 |   9.6% | CC0 |
## Schema Integrity

- ✅ **source_oqmd**: 171,780 entries

- ✅ **source_mp**: 69,279 entries

- ✅ **source_jarvis**: 25,673 entries

- ✅ **all_sources_known**: 3 valid sources

- ✅ **structure_json_valid**: all parseable

- ✅ **no_duplicate_ids**: all source IDs unique

## License Compliance

- **mp**: 69,279 entries: CC BY 4.0

- **oqmd**: 171,780 entries: non-commercial use OK

- **jarvis**: 25,673 entries: CC0

## Per-Source Statistics

- ✅ **mp_formation_energy_per_atom_present**: 0 missing (100% coverage)

- ✅ **mp_energy_above_hull_present**: 0 missing (100% coverage)

- ✅ **mp_band_gap_present**: 0 missing (100% coverage)

- ✅ **mp_space_group_present**: 0 missing (100% coverage)

- ✅ **mp_volume_present**: 0 missing (100% coverage)

- ✅ **mp_density_present**: 0 missing (100% coverage)

- ✅ **oqmd_formation_energy_per_atom_present**: 0 missing (100% coverage)

- ✅ **oqmd_energy_above_hull_present**: 0 missing (100% coverage)

- ⚠️ **oqmd_band_gap_missing**: 151 / 171,780 (0.1%)

- ⚠️ **oqmd_space_group_missing**: 16 / 171,780 (0.0%)

- ✅ **oqmd_volume_present**: 0 missing (100% coverage)

- ✅ **oqmd_density_present**: 0 missing (100% coverage)

- ✅ **jarvis_formation_energy_per_atom_present**: 0 missing (100% coverage)

- ❌ **jarvis_energy_above_hull_missing**: 25,673 / 25,673 (100.0%)

- ✅ **jarvis_band_gap_present**: 0 missing (100% coverage)

- ✅ **jarvis_space_group_present**: 0 missing (100% coverage)

- ✅ **jarvis_volume_present**: 0 missing (100% coverage)

- ✅ **jarvis_density_present**: 0 missing (100% coverage)

## Source Quality Summary

| Source | Entries | Quality Mean | Quality Median | Key Strengths | Key Weaknesses |
|--------|---------|-------------|----------------|---------------|----------------|
| mp       |  69,279 | 0.0 | 0.0 |  |  |
| oqmd     | 171,780 | 0.0 | 0.0 |  |  |
| jarvis   |  25,673 | 0.0 | 0.0 |  |  |
