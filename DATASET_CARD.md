---
license: cc-by-4.0
language:
- en
size_categories:
- 100K<n<1M
task_categories:
- other
tags:
- dft
- materials-project
- oqmd
- jarvis
- materials-screening
- dft-stability
- parquet
- materials-science
- battery-materials
- inorganic-materials
pretty_name: Scandium-Dataset
configs:
- config_name: default
  data_files:
  - split: train
    path: dataset/entries_v3.parquet
---

# Dataset Card — Scandium-Dataset v1.0.0

## Summary

Scandium-Dataset provides a harmonized, quality-scored foundation of DFT-computed structural and thermodynamic properties across 267,230 materials from Materials Project, OQMD, and JARVIS-DFT. It supports the **early screening stage** of battery materials discovery — filtering by phase stability, electronic structure, and structural family — before downstream property prediction (ionic conductivity, mechanical stability, electrochemical window) via AIMD, NEB, or targeted DFT.

*Previous versions positioned this as a solid-state battery discovery dataset. v1.0.0 corrects that framing: the data covers thermodynamic screening, not ionic transport. See [CHANGELOG](CHANGELOG.md) for details.*

- **Version:** v1.0.0
- **Total entries:** 267,230 (Gold: 96,242 | Validated: 140,382 | Raw: 30,108 | Experimental: 498)
- **Strict Gold:** 56,966 entries (subset of Gold with all gates passed)
- **Battery-relevant subset:** 82,925 entries | **Electrolyte candidate subset:** 41,665 entries (strict Gold)

  > *File names on disk (`battery_subset_v3.json`, `electrolyte_subset_v3.json`) predate the v1.0.0 scope clarification. They will be renamed to `battery_candidate_subset_v1.json` / `solid_electrolyte_candidate_subset_v1.json` in a future release alongside a full reference update. Until then, treat the current filenames as legacy identifiers — "subset" in the name never implied conductivity was validated.*
- **Storage:** Parquet (`dataset/entries_v3.parquet`, 47 columns) with indexed lookup — 184 MB instead of 1.6 GB JSON.
- **Experimental data:** 498 OBELiX entries integrated (Therrien et al. 2025) as `experimental_gold` tier with measured Li-ion conductivity.
- **Transport proxy draft:** 24,873 BVSE migration barriers computed (bvlain engine) at 23% Li/Na coverage — see "Roadmap" below for the gap this addresses.

## Included vs. Not Included

| Included | Not Included (requires augmentation) |
|---|---|
| Formation energy (eV/atom) — 100% | Ionic conductivity (S/cm) |
| Energy above hull (eV/atom) — 90.4% | Migration/activation energy (NEB) |
| Band gap (eV) — 99.9% | Electrochemical stability window |
| Space group, volume, density — 99.9%+ | Elastic/shear moduli (full DFT) |
| Crystal structure (pymatgen `Structure` JSON) — 100% | Experimental validation beyond pilot OBELiX integration |
| Quality tier (Gold/Validated/Raw) — 100% | |
| Provenance tracking (source, source_id, checksum) — 99.8% | |
| SSE family classification (composition-based) — 100% | |
| BVSE migration barrier proxy — 23% of Li/Na entries | |

## Suitable For / Not Suitable For

**Suitable for:** phase stability screening, structural family classification, band gap prediction, materials-informatics benchmarking, pretraining general property predictors on inorganic crystal structures, cross-source DFT property harmonization studies.

**Not suitable for (without augmentation):** direct ionic conductivity prediction, SSE performance ranking, electrochemical stability assessment. The dataset contains migration barrier proxies for 23% of Li/Na entries, but at ~75% skip rate due to bond-valence parameter coverage, these do not constitute a complete transport-property layer.

## What the Data Actually Supports

### Property coverage (verified against Parquet store)

| Property | Coverage | Notes |
|----------|----------|-------|
| Formation energy | 267,230 (100%) | From MP, OQMD, JARVIS-DFT |
| Energy above hull | 241,557 (90.4%) | **0% for JARVIS (25,673 entries)**; JARVIS EaH script has not been run against the Parquet store |
| Band gap | 267,079 (99.9%) | 151 OQMD entries with non-converged band gap |
| Space group | 267,214 (100%) | spglib symmetry analysis |
| Volume | 267,230 (100%) | From structure |
| Density | 267,230 (100%) | From elements + volume |
| Structure JSON | 267,230 (100%) | pymatgen Structure serialization |
| Quality score | 267,230 (100%) | Composite score (0–88) |
| Provenance | 267,230 (100%) | Source, source_id, checksum |
| Duplicate group | 21,140 (7.9%) | Entries in dedup groups (31,997 total removed upstream) |

### SSE screening fields (stored in `ssb_screening` block)

| Field | Coverage | Notes |
|-------|----------|-------|
| SSE family | 267,230 (100%) | Composition-based heuristic (not structure-based) |
| Mobile ion | 267,230 (100%) | Li/Na/Mg presence-based |
| CAVD channel dimensionality | **0%** | Algorithm was not re-run against Parquet store |
| SSE candidate score | 100% | 5-gate system (thermo + electronic + mobility + window + mechanical) |
| Thermo stability flag | 99.8% | E_hull < 0.025 eV/atom |
| Bulk/shear modulus | 100% | Geometric density-based proxy (not DFT elastic tensors) |
| Stability window | 1,814 (0.7%) | Grand-potential phase diagrams — computed for subset with low EaH |
| Interfacial reaction energy | 39,706 (14.9%) | Decomposition energy vs Li |
| BVSE migration barrier | 24,873 (23% of Li/Na) | bvlain v0.25.1, softBV percolation. **74.8% skip rate** on attempted entries (98,773) due to bond-valence parameter coverage gaps |

## Sources

| Source | Entries | License | Download Date |
|--------|---------|---------|---------------|
| Materials Project | 69,279 | CC BY 4.0 | 2026-07-20 |
| OQMD | 171,780 | Non-commercial + attribution | 2026-07-20 |
| JARVIS-DFT | 25,673 | CC0 | 2026-07-20 |
| OBELiX (experimental) | 498 | Per-article terms | 2026-07-24 |

## License Warning

⚠️ **This dataset is NOT uniformly licensed.** Each entry carries its own license.
- `license: "CC-BY-4.0"` → MP entries (commercial safe, 26.1%)
- `license: "CC0-1.0"` → JARVIS entries (commercial safe, 9.6%)
- `license: "OQMD-noncommercial"` → OQMD entries (non-commercial only, 64.3%)

See [`LICENSE_BREAKDOWN.md`](LICENSE_BREAKDOWN.md). A **Commercial-Safe edition** (MP+JARVIS, ~94,952 entries) is extractable via `scripts/extract_commercial_safe_edition.py`.

## Tier System

| Tier | Count | Criteria |
|------|-------|----------|
| **Strict Gold** ⭐ | **56,966** | 11 gates: base Gold + quality ≥ 80 + no defects + provenance |
| **Gold** | 96,242 | 8 gates: validated + unique + stable + complete metadata |
| **Validated** | 140,382 | 5 gates: valid structure + targets + no critical issues |
| **Raw** | 30,108 | Source + formula present (may have quality issues) |
| **Experimental Gold** | 498 | OBELiX entries with measured conductivity |

## Family Imbalance

The dataset skews heavily toward intermetallics (62.5%) and layered oxides (15.7%). Solid-electrolyte-relevant composition families are a small fraction:

| Family | Total | Gold | Validated | Raw |
|--------|-------|------|-----------|-----|
| Intermetallic | 166,930 | 36,520 | 109,056 | 21,354 |
| Layered oxide | 42,015 | 26,295 | 12,756 | 2,964 |
| Halide SSE | 18,803 | 12,560 | 5,211 | 1,032 |
| Sulfide SSE | 16,359 | 9,458 | 5,591 | 1,310 |
| NASICON | 560 | 488 | 70 | 2 |
| Garnet | 23 + 113 experimental | 19 | 4 | 0 |

If your target chemistry is garnets or sulfides specifically, usable Gold-tier entries number in the tens to low thousands — consider targeted acquisition (ICSD, structured literature extraction) before expecting ML models to generalize within these families.

## BVSE Migration Barriers (Draft Quality)

| Metric | Value |
|--------|-------|
| Total Li/Na entries | 108,015 |
| Excluded (>60 sites) | 8,744 |
| No structure (experimental) | 498 |
| **Attempted** | **98,773** |
| Barriers computed | 24,873 |
| Superionic (≤0.25 eV) | 1,501 |
| Good (0.25–0.40 eV) | 4,705 |
| Moderate (0.40–0.55 eV) | 5,009 |
| Poor (>0.55 eV) | 13,658 |
| Skipped (no BV params) | 73,900 |
| Errors | 0 |
| **Coverage of attempted** | **25.2%** |
| **Coverage of all Li/Na** | **23.0%** |

**Caveat:** 73,900 skipped entries (~75% of attempted) reflect bond-valence parameter coverage, not a sampling gap. Entries are flagged with `bvse_skip_reason`. Engine: bvlain v0.25.1, validated against 7 known SSEs (5/7 pass within literature, 2 known-marginal outliers documented in KNOWN_ISSUES.md).

## Roadmap to True SSE-Property Coverage

v1.0.0 provides thermodynamic and structural screening data. Planned extensions:

1. **CAVD re-computation** against the Parquet store (currently 0% coverage; algorithm exists in `scripts/compute_cavd_channel_dimensionality.py`)
2. **JARVIS EaH** re-computation against the Parquet store (currently 0% for 25,673 JARVIS entries; script exists in `scripts/compute_jarvis_hull_energy.py`)
3. **BVSE barrier expansion** — re-run with lower `--max-sites` threshold and extended parameter table to reduce the 75% skip rate
4. **MLIP-NEB migration barriers** for top-tier stable candidates (active development)
5. **DFT NEB validation** for a curated set of halide/sulfide/garnet candidates
6. **Elastic tensor data** from MP API for mechanical property validation (scaffold exists in `scripts/compute_mechanical_properties.py`)
7. **Experimental conductivity cross-references** beyond OBELiX pilot

## Benchmark

Frozen train/val/test splits at [`dataset/splits/`](dataset/splits/). Four split types with RF+Ridge baselines in [`MODEL_LEADERBOARD.md`](MODEL_LEADERBOARD.md):

| Split | Train | Val | Test | Purpose |
|-------|-------|-----|------|---------|
| Random 80/10/10 | 200,122 | 26,670 | 39,940 | Basic generalization |
| Composition held-out | 213,383 | 27,011 | 26,338 | No formula overlap |
| Family held-out | 260,984 | 5,165 | 583 | Cross-family |
| Chemistry held-out | 227,384 | 26,673 | 12,675 | OOD (halides) |

GNN baselines (CGCNN, MEGNet, ALIGNN) are in progress.

## Intended Use

- **Primary:** Upstream materials screening — filtering by phase stability, electronic structure, and structural family
- **Secondary:** Cross-source DFT property harmonization, materials-informatics benchmarking, pretraining structure-based property predictors
- **Not recommended for:** Quantitative phase diagram construction (use MP/OQMD directly), SSE conductivity ranking (requires transport-property labels not in this dataset)

## Maintenance

- Version: v1.0.0
- DOI: pending (Zenodo archival in progress)
- Issue tracking: GitHub Issues
- Contact: Scandium Labs
