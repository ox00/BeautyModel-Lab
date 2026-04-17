# INT-005 - Batch Recovery And Completion Guarantee

## Metadata
- Task ID: `INT-005`
- Module: `BeautyQA-TrendAgent + runtime reliability`
- Owner Type: `dev-agent / engineer / architecture-support`
- Status: `ready`
- Related Docs:
  - `docs/19-trendagent-runtime-strategy.md`
  - `docs/20-trend-signal-timeseries-strategy.md`
- Related Upstream Tasks:
  - `docs/check-issue/20-trendagent/TA-005-query-schedule-state.md`
  - `docs/check-issue/40-integration/INT-002-trendagent-crawler-runtime-link.md`

## Goal
- Make one runtime batch resumable, auditable, and classifiable as full / partial / failed completion.

## Why This Task Exists
- current runtime state is enough for audit, but not enough for interrupted-run continuation
- process exit, network loss, worker crash, or machine shutdown can leave a cycle unfinished
- the system needs to keep pushing one batch forward until completion is determined

## Scope
- add batch item schema for expected execution units
- add recovery / reconciliation logic
- add completion audit summary
- classify retryable vs terminal failure

## Non-Goals
- do not redesign vendor crawling here
- do not redesign QA retrieval here
- do not widen scope into benchmark work

## Required Outputs
- batch item schema
- one recovery reconciler or replay script / worker
- one completion audit report shape
- operator note for interrupted batch continuation

## Contract Constraints
- batch recovery must build on first-party batch state
- recovery should not blindly duplicate successful query units
- completion result must distinguish:
  - `completed_full`
  - `completed_partial`
  - `failed`

## Implementation Notes
- batch execution unit should align with `query_unit`
- stale `running` items need recovery rules
- `dispatched` but never-started items need requeue rules
- retryable and terminal failure should be explicit

## Backtest Requirements
- show one interrupted batch being resumed
- show one stale-running item being reconciled
- show one final batch audit summary with completion classification

## Acceptance Criteria
- one batch can be resumed after interruption
- incomplete items stay visible until resolved
- final batch status is explainable at full / partial / failed level

## Evidence Required In Return
- changed files
- schema summary
- recovery example
- completion audit example
- open risks

## Suggested Kickoff Instruction
```text
Task ID: INT-005
Goal: Add batch recovery and completion guarantee so one runtime cycle can continue after interruption and end as full / partial / failed.
Scope: batch item schema, recovery reconciler, completion audit summary, interrupted-batch operator note.
Non-goals: no vendor refactor, no QA retrieval redesign, no benchmark work.
Required outputs: changed files, schema summary, recovery example, completion audit example, open risks.
Backtest requirements: show interrupted-batch resume, stale-running reconciliation, and final completion classification.
Constraints: build on first-party batch state; do not duplicate already-successful query units.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
