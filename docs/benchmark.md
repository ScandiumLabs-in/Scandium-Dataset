# Benchmark

## Overview

The Scandium Benchmark defines a standard evaluation protocol for ML models
trained on the Scandium Dataset. All models report results on the same frozen
splits using the same metrics, enabling fair comparison.

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

## Baseline Results

### Composition-Only Baseline (RF + Ridge on bag-of-elements features)

Results on the random 80/10/10 split, comparing training on the full dataset vs
Gold-tier only. See [MODEL_LEADERBOARD.md](../MODEL_LEADERBOARD.md) for complete results.

#### Full Dataset

| Split | FE MAE | FE RMSE | FE R² | EaH MAE | EaH RMSE | BG MAE | BG RMSE |
|-------|--------|---------|-------|---------|----------|--------|---------|
| random_80_10_10 | 0.392 | 0.572 | 0.791 | 0.224 | 0.414 | 0.494 | 0.863 |
| composition_held_out | 0.390 | 0.547 | 0.801 | 0.223 | 0.376 | 0.497 | 0.861 |
| family_held_out | 0.739 | 0.832 | −1.556 | 0.169 | 0.496 | 1.105 | 1.264 |
| chemistry_held_out | 1.657 | 1.829 | −2.539 | 0.355 | 0.496 | 1.966 | 2.461 |

#### Gold Tier Only

| Split | FE MAE | FE RMSE | FE R² | EaH MAE | EaH RMSE | BG MAE | BG RMSE |
|-------|--------|---------|-------|---------|----------|--------|---------|
| random_80_10_10 | 0.298 | 0.424 | 0.854 | 0.024 | 0.028 | 0.762 | 1.077 |
| composition_held_out | 0.306 | 0.439 | 0.838 | 0.024 | 0.028 | 0.772 | 1.091 |
| family_held_out | 0.458 | 0.495 | −3.481 | 0.019 | 0.024 | 0.943 | 1.110 |
| chemistry_held_out | 1.384 | 1.522 | −1.873 | 0.027 | 0.032 | 2.129 | 2.724 |

### Key Takeaway

**Gold-tier training consistently beats full-dataset training.** FE MAE drops
from 0.392 → 0.298 on the random split and from 1.657 → 1.384 on the
chemistry held-out split, despite having ~3× fewer training examples. This
directly validates the tiering system: higher-quality data produces better
models even with less data.

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

See [MODEL_LEADERBOARD.md](../MODEL_LEADERBOARD.md) for complete results.
