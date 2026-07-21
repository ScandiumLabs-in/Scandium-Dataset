# Repair Pipeline

The Scandium Dataset documents every repair applied to the data. No silent
corrections — each repair is logged with before/after values.

## OQMD Coordinate Artifact

**Problem**: OQMD entries were ingested with `coords_are_cartesian=True` when
coordinates were actually fractional. This caused the characteristic √3/4 ≈ 0.433Å
minimum distance and ~43,000 false "overlapping atoms" flags.

**Detection**: Minimum interatomic distance ≈ 0.433Å (the √3/4 signature).

**Fix**: Reload from original jarvis-tools source with `coords_are_cartesian=False`.

**Scope**: 137,405 entries repaired. 0 errors, 0 skipped.

**Verification**: 500/500 sampled entries verified against original jarvis-tools.
100% property accuracy (FE, EaH, BG) confirmed. Repaired min_dist > 0.5Å in all cases.

**Confidence**: Type A (fully automated, fully verified, 0 failures).

## OQMD Symmetry Pass

**Problem**: OQMD entries had no space group (100% missing because symmetry was
never computed during ingest). This blocked all OQMD entries from Gold tier.

**Fix**: Compute space groups using spglib with symprec 1e-2 → 5e-3 → 1e-3 → 1e-1.

**Scope**: 171,764/171,780 found (16 failures).

**Speed**: 460 entries/second (parallel, 11 workers).

## OQMD Volume Repair

**Problem**: 47,807 OQMD entries had volume = 0 (no volume extracted during
original ingest when the coordinate artifact prevented valid structure parsing).

**Fix**: Extract volume from structure_json's lattice matrix.

**Scope**: 47,807 entries repaired.

## OQMD Density Repair

**Problem**: 47,807 OQMD entries had density = 0 (same root cause as volume).

**Fix**: Compute density from elemental masses and lattice volume.

**Scope**: 47,807 entries repaired.

## JARVIS Volume Extraction

**Problem**: 25,673 JARVIS entries had volume = 0 at top level (volume existed
only inside structure_json).

**Fix**: Extract volume from structure_json's lattice volume.

**Scope**: All 25,673 JARVIS entries repaired.

## Repair Logs

Complete repair logs with per-entry details:
- `reports/repair_reports/coordinate_repair_*.json`
- `reports/repair_reports/oqmd_symmetry_pass.json`
