# QA-004 - Trend Evidence Layer Integration

## Metadata
- Task ID: `QA-004`
- Module: `BeautyQA-core`
- Owner Type: `qa-owner / engineer / dev-agent`
- Status: `ready`
- Related Contract Docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`
  - `docs/16-trend-signal-to-qa-usage-guide.md`

## Goal
- Implement the QA evidence layer around first-party `trend_signal` so that downstream QA / RAG can consume trend evidence through a clear ingestion, retrieval, filtering, and context-block interface.

## Scope
- first-party `trend_signal` ingestion
- evidence item parsing
- retrieval and metadata-filter hooks
- trend context block output for downstream QA / RAG
- trace / debug field retention

## Non-Goals
- do not implement the final QA answer policy here
- do not redesign the full QA / RAG system here
- do not pull in vendor crawler dependencies
- do not redefine the trend-signal contract here

## Inputs
- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/16-trend-signal-to-qa-usage-guide.md`
- shared handoff sample under `data/pipeline_samples/trend_signal/`

## Required Outputs
- runtime ingestion path for first-party `trend_signal`
- evidence item representation
- retrieval/filter interface
- trend context block representation
- backtest or example output showing downstream-ready evidence package

## Contract Constraints
- runtime reads first-party `trend_signal` only
- retrieval should use `normalized_keyword / topic_cluster / trend_type / signal_summary / signal_evidence`
- metadata filter should preserve `fresh_until / confidence / risk_flag / trend_score`
- trace/debug fields such as `signal_id / source_url / support_count / evidence_ids` should remain accessible
- final answer governance remains owned by the main QA system

## Execution Boundary
- may change `BeautyQA-core/`
- may add or refine `trend_evidence` package interfaces
- may add tests, fixtures, and backtest helpers
- must not expand into main QA answer-policy ownership

## Implementation Notes
- separate evidence item layer from trend context block layer
- keep one path suitable for indexing / retrieval
- keep one path suitable for downstream prompt or orchestration input
- preserve explainability and traceability for engineering review

## Backtest Requirements
- show one parsed evidence item example
- show one trend context block example
- show one query retrieval example
- show one weak/stale/high-risk metadata example

## Acceptance Criteria
- QA evidence layer can parse and expose first-party `trend_signal`
- downstream QA / RAG can consume a clear trend context block
- retrieval/filter fields and trace/debug fields are both available
- module boundary remains limited to evidence-layer responsibility

## Evidence Required In Return
- changed files
- implementation summary
- sample trend context block
- backtest result
- open risks

## Suggested Kickoff Instruction
```text
Task ID: QA-004
Goal: Implement the QA trend evidence layer around first-party trend_signal for downstream QA/RAG use.
Scope: Work only in BeautyQA-core. Focus on trend_signal ingestion, evidence parsing, retrieval/filter hooks, and trend context block output. Do not take ownership of final answer policy.
Non-goals: No vendor dependency. No full QA engine redesign. No final answer-governance implementation.
Required outputs: changed files, implementation summary, sample trend context block, backtest result, open risks.
Constraints: follow docs/14-trendagent-to-qa-data-contract.md, docs/15-trend-signal-schema.md, and docs/16-trend-signal-to-qa-usage-guide.md.
Return format:
- changed files
- what was implemented
- backtest result
- open risks
```
