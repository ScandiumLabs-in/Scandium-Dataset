# Scandium Benchmark v0.0 — Model Leaderboard

**Dataset:** Scandium v0.0 RC (266,732 entries)
**Splits:** `dataset_v3/benchmark/splits/` (seed=42, formula-grouped)
**Updated:** 2026-07-21

## Baseline Results

| Model | Split | FE MAE | FE RMSE | EaH MAE | EaH RMSE | BG MAE | BG RMSE |
|-------|-------|--------|---------|---------|----------|--------|---------|
| Mean Baseline | random_80_10_10 | 1.017 | 1.249 | 0.328 | 0.503 | 0.883 | 1.287 |
| Median Baseline | random_80_10_10 | 0.963 | 1.196 | 0.300 | 0.474 | 0.550 | 0.957 |

## Submitted Results

| Model | Split | FE MAE | FE RMSE | EaH MAE | BG MAE | Per-Family | Date |
|-------|-------|--------|---------|---------|--------|------------|------|
| — | — | — | — | — | — | — | — |

## Per-Family Baseline (Mean, random_80_10_10)

| Family | FE MAE | EaH MAE | BG MAE |
|--------|--------|---------|--------|
| intermetallic | 0.787 | 0.334 | 0.588 |
| layered_oxide | 1.634 | 0.312 | 1.065 |
| halide_sse | 1.609 | 0.324 | 2.011 |
| sulfide_sse | 0.873 | 0.291 | 1.216 |
| polyanion | 1.744 | 0.390 | 2.553 |
| nasicon | 2.141 | 0.347 | 1.998 |
| borohydride | 0.991 | 0.344 | 3.774 |
| oxide | 1.195 | 0.318 | 1.362 |

## Per-Source Baseline (Mean, random_80_10_10)

| Source | FE MAE | EaH MAE | BG MAE |
|--------|--------|---------|--------|
| MP | 1.383 | 0.335 | 1.236 |
| OQMD | 0.885 | 0.326 | 0.719 |
| JARVIS | 0.911 | N/A | 1.014 |

## Submission Instructions

1. Train on frozen splits (seed=42, formula-grouped)
2. Evaluate on all 4 split types
3. Report: overall + per-family + per-source
4. Submit PR adding row to this table
