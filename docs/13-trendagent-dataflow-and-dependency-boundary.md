# TrendAgent Dataflow And Dependency Boundary

## Purpose

This document explains how `BeautyQA-TrendAgent/` currently works, which parts are project-owned, which parts depend on `BeautyQA-vendor/MediaCrawler/`, and where future changes should be applied first.

The goal is to make later design review easier:
- what we can safely change inside first-party code
- what is tightly coupled to the vendor crawler
- what should be treated as a data contract

## Current Module Scope

`BeautyQA-TrendAgent/` currently includes:
- keyword intake and scheduling
- LLM-based keyword expansion
- crawl task creation and orchestration
- subprocess-based crawler invocation
- raw data cleaning and normalized storage
- API and Celery task entrypoints

It does not implement a crawler engine itself.

Actual crawling is delegated to `BeautyQA-vendor/MediaCrawler/`.

## High-Level Runtime Flow

```text
trend-keyword.csv / trend_keywords table
  -> TrendAgent
  -> SchedulerAgent
  -> KeywordExpanderAgent
  -> CrawlTask records
  -> CrawlerAdapter / CrawlerProcessManager
  -> MediaCrawler subprocess
  -> raw MediaCrawler PostgreSQL tables
  -> CleaningAgent
  -> cleaned_trend_data table + local JSON output
```

## Data Acquisition Flow

### 1. Keyword source

Keyword input currently comes from:
- `backend/config/trend-keyword.csv`
- `trend_keywords` table after CSV import

Relevant files:
- `BeautyQA-TrendAgent/backend/app/config/settings.py`
- `BeautyQA-TrendAgent/backend/app/domain/services/keyword_service.py`
- `BeautyQA-TrendAgent/backend/run_pipeline.py`

### 2. Scheduling layer

Scheduling is split into two roles:

- `TrendAgent`
  - finds keywords that are due for crawling
- `SchedulerAgent`
  - expands keywords
  - parses crawlable platforms
  - creates `crawl_tasks`
  - dispatches crawl and clean chains

Relevant files:
- `BeautyQA-TrendAgent/backend/app/agents/trend_agent.py`
- `BeautyQA-TrendAgent/backend/app/agents/scheduler_agent.py`
- `BeautyQA-TrendAgent/backend/app/tasks/schedule_tasks.py`

### 3. Crawl execution layer

`BeautyQA-TrendAgent/` does not import crawler internals directly.

Instead it:
- builds a CLI command
- points the subprocess cwd at `BeautyQA-vendor/MediaCrawler`
- injects DB env vars expected by MediaCrawler
- waits for completion

Relevant files:
- `BeautyQA-TrendAgent/backend/app/config/settings.py`
- `BeautyQA-TrendAgent/backend/app/infrastructure/crawler/config_mapper.py`
- `BeautyQA-TrendAgent/backend/app/infrastructure/crawler/process_manager.py`
- `BeautyQA-TrendAgent/backend/app/infrastructure/crawler/adapter.py`
- `BeautyQA-TrendAgent/backend/app/agents/crawler_agent.py`

### 4. Raw data dependency

After crawling, `CleaningAgent` reads raw rows from MediaCrawler-owned PostgreSQL tables such as:
- `xhs_note`
- `douyin_aweme`
- `bilibili_video`
- `weibo_note`

This means the cleaning layer depends on the vendor crawler's raw table names and column names.

Relevant file:
- `BeautyQA-TrendAgent/backend/app/agents/cleaning_agent.py`

### 5. Cleaned output

Cleaned outputs are stored in:
- `cleaned_trend_data` table
- local JSON files under `backend/data/cleaned/{platform}/`

Relevant files:
- `BeautyQA-TrendAgent/backend/app/infrastructure/database/models.py`
- `BeautyQA-TrendAgent/backend/app/agents/cleaning_agent.py`

## Dependency Boundary

## First-party code

These parts are project-owned and are the right place for most future changes:

- keyword schema and import flow
- scheduling logic
- keyword expansion strategy
- crawl task config
- subprocess orchestration
- cleaning logic
- normalized storage schema
- API and Celery orchestration

Main directory:
- `BeautyQA-TrendAgent/`

## Vendor dependency

These parts should be treated as external dependency surface:

- crawler CLI entrypoint
- supported CLI arguments
- platform crawler implementations
- raw table creation and naming
- raw table field naming
- login / browser / platform automation behavior

Main directory:
- `BeautyQA-vendor/MediaCrawler/`

## Shared dependency contract

The real boundary is not “import” only. It is a runtime contract:

### Contract A: filesystem path

`BeautyQA-TrendAgent` needs a valid path to the vendor crawler root.

Current contract:
- `settings.MEDIACRAWLER_DIR`

If this path changes, subprocess execution breaks.

### Contract B: CLI contract

`BeautyQA-TrendAgent` assumes MediaCrawler accepts arguments like:
- `--platform`
- `--lt`
- `--type search`
- `--keywords`
- `--save_data_option`
- `--headless`
- `--get_comment`
- `--get_sub_comment`
- `--max_comments_count_singlenotes`
- `--max_concurrency_num`

If vendor CLI changes, command building breaks.

### Contract C: environment variable contract

`BeautyQA-TrendAgent` injects DB env vars for the subprocess:
- `POSTGRES_DB_HOST`
- `POSTGRES_DB_PORT`
- `POSTGRES_DB_USER`
- `POSTGRES_DB_PWD`
- `POSTGRES_DB_NAME`

If vendor DB config stops reading these env vars, DB writeback breaks.

### Contract D: raw database schema

`CleaningAgent` queries vendor-owned raw tables directly.

If vendor renames tables or columns, cleaning breaks even if crawling still succeeds.

This is currently the strongest coupling point.

## Changeability Map

### Safe to change inside `BeautyQA-TrendAgent`

- keyword scoring and due-keyword selection
- `trend-keyword.csv` / `trend_keywords` management
- keyword expansion strategy and prompt integration
- platform filtering logic
- task batching strategy
- crawl retry strategy
- cleaned output schema
- API shape
- local result storage format

### Change with care

- `CrawlerConfigMapper`
- `CrawlerProcessManager`
- DB env injection logic
- platform code normalization between business names and CLI names

These are still first-party, but directly touch the vendor runtime contract.

### Do not change casually unless crawler behavior must change

- files under `BeautyQA-vendor/MediaCrawler/`
- vendor raw table names
- vendor CLI interface assumptions without validation

## Current Implementation Findings

### 1. The vendor boundary is structurally improved

The current repo layout is better than before:
- first-party orchestration lives in `BeautyQA-TrendAgent/`
- external crawler code lives in `BeautyQA-vendor/MediaCrawler/`

This is the correct baseline for future refactor work.

### 2. The coupling is still runtime-heavy

Even without direct imports from vendor internals, the current system still depends on:
- vendor CLI args
- vendor working directory
- vendor raw DB schema

So the boundary is cleaner at the repo level, but still fairly tight at runtime.

### 3. Raw-table coupling is the main redesign target

The most fragile dependency is not subprocess invocation.
It is `CleaningAgent` reading vendor-owned raw tables directly.

If later you want cleaner modularity, this is the first place to redesign.

A better future direction would be:
- add a first-party raw ingestion adapter layer
- map vendor raw data into project-owned raw schema first
- run cleaning only against project-owned raw schema

### 4. Not all suggested platforms are crawlable

Current keyword schema supports:
- `industry_news`
- `taobao`

But the crawler adapter explicitly filters these out because MediaCrawler does not crawl them.

That means:
- the keyword system is broader than the actual crawler engine
- scheduling logic must keep handling “data source platform” and “crawlable platform” separately

### 5. `max_notes_count` is stored but not a real crawler control

The task schema stores `max_notes_count`, but current CLI integration does not support that control in MediaCrawler.

In this pass, the runtime bug from passing that field into `CrawlRequest` has been removed.

But the design question remains:
- either drop this field from the first-party task model
- or support it only after vendor-level capability is confirmed

## Suggested Future Modification Order

If the team wants to improve `BeautyQA-TrendAgent`, the recommended order is:

1. stabilize first-party keyword input contract
2. align keyword expansion with `data/eval/trend_monitor/`
3. formalize a first-party raw ingestion layer
4. reduce direct dependence on vendor raw table names
5. only then consider replacing or extending the crawler engine

## Practical Boundary Rule

When discussing future changes, use this rule:

- if the change is about scheduling, keyword selection, expansion, cleaning, storage, or API behavior, change `BeautyQA-TrendAgent/`
- if the change is about browser automation, platform crawling mechanics, or vendor raw storage behavior, treat it as `BeautyQA-vendor/MediaCrawler/` work
- if the change crosses both, design the contract first before touching code
