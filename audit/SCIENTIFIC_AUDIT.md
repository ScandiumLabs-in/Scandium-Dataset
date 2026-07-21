# Scientific Audit — Property Validation

**Date:** 2026-07-21 23:35:40  

## Formation Energy

**Valid entries:** 266,732 / 266,732

| Statistic | Value |
|-----------|-------|
| Mean      | -0.578 eV/atom |
| Median    | -0.196 eV/atom |
| Std Dev   | 1.249 eV/atom |
| Min       | -4.374 eV/atom |
| Max       | 45.171 eV/atom |
| P1       | -3.316 eV/atom |
| P5       | -2.816 eV/atom |
| P25       | -1.563 eV/atom |
| P50       | -0.196 eV/atom |
| P75       | 0.232 eV/atom |
| P95       | 1.064 eV/atom |
| P99       | 1.803 eV/atom |
## Energy Above Hull

**Valid entries:** 241,059 / 266,732

| Statistic | Value |
|-----------|-------|
| Mean      | 0.386 eV/atom |
| Median    | 0.237 eV/atom |
| Max       | 47.033 eV/atom |
- Entries > 1 eV/atom: **21,973** (9.1%)

## Band Gap

**Valid entries:** 266,581 / 266,732

- Metals (≤0.1 eV): **197,531** (74.1%)

- Narrow-gap (0.1–0.5 eV): **9,399** (3.5%)

- Wide-gap (>4 eV): **10,757** (4.0%)

## Critical Outliers — Documented

- **extreme_fe_hard**: 42 with |FE| > 5 (max=45.17, min=-4.37)

  *Resolution:* Documented in KNOWN_ISSUES.md. None affect Gold tier.*

- **extreme_eah_hard**: 87 with EaH > 5 (max=47.03)

  *Resolution:* Documented in KNOWN_ISSUES.md. None affect Gold tier.*

- **jarvis_energy_above_hull_missing**: 25,673/25,673 (100.0%)

  *Resolution:* Documented in KNOWN_ISSUES.md. None affect Gold tier.*

