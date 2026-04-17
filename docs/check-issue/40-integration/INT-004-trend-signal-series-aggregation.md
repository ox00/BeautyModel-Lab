# INT-004 - Trend Signal Series Aggregation

## Metadata
- Task ID: `INT-004`
- Module: `BeautyQA-TrendAgent + shared data handoff`
- Owner Type: `dev-agent / engineer / architecture-support`
- Status: `ready`
- Related Docs:
  - `docs/15-trend-signal-schema.md`
  - `docs/16-trend-signal-to-qa-usage-guide.md`
  - `docs/20-trend-signal-timeseries-strategy.md`
- Related Upstream Tasks:
  - `docs/check-issue/20-trendagent/TA-005-query-schedule-state.md`
  - `docs/check-issue/40-integration/INT-003-trend-signal-export-cron.md`

## Goal
- Upgrade single-run `trend_signal` outputs into time-bucket `trend_signal_series`.

## Why This Task Exists
- social trend observation is dynamic
- one-off per-task trend outputs are not enough for time-based trend judgment
- QA and analysis need aggregated trend movement, not isolated task snapshots only

## Scope
- define bucketed aggregation rules such as `12h` / `1d`
- aggregate first-party signal records into series rows
- compute deltas against previous bucket
- prepare series output for export and downstream consumption

## Non-Goals
- do not redesign QA retrieval here
- do not implement batch recovery here
- do not redesign vendor crawling here

## Required Outputs
- series schema or storage path
- one aggregation job or script
- one example bucketed output artifact
- note on how series output joins the stable handoff path

## Contract Constraints
- source must remain first-party cleaned / signal outputs
- QA must still avoid vendor raw tables
- series output must preserve traceability back to signal ids or task ids

## Implementation Notes
- series key should be aligned with:
  - `normalized_keyword`
  - `platform`
  - `time_bucket`
- include:
  - `support_count`
  - `avg_trend_score`
  - `delta_vs_prev_bucket`
  - representative evidence

## Backtest Requirements
- show one keyword over at least two buckets
- show previous-bucket delta calculation
- show how series output remains traceable to first-party signals

## Acceptance Criteria
- trend observation can be expressed as bucketed series, not only isolated task outputs
- export layer has a stable series input shape
- evidence trace remains explainable

## Evidence Required In Return
- changed files
- implementation summary
- example series artifact
- backtest result
- open risks

## Suggested Kickoff Instruction
```text
Task ID: INT-004
Goal: Upgrade single-run trend_signal outputs into time-bucket trend_signal_series for dynamic trend observation.
Scope: series schema, aggregation job, delta calculation, handoff note.
Non-goals: no QA retrieval redesign, no batch recovery, no vendor refactor.
Required outputs: changed files, implementation summary, example series artifact, backtest result, open risks.
Backtest requirements: show two buckets for one keyword, previous-bucket delta, and source traceability.
Constraints: use first-party signal outputs only; keep QA decoupled from vendor raw tables.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
