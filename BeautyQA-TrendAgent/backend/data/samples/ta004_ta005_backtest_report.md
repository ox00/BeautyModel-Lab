# TA-004 + TA-005 Backtest Report

## Scope
- Module: `BeautyQA-TrendAgent/backend`
- Contracts:
  - `docs/19-trendagent-runtime-strategy.md`
  - `docs/20-trend-signal-timeseries-strategy.md`
  - `docs/check-issue/20-trendagent/TA-004-expansion-registry.md`
  - `docs/check-issue/20-trendagent/TA-005-query-schedule-state.md`

## Layer A - Contract Check

### TA-004
- Added first-party `expansion_registry` schema with explicit:
  - `status`: `approved` / `candidate` / `deprecated`
  - `source_type`: `manual` / `llm` / `mined_from_data`
  - `review_status`
- Scheduler runtime path only uses `approved` + `is_active` rows.

### TA-005
- Added first-party `query_schedule_states` schema keyed by:
  - `query_unit_key = normalized_keyword + platform + expanded_query`
- Stored scheduling fields:
  - `tier`
  - `min_revisit_interval_minutes`
  - `retry_cooldown_minutes`
  - `next_due_at`
  - `last_scheduled_at` / `last_success_at` / `last_failed_at`

## Layer B - Pipeline Check
- Planner still builds candidate queries, but now writes to first-party registry.
- Scheduler no longer schedules directly from transient planner list.
- Scheduler flow now:
  1. upsert expansion registry
  2. ensure query schedule state for approved rows
  3. pick due query units (`next_due_at <= now`)
  4. schedule tasks and mark query state `last_scheduled_at`
- Postprocess now updates query schedule state:
  - success -> `next_due_at = now + min_revisit_interval`
  - failure -> `next_due_at = now + retry_cooldown`

## Layer C - Boundary Check
- No changes in `BeautyQA-vendor/MediaCrawler/`.
- No QA-side logic changes.
- No batch recovery/time-series aggregation logic introduced.

## Layer D - Output Quality Check
- Planner/schedule examples generated:
  - `backend/data/samples/ta004_ta005_examples.json`
- Tier interval policies visible and differentiated.
- Candidate and deprecated rows are persisted but not scheduled.

## Result
- TA-004 and TA-005 are continuously implemented under one schema design.

## Open Risks
- Registry bootstrap currently happens in scheduler path; heavy runtime may benefit from dedicated ingestion jobs.
- `query_unit_key` is string-concatenated; future normalization edge cases (whitespace/synonyms) may need stricter canonicalization.
- Tier rules are static defaults; should be made configurable per environment/profile later.
