# TA-003 Regression Backtest Plan

## Purpose

This file defines the minimum regression coverage required before treating `TA-003` as stable enough to sit on the TrendAgent mainline.

The goal is not only to prove that keyword expansion looks reasonable.
The goal is to prove that:
- structured keyword metadata is translated into stable crawl tasks
- target / reference boundaries stay intact
- scheduler output remains explainable after future changes

## Why This Backtest Exists

`TA-003` changes a production-facing orchestration layer.
It touches:
- keyword expansion behavior
- platform-level task generation
- crawler input payload shape
- reference-source filtering

Because this is a takeover of an existing code path, regression coverage matters more than adding more features right now.

## Backtest Layers

### Layer 1: Rule / Planning Backtest

Script:
- `scripts/run_ta003_backtest.py`

Checks:
- `crawl_targets` and `reference_sources` are separated before scheduling
- platform-specific query packages are present
- high-risk keywords preserve `review_needed=true`
- reference-only sources never appear in scheduled crawl targets

Artifacts:
- `BeautyQA-TrendAgent/backend/data/samples/ta003_backtest_report.json`
- `BeautyQA-TrendAgent/backend/data/samples/ta003_backtest_report.md`

### Layer 2: Scheduler Task Generation Backtest

Script:
- `scripts/run_ta003_scheduler_backtest.py`

Checks:
- one platform-aware query becomes one crawl task
- each task carries a single query payload in `keywords_for_crawler`
- task config includes trace fields such as:
  - `original_keyword`
  - `query_origin`
  - `based_on`
  - `reference_sources`
  - `task_dedup_key`
- target-platform filtering works when the scheduler is invoked with a specific platform

This layer should remain vendor-independent.
It is testing first-party scheduling behavior, not actual crawling.

### Layer 3: Runtime Smoke Checklist

This layer is intentionally small.
It should use one real platform and one or two keywords only.

Required checks:
- `CrawlTask` can be created and dispatched
- `CrawlerAdapter` can build the vendor CLI command
- vendor subprocess can start
- raw rows are written into vendor tables
- `CleaningAgent` can read those rows
- first-party `trend_signal` output is generated

This is not a benchmark.
This is a minimal runtime confidence gate.

## Suggested Commands

```bash
python3 scripts/run_ta003_backtest.py
python3 scripts/run_ta003_scheduler_backtest.py
python3 scripts/run_trendagent_vendor_contract_check.py
```

For runtime smoke, use the existing queue / API / Celery path rather than inventing a separate one-off path.

## Current Coverage Cases

Current rule and scheduler backtests should at least keep these representative cases:
- `KW_0002` `外泌体`
  - trend discovery
  - platform split + `industry_news` reference-only
- `KW_0031` `面部清洁`
  - category-oriented keyword
  - `taobao` reference-only
- `KW_0040` `快速美白`
  - high-risk monitoring
  - review gating and risk-oriented expansion

## Release Gate For TA-003

Treat `TA-003` as ready for mainline only when all of the following are true:
- rule backtest passes
- scheduler backtest passes
- vendor contract check passes
- one minimal runtime smoke passes on a real crawler path
- no vendor code change is required for the first-party task generation logic

## What Is Still Out Of Scope

This backtest plan does not yet solve:
- database-level task deduplication
- multi-run crawl yield scoring
- automatic expansion quality pruning based on downstream content quality
- broader benchmark design for QA answer quality

Those belong to later hardening or evaluation tasks.
