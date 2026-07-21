# Dataset Statistics

Comprehensive statistics for Scandium Dataset v0.0.0.

## Overview

| Metric | Value |
|--------|-------|
| Total entries | 266,732 |
| Unique formulas | 148,141 |
| Sources | 3 |
| Families | 10 |
| Carrier elements | 7 (Li, Na, Mg, Ca, Zn, Al, K) |

## Source Distribution

| Source | Count | % | Gold | Validated | Raw |
|--------|-------|---|------|-----------|-----|
| OQMD | 171,780 | 64.4% | 29,068 | 114,776 | 27,936 |
| MP | 69,279 | 26.0% | 43,607 | 25,606 | 66 |
| JARVIS | 25,673 | 9.6% | 23,567 | 0 | 2,106 |

## Tier Distribution

| Tier | Count | % |
|------|-------|---|
| Gold | 96,242 | 36.1% |
| Strict Gold | 56,966 | 21.4% |
| Validated | 140,382 | 52.6% |
| Raw | 30,108 | 11.3% |

## Family Distribution

| Family | Count | % | Battery |
|--------|-------|---|---------|
| intermetallic | 166,930 | 62.6% | No |
| layered_oxide | 42,015 | 15.8% | Yes |
| halide_sse | 18,803 | 7.0% | Yes |
| sulfide_sse | 16,359 | 6.1% | Yes |
| oxide | 11,928 | 4.5% | Partial |
| unknown | 4,949 | 1.9% | Unknown |
| polyanion | 4,519 | 1.7% | Yes |
| borohydride | 646 | 0.2% | Yes |
| nasicon | 560 | 0.2% | Yes |
| garnet | 23 | <0.01% | Yes |

## Property Distributions

### Formation Energy (eV/atom)

| Stat | Value |
|------|-------|
| Mean | −0.58 |
| Median | −0.20 |
| Std | 1.23 |
| Min | −5.46 |
| Max | 5.34 |
| Coverage | 100% |

### Energy Above Hull (eV/atom)

| Stat | Value |
|------|-------|
| Mean | 0.39 |
| Median | 0.24 |
| Std | 0.47 |
| Min | 0.00 |
| Max | 6.09 |
| Coverage | 90.4% (missing for JARVIS) |

### Band Gap (eV)

| Stat | Value |
|------|-------|
| Mean | 0.58 |
| Median | 0.00 |
| Std | 1.06 |
| Min | 0.00 |
| Max | 9.41 |
| Coverage | 99.9% (151 missing) |

## Structural Statistics

| Metric | Mean | Median | Min | Max |
|--------|------|--------|-----|-----|
| Volume (Å³) | 249.6 | 93.9 | 15.2 | 19,406.8 |
| Density (g/cm³) | 6.10 | 6.01 | 0.54 | 22.38 |
| Nsites | 15.0 | 4.0 | 1 | 404 |

## Space Groups

| Metric | Value |
|--------|-------|
| Unique space groups | 221 |
| Most common | 225 (Fm-3m), 139 (I4/mmm), 123 (P4/mmm) |
| Missing | 16 (all OQMD — spglib failed) |

## Quality Scores

| Range | Count | % |
|-------|-------|---|
| ≥ 80 | 83,649 | 31.4% |
| ≥ 70 | 229,650 | 86.1% |
| ≥ 60 | 261,923 | 98.2% |
| ≥ 50 | 266,730 | 100% |

Mean: 77.4 | Median: 78.0 | Std: 7.6

## Quality Score Calibration

| Score Bin | N | Valid% | SG% | Complete% | FE Out% | FE MAE |
|-----------|---|--------|-----|-----------|---------|--------|
| 50-60 | 4,807 | 0.1% | 0.1% | 0.0% | 0.31% | — |
| 60-70 | 32,273 | 27.9% | 2.0% | 0.0% | 0.01% | 0.80 |
| 70-80 | 146,001 | 77.4% | 8.8% | 0.1% | 0.00% | 0.23 |
| 80-90 | 83,649 | 85.2% | 97.4% | 82.7% | 0.00% | 0.18 |

Score 80-90 is research-grade: 97.4% have space group, 0% outliers, 0.18 eV MAE.

## Cross-Source Agreement

| Pair | Overlap | FE MAE | BG MAE | Density MAE | SG Agreement |
|------|---------|--------|--------|-------------|--------------|
| MP ↔ JARVIS | 11,741 | 0.20 eV | 0.29 eV | 7.5% | 78.6% |
| MP ↔ OQMD | 225 | 0.21 eV | 0.15 eV | 9.4% | N/A |
| OQMD ↔ JARVIS | 339 | 0.23 eV | 0.10 eV | 8.8% | N/A |

## Repairs

| Repair | Entries | Status |
|--------|---------|--------|
| OQMD coordinate artifact | 137,405 | ✅ |
| OQMD space group computation | 171,764 | ✅ |
| OQMD volume fix | 47,807 | ✅ |
| OQMD density fix | 47,807 | ✅ |
| JARVIS volume fix | 25,673 | ✅ |
| Duplicate removal | 31,997 | ✅ |

## Outliers

- **FE outliers** (>|10| eV/atom): 17 entries (all OQMD)
- **EaH outliers** (>5 eV/atom): 87 entries (all MP)
- **Volume outliers** (>10,000 Å³): 3 entries (supercells)

## Element Frequency (Top 10)

| Element | % of entries |
|---------|-------------|
| O | 27% |
| Li | 25% |
| Mg | 23% |
| Zn | 19% |
| Na | 16% |
| Ca | 15% |
| Al | 14% |
| Si | 12% |
| K | 11% |
| S | 10% |
