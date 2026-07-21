# Dataset Card — Scandium-Dataset v0.0.0

## Dataset Description

- **Name:** Scandium-Dataset
- **Version:** v0.0.0
- **Description:** Curated computational materials dataset for solid-state battery discovery, aggregated from Materials Project, OQMD, and JARVIS-DFT.
- **Total entries:** 266,732 (Gold: 96,242 | Validated: 140,382 | Raw: 30,108)
- **Battery subset:** 82,925 entries | **Electrolyte subset:** 41,665 entries (strict Gold)

## Sources

| Source | Entries | License | Download Date |
|--------|---------|---------|---------------|
| Materials Project | 69,279 | CC BY 4.0 | 2026-07-20 |
| OQMD | 171,780 | Non-commercial + attribution | 2026-07-20 |
| JARVIS-DFT | 25,673 | CC0 | 2026-07-20 |

## Fields

| Field | Type | Description | Coverage |
|-------|------|-------------|----------|
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
| `energy_above_hull` | float | EaH (eV/atom) | 90.4% |
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

## Intended Use

- **Primary:** Training machine learning models for property prediction of solid-state battery materials
- **Secondary:** Materials discovery, phase stability analysis, and computational screening
- **Not recommended for:** Quantitative phase diagram construction (use MP/OQMD directly)

## Maintenance

- Version: v0.0.0
- Release candidate — see RELEASES.md for stability guarantees
- Issue tracking: GitHub Issues
- Contact: Scandium Labs
