# QA-002 - Risk Gating And Contract Hardening

## Metadata
- Task ID: `QA-002`
- Module: `BeautyQA-core`
- Owner Type: `qa-owner / engineer / dev-agent`
- Status: `ready`
- Related Contract Docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`
- Related Review:
  - `docs/check-issue/30-qacore/QA-001-review.md`
- Related Benchmark / Backtest:
  - `QA-001` backtest assets

## Goal
- Harden the QA trend evidence gate so that high-risk signals do not enter the strong-evidence path and QA runtime depends on first-party trend contract data only.

## Scope
- risk-aware evidence gating
- behavior flag alignment
- contract-only runtime ingestion
- stronger backtest coverage

## Non-Goals
- do not redesign the whole QA answer system
- do not add crawler runtime dependency
- do not redesign TrendAgent output in this task

## Inputs
- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/check-issue/30-qacore/QA-001-review.md`
- current `BeautyQA-core` QA trend retrieval implementation

## Required Outputs
- updated QA evidence gate implementation
- explicit safety-filter path
- runtime path that reads first-party contract schema only
- updated tests and backtest cases

## Contract Constraints
- QA reads first-party `trend_signal` only in the runtime path
- stale / low-confidence / high-risk signals must not become strong evidence
- science and compliance remain hard constraints
- no vendor crawler dependency may be introduced

## Execution Boundary
- may change `BeautyQA-core/`
- may split runtime loaders from migration-only loaders
- may update tests, fixtures, and backtest scripts
- must not change TrendAgent or vendor crawler code in this task

## Implementation Notes
- add risk-based gating to evidence qualification
- use `trend_filtered_for_safety` when high-risk evidence is retrieved but blocked
- move legacy CSV compatibility to a separate migration/backfill path if still needed
- keep runtime repository API simple and contract-oriented

## Backtest Requirements
- one fresh usable case -> `trend_supported`
- one stale case -> `trend_weak_or_missing`
- one low-confidence case -> `trend_weak_or_missing`
- one high-risk case -> `trend_filtered_for_safety`
- report how runtime path differs from migration/backfill compatibility path

## Acceptance Criteria
- high-risk trend evidence cannot become strong evidence
- runtime ingestion path accepts first-party contract schema only
- `trend_filtered_for_safety` is observable in pipeline behavior
- tests and backtest cover stale / low-confidence / high-risk cases

## Evidence Required In Return
- changed files
- implementation summary
- backtest result
- QA examples
- open risks

## Suggested Kickoff Instruction
```text
Task ID: QA-002
Goal: Harden QA trend evidence gating so high-risk signals are filtered and the runtime path depends on first-party trend_signal contract data only.
Scope: Work only in BeautyQA-core. Improve evidence gating, split runtime contract ingestion from any legacy compatibility path, and expand backtest coverage.
Non-goals: No vendor crawler dependency. No TrendAgent redesign. No broad QA architecture rewrite.
Required outputs: changed files, implementation summary, backtest result, QA examples, open risks.
Constraints: follow docs/14-trendagent-to-qa-data-contract.md, docs/15-trend-signal-schema.md, and docs/check-issue/30-qacore/QA-001-review.md.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
