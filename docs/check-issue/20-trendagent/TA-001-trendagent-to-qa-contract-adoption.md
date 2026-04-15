# TA-001 - TrendAgent To QA Contract Adoption

## Metadata
- Task ID: `TA-001`
- Module: `BeautyQA-TrendAgent`
- Owner Type: `dev-agent / engineer`
- Status: `ready`
- Related Contract Docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`
- Related Benchmark / Backtest:
  - `docs/check-issue/00-governance/trendagent-backtest-standard.md`

## Goal
- Make `BeautyQA-TrendAgent` explicitly produce a first-party output path oriented toward `trend_signal`, not only `cleaned_trend_data`.

## Scope
- identify the current output boundary
- add first-party interfaces or placeholders needed for `trend_signal`
- keep vendor crawler execution behavior unchanged

## Non-Goals
- do not rewrite vendor crawler logic
- do not redesign QA retrieval yet
- do not change project-wide QA answer behavior

## Inputs
- current TrendAgent implementation
- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`

## Required Outputs
- code or interface changes that introduce a first-party `trend_signal` output path
- updated module docs if implementation surface changes
- one sample `trend_signal` object or fixture

## Contract Constraints
- QA must not depend on vendor raw tables
- vendor path resolution must remain valid
- `cleaned_trend_data` may remain as an intermediate layer

## Execution Boundary
- may change first-party TrendAgent code
- may add first-party schema / model / repository layers
- must not change `BeautyQA-vendor/MediaCrawler/`

## Implementation Notes
- prefer introducing a dedicated signal generation layer after cleaning
- keep the first implementation minimal and traceable
- preserve trace fields such as `keyword_id`, `crawl_task_id`, `source_platform`

## Backtest Requirements
- show one path from cleaned record to signal record
- verify no direct QA dependency on vendor raw tables is introduced
- provide one sample output conforming to `docs/15-trend-signal-schema.md`

## Acceptance Criteria
- first-party `trend_signal` output path exists or is clearly scaffolded
- output fields align with the schema draft
- no vendor code changes are required for the task to pass

## Evidence Required In Return
- changed files
- implementation summary
- sample signal output
- open risks

## Suggested Kickoff Instruction
```text
Task ID: TA-001
Goal: Introduce a first-party trend_signal output path in BeautyQA-TrendAgent based on the frozen contract and schema docs.
Scope: Work only inside BeautyQA-TrendAgent. Keep vendor crawler behavior unchanged. cleaned_trend_data may remain as the intermediate layer.
Non-goals: Do not edit BeautyQA-vendor/MediaCrawler. Do not redesign QA retrieval.
Required outputs: implementation summary, changed files, one sample trend_signal output, backtest notes.
Backtest requirements: show cleaned -> signal path, confirm schema alignment, report open risks.
Constraints: follow docs/14-trendagent-to-qa-data-contract.md and docs/15-trend-signal-schema.md.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
