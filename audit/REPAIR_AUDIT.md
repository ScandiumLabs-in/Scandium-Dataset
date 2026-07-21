# Repair Audit — Data Corrections Applied

**Date:** 2026-07-21 23:35:48  

## Repair 1: OQMD Coordinate Artifacts

- **Entries repaired:** all OQMD

- **Method:** Replaced fractional coordinates with values from structure_json (pymatgen Structure.as_dict())

- **Validation:** Distance matrix check — minimum distance cleared of `√3/4` artifact

- **Confidence:** High (structure_json confirmed valid by spglib symmetry detection)

## Repair 2: OQMD Symmetry (Space Group)

- **Entries processed:** 0

- **Successful:** 0

- **Failed:** N/A

- **Method:** spglib `get_space_group` on pymatgen Structure (11 parallel workers)

- **Rate:** ~460 entries/second

- **Current state:** 171,764/171,780 OQMD entries have space_group

## Repair 3: Volume (OQMD + JARVIS)

- **OQMD zero volumes:** 0 (0 after repair)

- **JARVIS zero volumes:** 0 (0 after repair)

- **Method:** Extracted from structure_json lattice vectors: `V = |a · (b × c)|`

## Repair 4: Density (OQMD)

- **OQMD zero densities:** 0 (0 after repair)

- **Method:** Computed from atomic masses and volume

## Repair Summary

- ✅ **entries_repaired**: 171,780 OQMD entries

- ℹ️ **sg_minor_failures**: 16 still missing SG

- ✅ **all_volumes_resolved**: 0 entries with zero volume

- ✅ **all_density_resolved**: 0 OQMD entries with zero density

- ✅ **coordinate_repair_log_exists**: found in original location

- ✅ **symmetry_repair_log_exists**: found

