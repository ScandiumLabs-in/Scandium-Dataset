# Quality Scoring

## Design Philosophy

Quality scores are not just "how good is this entry" — they measure **trustworthiness
for machine learning**. An entry might be perfectly valid DFT data but score low
on novelty (too many similar entries). This is intentional: a diverse, well-sampled
dataset produces better models than one with 100,000 copies of Li₂O.

## Score Components

The quality score is a composite of five sub-scores (max 95, normalized to 0-100):

| Sub-score | Max | What it measures |
|-----------|-----|-----------------|
| **Geometry** | 25 | Structure quality: nsites, volume, density reasonableness |
| **DFT** | 20 | Property completeness and physical range |
| **Metadata** | 15 | Space group, density, structure_json presence |
| **Novelty** | 20 | How unique this entry is relative to the dataset (diversity bonus) |
| **Chemical** | 15 | Chemical reasonableness (element combinations, valence, etc.) |

## Calibration

We proved the quality score is monotonically related to label reliability:

| Score Bin | N | Valid% | SG% | Complete% | FE Out% | FE MAE |
|-----------|---|--------|-----|-----------|---------|--------|
| 50-60 | 4,807 | 0.1% | 0.1% | 0.0% | 0.31% | — |
| 60-70 | 32,273 | 27.9% | 2.0% | 0.0% | 0.01% | 0.80 |
| 70-80 | 146,001 | 77.4% | 8.8% | 0.1% | 0.00% | 0.23 |
| 80-90 | 83,649 | 85.2% | 97.4% | 82.7% | 0.00% | 0.18 |

**Key finding**: score 80-90 is research-grade:
- 97.4% have verified space groups
- 0% property outliers
- 0.18 eV/atom cross-source FE MAE (close to DFT noise floor)

## Thresholds

| Threshold | Purpose |
|-----------|---------|
| ≥ 70 | Validated tier — basic research use |
| ≥ 80 | Strict Gold — publication-grade, benchmark-ready |
| ≥ 90 | Not yet achieved — reserved for experimentally validated entries |

## Score Distribution

```
50-60:   4,807 (1.8%)   ██
60-70:  32,273 (12.1%)  ████████████
70-80: 146,001 (54.7%)  ████████████████████████████████████████████████
80-90:  83,649 (31.4%)  ████████████████████████
90-100:  0 (0.0%)
```

## Sub-score Means

| Sub-score | Mean | Max |
|-----------|------|-----|
| Geometry | 16.7 | 25 |
| DFT | 19.7 | 20 |
| Metadata | 11.8 | 15 |
| Novelty | 14.2 | 20 |
| Chemical | 15.0 | 15 |

## Limitations

1. No score ≥ 90 — scoring is conservative; no entry has "perfect" metadata
2. OQMD entries score lower on metadata (missing space group until computed)
3. Novelty scoring may unfairly penalize common structures
