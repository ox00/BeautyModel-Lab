# TA-005 - Query Schedule State

## Metadata
- Task ID: `TA-005`
- Module: `BeautyQA-TrendAgent`
- Owner Type: `dev-agent / engineer`
- Status: `ready`
- Related Contract Docs:
  - `docs/19-trendagent-runtime-strategy.md`
  - `docs/20-trend-signal-timeseries-strategy.md`
- Related Benchmark / Backtest:
  - `docs/check-issue/00-governance/trendagent-backtest-standard.md`

## Goal
- Introduce first-party schedule state for each query unit so periodic crawling is driven by durable state, not just task dedup.

## Scope
- define `query_unit = normalized_keyword + platform + expanded_query`
- persist schedule state per query unit
- support watchlist tiering: `watchlist-hot`, `watchlist-normal`, `discovery`
- persist `min_revisit_interval`, `retry_cooldown`, `next_due_at`
- update scheduler to read due query units from schedule state

## Non-Goals
- do not implement batch recovery here
- do not implement trend signal time-bucket aggregation here
- do not redesign QA retrieval here

## Inputs
- `TA-004` expansion registry direction
- current task dedup and runtime policy path
- `docs/20-trend-signal-timeseries-strategy.md`

## Required Outputs
- query schedule state schema
- scheduler-side due selection based on schedule state
- tier-driven default interval rules
- operator note on how schedule state is updated after success / failure

## Contract Constraints
- task dedup remains a safety layer, not the only scheduling truth
- runtime policy by platform must remain compatible with current safety defaults
- QA remains decoupled from runtime scheduling internals

## Execution Boundary
- may change first-party scheduler / service / schema path
- may add migration and state-update logic after crawl result
- must not change vendor crawler code

## Implementation Notes
- store enough state to answer why a query unit is due now
- state should support both periodic observation and replay after failure
- tier should be explicit on the query-unit state, not hidden in ad hoc config only

## Backtest Requirements
- show one query unit across success -> next_due update
- show one failed query unit entering cooldown
- show tier A / B / C producing different revisit intervals

## Acceptance Criteria
- scheduler can explain due selection using persisted query state
- repeated runs are governed by revisit interval and cooldown, not only dedup
- watchlist tiering is visible in first-party state

## Evidence Required In Return
- changed files
- schema summary
- one success / failure schedule example
- backtest result
- open risks

## Suggested Kickoff Instruction
```text
Task ID: TA-005
Goal: Add first-party query schedule state so periodic crawl execution is governed by durable query-unit state instead of task dedup only.
Scope: query-unit schema, tiering, revisit interval, cooldown, next_due update, scheduler read path.
Non-goals: no batch recovery, no time-series aggregation, no vendor edits.
Required outputs: changed files, schema summary, one schedule example for success/failure, backtest result, open risks.
Backtest requirements: show next_due update after success, cooldown after failure, and tier A/B/C interval difference.
Constraints: keep QA decoupled; keep vendor boundary narrow; task dedup remains only a safety layer.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
