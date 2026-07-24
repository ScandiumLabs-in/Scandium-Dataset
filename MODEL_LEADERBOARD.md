# Model Leaderboard — Scandium-Dataset v0.3.0

Results on the four frozen benchmark splits. All models use the same train/val/test indices.

## Composition-Only Baselines (RF + Ridge Ensemble)

Feature representation: Bag-of-elements (89-element fraction vector), StandardScaler-normalized.

Model: 200-tree RandomForest (max_depth=20) + Ridge(α=1.0), prediction = 0.5×RF + 0.5×Ridge.

### Full Dataset (all tiers)

| Split | FE MAE | FE RMSE | FE R² | EaH MAE | EaH RMSE | EaH R² | BG MAE | BG RMSE | BG R² | N (test) |
|-------|--------|---------|-------|---------|----------|--------|--------|---------|-------|----------|
| random_80_10_10 | 0.3919 | 0.5717 | 0.7906 | 0.2244 | 0.4137 | 0.3246 | 0.4943 | 0.8633 | 0.5502 | 39,940 |
| composition_held_out | 0.3897 | 0.5474 | 0.8009 | 0.2226 | 0.3760 | 0.3825 | 0.4973 | 0.8608 | 0.5494 | 26,338 |
| family_held_out | 0.7387 | 0.8322 | −1.5562 | 0.1689 | 0.4963 | −0.0212 | 1.1045 | 1.2641 | 0.1378 | 583 |
| chemistry_held_out | 1.6565 | 1.8289 | −2.5386 | 0.3551 | 0.4959 | −0.9206 | 1.9662 | 2.4611 | −0.0893 | 12,675 |

### Gold Tier Only

| Split | FE MAE | FE RMSE | FE R² | EaH MAE | EaH RMSE | EaH R² | BG MAE | BG RMSE | BG R² | N (test) |
|-------|--------|---------|-------|---------|----------|--------|--------|---------|-------|----------|
| random_80_10_10 | 0.2984 | 0.4241 | 0.8543 | 0.0235 | 0.0280 | 0.2161 | 0.7621 | 1.0766 | 0.5990 | 14,721 |
| composition_held_out | 0.3062 | 0.4389 | 0.8378 | 0.0236 | 0.0280 | 0.2381 | 0.7719 | 1.0907 | 0.5958 | 9,453 |
| family_held_out | 0.4580 | 0.4953 | −3.4812 | 0.0190 | 0.0237 | 0.2592 | 0.9426 | 1.1103 | 0.2920 | 507 |
| chemistry_held_out | 1.3838 | 1.5222 | −1.8731 | 0.0274 | 0.0324 | −0.0667 | 2.1287 | 2.7238 | −0.3350 | 9,178 |

## Key Findings

1. **Gold-tier training consistently beats full-dataset training on FE** — MAE drops from 0.392 → 0.298 on random split, and from 1.657 → 1.384 on chemistry held-out. The tiering system demonstrably improves data quality for model training.

2. **EaH is dramatically better on Gold** (0.023 vs 0.224 MAE) — because Gold excludes JARVIS entries (which lack EaH) and filters OQMD EaH outliers.

3. **Band gap is harder on Gold** — likely because Gold contains fewer metallic entries (band gap = 0), shifting the distribution away from the population mean.

4. **Chemistry held-out is the hardest split** — halides are genuinely out-of-distribution for composition-only models. FE R² is negative for both configurations, indicating the model cannot generalize to unseen chemistries.

5. **Family held-out is also challenging for FE** — with only 583 test entries and unseen families, the R² is negative for both tier configurations.

## Next Baselines to Add

- CGCNN (requires structure parsing)
- MEGNet (requires structure parsing)
- ALIGNN (requires graph construction)
- CrabNet (attention-based composition encoding)
