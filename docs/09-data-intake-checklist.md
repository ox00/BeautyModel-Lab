# 09 - Data Intake Checklist

## 1. Purpose
This checklist defines how the team should receive, verify, clean, and hand off each beauty data batch for the MVP pipeline.

## 2. Current Batch
- Batch name: `baseline-0312-v1`
- Raw package: `data/base-line-0312/`
- Cleaning script: `scripts/clean_baseline_0312.py`
- Delivery package: `data/deliveries/2026-03-14-baseline-v1/`

## 3. Intake Scope
- `P0`: `product_sku`, `review_feedback`, `trend_signal`, `ingredient_knowledge`, `compliance_rule`
- `P1`: `review_feedback_raw`
- `REF`: `compliance_source_manifest`

## 4. Intake Steps
1. Confirm the raw batch folder is complete and versioned under `data/`.
2. Run `python3 scripts/clean_baseline_0312.py`.
3. Check `data/deliveries/2026-03-14-baseline-v1/reports/quality_report.md`.
4. Confirm `data_manifest.csv` row counts match the generated files.
5. Share only `P0` files with the general team workspace.
6. Keep `P1` files limited to the technical/data owners.
7. Use `REF` files only as source references, not training data.

## 5. Batch Acceptance Gates
- `product_sku.product_id` duplicate count = `0`
- `review_feedback.review_id` duplicate count = `0`
- `trend_signal.trend_id` duplicate count = `0`
- Required timestamps are normalized to `YYYY-MM-DD HH:MM:SS`
- `review_feedback.rating_bucket` may be `unknown`, but must not be null
- No PII fields are exported into `P0`

## 6. Mapping Rules
- `spu_id` is normalized to `product_id`
- `price_band` is preserved and split into `price_min` / `price_max`
- Review tags are normalized with `|` separator
- `trend_id` is generated deterministically from source fields
- Monthly trend buckets such as `202602` are normalized to `2026-02-01 00:00:00`
- Ingredient workbook is parsed via XML due source workbook style issues

## 7. Open Issues
- `review_feedback.rating_bucket` is missing in the source batch
- `trend_signal` uses monthly growth instead of short-window growth
- `ingredient_knowledge.inci_name` still has a small number of missing values
- `compliance_rule` is now available as a first-pass structured table, but obligation taxonomy and clause normalization are not complete yet

## 8. Suggested Next Batch Upgrades
- Normalize `compliance_rule` into obligation tags, scope taxonomy, and stronger article-level lineage
- Add `profile_bucket` once weak-profile rules are frozen
- Add holdout split generation for `P2` evaluation package
- Standardize trend windows to `7d` and `30d` together
