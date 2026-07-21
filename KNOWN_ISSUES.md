# Known Issues — Scandium-Dataset v0.0.0

> **Transparency note:** Every known limitation of this dataset is documented below. We believe honest documentation is the foundation of trust. No issue has been hidden.

---

## Critical Issues (Affect Specific Tiers)

### 1. JARVIS Energy Above Hull (EaH) Missing

- **Status:** By design, acknowledged
- **Scope:** 25,673 JARVIS entries (100%)
- **Impact:** No impact on Gold tier (gate G7 excludes entries missing EaH)
- **Root cause:** JARVIS-DFT does not compute convex hull distance. This is a fundamental source limitation.
- **Resolution:** Documented. Future versions may compute EaH using an internal convex hull.

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
- **Mitigation:** Use stratified sampling by family, or use battery/electrolyte subsets.

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

- **No Docker container** — environment setup requires pip install
- **No pyproject.toml** — package structure uses requirements.txt
- **Raw source downloads not included** — due to source redistribution policies, raw download scripts must be run by the user
- **Garnet family undercount** — only 23 garnet entries (many more exist but classified as other families)
- **Experimental data not yet integrated** — current sources are purely computational

---

## Reporting New Issues

If you discover an issue not listed here, please [open a GitHub Issue](.github/ISSUE_TEMPLATE/bug_report.md) with:
- Affected entry (source_id or formula)
- Description of the issue
- Expected vs observed value
- Any relevant context (pipeline version, date)
