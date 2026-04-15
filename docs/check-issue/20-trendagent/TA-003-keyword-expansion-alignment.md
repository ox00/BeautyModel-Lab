# TA-003 - Keyword Expansion Alignment

## Metadata
- Task ID: `TA-003`
- Module: `BeautyQA-TrendAgent`
- Owner Type: `dev-agent / engineer`
- Status: `ready`
- Related Contract Docs:
  - `data/eval/trend_monitor/trend_keyword_expansion_spec_cn.md`
  - `docs/14-trendagent-to-qa-data-contract.md`
- Related Benchmark / Backtest:
  - `docs/check-issue/00-governance/trendagent-backtest-standard.md`

## Goal
- Align TrendAgent keyword expansion input/output behavior with the structured `trend_monitor` keyword strategy.

## Scope
- review current keyword expander inputs
- reduce mismatch between first-party keyword metadata and LLM prompt usage
- prepare a more structured path for future platform-aware expansion

## Non-Goals
- do not try to solve every expansion quality issue in one pass
- do not redesign the full crawler system
- do not merge reference-only sources into crawl targets

## Inputs
- `BeautyQA-TrendAgent/backend/config/enhance_trend_keyword.md`
- `data/eval/trend_monitor/trend_keyword_expansion_spec_cn.md`
- current keyword schema and scheduler logic

## Required Outputs
- alignment notes or implementation update
- clarified input fields for keyword expansion
- explicit handling notes for crawl targets vs reference sources

## Contract Constraints
- `taobao` remains a reference source, not a crawler target
- `industry_news` remains separate from MediaCrawler crawl targets
- expansion must not force QA to know crawler internals

## Execution Boundary
- may change first-party expansion path and scheduler-side metadata usage
- must not change vendor crawler code

## Backtest Requirements
- show one example keyword before / after alignment
- show platform filtering behavior
- show how reference sources are kept out of crawler target execution

## Acceptance Criteria
- structured keyword metadata is better reflected in expansion behavior
- reference sources and crawl targets are not confused
- scheduler behavior remains explainable

## Evidence Required In Return
- changed files
- implementation or analysis summary
- example expansion output
- backtest notes

## Suggested Kickoff Instruction
```text
Task ID: TA-003
Goal: Align TrendAgent keyword expansion behavior with the structured trend_monitor spec.
Scope: Work on first-party expansion inputs and scheduler-side handling only.
Non-goals: No vendor edits. Do not treat taobao as a crawler target.
Required outputs: changed files, alignment summary, example expansion behavior, backtest notes.
Backtest requirements: show one keyword before/after alignment, platform filtering, reference-source handling.
Constraints: use data/eval/trend_monitor/trend_keyword_expansion_spec_cn.md as the source of truth for the new direction.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
