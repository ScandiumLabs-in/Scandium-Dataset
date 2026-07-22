# Source Snapshots

This file records the exact extraction dates and versions for each data source,
ensuring reproducibility of the Scandium Dataset.

## Materials Project

| Field | Value |
|-------|-------|
| **API version** | MPRester v3.1 |
| **Extraction date** | 2026-07-20 |
| **API endpoint** | `https://api.materialsproject.org/` |
| **Filter** | `chemsys` includes Li, Na, Mg, Ca, Zn, Al, K |
| **Fields** | `material_id`, `formula_pretty`, `structure`, `formation_energy_per_atom`, `energy_above_hull`, `band_gap`, `total_magnetization`, `volume`, `density`, `symmetry`, `is_stable` |
| **Entries** | 69,279 |
| **License** | CC BY 4.0 |
| **Reference** | Jain et al., APL Materials, 2013 |

## OQMD

| Field | Value |
|-------|-------|
| **API** | jarvis-tools `data("oqmd_3d_no_cfid")` |
| **Extraction date** | 2026-07-20 |
| **Dataset version** | OQMD v1.4 (no_cfid variant) |
| **Entries** | 171,780 |
| **License** | Non-commercial + attribution |
| **Reference** | Saal et al., JOM, 2013; Kirklin et al., npj Comp. Mater., 2015 |
| **Known issues at extraction** | Coordinate artifacts (137,405 entries), missing space groups (171,764 entries), zero volumes (47,807 entries) — all repaired in pipeline |

## JARVIS-DFT

| Field | Value |
|-------|-------|
| **API** | jarvis-tools `data("dft_3d")` |
| **Extraction date** | 2026-07-20 |
| **Dataset version** | JARVIS-DFT 2024 (dft_3d subset) |
| **Entries** | 25,673 |
| **License** | CC0 (Public Domain) |
| **Reference** | Choudhary et al., npj Comp. Mater., 2020 |
| **Known issues at extraction** | No energy_above_hull (by design — JARVIS does not compute convex hull distance) |

## Reproducibility Notes

To reproduce the dataset from scratch:

1. **MP entries**: Run `scripts/audit_phase1_raw_data.py` with your MP API key
2. **OQMD entries**: Run the same script — it fetches via jarvis-tools
3. **JARVIS entries**: Also fetched via jarvis-tools in the same script
4. **Repair pipeline**: Run `scripts/audit_phase2_structure.py` through `scripts/audit_phase6_quality.py` in sequence
5. **Final assembly**: Run `scripts/fix_dataset_v3.py`

Due to source redistribution policies, the raw downloaded files are not included
in the repository. The download scripts must be run by the user with appropriate
API credentials.
