# Making Scandium-Dataset the Best Solid-State Battery Materials Dataset

## A Research-Backed Strategic Roadmap

> **Status:** Planning document for v0.2+ releases
> **Current version:** v0.1.0-rc.2 (general inorganic materials aggregation)

---

## 0. Where the Dataset Stands Today

Scandium-Dataset (v0.1.0-rc.2) is currently a **general inorganic materials aggregation** with battery-relevant chemical filtering, not a purpose-built SSB dataset:

- 266,732 entries from MP (69,279), OQMD (171,780), JARVIS-DFT (25,673)
- Fields: formula, elements, space group, volume, density, formation energy, EaH, band gap, structure JSON, quality score, tier, provenance, SSE proxy features
- "Battery" subset (82,925) and "Electrolyte" subset (41,665) — chemistry-filtered, not physics-filtered
- Tiering (Strict Gold → Raw) is structural validity/completeness, not electrolyte-specific

### The Core Gap

None of the three physical properties that determine whether a solid is a viable SSE are present:

1. **Ionic conductivity / migration barrier** — is Li⁺/Na⁺ actually mobile?
2. **Electrochemical stability window** — does it survive contact with Li-metal?
3. **Mechanical properties** — can it suppress dendrite growth?

Formation energy, EaH, and band gap are necessary but not sufficient. A huge fraction of thermodynamically stable, wide-gap Li compounds are terrible ionic conductors. This is the central lesson of Sendek et al. and the entire computational SSE-screening literature.

---

## 1. What Defines a Good SSE (Screening Criteria)

Drawing on Sendek et al. (>12,000 candidates, *Energy Environ. Sci.*) and the broader ML-for-SSE literature (*Materials Horizons* 2024–25 review; *Scientific Data* hierarchical screening), a material must clear ~5 independent gates:

| Gate | Property | Typical Threshold | Why It Matters |
|------|----------|------------------|----------------|
| 1 | Thermodynamic stability | E_hull ≲ 0.02–0.1 eV/atom | Synthesizability |
| 2 | Electronic insulation | Band gap ≳ 1–2 eV | Prevent self-discharge |
| 3 | Ionic mobility | E_a ≲ 300–525 meV, σ ≳ 10⁻⁴ S/cm | The whole point of an SSE |
| 4 | Electrochemical window | 0–4+ V vs Li/Li⁺, or passivating interphase | Survive cycling |
| 5 | Dendrite suppression | Shear modulus G ≳ 2× G_Li (~4–6 GPa) | Prevent Li filament penetration |

A purpose-built dataset should compute or estimate **all five**, flag which gates each entry passes, and expose them as queryable fields.

### 1.1 Ionic Conductivity / Migration Barrier

The most expensive and most important property. Computation strategies, cheapest → most rigorous:

1. **CAVD (Channel Analysis of Void space for Diffusion)** — geometric/topological analysis of void networks to identify percolating diffusion pathways and channel dimensionality (0D/1D/2D/3D). Fast pre-filter: if no percolating channel exists, mobility is ruled out.
2. **BVSE (Bond Valence Site Energy)** — ~seconds-per-structure method estimating the energy landscape for a mobile ion. Tools: **softBV**, **BVSE + CAVD pipeline** (*Scientific Data*). Cheap enough for the entire dataset.
3. **MLIP-NEB with universal potentials (CHGNet, MACE-MP-0, M3GNet, Orb-v3)** — 100–1000× cheaper than DFT-NEB, ~82% classification accuracy vs DFT (*arXiv:2512.03642*). The practical high-throughput workhorse.
4. **DFT-NEB / AIMD** — ground truth (Sendek et al.). Reserve for a curated validation subset.

**Recommendation:** CAVD (percolation) → BVSE (fast energy) → MLIP-NEB (quantitative barrier) → DFT-NEB (gold-standard validation subset).

### 1.2 Electrochemical Stability Window

The Richards/Ceder methodology (*Chem. Mater.*) computes grand-potential phase diagrams against Li reservoirs at varying chemical potential. Directly implementable at scale via **pymatgen's `InterfacialReactivity`** using existing MP formation energies. **No new DFT required** — just phase-diagram construction on existing thermodynamic data.

**Fields to add:** `stability_window_low_V`, `stability_window_high_V`, `interfacial_reaction_energy_vs_Li_eV_atom`, `passivating_interphase`.

### 1.3 Mechanical Properties

The Monroe-Newman criterion states G_solid ≳ 2× G_Li for dendrite suppression (later work has refined the multiplier; cite as an evolving criterion).

**Strategy:** MLIP-based elastic tensor estimation (CHGNet/MACE under strain) as the default; full DFT elastic tensor calculations for the Strict-Gold validation subset.

**Fields to add:** `bulk_modulus_GPa`, `shear_modulus_GPa`, `youngs_modulus_GPa`, `poisson_ratio`, `dendrite_suppression_flag`.

### 1.4 Structural Descriptors Correlating with Conductivity

Cheap, seconds-per-structure, should be computed for 100% of the dataset:

- Mobile-ion volume fraction and site multiplicity
- Anion framework packing fraction / free volume
- Coordination number and bond-valence mismatch at mobile-ion site
- Channel dimensionality from CAVD (0D/1D/2D/3D)
- Anion sublattice polarizability (S²⁻/Cl⁻/Br⁻ give lower barriers than O²⁻)

---

## 2. Benchmark Against Existing SSE Resources

| Resource | What It Offers | Scale | Gap vs. Scandium Dataset Today |
|----------|----------------|-------|-------------------------------|
| **OBELiX** (NRC-Mila, arXiv:2502.14234) | Curated experimental ionic conductivities + crystal structures, leakage-resistant splits | 599 entries, 321 unique structures | Zero experimental conductivity labels; split methodology should be extended to conductivity tasks |
| **LiTraj** (AIRI Institute) | DFT-computed Li-ion migration data for benchmarking ML models | Purpose-built benchmark set | Directly analogous to MLIP-NEB + DFT-NEB validation subset |
| **Sendek et al.** | ~12,000 candidates screened via structural criteria + Ea threshold | 12,831 → 21 promising | Methodology should be reproduced/extended as screening logic backbone |
| **MP Electrolyte Genome** | Battery-specific views on MP | Subset of MP | Already ingests MP; needs battery-explorer-equivalent derived properties |
| **Family-specific databases** (garnet, NASICON, argyrodite papers) | Deep coverage of known fast-ion conductors | Small, fragmented | Should explicitly tag and enrich these families |

**Positioning:** Scandium's advantage is **scale** (266k vs. OBELiX's 599). The strategic move is to be the **largest computationally-screened SSE candidate pool with OBELiX-quality experimental ground truth stitched in as a gold-standard validation layer** — a combination that doesn't currently exist as a single open dataset.

---

## 3. Schema Additions

Extend the existing flat schema with an **SSB-screening properties block**:

```json
{
  "ssb_screening": {
    "mobile_ion": "Li | Na | Mg | null",
    "mobile_ion_fraction": 0.0,
    "cavd_channel_dimensionality": "0D | 1D | 2D | 3D | none",
    "bvse_migration_barrier_eV": null,
    "mlip_neb_migration_barrier_eV": null,
    "mlip_neb_potential": "CHGNet | MACE-MP-0 | M3GNet | Orb-v3",
    "dft_neb_migration_barrier_eV": null,
    "dft_neb_verified": false,
    "estimated_ionic_conductivity_S_cm": null,
    "conductivity_source": "computed_BVSE | computed_NEB | experimental_OBELiX | experimental_literature",
    "stability_window_low_V": null,
    "stability_window_high_V": null,
    "interfacial_reaction_energy_vs_Li_eV_atom": null,
    "passivating_interphase": null,
    "bulk_modulus_GPa": null,
    "shear_modulus_GPa": null,
    "elastic_source": "DFT | MLIP_estimated | ML_predicted",
    "dendrite_suppression_flag": null,
    "sse_family": "garnet | NASICON | argyrodite | perovskite | anti_perovskite | LISICON | halide | LGPS_type | other | none",
    "sse_candidate_score": null,
    "gates_passed": ["thermo_stability", "electronic_insulation", "ionic_mobility", "electrochemical_window", "mechanical"]
  }
}
```

`sse_candidate_score` should be a transparent, documented composite with the weighting scheme published.

---

## 4. Filling Coverage Gaps

1. **Enrich known fast-ion-conductor families** — garnets, NASICONs, argyrodites, LGPS-type, anti-perovskites, halides. These are under-represented in generic MP/OQMD pulls.
2. **Pull ICSD-derived experimental structures** where license permits — cross-referencing against experimentally realized phases increases trust for synthesizability.
3. **Ingest OBELiX directly** as a labeled gold subset (with attribution) — gives immediate experimental-conductivity validation.
4. **Widen beyond Li** — Na and Mg SSEs are comparatively data-poor and high-value.
5. **Polymer/composite SSEs** require separate handling — scope v1 to crystalline inorganics.

---

## 5. Validation and Honest Benchmarking

- Report accuracy against DFT-NEB / experimental ground truth for every MLIP or BVSE-derived barrier
- Publish **per-family accuracy** (MLIPs are systematically better/worse for oxide vs. sulfide vs. halide)
- Extend frozen splits to conductivity/stability tasks specifically
- Add `label_confidence` / `computed_vs_verified` field per property

---

## 6. Updated Tier System

Add an orthogonal **SSB-readiness axis**:

| SSB Tier | Criteria |
|----------|----------|
| **SSE-Verified** | DFT-NEB or experimental conductivity + DFT window + DFT elastic moduli |
| **SSE-Screened** | CAVD+BVSE+MLIP-NEB barrier, computed window, MLIP elastic — passes all 5 gates |
| **SSE-Candidate** | Passes thermodynamic + electronic gates only; descriptors present but no kinetic/mechanical data |
| **Not Screened** | General entry, no SSB-specific analysis run |

Crossed with existing quality tiers, users get a two-axis filter.

---

## 7. Implementation Roadmap

### Phase 1 — Cheap, High-Leverage, No New DFT (Weeks)
- [x] Tag mobile-ion content for all 266k entries
- [x] Compute carrier fraction, volume per carrier, FE per carrier
- [ ] Run CAVD channel-dimensionality analysis dataset-wide
- [ ] Build electrochemical stability windows from existing MP data via pymatgen
- [ ] Tag known SSE structural families (garnet/NASICON/argyrodite/LGPS-type)
- [ ] Create `ssb_screening` schema block

### Phase 2 — MLIP-Driven Scale-Up (Weeks–Months)
- [ ] Run BVSE across mobile-ion-containing subset (~50–100k entries)
- [ ] Run MLIP-NEB (CHGNet/MACE-MP-0) migration barriers on CAVD+BVSE-filtered subset
- [ ] Run MLIP-based elastic tensor estimation across same subset
- [ ] Publish first `sse_candidate_score`

### Phase 3 — Gold-Standard Validation Layer (Months)
- [ ] Stratified DFT-NEB/AIMD verification sample
- [ ] Ingest OBELiX as experimental gold subset
- [ ] Publish per-family, per-method accuracy tables

### Phase 4 — Community and Reproducibility
- [ ] Publish composite `sse_candidate_score` formula openly
- [ ] Extend frozen benchmark splits to conductivity/stability tasks
- [ ] Release leaderboard/benchmark harness for SSE ML sub-community

---

## 8. Key References

1. Sendek et al. *Holistic computational structure screening of >12,000 candidates for solid Li-ion conductor materials.* Energy Environ. Sci.
2. *Machine learning pipelines for the design of solid-state electrolytes.* Materials Horizons (RSC), 2024–25.
3. *Machine Learning Enabled Computational Screening of Inorganic Solid Electrolytes for Suppression of Dendrite Formation.* PMC/arXiv.
4. *High-throughput screening platform for solid electrolytes combining hierarchical ion-transport prediction algorithms.* Scientific Data (Nature).
5. *Computational screening of sodium solid electrolytes through unsupervised learning.* npj Comput. Mater.
6. OBELiX. *A Curated Dataset of Crystal Structures and Experimentally Measured Ionic Conductivities for Li SSEs.* arXiv:2502.14234.
7. Richards, Miara, Wang, Kim, Ceder. *Interface Stability in Solid-State Batteries.* Chem. Mater.
8. *First-Principles Prediction of the Electrochemical Stability and Reaction Mechanisms of SSEs.* JACS Au.
9. CAVD. *Towards better characterization of void space for ionic transport analysis.* Scientific Data.
10. softBV. *A software tool for screening the materials genome of inorganic fast ion conductors.*
11. LiTraj. *Datasets for benchmarking ML models for predicting Li-ion migration.* AIRI Institute.
12. *Evaluation of Foundational MLIPs for Migration Barrier Predictions.* arXiv:2512.03642.
13. *High-Throughput NEB for Li-Ion Conductor Discovery via Fine-Tuned CHGNet Potential.* arXiv.
14. Monroe & Newman. *The Impact of Elastic Deformation on Deposition Kinetics at Li/Polymer Interfaces.* J. Electrochem. Soc.
15. *Revisiting the Criterion for Mechanical Suppression of Dendrites at the Li/Electrolyte Interface.* IOPscience.
16. *Prediction, interpretation and extrapolation for shear modulus and bulk modulus of SSEs based on ML.* ScienceDirect 2024.
17. *Lithium Dendrite in All-Solid-State Batteries: Growth Mechanisms, Suppression Strategies, and Characterizations.* Matter (Cell Press).
