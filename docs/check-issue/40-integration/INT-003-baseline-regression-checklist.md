# INT-003 Baseline Regression Checklist

## Goal

Use the frozen operator baseline to verify one stable integration loop:

`seed -> expansion -> multi-platform crawl -> cleaning -> trend_signal -> export`

This checklist is the current main-thread gate before widening runtime scope.

## Inputs

- frozen seeds: `docs/check-issue/40-integration/INT-003-baseline-frozen-seeds.md`
- baseline source CSVs:
  - `data/eval/trend_monitor/2026-04-13-report-registry.csv`
  - `data/eval/trend_monitor/2026-04-13-trend-keyword-seed.csv`
- runtime baseline rule: `docs/21-cross-platform-runtime-baseline.md`
- runtime playbook: `docs/18-mediacrawler-runtime-playbook.md`

## Non-Goals

Do not block this loop on:

- `INT-004` time-bucket series
- `INT-005` batch recovery
- benchmark widening
- large watchlist expansion

## Phase 0: Environment Gate

Before any rerun:

- PostgreSQL and Redis are up
- shared `.venv` is usable
- first-party runtime accounts exist for `xhs`, `dy`, `bili`
- vendor browser-state login is valid for the target platform

Suggested checks:

```bash
./.venv/bin/python scripts/bootstrap_runtime_accounts.py --dry-run
./scripts/run_platform_smoke.sh xhs dy bili
```

## Phase 1: Baseline Bootstrap Gate

Freeze the current seed pack into the first-party runtime baseline:

```bash
./.venv/bin/python scripts/bootstrap_runtime_baseline.py --keyword-id 14 31 2 40
```

Pass conditions:

- each seed returns `status=ok`
- approved registry rows are created
- `query_schedule_states` are materialized for the requested platforms

## Phase 2: Platform Proof Gate

### 2.1 Control seed first

Run the control seed `护肤` across all three platforms.

Recommended commands:

```bash
./.venv/bin/python scripts/run_int002_runtime_smoke.py --platform xhs --runtime-profile safe_live --due-keyword-id 14 --max-tasks-per-keyword 1 --max-raw-items 1 --task-delay-seconds 0 --dedup-window-hours 0 --retry-cooldown-hours 0 --no-bootstrap-keywords
./.venv/bin/python scripts/run_int002_runtime_smoke.py --platform dy --runtime-profile safe_live --due-keyword-id 14 --max-tasks-per-keyword 1 --max-raw-items 1 --task-delay-seconds 0 --dedup-window-hours 0 --retry-cooldown-hours 0 --no-bootstrap-keywords
./.venv/bin/python scripts/run_int002_runtime_smoke.py --platform bili --runtime-profile safe_live --due-keyword-id 14 --max-tasks-per-keyword 1 --max-raw-items 1 --task-delay-seconds 0 --dedup-window-hours 0 --retry-cooldown-hours 0 --no-bootstrap-keywords
```

Pass conditions:

- each platform completes at least one task successfully
- raw rows are written into the corresponding vendor tables
- `cleaned_trend_data` is produced
- one `trend_signal` artifact is generated

### 2.2 Normal business seeds

After the control seed is stable, run:

- DB `31` / `面部清洁`
- DB `2` / `外泌体`

Suggested rule:

- run one platform first if the login/account state is sensitive
- then widen to the full `xhs | dy | bili` baseline

### 2.3 Risk seed last

Run DB `40` / `快速美白` last.

Pass conditions:

- runtime still completes normally
- risk-oriented seed does not break scheduling or cleaning
- output remains traceable and review-friendly

## Phase 3: Export Gate

After one or more successful `INT-002` runs, execute export:

```bash
./.venv/bin/python scripts/run_int003_export.py --source-run-id <int002_run_id>
```

Pass conditions:

- export finishes without exception
- output artifact lands in the first-party handoff path
- exported content points back to the source run / task / signal context

## Phase 4: Rerun Stability Gate

Rerun the same control seed again after the first successful pass.

What must be checked:

- no uncontrolled expansion explosion
- no obvious duplicate task storm for the same query unit
- `query_schedule_states` show sensible `last_success_at` / `next_due_at` changes
- batch audit remains readable in `runtime_batch_runs` and `runtime_batch_run_events`

This phase matters more than adding more seeds.

## SQL / State Checks

### Keyword state

```sql
select id, keyword_id, keyword, priority, source_scope
from trend_keywords
where id in (2, 14, 31, 40)
order by id;
```

### Expansion registry

```sql
select keyword_db_id, platform, expanded_query, status, review_status, is_active
from expansion_registry
where keyword_db_id in (2, 14, 31, 40)
order by keyword_db_id, platform, expanded_query;
```

### Query schedule state

```sql
select keyword_db_id, platform, expanded_query, last_success_at, next_due_at, last_task_status, failure_count
from query_schedule_states
where keyword_db_id in (2, 14, 31, 40)
order by keyword_db_id, platform, expanded_query;
```

### Runtime batch audit

```sql
select run_id, run_type, status, started_at, completed_at, summary
from runtime_batch_runs
order by id desc
limit 10;
```

```sql
select run_id, event_type, platform, keyword_id, task_id, message, created_at
from runtime_batch_run_events
order by id desc
limit 30;
```

## Release Decision

### Green

- control seed passes on `xhs`, `dy`, `bili`
- at least two additional frozen seeds pass end-to-end
- export succeeds
- rerun behavior is explainable and controlled

### Yellow

- one platform is still unstable, but the first-party loop is explainable and repeatable on the others
- main issues are environment/account/platform-specific, not contract or schema breakage

### Red

- repeated task storms, uncontrolled expansion growth, broken cleaning, or missing audit trail
- export cannot be trusted
- same seed cannot be rerun in a controlled way

## Evidence To Keep

For each completed regression wave, keep:

- `INT-002` run ids
- generated `trend_signal` artifact paths
- one export artifact path
- the SQL snapshots used to judge pass/fail
- one short note on open runtime risks
