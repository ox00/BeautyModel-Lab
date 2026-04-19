# INT-006 - TA To QA Runtime Smoke Report

## Date

2026-04-19

## Purpose

Record one formal runtime smoke proving the handoff path from TrendAgent to BeautyQA-core works on the real first-party export artifact.

## Scope

This report covers only:

- TrendAgent runtime export handoff
- QA evidence-layer runtime ingestion
- trend context block assembly

This report does not claim:

- full QA RAG integration
- full QA answer policy completion
- benchmark completion
- full multi-platform live regression completion

## Source Runtime

- source `INT-002` runtime run:
  - `int002_20260418_044745`
- export run:
  - `int003_20260418_050846_923620`

## Handoff Files

- `data/handoff/trend_signal/current/trend_signal_latest.csv`
- `data/handoff/trend_signal/current/trend_signal_latest.json`
- `data/handoff/trend_signal/current/manifest.json`

Manifest check:

- `source_mode=batch_events`
- `source_runtime_run_ids=["int002_20260418_044745"]`
- `exported_row_count=1`

## QA Runtime Check

Command:

```bash
cd BeautyQA-core
PYTHONPATH=src ../.venv/bin/python scripts/check_qa004_runtime.py
PYTHONPATH=src ../.venv/bin/python scripts/run_backtest_qa004_runtime.py
```

Observed result:

- runtime handoff file exists
- QA contract loader reads the real JSON handoff successfully
- one trend context block is produced
- `behavior_flag=trend_filtered_for_safety`
- top `signal_id=TS_20260418_23_22`
- top keyword: `快速美白`
- top platform: `bilibili`
- top risk flag: `high`
- top confidence: `medium`

## Interpretation

This is the expected result for the current payload.

The latest exported signal is high-risk, so QA should ingest it, retain trace metadata, and keep it out of the strong-evidence path.

That means the smoke is successful because:

- the handoff contract is readable
- the evidence layer can parse and rank the signal
- the safety boundary is preserved
- downstream QA receives a usable context block instead of raw crawler data

## Closure Statement

The accurate closure statement is:

`TrendAgent -> QA runtime data handoff is closed at the evidence-layer boundary.`

More specifically:

- TrendAgent is responsible for producing first-party `trend_signal` evidence
- QA evidence layer is responsible for reading and filtering that evidence
- QA main system remains responsible for later RAG integration and final answer governance

## Open Risks

- current smoke is based on one exported signal, not a wider multi-keyword runtime wave
- multi-platform repeated live regression still needs broader baseline reruns
- benchmark v1 is still pending

## Suggested Next Step

Run the frozen baseline regression wave before widening to all keywords:

- control seed first
- then normal business seeds
- risk seed last
- export again after successful runtime runs
