# Scandium-Dataset Roadmap

> **Vision:** Become the field's reference open dataset for battery-relevant materials **screening** — combining scale (267k+ entries) with harmonized quality scoring, cross-source provenance, and benchmark splits that no single-source dataset provides. Transport-property layers (ionic conductivity, migration barriers) are planned for future versions.

> **Strategic plan:** See [docs/ssb_strategic_roadmap.md](docs/ssb_strategic_roadmap.md).

---

## v0.1.0 — Foundation Release (Done)

**Focus:** Clean, validated, audited general inorganic materials aggregation

- [x] Aggregate MP, OQMD, JARVIS-DFT (267,230 entries)
- [x] Coordinate repair (171,780 OQMD entries)
- [x] Symmetry pass (171,764 space groups)
- [x] Volume/density repair (73,480 entries)
- [x] 11-gate validation pipeline
- [x] Multi-source deduplication (31,997 duplicates removed)
- [x] Quality scoring with 5 sub-scores
- [x] Three-tier system (Gold / Validated / Raw)
- [x] Battery-relevant (82,925) and electrolyte candidate (41,665) subsets
- [x] Benchmark splits (4 types: random, composition-held-out, family-held-out, chemistry-held-out)
- [x] Complete 8-phase audit
- [x] Full documentation (audit reports, trust report, dataset card, known issues)
- [x] Licensing resolved (per-entry `license` field)

---

## v1.0.0 — Scope Clarification + Parquet Store (Current)

**Focus:** Corrected scope (thermodynamic screening, not SSE discovery), Parquet storage, experimental integration, BVSE draft

- [x] Parquet dataset store (47 columns, 184 MB, indexed lookup)
- [x] OBELiX experimental data integration (498 entries with measured conductivity)
- [x] BVSE migration barrier proxy (24,873 barriers, 1,501 superionic)
- [x] KNOWN_ISSUES.md: scope clarified as thermodynamic screening
- [x] Dataset card: Included/Not Included and Suitable/Not Suitable sections added
- [x] Version bumped to v1.0.0, framing corrected from "SSB discovery" to "materials screening"

---

## Phase 1 — Property Gaps to Close (Next)

**Focus:** Close documentation-vs-data gaps, expand SSE screening fields

- [ ] Run CAVD channel-dimensionality analysis against Parquet store (currently 0% coverage; algorithm exists)
- [ ] Compute JARVIS EaH against Parquet store (currently 0% for 25,673 entries; script exists)
- [ ] Re-run garnet enrichment (target 500+) — currently 136 entries
- [ ] Reduce BVSE skip rate by adjusting --max-sites threshold and parameter table
- [ ] Expand electrochemical stability windows beyond 0.7% coverage

---

## Phase 2 — MLIP-Driven Transport Properties

**Focus:** Migration barriers + elastic tensors

- [ ] MLIP-NEB migration barriers on top SSE candidates
- [ ] DFT NEB validation for halide/sulfide/garnet subset
- [ ] Elastic tensor data from MP API (scaffold exists)
- [ ] Full `sse_candidate_score` with all 5 gates populated
- [ ] GNN baselines (CGCNN, MEGNet, ALIGNN) added to MODEL_LEADERBOARD

---

## Phase 3 — Production Transport Layer

- [ ] Benchmark-quality ionic conductivity predictions
- [ ] Experimental conductivity cross-references (beyond OBELiX pilot)
- [ ] DOI registration via Zenodo
- [ ] Third-party audit of data pipeline
