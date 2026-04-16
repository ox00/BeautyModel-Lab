# INT-001 - E2E Smoke Test

## Metadata
- Task ID: `INT-001`
- Module: `BeautyQA-TrendAgent + BeautyQA-core`
- Owner Type: `dev-agent / engineer / architecture-support`
- Status: `ready`
- Related Contract Docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`
- Related Upstream Tasks:
  - `docs/check-issue/20-trendagent/TA-002-trend-signal-generation-layer.md`
  - `docs/check-issue/30-qacore/QA-003-trend-evidence-boundary-tightening.md`

## Goal
- Verify that the minimum end-to-end path is actually runnable:
  - cleaned trend data
  - `trend_signal` generation
  - QA-side evidence ingestion
  - graceful fallback when trend evidence is absent or weak

## Scope
- one minimal shared fixture or sample dataset
- one executable smoke-test path or script
- one result report showing stage-by-stage success
- one or two representative queries for QA evidence usage

## Non-Goals
- do not build the full benchmark here
- do not expand into multi-platform production validation
- do not redesign QA answer policy here
- do not redesign crawler or keyword expansion here

## Inputs
- latest TA-002 output path
- latest QA-003 ingestion path
- one stable sample `trend_signal` fixture or generation input

## Required Outputs
- runnable smoke test entrypoint or documented run steps
- sample input and sample output artifacts
- stage-by-stage result summary
- one case with trend evidence present
- one case with trend evidence absent, stale, or weak

## Contract Constraints
- smoke test must consume first-party `trend_signal` only on the QA side
- vendor crawler internals must remain out of the QA path
- smoke test should be small enough to rerun quickly during review

## Execution Boundary
- may add scripts, fixtures, and test-only wiring in `BeautyQA-TrendAgent/` and `BeautyQA-core/`
- may add docs and sample artifacts
- must not widen the business scope beyond smoke verification

## Implementation Notes
- prefer deterministic fixtures over unstable live data
- keep the smoke test small enough for repeated regression checks
- if a true cross-repo script is awkward, documented two-step execution is acceptable
- the report should make it obvious where the chain breaks if it fails

## Backtest Requirements
- show cleaned input count
- show generated signal count
- show QA evidence retrieval result for one supportive case
- show QA graceful fallback result for one weak or absent-evidence case
- report total run steps and any manual prerequisites

## Acceptance Criteria
- the team can prove the pipeline is connected, not only separately scaffolded
- a reviewer can rerun the smoke test with local sample inputs
- failure stage is diagnosable from the returned report

## Evidence Required In Return
- changed files
- smoke test run result
- sample inputs / outputs
- stage summary
- open risks

## Suggested Kickoff Instruction
```text
Task ID: INT-001
Goal: Verify the minimum cleaned_trend_data -> trend_signal -> QA evidence ingestion path with a runnable smoke test.
Scope: Use sample inputs, minimal scripts/fixtures, and a small report only. Do not expand into full benchmark design.
Non-goals: No vendor redesign, no broad QA answer-policy redesign, no multi-platform production rollout.
Required outputs: changed files, smoke test run result, sample inputs/outputs, stage summary, open risks.
Constraints: follow docs/14-trendagent-to-qa-data-contract.md, docs/15-trend-signal-schema.md, TA-002, and QA-003.
Return format:
- changed files
- what was implemented
- smoke test result
- open risks
```
