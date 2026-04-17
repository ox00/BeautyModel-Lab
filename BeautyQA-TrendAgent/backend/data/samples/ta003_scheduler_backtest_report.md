# TA-003 Scheduler Backtest Report

## Scope
- Module: `BeautyQA-TrendAgent/backend`
- Task: `TA-003`
- Backtest script:
  - `scripts/run_ta003_scheduler_backtest.py`
- Seed input:
  - `data/eval/trend_monitor/2026-04-13-trend-keyword-seed.csv`

## What This Layer Checks
- scheduler turns one platform-aware query into one crawl task
- each generated task carries a single query payload in `keywords_for_crawler`
- task config includes trace and governance fields needed for replay and review
- target-platform filtering works when the scheduler is called with a specific platform

## Result Summary
- all-platform scheduled count: `16`
- target-platform (`xhs`) scheduled count: `8`
- all task configs complete: `true`
- all tasks use single-query payload: `true`
- reference sources never scheduled as crawler targets: `true`
- target-platform filter valid: `true`

## Representative Findings
- `外泌体`
  - generated `xhs` tasks: `外泌体`, `外泌体 护肤`, `外泌体 趋势`
  - generated `dy` tasks: `外泌体`, `外泌体 趋势`, `外泌体 成分`
  - keeps `industry_news` only in `reference_sources`
- `面部清洁`
  - generates category-oriented task queries separately per platform
  - keeps `taobao` only in `reference_sources`
- `快速美白`
  - generates risk-oriented task queries
  - sets `review_needed=true` in task config

## Open Risks
- this backtest validates scheduler output shape, not real vendor subprocess execution
- repeated scheduling windows still need stronger dedup policy at persistence level
