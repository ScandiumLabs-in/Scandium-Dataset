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
- solid-electrolyte
- lithium-ion-conductivity
- parquet
- materials-science
- battery-materials
- solid-state-electrolytes
pretty_name: Scandium-Dataset
configs:
- config_name: default
  data_files:
  - split: train
    path: dataset/entries_v3.parquet
---

# Dataset Card — Scandium-Dataset v0.3.0

## Dataset Description

- **Name:** Scandium-Dataset
- **Version:** v0.3.0
- **Description:** Curated multi-source DFT + experimental dataset for thermodynamic screening and benchmarking of battery-relevant inorganic materials, aggregated from Materials Project, OQMD, and JARVIS-DFT.
- **Total entries:** 267,230 (Gold: 96,242 | Validated: 140,382 | Raw: 30,108 | Experimental: 498)
- **Strict Gold:** 56,966 entries (subset of Gold with all gates passed)
- **Battery subset:** 82,925 entries | **Electrolyte subset:** 41,665 entries (strict Gold)
- **Storage:** Parquet (`dataset/entries_v3.parquet`, 47 columns) with indexed lookup — 184 MB instead of 1.6 GB JSON.
- **Experimental data:** 599 OBELiX entries integrated (Therrien et al. 2025, NRC-Mila), including 498 new `experimental_gold` tier entries with measured Li-ion conductivity.
- **Transport proxies:** BVSE migration barrier proxy (bvlain engine v0.25.1, softBV percolation method) computed for 98,773 Li/Na entries with ≤60 sites and crystal structures. Of these, 24,873 received a barrier (1,501 superionic ≤0.25 eV, 4,705 good 0.25–0.40 eV, 5,009 moderate 0.40–0.55 eV, 13,658 poor >0.55 eV); 73,900 were skipped because `bvlain`'s bond-valence parameter table has no entry for that composition. Validated against 7 known SSE structures pre-production (Li3PS4, Li7P3S11, Li6PS5Cl, Li7La3Zr2O12); 5/7 pass within literature ranges, 2 known-marginal outliers documented in KNOWN_ISSUES.md. See `scripts/compute_bvse_barriers.py` (sequential) and `scripts/compute_bvse_parallel.py` (parallel, 6 workers).

- **Coverage note:** Of 108,015 Li/Na entries total, 8,744 were excluded by `--max-sites 60` (unit cells with >60 atoms) and 498 experimental OBELiX entries lack crystal structures, leaving 98,773 attempted. The 73,900 skipped entries (~75% of attempted) are a structural limitation of `bvlain`'s parameter coverage, not a sampling gap — entries with unparameterized compositions are flagged explicitly via `skip_reason: "no BV params for composition"`.
- **Family imbalance:** The dataset is heavily skewed toward intermetallics (62.5%) and layered oxides (15.7%). Solid-electrolyte-relevant families (sulfides, halides, garnets, NASICON, LISICON, argyrodites) together account for <8%. See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for stratified sampling recommendations.

## Sources

| Source | Entries | License | Download Date |
|--------|---------|---------|---------------|
| Materials Project | 69,279 | CC BY 4.0 | 2026-07-20 |
| OQMD | 171,780 | Non-commercial + attribution | 2026-07-20 |
| JARVIS-DFT | 25,673 | CC0 | 2026-07-20 |

## License Warning

⚠️ **This dataset is NOT uniformly licensed.** Each entry carries its own license.
- `license: "CC-BY-4.0"` → MP entries (commercial safe)
- `license: "CC0-1.0"` → JARVIS entries (commercial safe)
- `license: "OQMD-noncommercial"` → OQMD entries (non-commercial only, 64.4%)

Filter by the `license` field for programmatic usage. See [`LICENSE_BREAKDOWN.md`](LICENSE_BREAKDOWN.md).

### Commercial-Safe Edition

A **Commercial-Safe edition** (`commercial_safe_subset_v3.json`) containing only MP + JARVIS entries (~94,952 entries) is available for commercial use. All entries are CC BY 4.0 or CC0 1.0 licensed. Any model trained for commercial deployment should be trained on this edition.

```python
import json
# Load commercial-safe edition
with open("dataset/commercial_safe_subset_v3.json") as f:
    entries = json.load(f)
print(f"{len(entries):,} entries — all commercial-safe")
```

### BVSE migration barriers (production run completed 2026-07-24)

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

**Caveat:** The 73,900 skipped entries (~75% of attempted) are entries whose composition is not covered by `bvlain`'s bond-valence parameter table. This is a structural limitation of the method, not a random gap. Entries are explicitly flagged with `skip_reason: "no BV params for composition"` in the `bvse_migration_barrier_eV` field. If you filter entries by `has_bvse_barrier: true`, you can safely use only the 24,873 that have computed values.

## Fields

### Primary fields

| Field | Type | Description | Coverage |
|-------|------|-------------|----------|
| `license` | str | Per-entry license tag | 100% |
| `source_id` | str | Original source ID | 100% |
| `formula` | str | Raw formula string | 100% |
| `structured_formula` | str | Reduced formula | 100% |
| `elements` | list[str] | Element symbols | 100% |
| `nsites` | int | Number of atoms in cell | 100% |
| `space_group` | int | International number | 99.99% |
| `space_group_symbol` | str | Hermann–Mauguin symbol | 99.99% |
| `volume` | float | Cell volume (Å³) | 100% |
| `density` | float | Density (g/cm³) | 100% |
| `formation_energy_per_atom` | float | FE (eV/atom) | 100% |
| `energy_above_hull` | float | EaH (eV/atom) | 90.4% → **100%** (JARVIS hull added) |
| `band_gap` | float | Band gap (eV) | 99.94% |
| `total_magnetization` | float | Total | 100% |
| `magnetic_ordering` | str | Magnetic ordering | 100% |
| `is_metal` | bool | Metallic character | 100% |
| `is_experimental` | bool | From experiment? | 100% |
| `families` | list[str] | Material families | 100% |
| `carrier_elements` | list[str] | Mobile ion carriers | 100% |
| `anions` | list[str] | Anion species | 100% |
| `structure_json` | str | JSON-encoded pymatgen Structure | 100% |
| `quality_score` | int | Composite quality (0–88) | 100% |
| `quality_sub_scores` | dict | Per-category scores | 100% |
| `quality_flags` | list[str] | Quality flags | 100% |
| `tier` | str | Gold / Validated / Raw | 100% |
| `tier_detail` | dict | Gate pass/fail details | 100% |
| `tier_gates` | dict | Per-gate results | 100% |
| `strict_gold` | dict | Strict Gold pass/fail | 100% |
| `duplicate_group` | int | Dedup group ID | 7.9% |
| `provenance` | dict | Full provenance chain | 100% |
| `source_weight` | float | Source priority weight | 100% |
| `references` | list[str] | Source references | 100% |

### SSE proxy fields (added in v0.1.0)

| Field | Type | Description | Coverage |
|-------|------|-------------|----------|
| `carrier_fraction` | float | Fraction of mobile ion carriers | 100% |
| `volume_per_carrier` | float | Volume per mobile carrier (Å³) | 100% |
| `fe_per_carrier` | float | Formation energy per carrier (eV) | 100% |
| `electronic_insulation` | bool | Band gap > 1.0 eV | 100% |
| `sse_family` | str | SSE family classification | 100% |
| `mobile_ion` | str | Primary mobile ion (Li/Na/Mg) | 61.1% |
| `oxidation_states` | dict | Per-element oxidation states | 100% |
| `predicted_oxidation_states_valid` | bool | BVA-validated prediction? | 100% |

### ssb_screening block (v0.2.0)

| Field | Type | Description | Coverage |
|-------|------|-------------|----------|
| `mobile_ion` | str | Mobile ion species | 61.1% |
| `mobile_ion_fraction` | float | Fraction of mobile ions | 100% |
| `sse_family` | str | SSE family tag | 100% |
| `electronic_insulation` | bool | Band gap > 1.0 eV | 100% |
| `thermo_stable` | bool | E_hull < 0.025 eV/atom | 100% |
| `gates_passed` | list[str] | SSE screening gates passed | 100% |
| `sse_candidate_score` | int | Composite SSE score (0–100) | 100% |
| `cavd_channel_dimensionality` | str | 0D/1D/2D/3D percolation | 0.0% (needs re-computation against Parquet store) |
| `stability_window_low_V` | float | Lower stability limit vs Li/Na | 0.7% |
| `stability_window_high_V` | float | Upper stability limit vs Li/Na | 0.7% |
| `window_width_V` | float | Electrochemical window width | 0.7% |
| `passivating_interphase` | bool | Forms passivating interphase? | ~14.9% |
| `interfacial_reaction_energy_vs_Li_eV_atom` | float | Decomposition energy vs Li | ~14.9% |
| `bulk_modulus_GPa` | float | Bulk modulus (geometric proxy) | 100% |
| `shear_modulus_GPa` | float | Shear modulus (geometric proxy) | 100% |
| `dendrite_suppression_flag` | bool | Shear modulus > 6 GPa | 100% |
| `elastic_source` | str | "MP_API" / "geometric_proxy" / null | 100% |

### bvse block (v0.3.0)

| Field | Type | Description | Coverage |
|-------|------|-------------|----------|
| `bvse_migration_barrier_eV` | float | Migration barrier (eV) | 23.0% of Li/Na |
| `bvse_mobility_class` | str | superionic/good/moderate/poor | 23.0% of Li/Na |
| `bvse_site_hop_counts` | dict | Per-site hop statistics | 23.0% of Li/Na |
| `bvse_percolation_type` | str | Percolation pathway type | 23.0% of Li/Na |
| `bvse_site_energy_above_percolation` | float | Site energy above percolation (eV) | 23.0% of Li/Na |
| `bvse_skip_reason` | str | Why barrier was not computed | 74.8% of attempted |
| `bvse_engine_version` | str | "bvlain v0.25.1" | 100% of attempted |

## Intended Use

- **Primary:** Training machine learning models for property prediction of solid-state battery materials
- **Secondary:** Materials discovery, phase stability analysis, and computational screening
- **Not recommended for:** Quantitative phase diagram construction (use MP/OQMD directly)

## Maintenance

- Version: v0.3.0
- DOI: pending (Zenodo archival in progress)
- Issue tracking: GitHub Issues
- Contact: Scandium Labs
