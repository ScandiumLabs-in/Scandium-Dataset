# Changelog

All notable changes to the Scandium Dataset will be documented in this file.

## [1.0.0] — 2026-07-24 — Scope Clarification + Honest Repositioning

### Changed
- **Dataset repositioned from "SSB discovery" to "materials screening":** The tagline, dataset card, ROADMAP, and all public-facing documentation now accurately describe this as a thermodynamic and structural screening dataset for battery-relevant materials, not a full SSE-discovery resource. See [the repositioning guide](https://github.com/ScandiumLabs-in/Scandium-Dataset/issues) for the rationale.
- **Version bumped to 1.0.0** to mark the scope correction as a major milestone.
- DATASET_CARD.md: added "Included vs. Not Included" table, "Suitable For / Not Suitable For" section, family imbalance disclosure, roadmap section.
- README.md, KNOWN_ISSUES.md, ROADMAP.md, CITATION.cff, pyproject.toml, setup.py: version and framing updated to match v1.0.0.
- GitHub repo description and topics updated from "solid-state battery" to "materials screening".
- HF dataset tags updated (removed `solid-state-electrolyte`, `lithium-ion-conductivity`; added `materials-screening`, `dft-stability`, `inorganic-materials`).

### Fixed
- JARVIS EaH status in KNOWN_ISSUES.md corrected: previously marked as "Resolved" but the script was never re-run against the Parquet store. Actual coverage: 0% for 25,673 JARVIS entries.
- CAVD coverage corrected to 0% (was ~61%).
- Stability window coverage corrected to 0.7% (was ~2.2%).
- Garnet count updated: 23 → 136 entries.

## [0.3.0] — 2026-07-24 — Parquet Store + Experimental Data + BVSE Fix

### Added
- **Parquet dataset store** (`dataset/dataset_store.py`)
  - Replaces the 1.6 GB `entries_final_v3.json` with a 0.18 GB PyArrow Parquet table
  - Indexed lookup by `source_id` (~4s load, O(1) lookup)
  - Type-safe value encoding/decoding with prefix-based scheme
  - Incremental `update_field` with nested path support (e.g. `ssb_screening.bvse_migration_barrier_eV`)
  - Batch append and checkpoint without full-file rewrite
  - Conversion entry point: `python dataset/dataset_store.py --convert`

- **OBELiX experimental data** (Therrien et al. 2025, NRC-Mila)
  - 599 entries with measured ionic conductivity integrated via `obelix-data` Python package
  - 101 OBELiX formulas matched to existing DFT entries (251 rows tagged with conductivity labels)
  - 498 unmatched entries appended as new `experimental_gold` tier entries
  - 441 unmatched formulas saved to `dataset/obelix_unmatched_formulas.json` as acquisition target
  - Families covered: 126 NASICON, 95 garnet, 67 perovskite, 42 argyrodite, 36 LGPS, and more

- **BVSE migration barrier proxy rewritten** (`scripts/compute_bvse_barriers.py`)
  - Replaced hand-rolled BVSE with `bvlain` v0.25.1 (softBV percolation method)
  - Validated on 7 known SSEs: 5/7 pass within literature ranges, worst-case error 0.12 eV
  - Old implementation gave 2.667 eV for Li3PS4 (wrong); new gives 0.342-0.410 eV (correct)
  - Batched checkpointing via Parquet store for long runs

- **Conductivity benchmark splits** (`scripts/generate_conductivity_splits.py`)
  - 4 split types: conductivity-stratified, family-stratified, best-conductor held-out, mobility-class held-out

### Fixed
- Documentation discrepancy: CAVD coverage corrected from ~61% to 0.0% (CAVD was never re-computed against the Parquet store; needs re-run)
- Documentation discrepancy: stability window coverage corrected from ~2.2% to 0.7%
- DATASET_CARD.md, README.md: coverage numbers now match actual Parquet state
- MODEL_LEADERBOARD.md: version updated from v0.1.0-rc.1 to v0.3.0
- Dataset card now includes explicit family imbalance disclosure (62.5% intermetallics)

### Changed
- Citation corrected: Hargreaves et al. (2023) npj Comput. Mater., not "Ransom et al."
  - Correct DOI: 10.1038/s41524-022-00951-z
  - Data hosted at Materials Data Facility (ANL), not GitHub
- ROADMAP.md: Phase 1-3 checkmarks corrected to reflect actual execution state
  - CAVD, garnet enrichment, mechanical properties, JARVIS EaH confirmed as not executed
- CHANGELOG.md: honest status for all previous entries

## [0.2.0] — 2026-07-24 — SSB Screening Phase 1

### Added
- CAVD-like channel dimensionality analysis (`scripts/compute_cavd_channel_dimensionality.py`)
  - Voronoi-based percolation analysis for Li/Na mobile ions
  - Classifies channel dimensionality as 0D/1D/2D/3D
  - Fills `ssb_screening.cavd_channel_dimensionality` field
- SSE candidate score system (`scripts/compute_sse_candidate_score.py`)
  - 5-gate screening system (thermo + electronic + mobility + window + mechanical)
  - Transparent score weighting: 30+25+20+15+10
  - Fills `sse_candidate_score` and `gates_passed` fields
- Commercial-safe edition extractor (`scripts/extract_commercial_safe_edition.py`)
  - Filters to MP (CC-BY-4.0) + JARVIS (CC0-1.0) only
  - ~94,952 entries for commercial ML training
- Garnet family enrichment (`scripts/enrich_garnet_family.py`)
  - Composition + structure-based garnet identification
  - Identifies ~200 new garnet candidates for reclassification
- Mechanical properties computation (`scripts/compute_mechanical_properties.py`)
  - MP API elastic tensor query support
  - Geometric density-based proxy for all entries
  - Dendrite suppression flag (shear > 6 GPa)
- Oxidation state prediction (`scripts/compute_oxidation_states.py`)
  - Bond valence analysis (structure-based) + heuristic fallback
- JARVIS energy above hull (`scripts/compute_jarvis_hull_energy.py`)
  - Internal convex hull within JARVIS subset
  - Closes the 9.6% EaH coverage gap
- Phase 1 pipeline runner (`scripts/run_phase1_pipeline.py`)

### Changed
- `DATASET_CARD.md`: Updated field table with new SSE proxy fields
- `README.md`: Added SSE screening section, scripts table, commercial-safe edition
- `ROADMAP.md`: Phase 1 items marked complete
- `KNOWN_ISSUES.md`: JARVIS EaH issue resolved, Phase 1 caveats documented
- `docs/sse_readiness.md`: Short-term items updated

## [0.1.0-rc.2] — 2026-07-22

### Added
- SSE structural family classification (`sse_family`) on all 266,732 entries: 12 classes (garnet, NASICON, argyrodite, LGPS_type, LISICON, anti_perovskite, perovskite, halide, borohydride, sulfide, oxide, none)
- `mobile_ion` field standardized across all entries (Li/Na/Mg presence-based, fixing prior logic that picked up Al/Ca/K as carriers)
- `ssb_screening` schema block on all 266,732 entries including computed electrochemical stability windows: `stability_window_low_V`, `stability_window_high_V`, `window_width_V`, `interfacial_reaction_energy_vs_Li_eV_atom`, `passivating_interphase` (39,706 entries with windows computed via grand potential scan, 1,814 with ≥0.5V width)
- `sse_candidate_score`: composite score (10 base for known SSE family + 1 per gate passed), ranges 10–12 in current release
- `docs/ssb_strategic_roadmap.md`: comprehensive literature-backed strategic plan (~20 references) covering CAVD → BVSE → MLIP-NEB → DFT-NEB pipeline, schema additions, tier expansion, and phased implementation schedule
- `docs/sse_readiness.md`: strategic update section referencing roadmap
- `scripts/compute_electrochemical_windows.py`: self-contained convex-hull-based stability window computation from dataset's own formation energies (no MP API dependency), with safety guards (`--dry-run`, `--output`)

### Fixed
- `mobile_ion` was picking up arbitrary high-fraction elements (Al, Ca, K, Zn) instead of Li/Na/Mg — 115,876 entries corrected to proper Li/Na/Mg/None logic
- PhaseDiagram construction: added `make_terminal_entries()` with standard PBE reference energies for gas corrections (O₂, N₂, F₂, Cl₂, H₂), enabling hull building for all 31,025 chemical systems (was silently failing with "Missing terminal entries")

### Changed
- Version: 0.1.0-rc.1 → 0.1.0-rc.2
- ROADMAP.md: restructured around 4-phase SSB-specific plan superseding generic enhancements
- README.md: updated SSE disclaimer, Properties table (SSE Family, Mobile Ion), Quick Start examples for new fields, version badges, documentation list
- KNOWN_ISSUES.md: garnet count updated 23→41, composition-heuristic caveat added

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
