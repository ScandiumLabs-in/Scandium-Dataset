# Scandium-Dataset Paper Outline

**Target Venues** (in priority order):
1. NeurIPS Datasets & Benchmarks (if benchmark experiments are the core contribution)
2. Scientific Data (if curation methodology is the core contribution)
3. npj Computational Materials (if materials science insight is the core contribution)
4. J. Chem. Inf. Model. (domain-specific data resource)

---

## Title

**Scandium: A Curated Multi-Source Dataset with Quality Tiering for ML-Driven Solid-State Battery Discovery**

---

## Authors

Scandium Labs (individual names if available)

---

## Abstract (draft)

*We introduce Scandium-Dataset, a unified computational materials dataset of 266,732 DFT-computed entries aggregated from Materials Project, OQMD, and JARVIS-DFT. Unlike prior harmonization efforts, Scandium implements a calibrated 4-tier quality system (Strict Gold / Gold / Validated / Raw) with per-entry provenance tracking, 31,997 duplicates removed, and 137,405 repaired structures. We provide frozen benchmark splits across four held-out strategies (random, composition, family, chemistry), enabling reproducible evaluation of generalization to unseen compositions and material families. Baseline experiments with a composition-only model show that training on Gold-tier data (96,242 entries) consistently outperforms training on the full dataset, achieving FE MAE of 0.298 vs 0.392 on random splits and 1.384 vs 1.657 on chemistry held-out splits — validating the tiering strategy. Battery (82,925 entries) and electrolyte (41,665 entries) subsets are provided for domain-specific applications. The dataset is released with full documentation, audit reports, and known limitations. All code and data are publicly available.*

---

## 1. Introduction

### Problem Statement
- Solid-state battery discovery is bottlenecked by slow DFT screening
- ML acceleration requires high-quality, well-characterized training data
- Existing data is scattered (MP, OQMD, JARVIS differ in schema, quality, conventions)

### Gaps in Prior Work
- Prior harmonization (LeMat-Traj) unifies schema but doesn't tier by quality
- Existing benchmarks (Matbench) use single-source data and lack OOD splits
- Battery-specific datasets (Electrolyte Genome) are small and experimental-only

### Contributions (numbered)
1. Multi-source unification with 4-tier quality system and 11 validation gates
2. Cross-source agreement quantification and systematic bias documentation
3. Battery/electrolyte classification methodology with 10 material families
4. Frozen benchmark splits (4 types) with OOD held-out configurations
5. Baseline experiments validating the tiering system

---

## 2. Related Work

(Expand from [related_work.md](related_work.md))

- **Materials databases:** MP, OQMD, JARVIS, AFLOW, NOMAD
- **Harmonized datasets:** LeMat-Traj (closest prior art — explicit comparison table)
- **Benchmarks:** Matbench, JARVIS-Leaderboard
- **Battery-specific:** Electrolyte Genome, BatteryHub
- **Novelty positioning:** Tiering methodology + battery curation + OOD splits

---

## 3. Curation Methodology

### 3.1 Source Selection
- Why MP, OQMD, JARVIS? Coverage, complementarity, license variation
- Extraction dates, API versions pinned for reproducibility

### 3.2 Schema Unification
- Field mapping across sources
- Unit normalization
- Structure standardization (pymatgen JSON)

### 3.3 Deduplication
- 31,997 duplicates removed across 21,140 groups
- Structure matching method (pymatgen StructureMatcher)
- Priority rules for choosing which entry to keep

### 3.4 Repair Pipeline
- OQMD coordinate artifacts (137,405 entries): `coords_are_cartesian=False`
- OQMD space group determination (171,764 entries): spglib symmetry pass
- Volume/density repair (73,480 entries): extraction from structure_json
- JARVIS volume extraction (25,673 entries)

### 3.5 Quality Scoring
- 5 sub-scores (geometry, DFT, metadata, novelty, chemical)
- Composite score range: 48–88 (intentionally conservative)
- Calibration: score 80-90 predicts 85.2% validation rate, 0.18 eV FE MAE

### 3.6 Tiering System
- 4 tiers with cumulative gates:
  - Strict Gold (56,966): 11 gates, quality ≥ 80, full provenance, no defects
  - Gold (96,242): 8 gates, validated + unique + stable + complete metadata
  - Validated (140,382): 5 gates, valid structure + targets + no critical issues
  - Raw (30,108): source + formula present
- Gate definitions and pass/fail criteria for each tier

### 3.7 Provenance Tracking
- Per-entry checksum, repair history, tier gate results, dedup resolution
- Enables auditability and reproducibility

### 3.8 Material Family Classification
- 10 families based on element composition
- Family distribution and battery relevance assessment
- Known issue: garnet undercount (23 entries)

---

## 4. Dataset Analysis

### 4.1 Overall Statistics
(Table: entries per source, per tier, per family)

### 4.2 Property Distributions
(Figures: FE, EaH, BG histograms by source and tier)

### 4.3 Cross-Source Agreement
- 11,741 formulas overlapping between MP and JARVIS
- FE MAE across overlaps: 0.20 eV/atom
- Source-level biases documented (MP mean quality 87.4 vs OQMD 73.2)

### 4.4 Quality Score Calibration
- Monotonic relationship between score and downstream prediction error
- Figure: score bin → validation rate, FE MAE, EaH MAE

### 4.5 Tier Impact Analysis
- Outlier removal effectiveness (Gold excludes 42 extreme-FE OQMD entries)
- Defect distribution by tier
- Missing data analysis (EaH for JARVIS: 100% missing by source limitation)

### 4.6 Battery and Electrolyte Subset Statistics
(Per-family breakdown, tier distribution within subsets)

---

## 5. Benchmark Baselines

### 5.1 Experimental Setup
- 4 split types (random, composition-held-out, family-held-out, chemistry-held-out)
- 2 training configurations (full dataset vs Gold-tier only)
- 8 experiments total

### 5.2 Model
- Composition-only: bag-of-elements + RF + Ridge ensemble
- Rationale: fast, reproducible, structure-agnostic lower bound

### 5.3 Results

**Key table (8 rows):**

| Training Data | Split | FE MAE | EaH MAE | BG MAE |
|---------------|-------|--------|---------|--------|
| Full | random | 0.392 | 0.224 | 0.494 |
| Gold | random | **0.298** | **0.024** | 0.762 |
| Full | composition | 0.390 | 0.223 | 0.497 |
| Gold | composition | **0.306** | **0.024** | 0.772 |
| Full | family | 0.739 | 0.169 | 1.105 |
| Gold | family | **0.458** | **0.019** | 0.943 |
| Full | chemistry | 1.657 | 0.355 | 1.966 |
| Gold | chemistry | **1.384** | **0.027** | 2.129 |

### 5.4 Analysis
- **Gold-tier training consistently beats full-dataset** on FE and EaH despite 3× less data
- **EaH dramatically benefits** from Gold filtering (excludes JARVIS with no EaH, filters OQMD outliers)
- **Chemistry held-out is hardest** — negative R² for both configurations
- **Band gap trade-off** — Gold has fewer metals (BG=0), making BG prediction harder
- **Per-family analysis** reveals model weaknesses (intermetallic bias, garnet data scarcity)

### 5.5 Discussion
- The tiering system is empirically validated: cleaner data beats more data
- OOD splits reveal limits of composition-only models
- Roadmap for structure-aware models (CGCNN, MEGNet, ALIGNN)

---

## 6. Limitations

(Lift directly from [KNOWN_ISSUES.md](../KNOWN_ISSUES.md))

- JARVIS EaH missing (25,673 entries) — fundamental source limitation
- MP vs OQMD quality score gap (87.4 vs 73.2 mean)
- Family imbalance (~63% intermetallics)
- Garnet family undercount (23 entries)
- No experimental validation — purely computational
- License complexity — 3 different licenses across sources
- Conservative quality scoring (max score: 88)
- No Docker container (since resolved in v0.1.0-rc.1)
- No DOI assigned yet (Zenodo archival in progress)

---

## 7. Conclusion

- Summary of contributions
- Empirical validation of tiering system via benchmark experiments
- Roadmap: JARVIS EaH computation, NOMAD/AFLOW integration, experimental data, ionic conductivity computation
- Call for community adoption

---

## Figures Needed

1. **Property distributions** — FE, EaH, BG histograms colored by source (3 panels)
2. **Quality score calibration** — score bin → validation rate (line plot with confidence bands)
3. **Cross-source agreement** — MP vs JARVIS FE scatter plot (11,741 overlapping formulas)
4. **Tier impact** — FE MAE bar chart across tiers (4 bars)
5. **Benchmark results** — FE MAE across 4 splits, full vs Gold (grouped bar chart)
6. **Family distribution** — bar chart of 10 families with battery relevance labels
7. **Battery subset composition** — pie chart or treemap

---

## Tables Needed

1. Source comparison (MP, OQMD, JARVIS — size, properties, license)
2. Tier system (4 tiers, counts, gate criteria)
3. Family classification (10 families, criteria, battery relevance)
4. Benchmark results (8 rows as above)
5. Comparison with prior work (Scandium vs LeMat-Traj, Matbench, JARVIS)
6. Dataset statistics per source (mean FE, EaH, BG, quality score)
7. Cross-source overlap statistics (11,741 formulas, FE MAE by source pair)

---

## Submission Checklist

- [ ] DOI obtained from Zenodo
- [ ] License conflict resolved (LICENSE_BREAKDOWN.md added)
- [ ] per-entry `license` field added to dataset
- [ ] Baseline benchmark results computed (8 experiments)
- [ ] Related work analyzed against LeMat-Traj, Matbench, JARVIS
- [ ] Battery/electrolyte methodology documented
- [ ] Version bumped to v0.1.0
- [ ] Evaluation runner fixed (metrics module created)
- [ ] Code and data archived for reproducibility
- [ ] All known issues documented
