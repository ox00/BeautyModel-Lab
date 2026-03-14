# Baseline 0312 Delivery

This folder contains the cleaned delivery package for the baseline batch imported on 2026-03-14.

## Structure
- `p0/`: safe structured package for training and team sharing
- `p1/`: restricted package containing raw review text
- `refs/`: source manifests and reference-only materials
- `reports/`: quality report and batch manifest

## Notes
- `review_feedback` source ratings are empty in this batch; the cleaned package keeps `rating_bucket=unknown`.
- `trend_signal` source uses monthly growth and monthly capture buckets; cleaned timestamps are normalized to the first day of the month.
- `ingredient_knowledge` is parsed from the source workbook via XML because the original workbook styles are not fully compatible with `openpyxl` read mode.
