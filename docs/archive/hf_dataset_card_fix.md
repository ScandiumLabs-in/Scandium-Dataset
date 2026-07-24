> **Historical — superseded by v1.0.0 reframe. All instructions here have been applied to the current dataset card. Kept for changelog context only.**

# HF Dataset Card Fix Instructions

The HF page at https://huggingface.co/datasets/Scandium-Labs/Scandium-Dataset
currently shows:

- License badge: `cc-by-4.0` (IMPORTANT: this is misleading — see §License below)
- Tags: `solid-state batteries`, `materials science`, `DFT`, `battery materials`, `electrolyte`, `materials discovery`

## What to Fix on HF

### 1. License Tag (Critical)

**Change:** Remove the single `cc-by-4.0` license tag. If HF supports, use
multiple license tags or a custom descriptor.

**On the HF dataset page settings, set:**

```
license: other
license_name: Multi-source (see LICENSE_BREAKDOWN.md)
license_link: https://github.com/ScandiumLabs-in/Scandium-Dataset/blob/main/LICENSE_BREAKDOWN.md
```

**Do NOT use `cc-by-4.0` as the top-level license.** 64.4% of entries are
OQMD non-commercial only.

### 2. Update Dataset Description

Add this warning at the top of the README displayed on HF:

> ⚠️ **License Warning:** This dataset is a multi-source compilation with 3 different
> licenses. 64.4% of entries (OQMD) are non-commercial only. Each entry has a
> `license` field. See `LICENSE_BREAKDOWN.md` before commercial use.

### 3. Upload the New Files

These new/updated files should be pushed to the HF repo:

```
LICENSE_BREAKDOWN.md           ← NEW (critically important)
SOURCE_SNAPSHOTS.md            ← NEW
docs/battery_methodology.md    ← NEW
docs/related_work.md           ← NEW
docs/paper_outline.md          ← NEW
DATASET_CARD.md                ← UPDATED
CHANGELOG.md                   ← UPDATED
```

### 4. Sync the Dataset Files

The dataset files on HF should also be updated with the per-entry `license` field:

- `entries_final_v3.json` — each entry now has `"license": "CC-BY-4.0"|"CC0-1.0"|"OQMD-noncommercial"`
- `battery_candidate_subset_v1.json` — same
- `solid_electrolyte_candidate_subset_v1.json` — same

Re-upload these from the local copies.
