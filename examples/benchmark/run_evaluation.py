"""Example: Run benchmark evaluation with baseline."""
import json, sys

# Use the benchmark evaluate script
sys.path.insert(0, "benchmark")
from evaluate import load_dataset, load_split, generate_baseline, evaluate_predictions, per_family_metrics

# Load dataset and split
entries = load_dataset()
split = load_split("random_80_10_10")
print(f"Loaded {len(entries):,} entries")
print(f"Split: train={len(split['train']):,}  val={len(split['val']):,}  test={len(split['test']):,}")

# Generate mean baseline
predictions = generate_baseline(entries, split, "mean")
print(f"\nGenerated mean baseline predictions")

# Evaluate
overall = evaluate_predictions(entries, split, predictions)
print(f"\nOverall Results:")
for target, metrics in overall.items():
    print(f"  {target}: MAE={metrics['mae']:.4f}  R²={metrics['r2']:.4f}  RMSE={metrics['rmse']:.4f}")

# Per-family
family_results = per_family_metrics(entries, split, predictions)
print(f"\nPer-Family FE MAE:")
for fam in sorted(family_results.keys()):
    fe = family_results[fam].get("FE", {})
    mae = fe.get("mae", float("nan"))
    print(f"  {fam:25s}: {mae:.4f}")
