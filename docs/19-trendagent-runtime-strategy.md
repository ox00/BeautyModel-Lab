# TrendAgent Runtime Strategy

This document defines the default live-run strategy for the first-party
`TrendAgent -> crawler -> cleaned_trend_data -> trend_signal` path.

The core position is:

- use repeated live verification on lower-risk platforms first
- treat `xhs` as sparse manual verification, not as the main regression loop
- keep repeated regression checks small, slow, and deduplicated

## Why this exists

Two risks are now clear:

1. repeated runs on the same keyword batch can create noisy duplicate crawl work
2. repeated real-platform smoke, especially on `xhs`, raises account-risk and ban-risk

So runtime strategy cannot be only a shell command.
It must be reflected in first-party defaults.

## Default runtime profile

`scripts/run_int002_runtime_smoke.py` now uses the `safe_live` profile by default.

Common defaults:

- `per_platform_limit=1`
- `max_tasks_per_keyword=1`
- `max_raw_items=1`
- `max_concurrency=1`
- comments off
- sub-comments off
- dedup window on
- failed-task cooldown on

These defaults are intentionally conservative.
They are meant for stable runtime verification, not for aggressive data acquisition.

## Platform policy

### xhs

- purpose: sparse manual verification only
- task delay: `20s`
- failed-task cooldown: `72h`
- operator guidance:
  - do not use as the default repeated smoke path
  - keep one keyword, one task, one browser context
  - prefer cookie reuse
  - avoid high-frequency reruns on the same account

### dy

- purpose: main repeated live verification path
- task delay: `10s`
- failed-task cooldown: `24h`
- operator guidance:
  - use for most repeated runtime checks before widening to `xhs`
  - still keep comments off and concurrency low

### bili

- purpose: lowest-risk repeated live verification path
- task delay: `8s`
- failed-task cooldown: `12h`
- operator guidance:
  - suitable for repeated smoke and replay checks
  - still keep run size small

## What dedup means here

Runtime dedup is currently based on `task_dedup_key`.

The scheduler now blocks new task creation when the same dedup key already has:

- a `pending` task
- a `running` task
- a `completed` task inside the dedup window
- a `failed` task inside the retry cooldown window

This is not only for DB cleanliness.
It is also part of platform-risk control.

## Batch history tables

First-party runtime execution history now has dedicated tables:

- `runtime_batch_runs`
- `runtime_batch_run_events`

Use them for:

- checking what a batch intended to run
- checking which keywords were scheduled or skipped
- checking which task ids belong to a batch
- checking whether a batch failed during scheduling or post-processing
- building later cron / audit / replay workflows

## Recommended team usage

### Repeated regression check

Prefer:

```bash
./.venv/bin/python scripts/run_int002_runtime_smoke.py --platform dy bili
```

### Minimal xhs verification

Use only when needed:

```bash
./.venv/bin/python scripts/run_int002_runtime_smoke.py --platform xhs
```

### Faster local debug

Only for controlled local debugging:

```bash
./.venv/bin/python scripts/run_int002_runtime_smoke.py --runtime-profile debug_fast --platform bili
```

## Operator rule

Do not let integration smoke turn into repeated full live crawl on `xhs`.
For repeated regressions, prefer:

1. first-party sample replay
2. existing raw-table replay
3. `dy` or `bili` minimal live verification
4. only then sparse `xhs` verification
