# Eval Assets

This folder stores machine-readable evaluation assets and result files.

## Structure
- `benchmark_dev_v0_seed.csv` - editable starter case bank for team iteration
- `benchmark_holdout_v0_seed.csv` - editable starter holdout-style case bank
- `drafts/` - raw question drafts and PM input materials
- `review/` - review outputs, triage tables, and structured assessment files
- `trend_monitor/` - report registry, keyword seeds, and agent-facing trend monitoring inputs
- `templates/` - reusable benchmark templates
- `results/` - versioned evaluation outputs

## Working rule
- `*_seed.csv` files are drafting assets, not frozen release benchmarks.
- Files under `drafts/` are input materials and should stay editable.
- Files under `review/` are intermediate review artifacts and should not be treated as frozen benchmarks.
- Files under `trend_monitor/` are structured inputs for trend-monitoring agents and keyword collection workflows.
- Frozen benchmark assets should be versioned under this folder.
- The policy and rubric definitions live under `docs/evaluation/`.
- Any benchmark asset change should be reflected in the experiment log and release review.
