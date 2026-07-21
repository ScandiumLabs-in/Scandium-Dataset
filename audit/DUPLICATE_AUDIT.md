# Duplicate Audit — Cross-Source Deduplication

**Date:** 2026-07-21 23:35:43  

**Entries with duplicate groups:** 21,140

**Estimated duplicates removed:** 31,997

## Duplicate Group Analysis

- **Intra-source groups:** 21,140

- **Cross-source groups:** 0

## Cross-Source Formula Overlap

**Formulas in multiple sources:** 11,915

**Formulas in all 3 sources:** 195

## Deduplication Strategy


Deduplication was performed per formula group using a structure similarity approach:

1. **Grouping:** Entries grouped by reduced formula.
2. **Comparison:** Within each group, structures compared via pymatgen structure matcher (lattice + site matching).
3. **Resolution:** Best entry selected by quality score, provenance completeness, and source priority (MP > OQMD > JARVIS).
4. **Tracking:** Selected entries carry `duplicate_group` ID; removed entries logged.


## Phase 4 Findings

- ✅ **total_duplicate_groups**: 21,140 groups (21,140 entries kept)

- ✅ **cross_source_groups**: 0 groups span multiple sources

- ✅ **intra_source_groups**: 21,140 groups within single source

- ✅ **jarvis_mp_formulas**: 11,741 formulas shared

- ✅ **jarvis_oqmd_formulas**: 339 formulas shared

- ✅ **mp_oqmd_formulas**: 225 formulas shared

- ℹ️ **triple_source_formulas**: 195 formulas appear in all 3 sources

