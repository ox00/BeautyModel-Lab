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
- Turn the TA-001 output scaffold into a stable first-party `trend_signal` generation layer that produces grouped, repeatable, and QA-usable signal records.

## Scope
- define deterministic signal grouping logic from `cleaned_trend_data`
- define signal scoring inputs and explicit confidence / risk assignment rule
- define freshness handling and representative evidence selection
- define stable persistence shape for `trend_signal`
- add a minimal refresh report or equivalent run summary if practical

## Non-Goals
- do not redesign crawling
- do not redesign account handling
- do not redesign QA answer behavior
- do not solve keyword expansion quality in this task

## Inputs
- `cleaned_trend_data`
- contract doc
- trend signal schema doc
- TA-001 implementation baseline

## Required Outputs
- signal generation implementation that groups multiple cleaned records into one or more signal outputs
- signal persistence implementation or export fixture
- sample grouped signal records
- grouping / scoring / freshness notes
- run summary showing cleaned input count and generated signal count

## Contract Constraints
- generated signal must preserve traceability
- confidence and risk must stay explicit
- vendor raw schema must not leak into downstream QA contract
- same cleaned inputs should not produce materially drifting signal structure on repeated runs

## Execution Boundary
- may change TrendAgent storage / repository / service code
- may add new first-party DB model(s)
- must not modify vendor crawler source
- must not move QA-side retrieval responsibility back into TrendAgent

## Implementation Notes
- start with one platform-safe baseline path if full cross-platform rollout is too wide
- prefer deterministic grouping before adding more complex scoring
- keep aggregation method explicit in code or metadata
- use one representative source/evidence selection rule that is explainable in review
- if persistence format changes, keep one QA-consumable sample fixture for follow-up integration tasks

## Backtest Requirements
- report number of cleaned records in sample input
- report number of generated signals
- show at least one grouped signal example with `support_count > 1` if sample input allows
- show one freshness assignment example
- show one confidence / risk assignment example
- show repeated-run result or explain why current implementation is deterministic

## Acceptance Criteria
- signal generation can be run repeatedly on the same cleaned inputs with stable structure
- output structure follows the schema doc
- grouping and scoring logic are explainable from code and sample output
- output is good enough for the next E2E smoke-test task to consume directly

## Evidence Required In Return
- changed files
- implementation summary
- one or more sample signals
- backtest result
- open risks

## Suggested Kickoff Instruction
```text
Task ID: TA-002
Goal: Turn the TA-001 trend_signal scaffold into a stable generation layer in BeautyQA-TrendAgent.
Scope: Build from cleaned_trend_data toward grouped first-party signal output. Keep crawler and vendor behavior unchanged.
Non-goals: No vendor edits, no QA retrieval redesign, no keyword expansion redesign.
Required outputs: changed files, implementation summary, sample generated signals, grouping/scoring notes, backtest notes.
Backtest requirements: report cleaned input count, generated signal count, grouped signal example, freshness/confidence/risk behavior, and repeated-run stability.
Constraints: align with docs/14-trendagent-to-qa-data-contract.md and docs/15-trend-signal-schema.md.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
