# Evaluation Docs

This folder stores the active evaluation documentation set for the MVP.

## Purpose
- Define how the team designs, reviews, freezes, and uses the benchmark set.
- Keep quality-control rules stable across engineering iterations.
- Separate evaluation rules from the machine-readable case assets stored under `data/eval/`.

## Files
1. `01-benchmark-scope.md` - benchmark goals, split design, and coverage rules
2. `02-case-schema.md` - case fields and annotation requirements
3. `03-scoring-rubric.md` - metric definitions and scoring criteria
4. `04-release-gates.md` - release decision rules tied to benchmark results
5. `05-experiment-log-template.md` - version-comparison and experiment logging template

## Working rule
- `docs/evaluation/` is the policy layer.
- `data/eval/` is the asset layer for frozen cases and result files.
- New benchmark versions should update both the case assets and the corresponding experiment log.
