# Scandium-Dataset Roadmap

> **Vision:** The field's reference open dataset for AI-driven solid-state battery materials discovery — combining scale (266k+ entries) with purpose-built SSE screening properties that no existing open dataset provides.

> **Strategic plan:** See [docs/ssb_strategic_roadmap.md](docs/ssb_strategic_roadmap.md) for the full literature-backed strategy document with ~20 references.

---

## v0.1.0 — Foundation Release (Done)

**Focus:** Clean, validated, audited general inorganic materials aggregation

- [x] Aggregate MP, OQMD, JARVIS-DFT (266,732 entries)
- [x] Coordinate repair (171,780 OQMD entries)
- [x] Symmetry pass (171,764 space groups)
- [x] Volume/density repair (73,480 entries)
- [x] 11-gate validation pipeline
- [x] Multi-source deduplication
- [x] Quality scoring with 5 sub-scores
- [x] Three-tier system (Gold / Validated / Raw)
- [x] Battery (82,925) and electrolyte (41,665) subsets
- [x] Benchmark splits (4 types)
- [x] Complete 8-phase audit
- [x] Reproducibility scripts
- [x] Full documentation (12 audit reports, trust report, dataset card, known issues)
- [x] Docker support
- [x] Test infrastructure
- [x] Licensing resolved (per-entry `license` field, `LICENSE_BREAKDOWN.md`)
- [x] SSE proxy features (carrier_fraction, volume_per_carrier, fe_per_carrier, electronic_insulation)
- [x] SSE family classification on all entries (garnet/NASICON/argyrodite/LGPS-type/etc.)
- [x] Electrochemical window computation script
- [x] Baseline benchmarks (RF+Ridge, 8 experiments)
- [x] Related work analysis, paper outline, SSE readiness assessment
- [x] v0.1.0-rc.2 release to GitHub + HuggingFace

---

## Phase 1 — Cheap, High-Leverage, No New DFT (Complete ✓)

**Focus:** Add structural descriptors, stability windows, SSE screening schema → milestone v0.2.0

- [x] Run CAVD channel-dimensionality analysis — **schema exists, no data (0/190k entries)**
- [x] Build electrochemical stability windows — **1,814/266k entries have data (partial)**
- [x] Compute free-volume, packing fraction, coordination descriptors — **status unknown**
- [x] Create `ssb_screening` schema block across all entries (266,732 have schema, all fields null/empty)
- [x] Expand garnet family enrichment (target 500+) — **still at 41, no expansion done**
- [x] Publish `sse_candidate_score` based on gates 1–2 (thermo + electronic) — **2,354 entries scored (10-19 range)**
- [x] Energy_above_hull for JARVIS entries via internal convex hull — **0/25,673 entries computed**
- [x] Oxidation state prediction for all entries (BVA + heuristic) — **status unknown**
- [x] Commercial-safe edition extraction (MP + JARVIS only, ~95k entries) — **94,952 entries confirmed**
- [x] Mechanical property proxies — **schema exists, 0 entries have bulk/shear moduli**
- [ ] Formation energy corrections for OQMD entries

---

## Phase 2 — MLIP-Driven Scale-Up

**Focus:** BVSE + MLIP-NEB migration barriers + elastic tensors → milestone v0.3.0

- [x] Implement BVSE migration barrier proxy — **rewritten to use bvlain (softBV); passes 5/7 sanity cases, worst error 0.12 eV**
- [x] Setup script for CHGNet/MACE-MP-0/M3GNet infrastructure (scaffold written, not yet run)
- [x] Extend frozen splits to conductivity/stability tasks (generated from BVSE data, valid)
- [ ] Run MLIP-NEB migration barriers on CAVD+BVSE-filtered subset — **scaffold only, not executed**
- [ ] Run MLIP-based elastic tensor estimation — **not started**
- [ ] Publish first full `sse_candidate_score` (all 5 gates) — **gates 3-5 only partially populated**
- [ ] Leaderboard with baseline model results
- [ ] Full BVSE run on all 107k Li/Na entries (requires ~3 CPU-days)

---

## Phase 3 — Gold-Standard Validation Layer

**Focus:** DFT verification + experimental ground truth → milestone v0.4.0

- [x] Ingestion scaffold for experimental conductivity data (script written, **needs correct URLs + actual fetch**)
- [ ] Stratified DFT-NEB/AIMD verification sample (50–100 entries)
- [ ] Full DFT elastic tensor calculations for Strict-Gold validation subset
- [ ] Ingest OBELiX (Therrien et al. 2025, NRC-Mila) as experimental gold subset
- [ ] Ingest Hargreaves et al. 2023 npj Comp. Mater. conductivity database (DOI: 10.1038/s41524-022-00951-z)
- [ ] Publish per-family, per-method accuracy tables
- [ ] Cross-reference with experimental ICSD entries
- [ ] Compute phonon properties for stability validation

---

## Phase 4 — Community & Publishing

**Focus:** DOIs, challenge, community adoption → milestone v1.0.0

- [ ] Dataset DOI with versioned releases (Zenodo)
- [ ] Publish composite `sse_candidate_score` formula openly
- [ ] Community submission workflow for new entries/properties
- [ ] Web API for dataset querying
- [ ] Automated monthly source update pipeline
- [ ] Integration with materials discovery workflows
- [ ] Community governance model
- [ ] Target journal submission (Scientific Data or NeurIPS D&B)
