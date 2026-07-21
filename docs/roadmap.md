# Roadmap

## Current Status (v0.0.0)

- ✅ Dataset frozen (266,732 entries, 3 sources)
- ✅ All known defects repaired (coordinates, volume, density, space groups)
- ✅ Provenance tracking per entry
- ✅ Strict Gold tier (11 gates)
- ✅ Quality score calibration (monotonic proof)
- ✅ Cross-source agreement quantified
- ✅ Dataset census complete
- ✅ Per-source and per-family reports
- ✅ Benchmark splits frozen
- ✅ Evaluation runner with baselines
- ✅ Documentation suite

## Short Term (v0.0.0 final)

| Task | Priority | Status |
|------|----------|--------|
| OQMD scoring review (G10 gap) | High | Planned |
| Garnet data enrichment | High | Planned |
| OQMD coordinate re-repair for non-artifact entries | Medium | Planned |
| GitHub release with DOI | High | Planned |
| Benchmark baselines (ScandiumNet, CHGNet, MEGNet) | High | Planned |

## Medium Term (v4.0)

| Feature | Description |
|---------|-------------|
| Battery-specific properties | Ionic conductivity, migration barriers |
| Experimental validation subset | Compare DFT with experimental measurements |
| Expanded garnet dataset | Additional garnet-type electrolytes |
| API | Programmatic dataset access |
| Data hosting | HF Datasets / Zenodo for easier access |

## Long Term

| Goal | Target |
|------|--------|
| 500k+ validated entries | v5.0 |
| 5+ sources (add AFLOW, NOMAD, others) | v5.0 |
| Multi-fidelity (DFT + DFT+U + hybrid) | v6.0 |
| Active learning integration | v6.0 |
