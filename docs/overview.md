# Overview

## What is the Scandium Dataset?

The Scandium Dataset is a **curated, validated, versioned compilation** of
DFT-calculated material properties from three major open databases —
Materials Project (MP), Open Quantum Materials Database (OQMD), and JARVIS-DFT —
unified under a single schema, deduplicated, repaired, quality-scored, and
organized for **thermodynamic screening and benchmarking of battery-relevant
inorganic materials**.

⚠️ **Important:** The dataset contains formation energy, band gap, and energy
above hull — not ionic conductivity, migration barriers, or electrochemical
stability windows. See [`sse_readiness.md`](sse_readiness.md) for a detailed
assessment of what it can and cannot do for solid-state electrolyte discovery.

## Why does it exist?

Materials science has a data problem:

1. **Fragmented**: 3+ major databases, 5+ formats, incompatible APIs
2. **Untrustworthy**: Raw database dumps contain artifacts, duplicates, missing metadata
3. **Not battery-focused**: General-purpose data is 62% intermetallics
4. **Not reproducible**: No standard splits, no frozen versions, no provenance
5. **Not validated**: Quality scores without calibration, claims without evidence

The Scandium Dataset solves all five problems.

## Design Principles

1. **Trust through transparency** — every claim has evidence, every defect is documented
2. **Battery-first** — three editions (General, Battery, Electrolyte) serve different use cases
3. **Research-grade quality** — strict Gold gates ensure only the best entries pass
4. **Versioned immutability** — once frozen, data never changes
5. **Reproducible benchmarks** — fixed splits, deterministic evaluation

## The Pipeline

```
MP ─┐
     ├── Merge → Validate → Repair → Dedup → Score → Tier → Release
OQMD ┘
JARVIS ─┘
```

## Key Facts

| Metric | Value |
|--------|-------|
| Total entries | 266,732 |
| Sources | 3 (MP, OQMD, JARVIS) |
| Families | 10 (7 battery-relevant) |
| Properties | FE, EaH, BG (per entry) |
| Quality sub-scores | 5 (geometry, DFT, metadata, novelty, chemical) |
| Gold tier | 96,242 (36.1%) |
| Strict Gold | 56,966 (21.4%) |
| Structures repaired | 137,405 (OQMD coordinates) |
| Space groups computed | 171,764 (OQMD via spglib) |
| Duplicates removed | 31,997 |
