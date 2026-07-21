"""Standardized v0.0 benchmark evaluation runner.

Usage:
    # Evaluate predictions on a split
    python dataset_v3/benchmark/evaluate.py \
        --splits random_80_10_10 \
        --predictions results/my_model_preds.json

    # Generate baseline predictions (dummy/no-skill)
    python dataset_v3/benchmark/evaluate.py --baseline mean
"""
import json, os, sys, time, argparse
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from src.evaluation.metrics import compute_metrics

BENCHMARK_DIR = Path("dataset_v3/benchmark")
SPLITS_DIR = BENCHMARK_DIR / "splits"
RESULTS_DIR = BENCHMARK_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DATASET_PATH = "dataset_v3/exports/entries_final_v3.json"
TARGETS = ["formation_energy_per_atom", "energy_above_hull", "band_gap"]
TARGET_LABELS = dict(zip(TARGETS, ["FE", "EaH", "BG"]))


def load_dataset():
    with open(DATASET_PATH) as f:
        return json.load(f)


def load_split(name):
    path = SPLITS_DIR / f"{name}.json"
    with open(path) as f:
        return json.load(f)


def evaluate_predictions(entries, split, predictions):
    """Compute metrics for each target on each split.

    predictions: dict {entry_index: {target: value, ...}}
    """
    results = {}
    for target in TARGETS:
        label = TARGET_LABELS[target]
        y_true, y_pred = [], []
        for idx in split["test"]:
            e = entries[idx]
            true_val = e.get(target)
            pred_val = predictions.get(str(idx), {}).get(target)
            if true_val is not None and pred_val is not None:
                y_true.append(true_val)
                y_pred.append(pred_val)

        if len(y_true) < 10:
            results[label] = {"n": len(y_true), "error": "insufficient data"}
            continue

        metrics = compute_metrics(np.array(y_true), np.array(y_pred))
        metrics["n"] = len(y_true)
        results[label] = metrics

    return results


def per_family_metrics(entries, split, predictions):
    """Metrics broken down by material family."""
    results = {}
    families = defaultdict(lambda: {t: {"y_true": [], "y_pred": []} for t in TARGETS})

    for idx in split["test"]:
        e = entries[idx]
        fams = e.get("families", ["unknown"])
        primary_fam = fams[0] if fams else "unknown"
        for target in TARGETS:
            true_val = e.get(target)
            pred_val = predictions.get(str(idx), {}).get(target)
            if true_val is not None and pred_val is not None:
                families[primary_fam][target]["y_true"].append(true_val)
                families[primary_fam][target]["y_pred"].append(pred_val)

    for fam, targets_dict in families.items():
        results[fam] = {}
        for target in TARGETS:
            label = TARGET_LABELS[target]
            yt = np.array(targets_dict[target]["y_true"])
            yp = np.array(targets_dict[target]["y_pred"])
            if len(yt) < 5:
                results[fam][label] = {"n": len(yt), "error": "insufficient data"}
            else:
                m = compute_metrics(yt, yp)
                m["n"] = len(yt)
                results[fam][label] = m

    return results


def per_source_metrics(entries, split, predictions):
    """Metrics broken down by source."""
    results = {}
    sources = defaultdict(lambda: {t: {"y_true": [], "y_pred": []} for t in TARGETS})

    for idx in split["test"]:
        e = entries[idx]
        src = e.get("source", "unknown")
        for target in TARGETS:
            tv = e.get(target)
            pv = predictions.get(str(idx), {}).get(target)
            if tv is not None and pv is not None:
                sources[src][target]["y_true"].append(tv)
                sources[src][target]["y_pred"].append(pv)

    for src, targets_dict in sources.items():
        results[src] = {}
        for target in TARGETS:
            label = TARGET_LABELS[target]
            yt = np.array(targets_dict[target]["y_true"])
            yp = np.array(targets_dict[target]["y_pred"])
            if len(yt) < 5:
                results[src][label] = {"n": len(yt), "error": "insufficient data"}
            else:
                m = compute_metrics(yt, yp)
                m["n"] = len(yt)
                results[src][label] = m

    return results


def generate_baseline(entries, split, strategy="mean"):
    """Generate baseline predictions (mean or median).
    
    Useful for measuring how much better models perform than trivial baselines.
    """
    predictions = {}
    targets_values = {t: [] for t in TARGETS}

    for idx in split["train"]:
        e = entries[idx]
        for t in TARGETS:
            v = e.get(t)
            if v is not None:
                targets_values[t].append(v)

    baseline = {}
    for t in TARGETS:
        arr = np.array(targets_values[t])
        if strategy == "mean":
            baseline[t] = float(np.mean(arr))
        elif strategy == "median":
            baseline[t] = float(np.median(arr))

    for idx in split["test"]:
        predictions[str(idx)] = dict(baseline)

    return predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--splits", type=str, nargs="+",
                        default=["random_80_10_10"],
                        help="Split names to evaluate on")
    parser.add_argument("--predictions", type=str, default=None,
                        help="JSON file with predictions {idx: {target: val}}")
    parser.add_argument("--baseline", type=str, default=None,
                        choices=["mean", "median"],
                        help="Generate baseline predictions instead of loading")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path for results")
    parser.add_argument("--model-name", type=str, default="baseline",
                        help="Model name for results")
    args = parser.parse_args()

    print("=" * 60, flush=True)
    print("  V3.0 BENCHMARK EVALUATION", flush=True)
    print("=" * 60, flush=True)

    entries = load_dataset()
    print(f"  Dataset: {len(entries):,} entries", flush=True)

    all_results = {}

    for split_name in args.splits:
        print(f"\n  Split: {split_name}", flush=True)
        split = load_split(split_name)
        print(f"    Train: {len(split['train']):,}  Val: {len(split['val']):,}  "
              f"Test: {len(split['test']):,}", flush=True)

        # Load or generate predictions
        if args.baseline:
            print(f"    Baseline: {args.baseline}", flush=True)
            predictions = generate_baseline(entries, split, args.baseline)
        elif args.predictions:
            with open(args.predictions) as f:
                predictions = json.load(f)
            print(f"    Predictions: {len(predictions)} entries", flush=True)
        else:
            print(f"    No predictions — use --predictions or --baseline", flush=True)
            continue

        # Overall metrics
        overall = evaluate_predictions(entries, split, predictions)
        print(f"\n    Overall:")
        for target, metrics in overall.items():
            if "error" in metrics:
                print(f"      {target:5s}: {metrics['error']}")
            else:
                print(f"      {target:5s}: MAE={metrics['mae']:.4f}  "
                      f"RMSE={metrics['rmse']:.4f}  R²={metrics['r2']:.4f}  "
                      f"N={metrics['n']:,}")

        # Per-family
        pf = per_family_metrics(entries, split, predictions)
        print(f"\n    Per-Family (MAE):")
        for fam in sorted(pf.keys()):
            vals = []
            for t in TARGETS:
                lbl = TARGET_LABELS[t]
                m = pf[fam].get(lbl, {})
                if "error" not in m:
                    vals.append(f"{m['mae']:.4f}")
                else:
                    vals.append("N/A")
            print(f"      {fam:25s}: FE={vals[0]:>8s}  EaH={vals[1]:>8s}  BG={vals[2]:>8s}")

        # Per-source
        ps = per_source_metrics(entries, split, predictions)
        print(f"\n    Per-Source (MAE):")
        for src in sorted(ps.keys()):
            vals = []
            for t in TARGETS:
                lbl = TARGET_LABELS[t]
                m = ps[src].get(lbl, {})
                if "error" not in m:
                    vals.append(f"{m['mae']:.4f}")
                else:
                    vals.append("N/A")
            print(f"      {src:10s}: FE={vals[0]:>8s}  EaH={vals[1]:>8s}  BG={vals[2]:>8s}")

        all_results[split_name] = {
            "model": args.model_name,
            "split": split_name,
            "overall": overall,
            "per_family": pf,
            "per_source": ps,
        }

    # Save
    if args.output:
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\n  Results saved: {args.output}", flush=True)
    else:
        # Save with default name
        default_name = f"results_{args.model_name}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        out_path = RESULTS_DIR / default_name
        with open(out_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\n  Results saved: {out_path}", flush=True)

    print(f"\n{'=' * 60}", flush=True)


if __name__ == "__main__":
    main()
