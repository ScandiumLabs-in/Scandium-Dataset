"""Fast sklearn baselines across all splits and tier configurations.
Uses RandomForest + Ridge ensemble on composition features (minutes not hours).

Usage:
    python benchmark/run_baselines.py --all
    python benchmark/run_baselines.py --split random_80_10_10 --tier gold
"""

import json, os, sys, time, argparse, warnings
from pathlib import Path
from collections import defaultdict

import numpy as np

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.evaluation.metrics import compute_metrics

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "dataset" / "entries_final_v3.json"
SPLITS_DIR = BASE_DIR / "benchmark" / "splits"
RESULTS_DIR = BASE_DIR / "benchmark" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = ["formation_energy_per_atom", "energy_above_hull", "band_gap"]
TARGET_LABELS = dict(zip(TARGETS, ["FE", "EaH", "BG"]))

ELEMENT_SYMBOLS = [
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
    "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
    "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb",
    "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac",
]
ELEMENT_INDEX = {sym: i for i, sym in enumerate(ELEMENT_SYMBOLS)}
NUM_ELEMENTS = len(ELEMENT_SYMBOLS)


def formula_to_vector(elements_list):
    vec = np.zeros(NUM_ELEMENTS, dtype=np.float32)
    if elements_list:
        for el in elements_list:
            idx = ELEMENT_INDEX.get(el)
            if idx is not None:
                vec[idx] += 1.0
    total = vec.sum()
    if total > 0:
        vec /= total
    return vec


def run_experiment(entries, split_name, tier_filter):
    split_path = SPLITS_DIR / f"{split_name}.json"
    with open(split_path) as f:
        split = json.load(f)

    train_idx = split["train"]
    val_idx = split["val"]
    test_idx = split["test"]

    if tier_filter:
        train_idx = [i for i in train_idx if entries[i].get("tier") == tier_filter]
        val_idx = [i for i in val_idx if entries[i].get("tier") == tier_filter]
        test_idx = [i for i in test_idx if entries[i].get("tier") == tier_filter]
        print(f"    {tier_filter} filter: {len(train_idx)} train, {len(val_idx)} val, {len(test_idx)} test")

    if len(train_idx) < 100:
        print(f"    Skipping: too few training examples ({len(train_idx)})")
        return None

    def build_features(indices):
        X_list = []
        y_dict = {t: [] for t in TARGETS}
        for i in indices:
            e = entries[i]
            vec = formula_to_vector(e.get("elements", []))
            X_list.append(vec)
            for t in TARGETS:
                v = e.get(t)
                if v is not None:
                    y_dict[t].append(v)
                else:
                    y_dict[t].append(np.nan)
        return np.array(X_list), {t: np.array(y_dict[t]) for t in TARGETS}

    print(f"    Building features...")
    X_train, y_train = build_features(train_idx)
    X_val, y_val = build_features(val_idx)
    X_test, y_test = build_features(test_idx)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    results = {}
    families_data = defaultdict(lambda: {t: {"y_true": [], "y_pred": []} for t in TARGETS})
    sources_data = defaultdict(lambda: {t: {"y_true": [], "y_pred": []} for t in TARGETS})

    for t in TARGETS:
        label = TARGET_LABELS[t]
        print(f"    Training {label}...")

        train_mask = ~np.isnan(y_train[t])
        val_mask = ~np.isnan(y_val[t])
        test_mask_orig = ~np.isnan(y_test[t])

        if train_mask.sum() < 50:
            results[label] = {"n": int(train_mask.sum()), "error": "insufficient training data"}
            continue

        rf = RandomForestRegressor(n_estimators=200, max_depth=20, n_jobs=-1, random_state=42, verbose=0)
        rf.fit(X_train_s[train_mask], y_train[t][train_mask])

        ridge = Ridge(alpha=1.0, random_state=42)
        ridge.fit(X_train_s[train_mask], y_train[t][train_mask])

        rf_preds = rf.predict(X_test_s)
        ridge_preds = ridge.predict(X_test_s)
        ensemble = 0.5 * rf_preds + 0.5 * ridge_preds

        mask = test_mask_orig
        yt = y_test[t][mask]
        yp = ensemble[mask]
        results[label] = compute_metrics(yt, yp)

        for i, idx in enumerate(test_idx):
            if test_mask_orig[i]:
                e = entries[idx]
                fams = e.get("families", ["unknown"])
                pf = fams[0] if fams else "unknown"
                src = e.get("source", "unknown")
                families_data[pf][t]["y_true"].append(y_test[t][i])
                families_data[pf][t]["y_pred"].append(float(ensemble[i]))
                sources_data[src][t]["y_true"].append(y_test[t][i])
                sources_data[src][t]["y_pred"].append(float(ensemble[i]))

    per_family_results = {}
    for fam, td in families_data.items():
        per_family_results[fam] = {}
        for t in TARGETS:
            yt_f = np.array(td[t]["y_true"])
            yp_f = np.array(td[t]["y_pred"])
            if len(yt_f) >= 5:
                per_family_results[fam][TARGET_LABELS[t]] = compute_metrics(yt_f, yp_f)
            else:
                per_family_results[fam][TARGET_LABELS[t]] = {"n": len(yt_f), "error": "insufficient data"}

    per_source_results = {}
    for src, td in sources_data.items():
        per_source_results[src] = {}
        for t in TARGETS:
            yt_s = np.array(td[t]["y_true"])
            yp_s = np.array(td[t]["y_pred"])
            if len(yt_s) >= 5:
                per_source_results[src][TARGET_LABELS[t]] = compute_metrics(yt_s, yp_s)
            else:
                per_source_results[src][TARGET_LABELS[t]] = {"n": len(yt_s), "error": "insufficient data"}

    return {
        "model": "RF+Ridge_ensemble",
        "split": split_name,
        "tier_filter": tier_filter or "all",
        "overall": results,
        "per_family": per_family_results,
        "per_source": per_source_results,
        "test_size": len(test_idx),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--split", type=str, default="random_80_10_10")
    parser.add_argument("--tier", type=str, default=None, choices=["gold", "validated", None])
    args = parser.parse_args()

    print("=" * 60)
    print("  SCANDIUM BENCHMARK — RF+Ridge Composition Baseline")
    print("=" * 60)

    print("\nLoading dataset...")
    with open(DATASET_PATH) as f:
        entries = json.load(f)
    print(f"  {len(entries):,} entries loaded")

    all_results = {}

    if args.all:
        splits = ["random_80_10_10", "composition_held_out", "family_held_out", "chemistry_held_out"]
        tier_filters = [None, "gold"]
    else:
        splits = [args.split]
        tier_filters = [args.tier] if args.tier else [None]

    for split_name in splits:
        for tier_filter in tier_filters:
            label = f"{split_name}_{tier_filter or 'full'}"
            print(f"\n{'─' * 50}")
            print(f"  {label}")
            print(f"{'─' * 50}")
            t0 = time.time()
            result = run_experiment(entries, split_name, tier_filter)
            elapsed = time.time() - t0
            if result:
                print(f"\n  Overall ({label}):")
                for t in TARGETS:
                    lbl = TARGET_LABELS[t]
                    m = result["overall"].get(lbl, {})
                    if "error" in m:
                        print(f"    {lbl:5s}: {m['error']}")
                    else:
                        print(f"    {lbl:5s}: MAE={m['mae']:.4f}  RMSE={m['rmse']:.4f}  R²={m['r2']:.4f}  N={m['n']:,}")
                result["elapsed_seconds"] = elapsed
                all_results[label] = result

    if all_results:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        out_path = RESULTS_DIR / f"results_rf_ridge_baseline_{timestamp}.json"
        with open(out_path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\nResults saved: {out_path}")
        print_summary(all_results)


def print_summary(results):
    print("\n" + "=" * 85)
    print("  BENCHMARK SUMMARY — RF+Ridge Composition Baseline")
    print("=" * 85)
    h = f"  {'Experiment':45s} {'FE MAE':>8s} {'EaH MAE':>8s} {'BG MAE':>8s} {'N':>8s}"
    print(h)
    print("  " + "-" * 82)
    for label in sorted(results.keys()):
        r = results[label]
        o = r.get("overall", {})
        fe = o.get("FE", {})
        eah = o.get("EaH", {})
        bg = o.get("BG", {})
        fe_m = f"{fe['mae']:.4f}" if "mae" in fe else "N/A"
        eah_m = f"{eah['mae']:.4f}" if "mae" in eah else "N/A"
        bg_m = f"{bg['mae']:.4f}" if "mae" in bg else "N/A"
        n = fe.get("n", 0)
        print(f"  {label:45s} {fe_m:>8s} {eah_m:>8s} {bg_m:>8s} {n:>8,}")
    print("=" * 85)


if __name__ == "__main__":
    main()
