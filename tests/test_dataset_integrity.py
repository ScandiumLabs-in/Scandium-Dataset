"""Test basic dataset integrity: format, required fields, property ranges, splits."""
import json
from pathlib import Path

DATASET = Path(__file__).parent.parent / "dataset/entries_final_v3.json"


def load_dataset():
    with open(DATASET) as f:
        return json.load(f)


_ENTRIES = None

def get_entries():
    global _ENTRIES
    if _ENTRIES is None:
        _ENTRIES = load_dataset()
    return _ENTRIES

class TestDatasetIntegrity:
    def setup_method(self):
        self.entries = get_entries()
        self.N = len(self.entries)

    def test_dataset_not_empty(self):
        assert self.N > 0, "Dataset is empty"

    def test_all_entries_have_formula(self):
        missing = [e for e in self.entries if not e.get("formula")]
        assert len(missing) == 0, f"{len(missing)} entries missing formula"

    def test_all_entries_have_structured_formula(self):
        missing = [e for e in self.entries if not e.get("structured_formula")]
        assert len(missing) == 0, f"{len(missing)} entries missing structured_formula"

    def test_all_entries_have_elements(self):
        missing = [e for e in self.entries if not e.get("elements")]
        assert len(missing) == 0, f"{len(missing)} entries missing elements"

    def test_all_entries_have_source(self):
        missing = [e for e in self.entries if not e.get("source")]
        assert len(missing) == 0, f"{len(missing)} entries missing source"

    def test_all_entries_have_quality_score(self):
        missing = [e for e in self.entries if e.get("quality_score") is None]
        assert len(missing) == 0, f"{len(missing)} entries missing quality_score"

    def test_all_entries_have_tier(self):
        missing = [e for e in self.entries if not e.get("tier")]
        assert len(missing) == 0, f"{len(missing)} entries missing tier"

    def test_all_entries_have_provenance(self):
        missing = [e for e in self.entries if not e.get("provenance")]
        assert len(missing) == 0, f"{len(missing)} entries missing provenance"

    def test_quality_score_range(self):
        scores = [e.get("quality_score", 0) for e in self.entries]
        assert all(0 <= s <= 100 for s in scores), "Quality score out of [0, 100]"

    def test_volume_non_negative(self):
        volumes = [e.get("volume", -1) for e in self.entries]
        assert all(v > 0 for v in volumes), f"{sum(1 for v in volumes if v <= 0)} entries with volume <= 0"

    def test_density_non_negative(self):
        densities = [e.get("density", -1) for e in self.entries]
        assert all(d >= 0 for d in densities), f"{sum(1 for d in densities if d < 0)} entries with density < 0"

    def test_known_sources(self):
        sources = set(e.get("source") for e in self.entries)
        assert sources <= {"mp", "oqmd", "jarvis"}, f"Unknown sources: {sources - {'mp', 'oqmd', 'jarvis'}}"

    def test_known_tiers(self):
        tiers = set(e.get("tier") for e in self.entries)
        assert tiers <= {"gold", "validated", "raw"}, f"Unknown tiers: {tiers - {'gold', 'validated', 'raw'}}"

    def test_no_stale_missing_spacegroup_flags(self):
        stale = [e for e in self.entries
                 if e.get("source") == "oqmd"
                 and e.get("space_group") is not None
                 and "missing_spacegroup" in e.get("quality_flags", [])]
        assert len(stale) == 0, f"{len(stale)} OQMD entries have stale missing_spacegroup flag"

    def test_gold_tier_no_extreme_fe(self):
        extreme = [e for e in self.entries
                   if e.get("tier") == "gold"
                   and e.get("formation_energy_per_atom") is not None
                   and abs(e.get("formation_energy_per_atom")) > 5]
        assert len(extreme) == 0, f"{len(extreme)} Gold entries have |FE| > 5 eV/atom"

    def test_gold_tier_no_extreme_eah(self):
        extreme = [e for e in self.entries
                   if e.get("tier") == "gold"
                   and e.get("energy_above_hull") is not None
                   and e.get("energy_above_hull") > 5]
        assert len(extreme) == 0, f"{len(extreme)} Gold entries have EaH > 5 eV/atom"

    def test_tier_distribution(self):
        tiers = {}
        for e in self.entries:
            tiers[e.get("tier")] = tiers.get(e.get("tier"), 0) + 1
        assert tiers.get("gold", 0) > 0, "No Gold entries"
        assert tiers.get("validated", 0) > 0, "No Validated entries"

    def test_source_distribution(self):
        for src in ["mp", "oqmd", "jarvis"]:
            cnt = sum(1 for e in self.entries if e.get("source") == src)
            assert cnt > 0, f"Source {src} has 0 entries"

    def test_splits_distinct(self):
        import json
        base = Path(__file__).parent.parent / "dataset/splits"
        splits = {}
        for name in ["random_80_10_10", "composition_held_out", "family_held_out", "chemistry_held_out"]:
            with open(base / f"{name}.json") as f:
                splits[name] = json.load(f)
        assert splits["random_80_10_10"]["train"] != splits["composition_held_out"]["train"], \
            "composition_held_out is identical to random_80_10_10 — split bug"

    def test_splits_no_overlap(self):
        import json
        base = Path(__file__).parent.parent / "dataset/splits"
        for name in ["random_80_10_10", "composition_held_out", "family_held_out", "chemistry_held_out"]:
            with open(base / f"{name}.json") as f:
                sp = json.load(f)
            train_s = set(sp["train"])
            val_s = set(sp["val"])
            test_s = set(sp["test"])
            assert len(train_s & val_s) == 0, f"{name}: train/val overlap"
            assert len(train_s & test_s) == 0, f"{name}: train/test overlap"
            assert len(val_s & test_s) == 0, f"{name}: val/test overlap"
