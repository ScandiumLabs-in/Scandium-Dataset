# Scandium Dataset

**Open Battery Materials Dataset for AI-Driven Solid-State Battery Discovery**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](LICENSE)
[![Dataset v0.0.0](https://img.shields.io/badge/version-0.0.0-blue)]()
[![DOI](https://img.shields.io/badge/DOI-pending-blue)]()
[![Entries](https://img.shields.io/badge/entries-266%2C732-green)]()
[![Sources](https://img.shields.io/badge/sources-3-orange)]()

---

**266,732 validated materials · 3 integrated databases · 10 material families  
31,997 duplicates removed · 137,405 repaired structures  
Cross-source validated · Quality scored · Versioned · Reproducible**

---

## Why Scandium Dataset?

| Problem | Solution |
|---------|----------|
| Materials data is scattered across incompatible sources | **Unified schema** — MP, OQMD, and JARVIS under one format |
| Sources disagree on property values | **Cross-source agreement quantified** — FE MAE 0.20 eV/atom across 11,741 overlapping formulas |
| You can't trust a quality score without calibration | **Score calibration proven** — score 80-90 predicts 85.2% valid, 0.18 eV FE MAE |
| Dataset flaws get discovered after publication | **Every defect documented and repaired** — 137,405 OQMD coordinates, 47,807 volumes, 171,764 space groups |
| Model benchmarks are not comparable | **Frozen splits, fixed metrics, reproducible evaluation** |
| You don't know where data came from | **Full provenance** — source, source_id, repair history, tier gates, checksum per entry |

## Quick Start

The dataset files are distributed as [GitHub Release assets](https://github.com/ScandiumLabs-in/Scandium-Dataset/releases/tag/v0.0.0) (not stored directly in git due to size).

### Option 1: Download from GitHub Release

```bash
# Download the full dataset (1.7 GB)
wget https://github.com/ScandiumLabs-in/Scandium-Dataset/releases/download/v0.0.0/entries_final_v3.json -P dataset/

# Or the smaller subsets
wget https://github.com/ScandiumLabs-in/Scandium-Dataset/releases/download/v0.0.0/battery_subset_v3.json -P dataset/
wget https://github.com/ScandiumLabs-in/Scandium-Dataset/releases/download/v0.0.0/electrolyte_subset_v3.json -P dataset/
```

### Option 2: Git LFS (coming in v0.1)

### Load the data

```python
import json

with open("dataset/entries_final_v3.json") as f:
    entries = json.load(f)

print(f"{len(entries):,} entries loaded")
# → 266,732 entries loaded

# Filter by tier
gold = [e for e in entries if e.get("tier") == "gold"]
print(f"Gold entries: {len(gold):,}")

# Filter by family
battery = [e for e in entries if "layered_oxide" in e.get("families", [])]
print(f"Layered oxides: {len(battery):,}")
```

See [`examples/`](examples/) for more.

## Dataset Editions

| Edition | Entries | Description | Download |
|---------|---------|-------------|----------|
| **General** | 266,732 | All sources, all tiers | [⬇ Download](https://github.com/ScandiumLabs-in/Scandium-Dataset/releases/download/v0.0.0/entries_final_v3.json) (1.7 GB) |
| **Battery** | 82,925 | Battery-relevant families | [⬇ Download](https://github.com/ScandiumLabs-in/Scandium-Dataset/releases/download/v0.0.0/battery_subset_v3.json) (828 MB) |
| **Electrolyte** | 41,665 | Strict Gold electrolytes only | [⬇ Download](https://github.com/ScandiumLabs-in/Scandium-Dataset/releases/download/v0.0.0/electrolyte_subset_v3.json) (492 MB) |

## Tier System

| Tier | Count | Criteria |
|------|-------|----------|
| **Strict Gold** ⭐ | **56,966** | 11 gates: base Gold + quality ≥ 80 + no defects + provenance |
| **Gold** | 96,242 | 8 gates: validated + unique + stable + complete metadata |
| **Validated** | 140,382 | 5 gates: valid structure + targets + no critical issues |
| **Raw** | 30,108 | Source + formula present (may have quality issues) |

## Properties

| Property | Unit | Coverage | Mean | Median |
|----------|------|----------|------|--------|
| Formation Energy (FE) | eV/atom | 100% | −0.58 | −0.20 |
| Energy Above Hull (EaH) | eV/atom | 90.4% | 0.39 | 0.24 |
| Band Gap (BG) | eV | 99.9% | 0.58 | 0.00 |

## Sources

| Source | Entries | Method | Key Strength |
|--------|---------|--------|-------------|
| [Materials Project](https://next-gen.materialsproject.org/) | 69,279 | DFT (PAW-PBE) | Complete metadata, trusted |
| [OQMD](https://oqmd.org/) | 171,780 | DFT (PAW-PBE) | Largest, metastable phases included |
| [JARVIS-DFT](https://jarvis.nist.gov/) | 25,673 | DFT (optPBE + TBmBJ) | TBmBJ band gaps, public domain |

## Benchmark

Frozen train/val/test splits are at [`dataset/splits/`](dataset/splits/). Four split types:

| Split | Train | Val | Test | Purpose |
|-------|-------|-----|------|---------|
| Random 80/10/10 | 200,122 | 26,670 | 39,940 | Basic generalization |
| Composition held-out | 200,122 | 26,670 | 39,940 | No formula overlap |
| Family held-out | 260,984 | 5,165 | 583 | Cross-family |
| Chemistry held-out | 227,384 | 26,673 | 12,675 | OOD (halides) |

See [`benchmark/`](benchmark/) and [`docs/benchmark.md`](docs/benchmark.md).

## Repository Structure

```
Scandium-Dataset/
├── README.md                 ← You are here
├── LICENSE
├── CITATION.cff
├── CHANGELOG.md
├── dataset/                  ← Data files and splits
├── docs/                     ← Documentation
├── reports/                  ← Validation and analysis reports
├── benchmark/                ← Benchmark framework
├── examples/                 ← Usage examples
├── scripts/                  ← Processing and analysis scripts
└── api/                      ← Programmatic access
```

## Documentation

| Document | Description |
|----------|-------------|
| [Overview](docs/overview.md) | What, why, and how |
| [Getting Started](docs/getting_started.md) | Install, load, filter |
| [Dataset Design](docs/dataset_design.md) | Schema, sources, integration |
| [Dataset Statistics](docs/dataset_statistics.md) | Every number counted |
| [Validation](docs/validation.md) | Gates, checks, verification |
| [Quality](docs/quality.md) | Scoring system, calibration |
| [Provenance](docs/provenance.md) | Per-entry history tracking |
| [Repair](docs/repair.md) | OQMD coordinate fix, symmetry pass |
| [Benchmark](docs/benchmark.md) | Splits, metrics, protocol |
| [Limitations](docs/limitations.md) | Known issues, gaps |
| [FAQ](docs/faq.md) | Common questions |
| [Citation](docs/citation.md) | How to cite |

## Citation

```bibtex
@software{scandium_dataset_v3,
  title        = {Scandium Dataset v0.0},
  version      = {0.0.0},
  date         = {2026-07-21},
  publisher    = {Scandium Labs},
  doi          = {pending},
  url          = {https://github.com/Scandium-Labs/Scandium-Dataset}
}
```

## License

- **MP entries**: CC BY 4.0 (attribution required)
- **JARVIS entries**: CC0 (public domain)
- **OQMD entries**: Free for non-commercial use
- **Scandium processing and quality scoring**: CC BY 4.0

See [`LICENSE`](LICENSE) for details.

---

<p align="center">
  <b>Scandium Labs</b> — Building trusted data infrastructure for battery materials discovery
</p>
