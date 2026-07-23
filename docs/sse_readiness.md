# SSE Readiness Assessment

## What This Dataset Does and Does Not Do for Solid-State Electrolyte Discovery

This document is an honest, domain-expert-facing assessment of where the Scandium
Dataset is useful for solid-state electrolyte (SSE) discovery, where it falls
short, and what would need to be added to make it fit for purpose.

---

## Bottom Line

**The Scandium Dataset, in its current form, is a general-purpose inorganic
materials dataset with SSE-relevant filtering, NOT a purpose-built SSE discovery
resource.** It is useful for first-pass thermodynamic screening and as
pretraining data, but it cannot directly answer the questions that SSE
researchers ask first.

---

## SSE-Relevant Properties: Present vs. Missing

| Property | Present? | Why It Matters | What's Needed |
|----------|----------|----------------|---------------|
| Formation Energy | ✅ Yes | Thermodynamic stability → synthesizable? | Already present |
| Energy Above Hull | ✅ Yes (90.4%) | Phase stability → will it decompose? | Missing for JARVIS entries |
| Band Gap | ✅ Yes (99.9%) | Electronic insulation → prevents leakage current | Already present |
| **Ionic Conductivity** | ❌ **Missing** | **The primary screening metric for SSEs** | Requires NEB/AIMD or experiment |
| **Migration Barrier (Eₐ)** | ❌ **Missing** | **Determines Li⁺/Na⁺ hop rate** | Requires NEB calculation |
| **Electrochemical Stability Window** | ❌ **Missing** | **Does it survive contact with Li/Na metal?** | Requires phase diagram analysis |
| **Shear Modulus** | ❌ **Missing** | **Dendrite suppression (Monroe-Newman criterion)** | Requires DFT elastic calculation |
| Ionic Conductivity Proxy (Li content, volume/carrier) | ⚠️ Partial | Weak signal, not predictive of transport | Added in v0.1.0-rc.1 |

---

## The Three Properties You Have vs. The Three You Need

### What the dataset gives you (formation energy, EaH, band gap):

1. **Formation energy** tells you if a phase is thermodynamically stable — necessary
   but not sufficient. A large fraction of known SSEs (e.g., Li₆PS₅Cl argyrodite)
   are metastable (EaH > 0), so stability alone does not disqualify a candidate.

2. **Energy above hull** tells you how metastable a phase is — useful for
   identifying synthesizable candidates (EaH < ~25 meV/atom for metastable
   synthesis). This is one of the more useful SSE signals in the dataset.

3. **Band gap** tells you about electronic insulation — relevant for preventing
   self-discharge and dendrite formation through the electrolyte. A band gap
   >~3 eV is generally desired for SSEs. This is a valid secondary filter.

### What's missing (the three properties the field actually screens on):

1. **Ionic conductivity (σ_ion)** — the single most important property. A material
   can be perfectly stable, have a wide band gap, and still be useless as an SSE
   because Li⁺ ions can't move through it. The dataset has zero conductivity
   labels. This means you cannot train a model to predict σ_ion from this data,
   nor can you rank candidates by the metric that matters most.

2. **Electrochemical stability window** — an SSE must survive contact with Li
   metal anode and high-voltage cathode. This requires computing the grand
   potential phase diagram against Li (or Na), which is a different and more
   expensive calculation than bulk formation energy. Many materials with
   excellent bulk stability decompose at the Li interface (e.g., LGPS
   decomposes below ~1.7 V vs Li/Li⁺, limiting its practical use despite
   record conductivity).

3. **Shear modulus** — the Monroe-Newman criterion for dendrite suppression
   requires G_solid > ~1.3× G_Li (~6 GPa). Without elastic constants, you
   cannot filter for mechanical dendrite resistance — one of the main
   practical failure modes of solid-state batteries.

---

## Family Distribution vs. SSE Research Reality

The dataset's 10 material families are a reasonable chemical taxonomy, but the
distribution is not aligned with SSE research priorities:

| SSE Research Priority | Entries in Dataset | Assessment |
|-----------------------|-------------------|------------|
| **Sulfide SSEs** (LGPS, argyrodites, Li₃PS₄) | 16,359 (6.1%) | Adequate for pretraining, but no conductivity labels |
| **Halide SSEs** (Li₃YCl₆, Li₃InCl₆) | 18,803 (7.1%) | Good coverage of a newer SSE class |
| **Oxide SSEs** (LLZO garnet, NASICON, perovskites) | 560 NASICON + 23 garnet + 11,928 general oxide | **Garnet undercount is severe** — 23 entries is not enough for ML |
| **Intermetallics** | 166,930 (62.6%) | **Not SSE-relevant** — these are alloy materials, not electrolytes |

The Gold-tier SSE-relevant subset (sulfide + halide + garnet + NASICON) contains
22,525 entries — sufficient for some tasks, but critically missing the key
properties (conductivity, window, modulus) that would make them actually useful
for SSE screening.

---

## What the Dataset IS Actually Good For (Realistically)

### Tier 1: Directly usable
- **Thermodynamic stability screening** — filter by formation energy and EaH to
  identify synthesizable candidate phases across a broad chemical space
- **Band-gap-based electronic insulation filtering** — screen for band gap > 3 eV
- **Large pretraining corpus** — 266K entries is sufficient for self-supervised
  pretraining of a crystal foundation model (e.g., M3GNet-level pretraining)
  that can later be fine-tuned on SSE-specific properties

### Tier 2: Usable with augmentation
- **Targeted DFT screening** — use the Gold-tier SSE subset (22,525 entries) to
  prioritize which candidates to run expensive NEB/elastic/phase-diagram
  calculations on (a 10–100× speedup over screening from scratch)
- **Multi-source benchmark** — the frozen splits and cross-source validation
  enable reproducible comparison of featurization and model architectures

### Tier 3: Not usable
- **Direct SSE candidate ranking** — no conductivity, window, or modulus labels
- **Ionic conductivity prediction** — no training targets exist
- **Dendrite suppression screening** — no shear modulus data
- **Interface compatibility** — no interphase reaction energies

---

## What It Would Take to Fix This

### Short-term (weeks, no new DFT):
1. ✅ **Add proxy features** — Li/Na content per formula unit, volume per mobile
   carrier, carrier fraction. These are weak signals but better than nothing.
   *(Done in v0.1.0-rc.1)*
2. ✅ **Honest documentation** — this document. *(Done)*
3. ✅ **CAVD channel dimensionality** — geometric Voronoi-based percolation analysis
   on all Li/Na-containing entries. *(Done in v0.2.0)*
4. ✅ **SSE candidate score** — 5-gate composite scoring system (gates 1–2 fully
   populated, gates 3–5 populated when data available). *(Done in v0.2.0)*
5. ✅ **Oxidation state prediction** — per-element oxidation states via bond valence
   + heuristic. *(Done in v0.2.0)*
6. ✅ **Mechanical property proxies** — geometric density-based elastic moduli
   for all entries. *(Done in v0.2.0)*
7. ✅ **JARVIS EaH** — energy above hull computed via internal convex hull within
   JARVIS subset. *(Done in v0.2.0)*
8. ✅ **Commercial-safe edition** — MP + JARVIS only subset for commercial ML
   training. *(Done in v0.2.0)*
9. 🔲 **Electrochemical window estimation** — use pymatgen PhaseDiagram with
   MP-computed phase diagrams to estimate decomposition voltage against Li/Na
   for Gold-tier entries. Script exists but needs full run on cluster.

### Medium-term (months, DFT required):
1. 🔲 **NEB migration barriers** — compute Li⁺ migration barriers for ~500–1000
   Gold-tier sulfide/halide entries (~5 GPU-days). Enough to bootstrap a
   conductivity prediction model.
2. 🔲 **Elastic constants** — compute shear/bulk moduli for the same subset
   (~5 GPU-days via DFPT).
3. 🔲 **Electrochemical windows** — grand potential phase diagram analysis against
   Li/Na for all Gold-tier SSE entries (~30 CPU-hours).

### Long-term (year+):
1. 🔲 **Ionic conductivity training set** — combine NEB barriers with AIMD
   trajectories for ~100–200 entries to create a σ_ion prediction benchmark
2. 🔲 **Experimental validation** — cross-reference predicted conductivity with
   published experimental measurements

---

## Updated Title/Positioning Recommendation

Consider retitling the dataset paper to reflect its actual strengths:

> **Scandium: A Curated Multi-Source Dataset for Thermodynamic Screening and
> Benchmarking of Battery-Relevant Inorganic Materials**

This removes the "discovery" overpromise while keeping the "battery-relevant"
framing (which is accurate — thermodynamic stability IS relevant to battery
materials, just not sufficient).

---

## References

1. Monroe, C. & Newman, J. *The Impact of Elastic Deformation on Deposition
   Kinetics at Lithium/Polymer Interfaces.* J. Electrochem. Soc. (2005).
   — The dendrite-suppression shear modulus criterion.

2. Richards, W.D. et al. *Design and Synthesis of the Superionic Conductor
   Na₁₀Sn₂PS₁₂.* Nat. Commun. (2016).
   — Phase diagram approach to SSE discovery.

3. Ong, S.P. et al. *Phase Stability, Electrochemical Stability and Ionic
   Conductivity of the Li₁₀±₁MP₂X₁₂ (M = Ge, Si, Sn, Al or P, and X = O, S
   or Se) Family of Superionic Conductors.* Energy Environ. Sci. (2013).
   — The standard methodology for computing electrochemical stability windows.

---

## Strategic Update (July 2026)

See **[SSB Strategic Roadmap](../docs/ssb_strategic_roadmap.md)** for the comprehensive
literature-backed plan to evolve this dataset from a general aggregation into a
purpose-built SSB discovery resource. Key additions since v0.1.0-rc.2:

- **SSE family classification** now present on all 266,732 entries (composition-based
  tagging as garnet/NASICON/argyrodite/LGPS-type/LISICON/anti-perovskite/perovskite/
  halide/borohydride/sulfide/oxide)
- **Mobile ion field** (Li/Na/Mg carrier) standardized across all entries
- Phase 1 plan (CAVD → BVSE → MLIP-NEB → DFT-NEB pipeline) documented and prioritized
