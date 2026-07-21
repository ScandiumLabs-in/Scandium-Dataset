# Benchmark

## Overview

The Scandium Benchmark v0.0 defines the standard evaluation protocol for ML
models trained on the Scandium Dataset. All models report results on the same
frozen splits, using the same metrics, for fair comparison.

## Splits

Four split types, all formula-grouped (no same formula across splits), seed=42:

| Split | Train | Val | Test | Tests |
|-------|-------|-----|------|-------|
| `random_80_10_10` | 200,122 | 26,670 | 39,940 | Basic generalization |
| `composition_held_out` | 213,383 | 27,011 | 26,338 | No formula overlap |
| `family_held_out` | 260,984 | 5,165 | 583 | Cross-family generalization |
| `chemistry_held_out` | 227,384 | 26,673 | 12,675 | OOD (all halides as test) |

## Metrics

### Required
- MAE, RMSE, R² for FE, EaH, BG
- Report per split, per family, per source

### Recommended
- ECE (Expected Calibration Error)
- Spearman ρ (ranking correlation)
- F1 for stability classification (EaH < 25 meV)

## Baseline Results (random_80_10_10)

| Model | FE MAE | FE RMSE | EaH MAE | EaH RMSE | BG MAE | BG RMSE |
|-------|--------|---------|---------|----------|--------|---------|
| Mean baseline | 1.017 | 1.249 | 0.328 | 0.503 | 0.883 | 1.287 |
| Median baseline | 0.963 | 1.196 | 0.300 | 0.474 | 0.550 | 0.957 |

## Evaluation Runner

```bash
# Evaluate predictions on all splits
python benchmark/evaluate.py \
    --splits random_80_10_10 composition_held_out \
    --predictions predictions.json \
    --model-name my_model

# Run baseline
python benchmark/evaluate.py --baseline mean
python benchmark/evaluate.py --baseline median
```

## Leaderboard

See [benchmark/results/](../benchmark/results/) for complete results and
[MODEL_LEADERBOARD.md](../MODEL_LEADERBOARD.md) for the leaderboard.
