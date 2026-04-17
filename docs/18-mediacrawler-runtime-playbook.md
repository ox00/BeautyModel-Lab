# MediaCrawler Runtime Playbook

This document standardizes how the team should run `BeautyQA-vendor/MediaCrawler/`
inside the shared repo environment.

## Why this exists

Recent runtime issues came from two sources:

1. manual runs did not inherit the same PostgreSQL target as `BeautyQA-TrendAgent`
2. team members were copying long commands and accidentally connecting to local `5432`
   instead of the Docker database on `5433`

The project should treat:

- `BeautyQA-TrendAgent/backend/.env` as the single source of truth for runtime DB config
- `scripts/run_mediacrawler.sh` as the standard manual entrypoint for vendor crawler smoke tests
- `scripts/run_platform_smoke.sh` as the fast smoke entrypoint for common team usage

## Fast smoke entrypoint

For common smoke checks, use the higher-level wrapper:

```bash
./scripts/run_platform_smoke.sh xhs
./scripts/run_platform_smoke.sh xhs dy bili
./scripts/run_platform_smoke.sh --fresh-login xhs
```

This wrapper:
- only requires platform codes such as `xhs`, `dy`, `bili`
- uses the project-tested default keywords per platform
- reuses `scripts/run_mediacrawler.sh` underneath
- is intended for repeatable smoke runs, not arbitrary crawler configuration

## Standard entrypoint

From the repo root:

```bash
./scripts/run_mediacrawler.sh --help
```

What the wrapper does:

- uses the shared Python at `./.venv/bin/python`
- loads `BeautyQA-TrendAgent/backend/.env` when present
- exports `POSTGRES_DB_*` defaults that match the Docker PostgreSQL runtime
- sets writable cache dirs for matplotlib/font cache side effects
- runs `BeautyQA-vendor/MediaCrawler/main.py`

Use `scripts/run_mediacrawler.sh` when you need full low-level control.
Use `scripts/run_platform_smoke.sh` when you just want to smoke one or more common platforms quickly.

## Shared environment baseline

Install shared dependencies from the repo root:

```bash
./.venv/bin/pip install -r requirements.txt
./.venv/bin/playwright install chromium
```

The canonical shared dependency entrypoint is:

- `requirements.txt`

That file delegates to:

- `BeautyQA-TrendAgent/requirements.txt`

This keeps one install command for the whole repo while preserving the existing
TrendAgent dependency manifest.

## Required local services

Before running any vendor smoke test:

```bash
docker compose -f BeautyQA-TrendAgent/backend/docker-compose.yml up -d
```

Expected runtime targets:

- PostgreSQL: `localhost:5433`
- Redis: `localhost:6379`

## Platform smoke workflow

Recommended execution order for the current team focus:

1. `xhs`
2. `dy`
3. `bili`

Reason:

- `xhs` is the most sensitive to login-state and browser-context problems
- `dy` adds local `node` / `pyexecjs` dependency requirements
- `bili` is still important, but usually lower risk than `xhs`

### XHS first login

```bash
./scripts/run_mediacrawler.sh \
  --platform xhs \
  --lt qrcode \
  --type search \
  --keywords "以油养肤" \
  --save_data_option postgres \
  --headless false \
  --get_comment false \
  --get_sub_comment false \
  --max_comments_count_singlenotes 2 \
  --max_concurrency_num 1
```

Use this only for first-time login-state creation or when the saved state is invalid.

### XHS login-state reuse

```bash
./scripts/run_mediacrawler.sh \
  --platform xhs \
  --lt cookie \
  --type search \
  --keywords "以油养肤" \
  --save_data_option postgres \
  --headless false \
  --get_comment false \
  --get_sub_comment false \
  --max_comments_count_singlenotes 2 \
  --max_concurrency_num 1
```

XHS success signals:

- browser starts successfully
- login state check returns `True` when using `--lt cookie`
- crawler reaches `Begin search Xiaohongshu keywords`
- process exits without Python exception

XHS database validation:

```bash
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select count(*) as xhs_note_count from xhs_note;"
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select note_id, left(title,40) as title, source_keyword from xhs_note order by id desc limit 5;"
```

### Douyin smoke

```bash
./scripts/run_mediacrawler.sh \
  --platform dy \
  --lt qrcode \
  --type search \
  --keywords "油敷法" \
  --save_data_option postgres \
  --headless false \
  --get_comment false \
  --get_sub_comment false \
  --max_comments_count_singlenotes 2 \
  --max_concurrency_num 1
```

Notes:

- local `node` must exist because Douyin helper code uses `pyexecjs`
- after first successful login, switch to `--lt cookie`
- first smoke should still use one keyword and no comments

Douyin login-state reuse:

```bash
./scripts/run_mediacrawler.sh \
  --platform dy \
  --lt cookie \
  --type search \
  --keywords "油敷法" \
  --save_data_option postgres \
  --headless false \
  --get_comment false \
  --get_sub_comment false \
  --max_comments_count_singlenotes 2 \
  --max_concurrency_num 1
```

Douyin success signals:

- browser starts successfully
- login state is accepted or reused without forcing a new full login
- crawler reaches search execution for the keyword
- process exits without Python exception

Douyin database validation:

```bash
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select count(*) as douyin_aweme_count from douyin_aweme;"
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select aweme_id, left(coalesce(title,''),40) as title, source_keyword from douyin_aweme order by id desc limit 5;"
```

### Bilibili smoke

```bash
./scripts/run_mediacrawler.sh \
  --platform bili \
  --lt qrcode \
  --type search \
  --keywords "以油养肤" \
  --save_data_option postgres \
  --headless false \
  --get_comment false \
  --get_sub_comment false \
  --max_comments_count_singlenotes 2 \
  --max_concurrency_num 1
```

Bilibili login-state reuse:

```bash
./scripts/run_mediacrawler.sh \
  --platform bili \
  --lt cookie \
  --type search \
  --keywords "以油养肤" \
  --save_data_option postgres \
  --headless false \
  --get_comment false \
  --get_sub_comment false \
  --max_comments_count_singlenotes 2 \
  --max_concurrency_num 1
```

Bilibili success signals:

- browser starts successfully
- login is accepted or reused
- crawler reaches search execution for the keyword
- process exits without Python exception

Bilibili database validation:

```bash
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select count(*) as bilibili_video_count from bilibili_video;"
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select video_id, left(coalesce(title,''),40) as title, source_keyword from bilibili_video order by id desc limit 5;"
```

## Validation checks

After a successful smoke run, confirm database writes on the Docker PostgreSQL instance:

```bash
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select count(*) from xhs_note;"
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select count(*) from douyin_aweme;"
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select count(*) from bilibili_video;"
```

## Smoke acceptance checklist

Treat a platform smoke as complete only if all items below are true:

1. the crawler command starts from `./scripts/run_mediacrawler.sh`
2. the platform login succeeds or a saved login state is reused
3. the run reaches the actual keyword search stage
4. the run exits without Python traceback
5. the expected PostgreSQL table row count increases or at least contains the target `source_keyword`
6. the latest rows look structurally correct when sampled from SQL

Recommended SQL checks by platform:

```bash
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select source_keyword, count(*) from xhs_note group by source_keyword order by count(*) desc limit 10;"
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select source_keyword, count(*) from douyin_aweme group by source_keyword order by count(*) desc limit 10;"
PGPASSWORD=123456 psql -h localhost -p 5433 -U postgres -d media_crawler -c "select source_keyword, count(*) from bilibili_video group by source_keyword order by count(*) desc limit 10;"
```

## Before integration backtesting

Before moving into TrendAgent / QA integration backtesting, confirm:

1. `xhs` has one successful `qrcode` run and one successful `cookie` reuse run
2. `dy` has one successful smoke run on the shared database target
3. `bili` has one successful smoke run on the shared database target
4. all smoke runs write to Docker PostgreSQL `5433`, not a local standalone `5432`
5. the team uses the wrapper script rather than raw `main.py` commands for repeatability

## Team rule

Do not run `BeautyQA-vendor/MediaCrawler/main.py` manually with raw environment defaults
unless you also explicitly export `POSTGRES_DB_*`.

For team collaboration, the default expectation is:

- use `./scripts/run_mediacrawler.sh`
- keep DB config in `BeautyQA-TrendAgent/backend/.env`
- treat direct `main.py` runs as debugging-only
