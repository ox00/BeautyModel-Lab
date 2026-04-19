# QA-004 Runtime Closure Note

## Date

2026-04-19

## Purpose

This note records the closure of the QA-side runtime handoff path for `QA-004`.

The target question was:

`Can BeautyQA-core read the real first-party runtime handoff, assemble trend evidence, and produce a downstream-ready trend context block without depending on TrendAgent internals or vendor crawler internals?`

## Result

Answer: yes, at the QA evidence-layer level.

The QA-side runtime closure now includes:

- runtime ingestion from:
  - `data/handoff/trend_signal/current/trend_signal_latest.json`
- contract-only parsing through `TrendSignalRepository`
- retrieval and evidence qualification through `QAPipeline`
- downstream-ready `trend context block` generation

## What Was Added

- runtime JSON contract loader in `BeautyQA-core/src/trend_evidence/trend_retrieval.py`
- trend context block representation in `BeautyQA-core/src/trend_evidence/models.py`
- context-block builder and default runtime handoff path helpers in `BeautyQA-core/src/trend_evidence/pipeline.py`
- runtime smoke / backtest script:
  - `BeautyQA-core/scripts/run_backtest_qa004_runtime.py`
- direct assertion check:
  - `BeautyQA-core/scripts/check_qa004_runtime.py`

## Runtime Smoke Evidence

Current runtime smoke reads the real handoff file and returns:

- `behavior_flag=trend_filtered_for_safety`
- top keyword: `快速美白`
- top platform: `bilibili`
- top risk flag: `high`
- one context item generated successfully

This is the expected result for the current handoff payload because the latest exported signal is a high-risk trend signal and should not become strong evidence.

## Boundary Confirmation

This closure confirms:

- QA runtime reads first-party handoff only
- QA does not read vendor raw tables
- QA does not need crawler runtime metadata to assemble evidence
- risk / freshness / confidence remain exposed as evidence-layer metadata
- final answer governance is still outside this layer

## What This Does Not Claim

This note does not claim:

- full QA answer-policy completion
- production-ready benchmark coverage
- full multi-platform runtime stability

It only closes the runtime handoff boundary from:

`TrendAgent first-party export -> QA evidence-layer runtime ingestion`

## New Bottom Line

The project can now credibly say:

`TrendAgent to QA runtime data handoff is closed at the evidence-layer boundary.`
