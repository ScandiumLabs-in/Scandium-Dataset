# Scandium-Dataset Ground Truth (v1.0.0 Audit)

## Property Coverage (Parquet Store, 267,230 entries)

### Primary columns
| Property | Coverage | Notes |
|----------|----------|-------|
| formation_energy_per_atom | 267,230 (100%) | All sources |
| energy_above_hull | 241,557 (90.4%) | JARVIS: 0% (25,673 missing). OBELiX: 0% (498 missing) |
| band_gap | 267,079 (99.9%) | 151 OQMD entries non-converged |
| nsites | 267,230 (100%) | |
| volume | 267,230 (100%) | |
| density | 267,230 (100%) | |
| space_group | 267,214 (100%) | |
| space_group_symbol | 266,716 (99.8%) | |
| structure_json | 267,230 (100%) | |
| tier | 267,230 (100%) | |
| quality_score | 267,230 (100%) | |
| provenance | 267,230 (100%) | Checksum in 266,732 (99.8%). No repair_history in Parquet |
| license | 267,230 (100%) | |
| source | 267,230 (100%) | mp=69,279, oqmd=171,780, jarvis=25,673, OBELiX=498 |
| mobile_ion | 267,230 (100%) | Li/Na=108,015 |
| sse_family | 267,230 (100%) | |
| duplicate_group | 21,140 (7.9%) | 31,997 total removed upstream |

### ssb_screening block
| Field | Coverage | Notes |
|-------|----------|-------|
| SSE family | 100% | Composition-based |
| Mobile ion | 100% | Li/Na/Mg presence-based |
| Thermo stable | 99.8% | |
| SSE candidate score | 100% | |
| Bulk/shear modulus | 100% | Geometric proxy, not DFT |
| BVSE barrier | 24,873 (23% of Li/Na) | 73,900 skipped (74.8% of 98,773 attempted) |
| Interfacial energy | 39,706 (14.9%) | |
| Stability window | 1,814 (0.7%) | |
| CAVD dimensionality | 0 (0%) | Not computed against Parquet |
| MLIP-NEB barrier | — | Scaffold, not run |
| DFT-NEB barrier | — | Not started |

## Tier Breakdown
- Gold: 96,242 (36.0%)
- Validated: 140,382 (52.5%)
- Raw: 30,108 (11.3%)
- experimental_gold: 498 (0.2%)
- Strict Gold: 56,966

## Family x Tier (SSE-relevant)
- Garnet: total 136 (Gold 19, Validated 4, Raw 0, OBELiX ~113)
- Halide SSE: total 18,803 (Gold 12,560)
- Sulfide SSE: total 16,359 (Gold 9,458)
- NASICON: total 560 (Gold 488)
- Intermetallic: total 166,930 (Gold 36,520)
- Layered oxide: total 42,015 (Gold 26,295)

## License Breakdown
- OQMD-noncommercial: 171,780 (64.3%) — non-commercial only
- CC-BY-4.0: 69,777 (26.1%) — commercial safe
- CC0-1.0: 25,673 (9.6%) — public domain

## Duplicate/Repair Log
- 31,997 duplicates removed upstream (pre-Parquet)
- 21,140 entries retain duplicate_group IDs in Parquet
- 137,405 repaired structures (OQMD coordinate fix) — repair_history NOT preserved in Parquet provenance
- 171,764 space groups computed (spglib) — all in Parquet
