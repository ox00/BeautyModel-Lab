# 05 - Experiment Log Template

## Required header
- benchmark version
- data batch version
- system version
- evaluation date
- reviewers

## Metric note
- `latency_p95` means the p95 end-to-end response time for benchmark cases, measured from query input to final answer output.
- It should include retrieval, reasoning, compliance checks, and final answer assembly, rather than only one module such as model generation.

## Comparison table

| system_version | benchmark_version | split | correctness | completeness | safety | trend_freshness | explainability | hallucination_rate | latency_p95 | notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| example_v1 | benchmark_v1 | holdout | 1.5 | 1.3 | 1.9 | 1.4 | 1.5 | 0.03 | 4.2 | first runnable baseline |

## Required notes
- major failure patterns
- high-risk case outcomes
- question-type breakdown summary
- release or no-release decision
- next action items
