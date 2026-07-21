# Scandium-Dataset Roadmap

> **Vision:** The world's most trusted open dataset and benchmarking platform for AI-driven solid-state battery discovery.

---

## v0.0.0 — Foundation Release (Current)

**Focus:** Clean, validated, audited foundation dataset

- [x] Aggregate MP, OQMD, JARVIS-DFT (266,732 entries)
- [x] Coordinate repair (171,780 OQMD entries)
- [x] Symmetry pass (171,764 space groups)
- [x] Volume/density repair (73,480 entries)
- [x] 11-gate validation pipeline
- [x] Multi-source deduplication
- [x] Quality scoring with 5 sub-scores
- [x] Three-tier system (Gold / Validated / Raw)
- [x] Battery and electrolyte subsets
- [x] Benchmark splits (4 types)
- [x] Complete 8-phase audit
- [x] Reproducibility scripts
- [x] Full documentation (12 audit reports, trust report, dataset card, known issues)
- [x] Docker support
- [x] Test infrastructure

---

## v3.1.0 — Scientific Enhancement (Next)

**Focus:** Expand battery coverage, add computed properties

- [ ] Compute energy_above_hull for JARVIS entries via internal convex hull
- [ ] Add oxidation state prediction for all entries
- [ ] Expand garnet family classification (currently undercounted)
- [ ] Add ionic conductivity proxy features
- [ ] Cross-reference with experimental ICSD entries
- [ ] Add formation energy corrections for OQMD entries
- [ ] Family-balanced subsampling for model training

---

## v3.2.0 — Benchmark Platform

**Focus:** Standardized model evaluation

- [ ] Leaderboard with baseline model results
- [ ] Pre-computed train/val/test splits for battery tasks
- [ ] Task-specific subsets (formation energy, band gap, classification)
- [ ] Evaluation protocol with statistical significance testing
- [ ] Model cards for published baselines
- [ ] Community submission workflow

---

## v4.0.0 — Expanded Coverage

**Focus:** Add new sources and material types

- [ ] Integrate NOMAD dataset
- [ ] Integrate AFLOW data
- [ ] Add computational phonon properties
- [ ] Add elastic tensor data
- [ ] Add experimental conductivity database
- [ ] Time-series tracking of source updates

---

## Long-term

- [ ] Automated monthly source updates
- [ ] Active learning for targeted property prediction
- [ ] Web API for dataset querying
- [ ] Integration with materials discovery workflows
- [ ] Community governance model
- [ ] Dataset DOI with versioned releases
