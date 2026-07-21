"""Scandium Dataset API — programmatic access to the dataset.

Provides simple query and filter functions without loading the full dataset
into memory (uses iterative parsing for large files).

If the full dataset is loaded, use the in-memory functions for speed.
"""
import json
from pathlib import Path
from collections import Counter

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"


def load_entries(path=None, edition="general"):
    """Load the dataset (or specified edition) into memory.

    Args:
        path: Direct path to a JSON file. If None, uses edition name.
        edition: "general", "battery", or "electrolyte".

    Returns:
        List of entry dicts.
    """
    if path is None:
        names = {
            "general": "entries_final_v3.json",
            "battery": "battery_subset_v3.json",
            "electrolyte": "electrolyte_subset_v3.json",
        }
        path = DATASET_DIR / names[edition.lower()]

    with open(path) as f:
        return json.load(f)


def filter_by_tier(entries, tier):
    """Filter entries by tier ('gold', 'validated', 'raw')."""
    return [e for e in entries if e.get("tier") == tier]


def filter_by_source(entries, source):
    """Filter entries by source ('mp', 'oqmd', 'jarvis')."""
    return [e for e in entries if e.get("source") == source]


def filter_by_family(entries, family):
    """Filter entries by material family."""
    return [e for e in entries if family in e.get("families", [])]


def filter_battery(entries):
    """Filter to battery-relevant families."""
    battery = {"layered_oxide", "sulfide_sse", "halide_sse",
               "polyanion", "nasicon", "garnet", "borohydride"}
    return [e for e in entries if set(e.get("families", [])) & battery]


def filter_by_score(entries, min_score=0, max_score=100):
    """Filter entries by quality score range."""
    return [e for e in entries
            if min_score <= e.get("quality_score", 0) <= max_score]


def get_property(entries, prop):
    """Extract property values, excluding None."""
    vals = [e.get(prop) for e in entries if e.get(prop) is not None]
    return vals


def summary(entries):
    """Get a quick summary of the entry list."""
    return {
        "count": len(entries),
        "sources": dict(Counter(e.get("source", "?") for e in entries).most_common()),
        "tiers": dict(Counter(e.get("tier", "?") for e in entries).most_common()),
        "families": dict(Counter(
            f for e in entries for f in e.get("families", ["?"])
        ).most_common(5)),
        "properties": {
            "fe": sum(1 for e in entries if e.get("formation_energy_per_atom") is not None),
            "eah": sum(1 for e in entries if e.get("energy_above_hull") is not None),
            "bg": sum(1 for e in entries if e.get("band_gap") is not None),
        },
    }
