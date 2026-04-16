# QA-003 - Trend Evidence Boundary Tightening

## Metadata
- Task ID: `QA-003`
- Module: `BeautyQA-core`
- Owner Type: `qa-owner / engineer / dev-agent`
- Status: `ready`
- Related Contract Docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`
- Related Background:
  - `docs/check-issue/30-qacore/QA-001-trend-signal-retrieval-integration.md`
  - `docs/check-issue/30-qacore/QA-002-risk-gating-and-contract-hardening.md`

## Goal
- Tighten the QA-side trend integration back to the intended boundary: first-party `trend_signal` ingestion, retrieval, and evidence assembly for downstream RAG use.

## Why This Task Exists
- `QA-001` correctly established the trend-signal ingestion direction.
- `QA-002` pushed further into answer-policy territory.
- The project owner clarified that final safety / compliance hard constraints belong to the main QA / RAG answer system, not to this trend-signal integration subtask.

This task is a boundary-tightening task, not a negation of previous work.

## Scope
- contract-only runtime ingestion
- retrieval and ranking hooks for `trend_signal`
- evidence assembly for downstream QA / RAG
- metadata pass-through:
  - `fresh_until`
  - `confidence`
  - `risk_flag`
  - `source_platform`
  - `source_url`
- graceful fallback when trend data is absent or weak

## Non-Goals
- do not finalize safety answer policy here
- do not finalize compliance answer policy here
- do not encode project-wide medical / efficacy decision rules here
- do not redesign the full QA answer engine here

## Inputs
- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- current `BeautyQA-core` trend retrieval implementation
- current QA / RAG integration direction from the QA owner

## Required Outputs
- QA runtime path that cleanly reads first-party `trend_signal`
- retrieval/evidence assembly layer suitable for downstream RAG usage
- explicit metadata output or hook surface for freshness / confidence / risk
- rollback note explaining what was tightened or downgraded from QA-002 behavior

## Contract Constraints
- QA runtime reads first-party `trend_signal` only
- no vendor crawler dependency may be introduced
- trend module may expose metadata and evidence quality flags
- final answer governance remains owned by the main QA / RAG system

## Execution Boundary
- may change `BeautyQA-core/`
- may simplify or downgrade answer-policy logic introduced by `QA-002`
- may keep safety-related fields as metadata, filter flags, or hook inputs
- must not redefine project-wide QA hard-constraint policy in this task

## Implementation Notes
- if `QA-002` already introduced strong safety gating into runtime answers, convert it to:
  - metadata / flag output
  - retrieval-side evidence qualification
  - or pluggable hook points for the QA owner
- keep `stale`, `low_confidence`, and `high_risk` visible to downstream QA logic
- it is acceptable to keep lightweight retrieval-side downgrading, but not to let this task own final answer policy
- contract boundary hardening from `QA-002` may remain if it serves ingestion clarity

## Backtest Requirements
- show one case where trend evidence is retrieved and passed through to QA/RAG
- show one case where trend evidence is missing or stale and QA path degrades gracefully
- show one example of `risk_flag` being exposed to downstream logic without this task claiming final safety policy ownership
- summarize what was kept from `QA-002` and what was intentionally tightened back

## Acceptance Criteria
- QA-side module is clearly positioned as trend evidence ingestion / retrieval / assembly
- final safety/compliance answer policy is not hard-coded as the responsibility of this subtask
- first-party contract boundary remains clear
- downstream QA engineer can use the output without needing crawler internals

## Evidence Required In Return
- changed files
- implementation summary
- rollback / tightening summary
- backtest result
- open risks

## Suggested Kickoff Instruction
```text
Task ID: QA-003
Goal: Tighten QA trend integration back to the intended boundary: first-party trend_signal ingestion, retrieval, and evidence assembly for downstream QA/RAG use.
Scope: Work only in BeautyQA-core. Keep contract-only ingestion and retrieval/evidence assembly, but do not let this task own final safety/compliance answer policy.
Non-goals: No vendor crawler dependency. No project-wide answer-policy ownership. No full QA engine redesign.
Required outputs: changed files, implementation summary, rollback/tightening summary, backtest result, open risks.
Constraints: follow docs/14-trendagent-to-qa-data-contract.md, docs/15-trend-signal-schema.md, and docs/check-issue/30-qacore/QA-003-trend-evidence-boundary-tightening.md.
Return format:
- changed files
- what was implemented
- rollback/tightening summary
- backtest result
- open risks
```
