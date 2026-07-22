# Related Work

This document positions the Scandium Dataset against existing materials datasets
and benchmarks. Prepared for the dataset paper.

---

## 1. Existing Materials Databases

### Materials Project (MP)
- **Size:** ~154,000 inorganic compounds
- **Properties:** Formation energy, band gap, elastic constants, piezoelectric, dielectric, magnetic
- **Method:** DFT (PAW-PBE/PBE+U/HSE06)
- **License:** CC BY 4.0
- **Limitation:** Single-source, no cross-validation. Some properties (e.g., ion mobility) not available.
- **Relationship to this work:** MP is one of three constituent sources (69,279 entries).

### OQMD (Open Quantum Materials Database)
- **Size:** ~1,000,000 structures
- **Properties:** Formation energy, stability
- **Method:** DFT (PAW-PBE)
- **License:** Non-commercial + attribution
- **Limitation:** Less curated than MP. Known issues with coordinate artifacts and missing symmetry metadata.
- **Relationship to this work:** OQMD is the largest constituent source (171,780 entries). The Scandium Dataset repairs known OQMD defects (coordinate artifacts, space group determination, volume extraction).

### JARVIS-DFT
- **Size:** ~76,000 structures (DFT 3D subset: 25,673)
- **Properties:** Formation energy, band gap (TBmBJ), elastic, optical, magnetic, phonons, 2D
- **Method:** DFT (optPBE + TBmBJ)
- **License:** CC0 (Public Domain)
- **Limitation:** No convex hull distance (energy above hull). Uses different functionals than MP/OQMD.
- **Relationship to this work:** JARVIS contributes 25,673 entries. Its TBmBJ band gaps provide complementary information. The EaH gap is documented as a known limitation.

### AFLOW
- **Size:** ~3,500,000 entries
- **Properties:** Formation energy, band gap, elastic
- **Method:** DFT (PAW-PBE)
- **License:** Varies
- **Relationship to this work:** Not included as a source (planned for v4.0). AFLOW is larger but less curated per-entry.

### NOMAD
- **Size:** 12,000,000+ calculations
- **Properties:** Raw DFT outputs
- **Method:** Various (community-contributed)
- **License:** CC BY 4.0
- **Relationship to this work:** Not included (planned for v4.0). NOMAD's heterogeneity makes quality scoring more difficult.

---

## 2. Aggregated/Harmonized Datasets

### LeMat-Traj (arXiv 2025)
- **Source:** MP + Alexandria + OQMD
- **Key innovation:** Harmonized schema across multiple DFT functionals; reusable fetching/curation library; trajectory data for MD simulations
- **Differences from this work:**
  - LeMat-Traj includes trajectory/relaxation data; Scandium focuses on static properties
  - LeMat-Traj does not implement a quality tiering system with calibrated gates
  - Scandium adds battery-specific family classification and frozen benchmark splits
  - Scandium provides cross-source agreement quantification (FE MAE 0.20 eV/atom across 11,741 overlapping formulas)
  - Scandium adds provenance tracking and explicit defect documentation per entry
- **Relationship:** LeMat-Traj is the closest prior art. The tiering methodology and battery-specific curation are the primary differentiators. The paper must explicitly acknowledge LeMat-Traj and narrow the novelty claim to these differentiators.

### Matbench
- **Format:** Benchmark suite with 13 tasks across formation energy, band gap, elastic constants, phonons, perovskites
- **Key innovation:** Standardized train/val/test splits and evaluation protocol
- **Differences from this work:**
  - Matbench tasks are smaller (1.3K–132K entries)
  - Matbench uses frozen single-source splits (primarily MP)
  - Scandium provides multi-source splits with multiple held-out strategies
  - Scandium includes battery-specific task definitions and tier-based evaluation
  - Matbench has broad property coverage; Scandium focuses on battery-relevant properties
- **Relationship:** Matbench is the standard benchmark for crystal property prediction. The Scandium benchmark adds multi-source and OOD dimensions not covered by Matbench.

### JARVIS-Leaderboard
- **Format:** Benchmark across DFT, force fields, ML, and 2D materials
- **Key innovation:** Multi-property benchmark with leaderboard
- **Differences from this work:**
  - JARVIS-Leaderboard includes force fields and molecular dynamics; Scandium is property-prediction focused
  - Scandium provides per-entry quality scoring, tiering, and provenance
  - Scandium's battery-specific subset and cross-source validation are unique

---

## 3. Battery-Specific Datasets

### Electrolyte Genome (Materials Project)
- **Focus:** Liquid and solid electrolyte properties
- **Properties:** Ionic conductivity, electrochemical stability, diffusion barriers
- **Relationship:** The Electrolyte Genome focuses on computed transport properties; Scandium provides foundational structural and thermodynamic data that can be used to train models for such properties.

### BatteryHub
- **Focus:** Battery materials property database
- **Properties:** Formation energy, band gap, ionic conductivity, experimental data
- **Relationship:** BatteryHub includes experimental data not present in Scandium. Future versions plan to integrate experimental validation.

---

## Summary Table

| Dataset | Size | Sources | Quality Scoring | Benchmark Splits | Battery Focus | License |
|---------|------|---------|----------------|-----------------|---------------|---------|
| **Scandium (this work)** | **266,732** | **MP+OQMD+JARVIS** | **✓ (4 tiers, 11 gates)** | **✓ (4 types, OOD)** | **✓** | **Multi** |
| Materials Project | ~154K | Single | ✗ | Partial (Matbench) | Partial | CC BY 4.0 |
| OQMD | ~1M | Single | ✗ | ✗ | Partial | Non-commercial |
| JARVIS-DFT | ~76K | Single | Partial | Leaderboard | ✗ | CC0 |
| LeMat-Traj | ~500K | MP+Alexandria+OQMD | ✗ | ✗ | ✗ | Multi |
| Matbench | 1.3K–132K | MP (+others) | ✗ | ✓ (frozen) | ✗ | CC BY 4.0 |
| AFLOW | ~3.5M | Single | ✗ | ✗ | ✗ | Varies |
| Electrolyte Genome | ~50K | MP | ✗ | ✗ | ✓ | CC BY 4.0 |

## Novelty Claim (for paper)

The Scandium Dataset's contributions are:

1. **Multi-source unification with quality tiering** — not just schema harmonization (done by LeMat-Traj), but a calibrated 4-tier quality system with provenance tracking per entry
2. **Cross-source validation** — quantifying agreement across sources (FE MAE 0.20 eV/atom) and documenting systematic biases (MP vs OQMD quality score gap: 87.4 vs 73.2)
3. **Battery-specific curation** — family classification, battery (82,925) and electrolyte (41,665) subsets with relevance methodology
4. **Frozen OOD benchmark splits** — including chemistry held-out (halides) and family held-out splits that test generalization beyond training distribution
5. **Repair documentation** — 137,405 coordinate repairs, 47,807 volume repairs, with full provenance chain per entry
