# Scandium Dataset v0.0.0

**Release Date:** 2026-07-21
**Version:** 0.0.0
**Status:** Release Candidate 1

## Dataset Contents

| Edition | Entries | Description |
|---------|---------|-------------|
| General | 266,732 | All sources, all tiers |
| Battery | 82,925 | Battery-relevant families |
| Electrolyte | 41,665 | Strict Gold electrolytes only |

## Source Distribution
| Source | Count | % |
|--------|-------|---|
| oqmd       | 171,780 | 64.4% |
| mp         | 69,279 | 26.0% |
| jarvis     | 25,673 | 9.6% |

## Tier Distribution
| Tier | Count |
|------|-------|
| validated    | 140,382 |
| gold         | 96,242 |
| raw          | 30,108 |

| **Strict Gold** (11 gates) | 56,966 |

## Property Coverage
| Property | N | Missing | Mean | Median |
|----------|---|---------|------|--------|
| formation_energy_per_atom                | 266,732 |      0 |  -0.5777 |  -0.1956 |
| energy_above_hull                        | 241,059 | 25,673 |   0.3857 |   0.2369 |
| band_gap                                 | 266,581 |    151 |   0.5825 |      N/A |

## Families
| Family | Count | % |
|--------|-------|---|
| intermetallic             | 166,930 | 62.6% |
| layered_oxide             | 42,015 | 15.8% |
| halide_sse                | 18,803 | 7.0% |
| sulfide_sse               | 16,359 | 6.1% |
| oxide                     | 11,928 | 4.5% |
| unknown                   |  4,949 | 1.9% |
| polyanion                 |  4,519 | 1.7% |
| borohydride               |    646 | 0.2% |
| nasicon                   |    560 | 0.2% |
| garnet                    |     23 | 0.0% |

## Verification Status
- [x] OQMD coordinate artifact repaired (137,405 entries, Type A, 0 errors)
- [x] Deduplication complete (31,997 duplicates removed)
- [x] Quality scoring v2 (5 sub-scores, mean 77.4)
- [x] Tier classification (3-tier + Strict Gold)
- [x] Cross-source agreement study (MP↔JARVIS: 11,741 overlaps, FE MAE 0.20 eV)
- [x] Quality score calibration (monotonic proof — score↑ = reliability↑)
- [x] Dataset census (221 space groups, element frequencies, outlier detection)
- [x] Per-source reports (MP, OQMD, JARVIS — strengths, weaknesses, biases)
- [x] Per-family reports (10 families, battery relevance assessments)
- [x] Provenance tracking (every entry v0.0+)
- [x] Strict Gold gates (11 gates, 83.3% retention from base Gold)
- [x] OQMD symmetry pass — 171,764/171,780 space groups computed via spglib
- [x] OQMD volume=0 repair — all 47,807 entries fixed

## Known Issues
1. OQMD space_group now computed — RESOLVED ✅
2. OQMD volume=0 now fixed — RESOLVED ✅
3. OQMD density=0 now fixed — RESOLVED ✅
4. JARVIS volume now populated — RESOLVED ✅
5. 39,276 base Gold entries have quality 70-79 (pass base Gold but not Strict Gold) — needs scoring review
6. JARVIS entries missing energy_above_hull (100%, 25,673 entries) — fundamental limitation
7. Garnet family only has 23 entries — insufficient for ML training

## Checksums
| File | SHA256 |
|------|--------|
| entries_final_v3.json                                   | f6148e63f9e1ccbb29f19c26be01ba6c60257ef4dc32e9c56baa4d305aaeb4c4 |
| battery_subset_v3.json                                  | 4ef02c8e0000dca1dbad54b0e197222f564ccb7a16613bbd214f50b7ba2b8411 |
| electrolyte_subset_v3.json                              | 788bf8048aaa4b98966a712cd2a5b6b7a7c2b1c7e77b0b7376e67d8a8c69a8a3 |

## Strict Gold Definition
Strict Gold = base Gold (8 gates: entry exists, valid structure, targets present,
no critical flags, quality ≥70, unique, no label conflicts, stable, complete metadata)
**+ 3 additional gates:**
- G9: Provenance complete (source_id + checksum)
- G10: Quality score ≥ 80 (calibrated: 85.2% valid, 0.97 SG, 0.18 FE MAE)
- G11: No known defects (volume > 0, density > 0, space_group present)

## Citation
```
@software{scandium_labs_dataset_v3,
  title = {Scandium Dataset v0.0},
  version = {0.0.0},
  date = {2026-07-21},
  publisher = {Scandium Labs},
}
```

## License
- MP entries: CC BY 4.0 (attribution required)
- JARVIS entries: CC0 (public domain)
- OQMD entries: Free for non-commercial use
- Scandium processing/scoring: CC BY 4.0
