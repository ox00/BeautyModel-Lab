# BeautyQA-core

QA core implementation for retrieval/orchestration.

## QA-003 Delivery

This module now focuses on first-party `trend_signal` ingestion + retrieval/evidence assembly boundary:
- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/check-issue/30-qacore/QA-003-trend-evidence-boundary-tightening.md`

Key boundary guarantees:
- runtime reads first-party `trend_signal` contract data only
- retrieval exposes freshness/confidence/risk metadata + evidence quality flags
- graceful fallback is exposed via behavior flags and metadata
- final safety/compliance answer policy is pluggable via hook (not hard-coded here)
- no vendor crawler runtime dependency
- no direct vendor raw table usage
- legacy CSV compatibility is migration-only (`from_legacy_csv_for_migration`)

## Run Backtest

```bash
cd BeautyQA-core
PYTHONPATH=src python3 scripts/run_backtest_qa003.py
```

## Run Tests

```bash
cd BeautyQA-core
PYTHONPATH=src python3 -m pytest -q
```
