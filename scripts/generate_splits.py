"""Generate benchmark splits: random, formula-grouped, family-held-out, chemistry-held-out."""
import json, random, os
from pathlib import Path
from collections import defaultdict

random.seed(42)

DATASET = Path(__file__).parent.parent / "dataset/entries_final_v3.json"
SPLITS_DIR = Path(__file__).parent.parent / "dataset/splits"
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

with open(DATASET) as f:
    entries = json.load(f)
N = len(entries)

# Group by formula for formula-held-out split
formula_groups = defaultdict(list)
for i, e in enumerate(entries):
    f = e.get("structured_formula") or e.get("formula", "")
    formula_groups[f].append(i)

formulas = list(formula_groups.keys())
random.shuffle(formulas)

n_formula = len(formulas)
n_train_f = int(0.8 * n_formula)
n_val_f = int(0.1 * n_formula)

train_formulas = set(formulas[:n_train_f])
val_formulas = set(formulas[n_train_f:n_train_f + n_val_f])
test_formulas = set(formulas[n_train_f + n_val_f:])

comp_train = sorted(i for f in train_formulas for i in formula_groups[f])
comp_val = sorted(i for f in val_formulas for i in formula_groups[f])
comp_test = sorted(i for f in test_formulas for i in formula_groups[f])

# Validate no overlap
assert len(set(comp_train) & set(comp_val)) == 0
assert len(set(comp_train) & set(comp_test)) == 0
assert len(set(comp_val) & set(comp_test)) == 0
assert len(comp_train) + len(comp_val) + len(comp_test) == N

composition = {
    "type": "composition_held_out",
    "seed": 42,
    "train": comp_train,
    "val": comp_val,
    "test": comp_test,
}

with open(SPLITS_DIR / "composition_held_out.json", "w") as f:
    json.dump(composition, f, indent=2)
print(f"composition_held_out: train={len(comp_train):,} val={len(comp_val):,} test={len(comp_test):,}")
print(f"  Unique formulas: train={len(train_formulas):,} val={len(val_formulas):,} test={len(test_formulas):,}")

# Verify it's different from random
import json
with open(SPLITS_DIR / "random_80_10_10.json") as f:
    random_split = json.load(f)
is_same = (random_split["train"] == comp_train and 
           random_split["val"] == comp_val and 
           random_split["test"] == comp_test)
print(f"  Different from random: {not is_same}")
