# 05 - Evaluation Protocol

## Baselines
- Baseline A: scientific-only QA
- Baseline B: trend-only recommendation
- Baseline C: general LLM assistant

## Metrics
- correctness
- completeness
- safety
- trend freshness
- latency (P95)
- explainability
- hallucination rate

## Ablations
- w/o trend engine
- w/o compliance gate
- w/o distillation flywheel

## Release gates (MVP)
- correctness >= 1.4/2
- completeness >= 1.2/2
- safety >= 1.8/2
- high-risk violation = 0
- latency P95 <= 5s

## Required reports
- sampling report
- data quality report
- eval report
- risk report
- rollback plan
