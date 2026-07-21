# Changelog

All notable changes to the Scandium Dataset will be documented in this file.

## [0.0.0] — 2026-07-21

### Added
- OQMD symmetry pass: 171,764/171,780 space groups computed via spglib
- OQMD volume repair: 47,807 entries with extracted volume from structure_json
- OQMD density repair: 47,807 entries with computed density from elements + volume
- JARVIS volume extraction: 25,673 entries with volume from structure_json
- Strict Gold definition: 11 total gates (8 base + G9 provenance + G10 quality ≥ 80 + G11 no defects)
- Provenance tracking: checksum, repair history, tier gates per entry
- Cross-source agreement study: 11,741 MP↔JARVIS overlapping formulas quantified
- Quality score calibration: monotonic improvement proven across 6 metrics
- Dataset census: 221 space groups, element frequencies, outlier detection
- Per-source reports: MP, OQMD, JARVIS strengths, weaknesses, biases
- Per-family reports: 10 families with battery relevance assessments
- Battery subset: 82,925 entries (7 battery families)
- Electrolyte subset: 41,665 entries (strict Gold, no OQMD)
- Four benchmark split types: random, composition, family, chemistry held-out
- Evaluation runner with baseline results
- This CHANGELOG

### Changed
- Gold tier: 67,174 → 96,242 entries (+29,068 OQMD entries unblocked by symmetry pass)
- Strict Gold: 55,944 → 56,966 entries (G11 defects now zero)

### Fixed
- OQMD coordinate artifact: 137,405 entries re-loaded with coords_are_cartesian=False
- OQMD space_group: None → 171,764 computed (was blocking Gold tier)
- OQMD volume: 47,807 zero → all populated from structure_json
- OQMD density: 47,807 zero → all computed from elements + volume
- JARVIS volume: 25,673 zero → all populated from structure_json

### Removed
- 31,997 duplicate entries (21,140 groups) removed during dedup

### Known Issues
- 39,276 base Gold entries have quality 70-79 (passes base Gold but not Strict Gold G10)
- JARVIS entries missing energy_above_hull (100%, 25,673 entries) — fundamental limitation
- Garnet family only 23 entries — insufficient for ML training
- 16 OQMD entries where spglib failed to find space group

## [v2.0] — 2026-07-20

### Changed
- Initial multi-source integration (MP + OQMD + JARVIS)
- Quality scoring v2 with 5 sub-scores

## [v1.0] — 2026-07-18

### Added
- Initial release with MP-only dataset
- Basic validation and tiering
