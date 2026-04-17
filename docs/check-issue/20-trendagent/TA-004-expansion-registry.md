# TA-004 - Expansion Registry

## Metadata
- Task ID: `TA-004`
- Module: `BeautyQA-TrendAgent`
- Owner Type: `dev-agent / engineer`
- Status: `ready`
- Related Contract Docs:
  - `docs/19-trendagent-runtime-strategy.md`
  - `docs/20-trend-signal-timeseries-strategy.md`
- Related Benchmark / Backtest:
  - `docs/check-issue/00-governance/trendagent-backtest-standard.md`

## Goal
- Turn keyword expansion from per-run temporary output into a first-party managed registry.

## Scope
- add expansion registry schema
- distinguish `approved` / `candidate` / `deprecated`
- record expansion source such as `manual`, `llm`, `mined_from_data`
- support reading approved expansions during planning

## Non-Goals
- do not redesign the full crawler runtime here
- do not implement time-bucket trend aggregation here
- do not solve batch recovery here

## Inputs
- current keyword expansion path
- `docs/20-trend-signal-timeseries-strategy.md`
- current scheduler and keyword metadata usage

## Required Outputs
- expansion registry schema and persistence path
- one read path for scheduler / planner to use approved expansions
- one candidate-ingestion path or placeholder contract for mined terms
- operator / developer note on how candidates become approved

## Contract Constraints
- QA must still consume only first-party `trend_signal`, not expansion internals
- vendor crawler code remains untouched
- `taobao` remains reference-only, not crawler target

## Execution Boundary
- may change first-party expansion models, services, and scheduler integration
- must not change `BeautyQA-vendor/MediaCrawler/`

## Implementation Notes
- model expansions as first-party persistent objects, not transient prompt output
- support ttl / review status even if the first version is simple
- preserve compatibility with current seed keyword metadata

## Backtest Requirements
- show one keyword with approved expansions loaded from registry
- show candidate expansions not entering runtime before approval
- show deprecated expansions not being scheduled

## Acceptance Criteria
- scheduler no longer depends only on transient expansion generation
- approved expansions become the stable default execution source
- candidate / approved boundary is explicit

## Evidence Required In Return
- changed files
- schema summary
- one before / after planner example
- backtest result
- open risks

## Suggested Kickoff Instruction
```text
Task ID: TA-004
Goal: Add a first-party expansion registry so TrendAgent does not rely on per-run temporary expansion output only.
Scope: expansion schema, approved/candidate/deprecated state, scheduler read path, candidate-ingestion boundary.
Non-goals: no vendor edits, no batch recovery, no time-series aggregation.
Required outputs: changed files, schema summary, one planner example, backtest result, open risks.
Backtest requirements: show approved expansions are used, candidate expansions are blocked from runtime, deprecated expansions are ignored.
Constraints: keep QA decoupled from expansion internals; do not treat taobao as crawler target.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
