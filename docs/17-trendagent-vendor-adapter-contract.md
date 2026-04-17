# TrendAgent Vendor Adapter Contract

## Purpose

This document defines the stable coordination boundary between:
- `BeautyQA-TrendAgent/`
- `BeautyQA-vendor/MediaCrawler/`

The point is to make the crawler line easier to maintain without pushing vendor-specific details upward into TrendAgent scheduling or QA integration.

## Core Position

TrendAgent owns:
- keyword strategy
- task generation
- scheduler policy
- first-party cleaning and `trend_signal` output
- task traceability and replayability

Vendor owns:
- crawler engine implementation
- browser automation
- platform-specific crawling logic
- vendor raw table creation and storage details

The adapter layer is the only place where these two sides should touch directly.

## The Four Active Contracts

### 1. Path Contract

TrendAgent assumes the vendor crawler root exists at:
- `settings.MEDIACRAWLER_DIR`

If this path is wrong, subprocess execution fails before crawling starts.

First-party files involved:
- `BeautyQA-TrendAgent/backend/app/config/settings.py`
- `BeautyQA-TrendAgent/backend/app/infrastructure/crawler/config_mapper.py`
- `BeautyQA-TrendAgent/backend/app/infrastructure/crawler/process_manager.py`

### 2. CLI Contract

TrendAgent currently assumes the vendor CLI still accepts these arguments:
- `--platform`
- `--lt`
- `--type`
- `--keywords`
- `--save_data_option`
- `--headless`
- `--get_comment`
- `--get_sub_comment`
- `--max_comments_count_singlenotes`
- `--max_concurrency_num`
- `--init_db`

This is the direct dependency surface between `CrawlerConfigMapper` and vendor `cmd_arg/arg.py`.

If vendor renames or removes these arguments, TrendAgent command building breaks.

### 3. Environment Contract

TrendAgent assumes the vendor crawler still reads PostgreSQL config from environment variables:
- `POSTGRES_DB_HOST`
- `POSTGRES_DB_PORT`
- `POSTGRES_DB_USER`
- `POSTGRES_DB_PWD`
- `POSTGRES_DB_NAME`

This matters because TrendAgent injects runtime env vars when starting the subprocess.
If vendor stops reading those env vars, crawling may still run, but raw-data writeback can silently break.

### 4. Raw Schema Contract

TrendAgent cleaning currently reads vendor-owned raw tables directly.
This is the tightest runtime coupling.

Current required raw tables:
- `xhs_note`
- `douyin_aweme`
- `bilibili_video`
- `weibo_note`

If vendor changes these table names or key fields, the crawl step may still succeed while cleaning fails afterward.

## Coordination Lines

### Line A: TrendAgent -> QA

This line should stay first-party and contract-based.
QA should only see:
- `trend_signal`
- first-party samples
- first-party schema / contract docs

Relevant docs:
- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/16-trend-signal-to-qa-usage-guide.md`

### Line B: TrendAgent -> Vendor Crawler

This line should stay adapter-based.
TrendAgent should not leak vendor crawler assumptions into:
- keyword strategy docs
- QA data contract
- QA runtime integration

The adapter layer should absorb:
- platform code mapping
- CLI shape
- subprocess cwd / env setup
- raw-table dependency detection

## What TA-003 Changes Here

`TA-003` does not change vendor code.
It changes first-party preparation before the adapter layer:
- platform-aware keyword execution planning
- target / reference separation
- one query per crawl task
- better task trace fields

This is the correct direction because it improves first-party control without increasing vendor coupling.

## Required Stability Checks

Before treating the crawler line as stable, run three types of checks:

### A. First-party rule backtest
- `scripts/run_ta003_backtest.py`

### B. First-party scheduler backtest
- `scripts/run_ta003_scheduler_backtest.py`

### C. Vendor contract check
- `scripts/run_trendagent_vendor_contract_check.py`

These checks should be considered the minimum change gate for adapter-related work.

## Current Weak Point

The weakest dependency is not subprocess invocation itself.
The weakest dependency is direct cleaning against vendor raw tables.

That means the future hardening order should be:
1. keep adapter contract visible and testable
2. detect vendor schema drift earlier
3. add a first-party raw-ingestion adapter if needed
4. only then consider larger crawler refactors

## Suggested Near-Term Hardening

### 1. Add scheduler-level regression coverage
This is already started in `TA-003`.
Keep extending it before changing more crawler logic.

### 2. Add vendor contract checks to every adapter-related change
Any change touching:
- `config_mapper.py`
- `adapter.py`
- `process_manager.py`
- `cleaning_agent.py`

should rerun the contract check script.

### 3. Add one small real runtime smoke gate
Not a benchmark.
Just enough to prove the adapter still works end to end.

### 4. Consider a first-party raw snapshot layer later
If vendor table drift becomes frequent, the next architectural move should be:
- vendor raw tables
- first-party raw snapshot / normalization layer
- cleaning against first-party raw schema

That would reduce the strongest current coupling point.

## Working Rule

When a future change is proposed, classify it first:
- first-party scheduling change
- adapter contract change
- vendor crawler change
- QA contract change

Do not mix these categories in one implementation task unless absolutely necessary.
