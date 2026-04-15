# TA-002 - Trend Signal Generation Layer

## Metadata
- Task ID: `TA-002`
- Module: `BeautyQA-TrendAgent`
- Owner Type: `dev-agent / engineer`
- Status: `ready`
- Related Contract Docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`
- Related Benchmark / Backtest:
  - `docs/check-issue/00-governance/trendagent-backtest-standard.md`

## Goal
- Add a stable first-party layer that aggregates cleaned trend data into `trend_signal` records.

## Scope
- define signal grouping logic
- define signal scoring inputs
- define freshness handling
- define persistence shape for `trend_signal`

## Non-Goals
- do not redesign crawling
- do not redesign account handling
- do not redesign QA usage yet

## Inputs
- `cleaned_trend_data`
- contract doc
- trend signal schema doc

## Required Outputs
- signal generation implementation
- signal persistence implementation or export fixture
- sample records
- grouping / freshness notes

## Contract Constraints
- generated signal must preserve traceability
- confidence and risk must stay explicit
- vendor raw schema must not leak into downstream QA contract

## Execution Boundary
- may change TrendAgent storage / repository / service code
- may add new first-party DB model(s)
- must not modify vendor crawler source

## Implementation Notes
- start with one platform-safe baseline path if full cross-platform rollout is too wide
- use deterministic grouping before adding more complex scoring
- keep aggregation method explicit in code or metadata

## Backtest Requirements
- report number of cleaned records in sample input
- report number of generated signals
- show at least one grouped signal example
- show freshness and confidence assignment example

## Acceptance Criteria
- signal generation can be run repeatedly on the same cleaned inputs
- output structure follows the schema doc
- grouping and scoring logic are explainable from code and sample output

## Evidence Required In Return
- changed files
- implementation summary
- one or more sample signals
- backtest result
- open risks

## Suggested Kickoff Instruction
```text
Task ID: TA-002
Goal: Implement the first usable trend_signal generation layer in BeautyQA-TrendAgent.
Scope: Build from cleaned_trend_data toward first-party signal output. Keep crawler and vendor behavior unchanged.
Non-goals: No vendor edits, no QA retrieval redesign.
Required outputs: changed files, implementation summary, sample generated signals, backtest notes.
Backtest requirements: report cleaned input count, generated signal count, sample freshness/confidence behavior.
Constraints: align with docs/14-trendagent-to-qa-data-contract.md and docs/15-trend-signal-schema.md.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
