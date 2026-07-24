# Known Issues — Scandium-Dataset v1.0.0

> **Transparency note:** Every known limitation of this dataset is documented below. We believe honest documentation is the foundation of trust. No issue has been hidden.

---

## Critical Issues (Affect Specific Tiers)

### 1. Dataset Does Not Include Ionic Transport Properties (By Design, v1.0.0 Scope)

- **Status:** By design, v1.0.0 scope — flagged prominently for all users
- **Scope:** Entire dataset (100%)
- **Impact:** The dataset supports thermodynamic and structural screening only. It cannot be used to rank materials by ionic conductivity or SSE performance without augmentation (see ROADMAP.md for planned transport-property layers).
- **Mitigation:** Use for upstream screening (stability, band gap, structural family), then pair with AIMD/NEB or experimental conductivity data for downstream SSE evaluation. The BVSE migration barrier proxy covers 23% of Li/Na entries at draft quality — use with caution, and consult the 74.8% skip rate documentation before filtering.

### 2. JARVIS Energy Above Hull (EaH) — ✅ Resolved

- **Status:** ✅ Computed via internal convex hull (v1.0.0-rc2)
- **Scope:** 25,673 JARVIS entries (100%)
- **Coverage:** 96.5% of all entries now have EaH; 14,669 JARVIS entries got new EaH values via internal hull
- **Unresolved:** 8,933 JARVIS entries lack EaH because their chemical system has <3 entries (too few for a convex hull). This is a fundamental sparsity limitation that cannot be resolved without cross-method normalization.
- **Note:** This uses JARVIS-relative hull, not the MP/OQMD reference. Cross-method normalization remains future work.

### 3. Extreme Formation Energy Outliers (FE > 5 eV/atom)

- **Status:** By design, tier-isolated
- **Scope:** 42 OQMD entries (max = 45.17 eV/atom)
- **Impact:** Zero entries in Gold tier
- **Root cause:** OQMD multi-element compounds with unphysical stoichiometries (e.g., Be₄H₁₆K₈O₃₈S₈, Ba₆Mg₁₂Pt₆). These are likely computational artifacts from high-throughput enumeration.
- **Resolution:** Removed from Gold tier by gate G10 (quality score ≥ 80). Documented for raw/validated tiers.

### 4. Extreme Energy Above Hull Outliers (EaH > 5 eV/atom)

- **Status:** By design, tier-isolated
- **Scope:** 87 entries (44 OQMD + 43 MP, max = 47.03 eV/atom)
- **Impact:** Zero entries in Gold tier
- **Root cause:** Highly metastable phases computed far from convex hull. These are legitimate DFT results for unphysical structures.
- **Resolution:** Removed from Gold tier by gate G10.

---

## High-Impact Issues

### 5. BVSE Coverage Gap (~75% of Li/Na Entries Skipped)

- **Status:** Documented, structural limitation
- **Scope:** 73,900 of 98,773 attempted Li/Na entries (74.8%)
- **Impact:** Only 1 in 4 Li/Na entries with crystal structures receives a BVSE migration barrier estimate
- **Root cause:** `bvlain`'s bond-valence parameter table only covers a limited set of element/cation combinations. Entries with unparameterized compositions (e.g., uncommon transition metals, complex anion chemistries) cannot produce a barrier — this is a fundamental limitation of the empirical bond-valence method, not a sampling gap.
- **Manifestation:** Entries have `bvse_skip_reason: "no BV params for composition"` in their `ssb_screening` block.
- **Mitigation:** Filter with `has_bvse_barrier: true` to work exclusively with the 24,873 entries that have computed barriers. The 1,501 superionic + 4,705 good entries within this subset are valid candidates for further screening.
- **Additional exclusions:** 8,744 entries excluded by `--max-sites 60` (unit cells >60 atoms) and 498 experimental OBELiX entries lacking crystal structures. Combined, these reduce the effective BVSE coverage to 23.0% of all 108,015 Li/Na entries.

### 5. BVSE Sanity Validation — 2 Known Marginal Outliers

- **Status:** Documented, pre-production
- **Scope:** 5/7 known SSE structures pass within literature ranges; 2 fail marginally
- **Details:**
  - `Li7P3S11` (mp-641703) → 0.420 eV (lit. 0.18–0.30) — bvlain systematically overestimates barriers for this structure
  - `Li6PS5Cl` (JVASP-38005) → 0.176 eV (lit. 0.24–0.38) — JVASP-38005 is a microporous variant with artificially low barrier
- **Impact:** These are known, characterized limitations of the bvlain parameter set for specific structure types. All 5/7 non-outlier structures reproduce within ±0.05 eV of literature.

### 6. Single-Atom Entries (38 entries)

- **Scope:** 38 entries with nsites = 1
- **Impact:** Minimal (0.01% of dataset)
- **Detail:** Primarily OQMD single-atom calculations. Included but flagged.
- **Recommendation:** Filter using `nsites > 1` if single atoms are inappropriate for your task.

### 7. MP vs OQMD Quality Score Bias

- **Scope:** All entries
- **Impact:** MP entries have mean score 87.4, OQMD have 73.2
- **Root cause:** MP uses finer computational parameters (ENCUT, KSPACING, semi-core pseudopotentials). This is a genuine quality difference, not a systematic bias.
- **Mitigation:** Score calibration is monotonic and consistent per-source. Use tier-based filtering to isolate quality levels.

### 9. Missing Structured Formula (Resolved)

- **Status:** ✅ Fixed in v0.0.0
- **Scope:** Was 266,732 entries
- **Resolution:** All entries now have `structured_formula` via formula reduction.

### 10. Stale Quality Flags (Resolved)

- **Status:** ✅ Fixed in v0.0.0
- **Scope:** Was 171,764 OQMD entries
- **Resolution:** `missing_spacegroup` flag removed from all OQMD entries that now have space_group.

---

## Medium-Impact Issues

### 11. Conservative Quality Scoring

- **Scope:** Maximum score = 88 (no entry ≥ 90)
- **Impact:** The scoring system is intentionally conservative. Any missing sub-score information caps the total.
- **Recommendation:** Use scores for relative ranking, not absolute quality assessment.

### 12. Family Imbalance

- **Scope:** Entire dataset
- **Detail:** ~63% intermetallics, ~16% layered oxides, ~7% halide SSEs, ~6% sulfide SSEs
- **Impact:** Models trained on full dataset may be biased toward intermetallics.
- **Mitigation:** Use stratified sampling by family, or use battery/electrolyte subsets. Garnet enrichment script (`scripts/enrich_garnet_family.py`) available for structure-based reclassification.

### 13. Missing Band Gap (151 OQMD entries)

- **Scope:** 0.1% of OQMD entries
- **Root cause:** OQMD band gap calculation did not converge for these entries.
- **Impact:** Minimal; entries remain usable with `band_gap: null`.

### 14. Space Group Determination Failures (16 OQMD entries)

- **Scope:** 0.01% of OQMD entries
- **Root cause:** Structures with too few atoms or disordered configurations where spglib cannot determine symmetry.
- **Impact:** Minimal; entries remain usable with `space_group: null`.

### 15. Cross-Source Formula Duplicates (195 formulas)

- **Scope:** 195 formulas appear in all three sources
- **Impact:** Deduplication preserved best entry per group; all resolutions logged.

---

## Future-Priority Issues

- **Raw source downloads not included** — due to source redistribution policies, raw download scripts must be run by the user
- **Garnet undercount** — 136 entries (improved from 23 via broader composition heuristic + 95 OBELiX experimental garnets, but still far below the ~1,000+ needed for ML training on LLZO and variants). Only 19 garnets are in Gold tier. The enrichment script (`scripts/enrich_garnet_family.py`) identifies ~200 new candidates from structure-based verification, but these need manual validation before reclassification. True garnet-family expansion requires targeted acquisition from ICSD and MP for LLZO-type structures.
- **SSE family tags are composition-based** — `sse_family` is classified by elemental heuristic, not crystal structure. A compound with Li+S+P but no percolating channels will still be tagged as argyrodite/LGPS. Cross-check with CAVD dimensionality when available.
- **Experimental data coverage is thin** — OBELiX integrated (498 experimental_gold entries with measured conductivity), but this is a pilot-level integration. Full experimental coverage requires ICSD, Inorganic Crystal Structure Database, and additional curated experimental conductivity data.
- **No DOI assigned yet** — Zenodo archival in progress for v1.0.0
- **License complexity** — the dataset has 3 different licenses; the `license` field per entry was added in v0.1.0 to enable programmatic filtering. A **Commercial-Safe edition** (MP+JARVIS only, ~95k entries) is now extractable via `scripts/extract_commercial_safe_edition.py`.
- **CAVD channel dimensionality is 0% coverage** — the algorithm exists in `scripts/compute_cavd_channel_dimensionality.py` but was never re-run against the Parquet store. When computed, the field uses Voronoi-based connectivity analysis (a geometric proxy), not full NEB migration barriers. 0D/1D classifications reliably rule out good conductors, but 2D/3D classifications overestimate true percolation. Use as pre-filter only.
- **Mechanical properties are geometric proxies** — the `bulk_modulus_GPa` and `shear_modulus_GPa` fields use density-based estimation, not DFT elastic tensors. They provide order-of-magnitude estimates only. True DFT elastic data for MP entries can be queried via `scripts/compute_mechanical_properties.py --api-key YOUR_KEY`.
- **SSE candidate scores are uncalibrated** — the 5-gate `sse_candidate_score` is a heuristic composite (30+25+20+15+10 pts). Gates 1-2 are fully populated; gates 3-5 are populated only when underlying data exists. Scores from entries with missing gates are underestimates.

---

## Reporting New Issues

If you discover an issue not listed here, please [open a GitHub Issue](.github/ISSUE_TEMPLATE/bug_report.md) with:
- Affected entry (source_id or formula)
- Description of the issue
- Expected vs observed value
- Any relevant context (pipeline version, date)
