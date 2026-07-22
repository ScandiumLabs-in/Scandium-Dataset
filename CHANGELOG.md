# Changelog

All notable changes to the Scandium Dataset will be documented in this file.

## [0.1.0-rc.1] — 2026-07-22

### Added
- Per-entry `license` field (CC-BY-4.0 / CC0-1.0 / OQMD-noncommercial) for programmatic filtering
- `LICENSE_BREAKDOWN.md` documenting multi-source license terms and commercial-safe subset
- Baseline benchmark results: RF+Ridge ensemble across 4 splits × 2 tier configurations (8 experiments)
- `src/evaluation/metrics.py` module with standardized compute_metrics()
- `MODEL_LEADERBOARD.md` with full results table and tiering validation analysis
- Battery methodology doc (`docs/battery_methodology.md`) with family relevance justification
- Related work analysis (`docs/related_work.md`) positioning against LeMat-Traj, Matbench, JARVIS
- Paper outline (`docs/paper_outline.md`) for NeurIPS D&B / Scientific Data submission

### Changed
- Version: 0.0.0 → 0.1.0-rc.1
- README.md license badge: "CC BY 4.0" → "MULTIPLE" (links to LICENSE_BREAKDOWN.md)
- LICENSE file: shortened to redirect to LICENSE_BREAKDOWN.md for per-source terms
- DATASET_CARD.md: added license warning section, `license` field documentation
- CITATION.cff: version bumped, license explanation added
- pyproject.toml: version bumped to 0.1.0-rc.1
- KNOWN_ISSUES.md: removed resolved items (Docker, pyproject.toml), added license complexity note
- benchmark/evaluate.py: fixed import paths, DATASET_PATH, SPLITS_DIR resolution

### Fixed
- Missing `src/evaluation/metrics.py` module (evaluate.py was importing from non-existent path)
- License conflict: blanket "cc-by-4.0" tag on HF page while 64.4% of entries are OQMD non-commercial

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
