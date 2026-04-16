# TA-002 Backtest Report

## Scope
- Module: `BeautyQA-TrendAgent/backend`
- Task: `TA-002`
- Sample input:
  - `data/pipeline_samples/trend_signal/sample_cleaned_records.json`

## What Changed
- `trend_signal` generation now groups multiple cleaned records into one first-party signal record.
- grouping rule is deterministic:
  - `normalized_keyword + topic_cluster + trend_type + source_platform`
- output includes:
  - `support_count`
  - `evidence_ids`
  - `aggregation_method`
  - explicit `confidence` / `risk_flag`
  - run summary in JSON envelope

## Sample Result
- cleaned input count: `6`
- generated signal count: `4`
- max support count: `2`
- shared grouped output:
  - `data/pipeline_samples/trend_signal/trend_signal_first_party_sample.json`
- shared QA-consumable contract sample:
  - `data/pipeline_samples/trend_signal/trend_signal_first_party_sample.csv`

## Representative Grouped Signal
- `外泌体`
  - support count: `2`
  - source platform: `xiaohongshu`
  - confidence: `medium`
  - risk flag: `medium`

## Determinism Note
- the same sample cleaned input is grouped with a fixed sort rule
- representative record selection uses score / timestamp / id ordering
- run summary marks this implementation as `deterministic: true`

## Open Risks
- confidence / score rules are still heuristic `v0.2`
- current runtime persistence is JSON-file-backed, not yet a hardened repository/table
- grouping currently uses one platform within one signal; cross-platform fusion is intentionally deferred
