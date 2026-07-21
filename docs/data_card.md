# Data Card: Scandium Dataset v0.0

## Dataset Description

- **Name**: Scandium Dataset v0.0
- **Version**: 0.0.0
- **Date**: 2026-07-21
- **Publisher**: Scandium Labs
- **License**: Multiple (CC BY 4.0 + CC0 + OQMD non-commercial)
- **DOI**: pending
- **Repository**: https://github.com/Scandium-Labs/Scandium-Dataset

## Composition

- **Total entries**: 266,732
- **Unique formulas**: 148,141
- **Sources**: 3 (MP 69,279 + OQMD 171,780 + JARVIS 25,673)
- **Material families**: 10 (7 battery-relevant)
- **Carrier elements**: Li, Na, Mg, Ca, Zn, Al, K

## Properties

| Property | Unit | Coverage | Type |
|----------|------|----------|------|
| Formation Energy | eV/atom | 100% | Continuous |
| Energy Above Hull | eV/atom | 90.4% | Continuous |
| Band Gap | eV | 99.9% | Continuous |

## Collection Methodology

All entries are sourced from established open DFT databases:
- **Materials Project**: PAW-PBE pseudopotentials, computed by MP consortium
- **OQMD**: PAW-PBE, computed by Wolverton group at Northwestern
- **JARVIS-DFT**: optPBE + TBmBJ band gaps, computed by NIST

## Preprocessing

1. **Unified schema**: All sources mapped to common field names
2. **Deduplication**: 31,997 duplicates removed (chunked fingerprint matching)
3. **Repair**: 137,405 OQMD coordinate repairs, 171,764 space group computations
4. **Quality scoring**: 5 sub-scores (geometry, DFT, metadata, novelty, chemical)
5. **Tiering**: 3 tiers (Raw, Validated, Gold) + Strict Gold (11 gates)
6. **Provenance**: Checksums, repair history, dedup resolution per entry

## Splits

Four frozen split types for benchmarking:
- Random 80/10/10
- Composition held-out (no formula overlap)
- Family held-out (smallest families as test)
- Chemistry held-out (halides as OOD test)

## Quality Metrics

- Quality score range: 50-88 (0-100 scale, mean 77.4)
- Score calibration verified: monotonic relationship with label reliability
- Cross-source FE agreement: 0.20-0.23 eV/atom MAE
- Space group agreement (MP↔JARVIS): 78.6%

## Intended Use

- Materials property prediction (FE, EaH, BG)
- Battery materials screening
- Representation learning pre-training
- Cross-source DFT comparison

## Known Limitations

- No experimentally validated entries
- No ionic conductivity or migration barriers
- JARVIS entries lack EaH
- 16 OQMD entries missing space group
- Garnet family only 23 entries

## Citation

```bibtex
@software{scandium_dataset_v3,
  title = {Scandium Dataset v0.0},
  version = {0.0.0},
  date = {2026-07-21},
  publisher = {Scandium Labs}
}
```
