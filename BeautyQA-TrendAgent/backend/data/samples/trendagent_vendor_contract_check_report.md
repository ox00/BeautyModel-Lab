# TrendAgent Vendor Contract Check Report

## Scope
- Module boundary:
  - `BeautyQA-TrendAgent/`
  - `BeautyQA-vendor/MediaCrawler/`
- Check script:
  - `scripts/run_trendagent_vendor_contract_check.py`

## What Was Checked
- vendor root path and key entry files exist
- vendor CLI still exposes the arguments expected by `CrawlerConfigMapper`
- vendor PostgreSQL env variables still exist in `config/db_config.py`
- vendor raw table names still match the tables queried by `CleaningAgent`
- a sample crawl command can still be built with the current adapter code

## Result Summary
- path contract ok: `true`
- CLI contract ok: `true`
- env contract ok: `true`
- raw schema contract ok: `true`
- all contracts ok: `true`

## Confirmed Dependency Surface
- path:
  - `settings.MEDIACRAWLER_DIR`
- CLI args:
  - `--platform`, `--lt`, `--type`, `--keywords`, `--save_data_option`, `--headless`, `--get_comment`, `--get_sub_comment`, `--max_comments_count_singlenotes`, `--max_concurrency_num`, `--init_db`
- env vars:
  - `POSTGRES_DB_HOST`, `POSTGRES_DB_PORT`, `POSTGRES_DB_USER`, `POSTGRES_DB_PWD`, `POSTGRES_DB_NAME`
- raw tables:
  - `xhs_note`, `douyin_aweme`, `bilibili_video`, `weibo_note`

## Open Risks
- this check proves static contract consistency, not real crawl success on a live platform
- the strongest runtime coupling remains direct cleaning against vendor raw tables
