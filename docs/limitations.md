# Limitations

## Known Issues

### 1. 39,276 Gold entries below Strict Gold threshold
39,276 base Gold entries have quality scores 70-79. They pass the base Gold
gate (≥70) but not Strict Gold (≥80). These entries are:
- Mostly OQMD (recently promoted to Gold by symmetry pass)
- Have valid structures and complete metadata
- But lack the metadata completeness needed for higher scores

### 2. JARVIS missing energy_above_hull (100%)
All 25,673 JARVIS entries lack energy_above_hull. This is a fundamental
limitation — JARVIS does not compute convex hull energies. These entries:
- Cannot contribute to EaH prediction tasks
- Are still valid for FE and BG prediction
- Can still achieve Gold tier (Gate 7 passes with null EaH)

### 3. Garnet family: 23 entries
Only 23 garnet-type solid electrolytes (LLZO, etc.) in the dataset. This is
insufficient for ML training. Garnet-specific models are not feasible with
current data.

### 4. 16 OQMD entries without space group
Spglib failed to find a space group for 16 OQMD entries. These remain in
Validated/Raw tier — cannot enter Gold without space group.

### 5. No experimentally validated entries
All entries are DFT-computed. No experimental validation is included. The
quality score measures DFT self-consistency, not experimental accuracy.

### 6. No battery-specific properties
The dataset does not include:
- Ionic conductivity
- Migration barriers
- Electrochemical stability windows
- Interface compatibility metrics

These are planned for future releases.

### 7. Source imbalance
OQMD dominates at 64.4%. Models trained on the full dataset may be biased
toward OQMD's distribution of structures and properties.

## Known Non-issues

These were flagged during development and are now resolved:
- OQMD space group missing → computed (171,764/171,780)
- OQMD volume = 0 → all fixed (47,807 entries)
- OQMD density = 0 → all computed (47,807 entries)
- JARVIS volume = 0 → all extracted (25,673 entries)
- OQMD coordinate artifact → repaired (137,405 entries)

## Intended Use

✅ Materials property prediction (FE, EaH, BG)
✅ Battery materials screening
✅ Cross-source DFT comparison studies
✅ Representation learning pre-training
✅ Transfer learning to experimental data

## Not Intended Use

❌ Predicting properties not in the dataset
❌ Modelling without acknowledging known limitations
❌ Claiming experimental accuracy for DFT-predicted properties
❌ Using without citation
