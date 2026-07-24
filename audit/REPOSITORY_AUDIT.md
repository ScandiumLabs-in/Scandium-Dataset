# Repository Structure Audit

**Date:** 2026-07-21 23:36:29  

## Expected Files

| File | Present |
|------|---------|
| README.md            | ✅ |
| LICENSE              | ✅ |
| CITATION.cff         | ✅ |
| CHANGELOG.md         | ✅ |
| CODE_OF_CONDUCT.md   | ✅ |
| CONTRIBUTING.md      | ✅ |
| SECURITY.md          | ✅ |
| .gitignore           | ✅ |
| requirements.txt     | ✅ |
| Dockerfile           | ✅ |
| setup.py             | ✅ |
| pyproject.toml       | ✅ |
## Expected Directories

| Directory | Present |
|-----------|---------|
| docs/           | ✅ |
| audit/          | ✅ |
| benchmark/      | ✅ |
| examples/       | ✅ |
| scripts/        | ✅ |
| dataset/        | ✅ |
| api/            | ✅ |
| tests/          | ✅ |
| .github/        | ✅ |
| configs/        | ✅ |
| manifests/      | ❌ |
| releases/       | ❌ |
## Missing Items

**Missing directories:** manifests/, releases/

## Current Structure

```
📄 .gitignore
📄 CHANGELOG.md
📄 CITATION.cff
📄 CODE_OF_CONDUCT.md
📄 CONTRIBUTING.md
📄 DATASET_CARD.md
📄 Dockerfile
📄 KNOWN_ISSUES.md
📄 LICENSE
📄 MODEL_LEADERBOARD.md
📄 README.md
📄 RELEASES.md
📄 ROADMAP.md
📄 SECURITY.md
📄 TRUST_REPORT.md
📄 pyproject.toml
📄 requirements.txt
📄 setup.py
📁 .github/
📁 api/
📁 assets/
📁 audit/
📁 benchmark/
📁 configs/
📁 dataset/
📁 docs/
📁 examples/
📁 models/
📁 reports/
📁 scripts/
📁 tests/
📁 __init__.py
📁 test_dataset_integrity.py
📁 scandium_api.py
📁 BATTERY_AUDIT.md
📁 DATASET_BENCHMARK.md
📁 DUPLICATE_AUDIT.md
📁 QUALITY_AUDIT.md
📁 RELEASE_AUDIT.md
📁 REPAIR_AUDIT.md
📁 REPOSITORY_AUDIT.md
📁 REPRODUCIBILITY_AUDIT.md
📁 SCIENTIFIC_AUDIT.md
📁 SOURCE_AUDIT.md
📁 STATISTICAL_AUDIT.md
📁 STRUCTURE_AUDIT.md
  📁 source_reports.json
  📁 family_reports.json
  📁 cross_source_agreement.json
  📁 dataset_census.json
  📁 dataset_census_v3.json
  📁 strict_gold_summary.json
  📁 quality_calibration.json
  📁 coordinate_repair_20260721_200923.json
  📁 oqmd_symmetry_pass.json
📁 evaluate.py
  📁 results_mean_baseline_20260721_225304.json
  📁 results_median_baseline_20260721_225434.json
📁 battery_candidate_subset_v1.json
📁 solid_electrolyte_candidate_subset_v1.json
📁 entries_final_v3.json
  📁 chemistry_held_out.json
  📁 composition_held_out.json
  📁 family_held_out.json
  📁 manifest.json
  📁 random_80_10_10.json
  📁 battery_subsets.json
  📁 cross_source_agreement.json
  📁 dataset_census.json
  📁 dataset_census_v3.json
  📁 family_reports.json
  📁 quality_calibration.json
  📁 source_reports.json
  📁 strict_gold_summary.json
  📁 MANIFEST_v3.json
  📁 RELEASE_v0.0.md
📁 pipeline_config.json
📁 benchmark.md
📁 citation.md
📁 data_card.md
```
**Repository Structure Score:** 9.2/10 (22/24)

