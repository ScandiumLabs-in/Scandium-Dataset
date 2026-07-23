# Dataset Card — Scandium-Dataset v0.3.0

## Dataset Description

- **Name:** Scandium-Dataset
- **Version:** v0.3.0
- **Description:** Curated multi-source DFT + experimental dataset for thermodynamic screening and benchmarking of battery-relevant inorganic materials, aggregated from Materials Project, OQMD, and JARVIS-DFT.
- **Total entries:** 267,230 (Gold: 96,242 | Validated: 140,382 | Raw: 30,108 | Experimental: 498)
- **Battery subset:** 82,925 entries | **Electrolyte subset:** 41,665 entries (strict Gold)
- **Storage:** Parquet (`dataset/entries_v3.parquet`) with indexed lookup — 0.18 GB instead of 1.6 GB JSON.
- **Experimental data:** 599 OBELiX entries integrated (Therrien et al. 2025, NRC-Mila), including 498 new `experimental_gold` tier entries with measured Li-ion conductivity.
- **Transport proxies:** BVSE migration barrier proxy (bvlain engine, validated against 7 known SSEs, 5/7 pass within literature ranges). See `scripts/compute_bvse_barriers.py`.

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
| `cavd_channel_dimensionality` | str | 0D/1D/2D/3D percolation | ~61% |
| `stability_window_low_V` | float | Lower stability limit vs Li/Na | ~2.2% |
| `stability_window_high_V` | float | Upper stability limit vs Li/Na | ~2.2% |
| `window_width_V` | float | Electrochemical window width | ~2.2% |
| `passivating_interphase` | bool | Forms passivating interphase? | ~14.9% |
| `interfacial_reaction_energy_vs_Li_eV_atom` | float | Decomposition energy vs Li | ~14.9% |
| `bulk_modulus_GPa` | float | Bulk modulus (geometric proxy) | 100% |
| `shear_modulus_GPa` | float | Shear modulus (geometric proxy) | 100% |
| `dendrite_suppression_flag` | bool | Shear modulus > 6 GPa | 100% |
| `elastic_source` | str | "MP_API" / "geometric_proxy" / null | 100% |

## Intended Use

- **Primary:** Training machine learning models for property prediction of solid-state battery materials
- **Secondary:** Materials discovery, phase stability analysis, and computational screening
- **Not recommended for:** Quantitative phase diagram construction (use MP/OQMD directly)

## Maintenance

- Version: v0.1.0-rc.1
- DOI: pending (Zenodo archival in progress)
- Issue tracking: GitHub Issues
- Contact: Scandium Labs
