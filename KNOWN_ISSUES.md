# Known Issues — Scandium-Dataset v0.0.0

> **Transparency note:** Every known limitation of this dataset is documented below. We believe honest documentation is the foundation of trust. No issue has been hidden.

---

## Critical Issues (Affect Specific Tiers)

### 1. JARVIS Energy Above Hull (EaH) Missing

- **Status:** ✅ Resolved in v0.2.0 via internal convex hull
- **Scope:** 25,673 JARVIS entries (100%)
- **Impact:** No impact on Gold tier (gate G7 excludes entries missing EaH)
- **Root cause:** JARVIS-DFT does not compute convex hull distance. This is a fundamental source limitation.
- **Resolution:** Internal convex hull built within JARVIS subset using pymatgen PhaseDiagram. Script: `scripts/compute_jarvis_hull_energy.py`. Note: this uses JARVIS-relative hull, not the MP/OQMD reference. Cross-method normalization remains future work.

### 2. Extreme Formation Energy Outliers (FE > 5 eV/atom)

- **Status:** By design, tier-isolated
- **Scope:** 42 OQMD entries (max = 45.17 eV/atom)
- **Impact:** Zero entries in Gold tier
- **Root cause:** OQMD multi-element compounds with unphysical stoichiometries (e.g., Be₄H₁₆K₈O₃₈S₈, Ba₆Mg₁₂Pt₆). These are likely computational artifacts from high-throughput enumeration.
- **Resolution:** Removed from Gold tier by gate G10 (quality score ≥ 80). Documented for raw/validated tiers.

### 3. Extreme Energy Above Hull Outliers (EaH > 5 eV/atom)

- **Status:** By design, tier-isolated
- **Scope:** 87 entries (44 OQMD + 43 MP, max = 47.03 eV/atom)
- **Impact:** Zero entries in Gold tier
- **Root cause:** Highly metastable phases computed far from convex hull. These are legitimate DFT results for unphysical structures.
- **Resolution:** Removed from Gold tier by gate G10.

---

## High-Impact Issues

### 4. Single-Atom Entries (38 entries)

- **Scope:** 38 entries with nsites = 1
- **Impact:** Minimal (0.01% of dataset)
- **Detail:** Primarily OQMD single-atom calculations. Included but flagged.
- **Recommendation:** Filter using `nsites > 1` if single atoms are inappropriate for your task.

### 5. MP vs OQMD Quality Score Bias

- **Scope:** All entries
- **Impact:** MP entries have mean score 87.4, OQMD have 73.2
- **Root cause:** MP uses finer computational parameters (ENCUT, KSPACING, semi-core pseudopotentials). This is a genuine quality difference, not a systematic bias.
- **Mitigation:** Score calibration is monotonic and consistent per-source. Use tier-based filtering to isolate quality levels.

### 6. Missing Structured Formula (Resolved)

- **Status:** ✅ Fixed in v0.0.0
- **Scope:** Was 266,732 entries
- **Resolution:** All entries now have `structured_formula` via formula reduction.

### 7. Stale Quality Flags (Resolved)

- **Status:** ✅ Fixed in v0.0.0
- **Scope:** Was 171,764 OQMD entries
- **Resolution:** `missing_spacegroup` flag removed from all OQMD entries that now have space_group.

---

## Medium-Impact Issues

### 8. Conservative Quality Scoring

- **Scope:** Maximum score = 88 (no entry ≥ 90)
- **Impact:** The scoring system is intentionally conservative. Any missing sub-score information caps the total.
- **Recommendation:** Use scores for relative ranking, not absolute quality assessment.

### 9. Family Imbalance

- **Scope:** Entire dataset
- **Detail:** ~63% intermetallics, ~16% layered oxides, ~7% halide SSEs, ~6% sulfide SSEs
- **Impact:** Models trained on full dataset may be biased toward intermetallics.
- **Mitigation:** Use stratified sampling by family, or use battery/electrolyte subsets. Garnet enrichment script (`scripts/enrich_garnet_family.py`) available for structure-based reclassification.

### 10. Missing Band Gap (151 OQMD entries)

- **Scope:** 0.1% of OQMD entries
- **Root cause:** OQMD band gap calculation did not converge for these entries.
- **Impact:** Minimal; entries remain usable with `band_gap: null`.

### 11. Space Group Determination Failures (16 OQMD entries)

- **Scope:** 0.01% of OQMD entries
- **Root cause:** Structures with too few atoms or disordered configurations where spglib cannot determine symmetry.
- **Impact:** Minimal; entries remain usable with `space_group: null`.

### 12. Cross-Source Formula Duplicates (195 formulas)

- **Scope:** 195 formulas appear in all three sources
- **Impact:** Deduplication preserved best entry per group; all resolutions logged.

---

## Future-Priority Issues

- **Raw source downloads not included** — due to source redistribution policies, raw download scripts must be run by the user
- **Garnet undercount** — 41 entries (improved from 23 via broader composition heuristic, but still far below the ~1,000+ needed for ML training on LLZO and variants). The enrichment script (`scripts/enrich_garnet_family.py`) identifies ~200 new candidates from structure-based verification, but these need manual validation before reclassification. True garnet-family expansion requires targeted acquisition from ICSD and MP for LLZO-type structures.
- **SSE family tags are composition-based** — `sse_family` is classified by elemental heuristic, not crystal structure. A compound with Li+S+P but no percolating channels will still be tagged as argyrodite/LGPS. Cross-check with CAVD dimensionality when available.
- **Experimental data not yet integrated** — current sources are purely computational. The 820-entry OBELiX database (npj Comput. Mater. 2023) is the highest-priority integration target.
- **No DOI assigned yet** — Zenodo archival in progress for v0.1.0
- **License complexity** — the dataset has 3 different licenses; the `license` field per entry was added in v0.1.0 to enable programmatic filtering. A **Commercial-Safe edition** (MP+JARVIS only, ~95k entries) is now extractable via `scripts/extract_commercial_safe_edition.py`.
- **CAVD channel dimensionality is a geometric proxy** — the `cavd_channel_dimensionality` field uses Voronoi-based connectivity analysis, not full NEB migration barriers. 0D/1D classifications reliably rule out good conductors, but 2D/3D classifications overestimate true percolation. Use as pre-filter only.
- **Mechanical properties are geometric proxies** — the `bulk_modulus_GPa` and `shear_modulus_GPa` fields use density-based estimation, not DFT elastic tensors. They provide order-of-magnitude estimates only. True DFT elastic data for MP entries can be queried via `scripts/compute_mechanical_properties.py --api-key YOUR_KEY`.
- **SSE candidate scores are uncalibrated** — the 5-gate `sse_candidate_score` is a heuristic composite (30+25+20+15+10 pts). Gates 1-2 are fully populated; gates 3-5 are populated only when underlying data exists. Scores from entries with missing gates are underestimates.

---

## Reporting New Issues

If you discover an issue not listed here, please [open a GitHub Issue](.github/ISSUE_TEMPLATE/bug_report.md) with:
- Affected entry (source_id or formula)
- Description of the issue
- Expected vs observed value
- Any relevant context (pipeline version, date)
