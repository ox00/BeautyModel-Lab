# Eval Assets

This folder stores machine-readable evaluation assets and result files.

## Structure
- `benchmark_dev_v0_seed.csv` - editable starter case bank for team iteration
- `benchmark_holdout_v0_seed.csv` - editable starter holdout-style case bank
- `templates/` - reusable benchmark templates
- `results/` - versioned evaluation outputs

## Working rule
- `*_seed.csv` files are drafting assets, not frozen release benchmarks.
- Frozen benchmark assets should be versioned under this folder.
- The policy and rubric definitions live under `docs/evaluation/`.
- Any benchmark asset change should be reflected in the experiment log and release review.
