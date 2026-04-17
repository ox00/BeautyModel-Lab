# Trend Signal Timeseries Strategy

This document consolidates the recent runtime, export, scheduling, and recovery
discussions into one architecture direction.

The core position is:

- do not treat `trend keywords -> expand -> crawler` as one flat loop
- separate stable planning state from periodic observation state
- separate one-run artifacts from time-bucket trend series
- separate task execution from batch completion and recovery

## One-line Model

The target line is:

`stable keyword registry -> controlled expansion registry -> cooled periodic observation -> time-bucket trend signal series -> stable QA handoff`

## Why the old mental model is not enough

The older line was still too close to:

- trend keyword
- expand
- crawl
- output signal

That is enough for one-off smoke and small runtime validation.
It is not enough for:

- social data as dynamic observation
- repeated periodic crawling
- partial completion tracking
- interrupted-run recovery
- QA handoff as a stable runtime product

## Two Loops

### 1. Planning Loop

This loop answers: what should we observe?

Objects:

- `keyword_registry`
- `expansion_registry`
- watchlist tiering
- platform scope

Cadence:

- seed keywords: weekly or biweekly
- approved expansions: every 3 to 7 days
- candidate new terms: daily candidate refresh is acceptable

### 2. Observation Loop

This loop answers: what changed over time?

Objects:

- `query_schedule_state`
- periodic crawl execution
- `runtime_batch_runs`
- `runtime_batch_items`
- `trend_signal_series`

Cadence:

- `watchlist-hot`: 12h
- `watchlist-normal`: 24h to 48h
- `discovery`: 3d to 7d

## Layered Scheduling

### Tier A: watchlist-hot

- true active trend watch
- highest business value
- shortest interval
- still protected by cooldown and dedup

Recommended cadence:

- `dy` / `bili`: 12h
- `xhs`: 24h

### Tier B: watchlist-normal

- stable ongoing trend observation
- normal production path

Recommended cadence:

- `dy` / `bili`: 24h
- `xhs`: 48h

### Tier C: discovery

- low-frequency exploration
- new-term mining
- lower coverage expectation

Recommended cadence:

- all platforms: 3d to 7d

## First-party Registries And State

### 1. Keyword Registry

Keeps:

- seed trend keyword
- normalized theme
- topic cluster
- business priority
- watchlist tier
- platform scope

This stays relatively stable.

### 2. Expansion Registry

Keeps:

- approved expansions
- candidate expansions
- source type: manual / llm / mined_from_data
- review status
- ttl or refresh horizon

This prevents the system from regenerating all expansions on every run.

### 3. Query Schedule State

The runtime unit should be:

`query_unit = normalized_keyword + platform + expanded_query`

For each `query_unit`, keep:

- `last_scheduled_at`
- `last_success_at`
- `last_failed_at`
- `min_revisit_interval`
- `retry_cooldown`
- `next_due_at`
- `tier`
- `risk_level`

This should become the scheduling truth instead of relying only on ad hoc task dedup.

### 4. Runtime Batch State

The system needs batch-level persistence for one cycle of execution.

Batch-level tables should express:

- what was intended
- what got dispatched
- what completed
- what remained incomplete
- whether the cycle finished as full / partial / failed

Existing:

- `runtime_batch_runs`
- `runtime_batch_run_events`

Still needed:

- `runtime_batch_items`

## Time Series Is Not Post-Level

Do not treat each crawled post as the time series unit.

The timeseries unit should be an aggregated signal bucket.

Recommended bucket levels:

- `12h`
- `1d`
- later optional rolling `7d`

Recommended series key:

`normalized_keyword + platform + time_bucket`

Recommended fields:

- `bucket_start`
- `bucket_end`
- `support_count`
- `avg_trend_score`
- `top_evidence`
- `new_term_count`
- `platform_distribution`
- `delta_vs_prev_bucket`
- `series_status`: emerging / stable / cooling

## Batch Completion Principle

Starting one runtime batch should mean:

- the expected query set for that cycle is frozen
- unfinished items remain visible
- interruptions do not silently erase execution intent

The system should be able to conclude one batch as:

- `completed_full`
- `completed_partial`
- `failed`

## Export Principle

QA should not read:

- vendor raw tables
- ad hoc task JSON folders
- sample fixtures as runtime source

QA should read:

- stable handoff exports derived from first-party trend signal outputs
- runtime manifests with freshness and batch metadata

INT-003 should therefore consume:

- `runtime_batch_runs`
- `runtime_batch_run_events`
- stable first-party `trend_signal` outputs

## Recovery Principle

The system must support:

- interrupted process recovery
- stale-running detection
- partial batch continuation
- completion audit

This requires:

- batch item schema
- retryable vs terminal failure distinction
- recovery reconciler
- completion report

## Recommended Task Order

### Phase 1: Stabilize Handoff And State

1. `INT-003` export cron + SQL checklist
2. `TA-004` expansion registry
3. `TA-005` query schedule state

### Phase 2: Upgrade Observation Model

4. `INT-004` trend signal series aggregation
5. `INT-005` batch recovery and completion guarantee

## Dependency Logic

- `INT-003` can start first because QA handoff should stabilize early
- `TA-004` and `TA-005` define the durable upstream scheduling model
- `INT-004` should build on query state and time bucket rules
- `INT-005` depends on durable batch item planning and execution state

## Delivery Rule

Do not mix all five tasks into one implementation thread.

Use architecture control to freeze:

- object definitions
- task order
- acceptance criteria

Then hand off execution in separate threads with clear ownership.
