# QA-001 - Trend Signal Retrieval Integration

## Metadata
- Task ID: `QA-001`
- Module: `BeautyQA-core`
- Owner Type: `qa-owner / engineer / dev-agent`
- Status: `ready`
- Related Contract Docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`
- Related Benchmark / Backtest:
  - existing QA evaluation assets

## Goal
- Integrate first-party `trend_signal` retrieval into the QA pipeline without coupling QA to crawler implementation details.

## Scope
- retrieval input contract
- trend evidence loading
- trend evidence ranking or filtering hooks
- answer-layer use of trend evidence

## Non-Goals
- do not call vendor crawler from QA
- do not depend on vendor raw tables
- do not redesign the full QA answer system in this task

## Inputs
- `trend_signal` contract
- `trend_signal` schema
- current QA architecture docs

## Required Outputs
- retrieval integration design or implementation
- one example of QA consuming `trend_signal`
- explicit handling of stale / low-confidence signals

## Contract Constraints
- science and compliance remain hard constraints
- trend evidence is supportive, not authoritative
- QA must degrade gracefully if trend data is missing

## Execution Boundary
- may change `BeautyQA-core/`
- may define retrieval and evidence assembly around `trend_signal`
- must not pull in vendor crawler dependencies

## Backtest Requirements
- show one QA example with trend evidence present
- show one QA example with trend evidence absent or stale
- report whether answer behavior remains conservative under weak trend evidence

## Acceptance Criteria
- QA reads first-party trend output only
- stale / low-confidence trend evidence does not dominate answer behavior
- no crawler runtime dependency is introduced into QA

## Evidence Required In Return
- changed files
- implementation summary
- QA examples
- backtest result
- open risks

## Suggested Kickoff Instruction
```text
Task ID: QA-001
Goal: Integrate first-party trend_signal retrieval into BeautyQA-core without coupling QA to crawler implementation details.
Scope: Work only in BeautyQA-core and QA-facing retrieval / evidence assembly.
Non-goals: No vendor crawler dependency. No direct use of raw crawler tables.
Required outputs: changed files, implementation summary, one QA example with trend evidence, one QA example with weak/absent trend evidence, backtest notes.
Constraints: follow docs/14-trendagent-to-qa-data-contract.md and docs/15-trend-signal-schema.md.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
