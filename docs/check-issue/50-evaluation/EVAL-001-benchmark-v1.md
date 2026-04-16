# EVAL-001 - Benchmark V1

## Metadata
- Task ID: `EVAL-001`
- Module: `evaluation`
- Owner Type: `pm / qa-owner / architecture-control / engineer-support`
- Status: `ready`
- Related Policy Docs:
  - `docs/evaluation/01-benchmark-scope.md`
  - `docs/evaluation/02-case-schema.md`
  - `docs/evaluation/03-scoring-rubric.md`
  - `docs/evaluation/04-release-gates.md`
- Related Integration Task:
  - `docs/check-issue/40-integration/INT-001-e2e-smoke-test.md`

## Goal
- Design the first benchmark package that can be used for iteration comparison and later release gating around the trend-aware QA path.

## Scope
- benchmark v1 structure
- `dev / holdout` split
- case inventory and coverage matrix
- trend-evidence usage categories
- scoring execution notes
- asset organization plan under `data/eval/`

## Non-Goals
- do not generate a very large benchmark in this task
- do not run full model scoring in this task
- do not redesign the evaluation policy docs from scratch

## Inputs
- current evaluation policy docs
- current QA / trend integration boundary
- current sample assets under `data/eval/`
- lessons from the E2E smoke test

## Required Outputs
- benchmark v1 package design doc
- first-pass case list or case index
- coverage matrix
- recommended `dev / holdout` split
- asset/file organization recommendation for benchmark v1

## Coverage Rule For V1
- include cases where trend evidence should be used
- include cases where trend evidence may appear but must not dominate the answer
- include cases where missing / stale / weak trend evidence should trigger fallback
- include low-, medium-, and high-risk cases
- include at least one clarification or conservative-answer case per major type

## Suggested Case Bands
- total initial size: `30-40`
- `dev`: `22-30`
- `holdout`: `8-10`

## Execution Boundary
- may change docs under `docs/evaluation/`
- may add planning docs or inventories under `docs/check-issue/50-evaluation/`
- may propose asset layout under `data/eval/`
- should avoid prematurely freezing large asset files if the case list is still unstable

## Implementation Notes
- benchmark v1 should be small but structurally complete
- keep the evaluation package understandable for both PM and engineering roles
- every case should indicate whether `trend_signal` is expected, optional, or intentionally absent
- keep room for later automation, but do not block on automation design now

## Backtest Requirements
- provide the coverage matrix
- provide the draft case count by type and split
- provide one example row or mini-sample for each major case band
- state unresolved dependencies before the benchmark can be frozen

## Acceptance Criteria
- the team can see what benchmark v1 will test and why
- benchmark v1 is aligned with the current QA / trend integration boundary
- the package is concrete enough for collaborative case writing next

## Evidence Required In Return
- changed files
- benchmark package summary
- coverage matrix
- draft case inventory
- open risks

## Suggested Kickoff Instruction
```text
Task ID: EVAL-001
Goal: Design benchmark v1 for the trend-aware QA path so the team can write cases against a clear structure.
Scope: Produce benchmark structure, dev/holdout split, coverage matrix, case inventory, and asset organization plan. Do not expand into large-scale case generation yet.
Non-goals: No full scoring run. No evaluation-policy rewrite from scratch.
Required outputs: changed files, benchmark package summary, coverage matrix, draft case inventory, open risks.
Constraints: align with docs/evaluation/* policy docs and the current QA/trend integration boundary.
Return format:
- changed files
- what was implemented
- benchmark package summary
- open risks
```
