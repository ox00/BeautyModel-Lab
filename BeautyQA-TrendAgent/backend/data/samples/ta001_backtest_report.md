# TA-001 Backtest Report

## Scope
- Module: `BeautyQA-TrendAgent/backend`
- Contract refs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`

## Layer A - Contract Check
- Required fields in output path are covered by `build_trend_signal_record`:
  - `signal_id`, `keyword_id`, `crawl_task_id`, `normalized_keyword`, `topic_cluster`, `trend_type`, `signal_summary`, `signal_evidence`, `source_platform`, `source_url`, `trend_score`, `confidence`, `risk_flag`, `observed_at`, `fresh_until`
- Recommended fields included:
  - `report_id`, `signal_period_type`, `signal_period_label`, `source_scope`, `support_count`, `evidence_ids`, `aggregation_method`, `version`

## Layer B - Pipeline Check
- Existing path: `crawl_platform -> process_trend_data(cleaning)`
- New path: `crawl_platform -> process_trend_data(cleaning + signal generation)`
- Signal generation entrypoint:
  - `app/agents/signal_agent.py`
- First-party output persistence:
  - `backend/data/trend_signal/{platform}/*.json`

## Layer C - Boundary Check
- No change under `BeautyQA-vendor/MediaCrawler/`
- No change under `BeautyQA-core/`
- QA can consume first-party `trend_signal` JSON/API without vendor raw table names
- Internal cleaning still reads vendor raw tables as upstream implementation detail (unchanged)

## Layer D - Output Quality Check
- Sample output count: 1
- Sample file:
  - `backend/data/samples/sample_trend_signal_ta001.json`
- Representative `source_url` fallback format:
  - `about:source/{platform}/{source_id}` when raw URL unavailable

## Result
- TA-001 passes as a minimal, traceable first-party trend_signal output path scaffolding.

## Open Risks
- `source_url` quality depends on raw_data carrying URL; currently fallback placeholder may reduce downstream citation quality.
- `trend_signal` is currently file-backed JSON output, not a dedicated DB table; high-volume querying may need repository/storage hardening.
- confidence/risk rules are heuristic v0 and should be calibrated with domain review before production use.
