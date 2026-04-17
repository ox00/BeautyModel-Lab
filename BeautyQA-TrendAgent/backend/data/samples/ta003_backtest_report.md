# TA-003 Backtest Report

## Scope
- Module: `BeautyQA-TrendAgent/backend`
- Task: `TA-003`
- Seed input:
  - `data/eval/trend_monitor/2026-04-13-trend-keyword-seed.csv`
- Backtest script:
  - `scripts/run_ta003_backtest.py`

## What Changed
- keyword expansion is no longer a single flattened keyword list shared by every platform
- TrendAgent now builds a first-party `keyword execution plan`
- crawl targets and reference sources are split explicitly before task creation
- scheduler now creates one crawl task per platform-aware query instead of sending one merged keyword bundle everywhere
- task config now carries origin fields such as `original_keyword`, `query_origin`, `based_on`, `reference_sources`, and `task_dedup_key`

## Backtest Coverage
- `KW_0002` `外泌体`
  - verifies `industry_news` stays reference-only
  - verifies `xiaohongshu` and `douyin` get different rule-layer queries
- `KW_0031` `面部清洁`
  - verifies `taobao` stays reference-only
  - verifies category-oriented terms are converted into crawlable platform packages
- `KW_0040` `快速美白`
  - verifies high-risk monitoring terms are marked `review_needed=true`
  - verifies risk-oriented query expansion is preserved in crawler task generation

## Result Summary
- selected case count: `3`
- reference sources scheduled as crawl targets: `false`
- platform filtering valid: `true`
- platform-specific packages present: `true`

## Representative Before / After
- before:
  - one merged string like `快速美白,7天美白,28天焕白`
  - same query bundle sent to every crawl target
  - `taobao` or `industry_news` only filtered later, not expressed as a first-party execution boundary
- after:
  - `douyin`: `快速美白`, `快速美白 风险`
  - `xiaohongshu`: `快速美白`, `快速美白 风险`
  - `taobao`: kept in `reference_packages`, not scheduled into crawler tasks

## Engineering Impact
- task generation is now easier to trace and replay
- crawler-side execution receives one query per task, which is closer to the existing subprocess isolation note in the adapter layer
- future agent work can add stronger dedup, persistence, or QA-facing monitoring without changing vendor crawler code

## Open Risks
- this is still rule-first `v1`; platform query quality will need iterative calibration with real crawl yield
- scheduler does not yet enforce cross-run dedup at the database level; repeated scheduling windows can still create semantically similar tasks
- LLM supplements are optional and currently best-effort; offline mode still relies fully on deterministic rules
