# 04 - Component Contract

## Team split basis
- Engineer A owns upstream volatility (data/trend pipeline)
- Engineer B owns downstream determinism (QA reasoning/safety/eval)
- Product/PM pair owns scenario quality, acceptance, and reporting
- Tech artitecture owns architecture, data contract, domain guardrails

## Engineer A (Data + Trend)
### Inputs
- source connectors
- sampling budget
- trend trigger rules
### Outputs
- normalized datasets
- trend_signals
- data_quality_report

## Engineer B (Reasoning + Safety + Eval)
### Inputs
- normalized data and trend_signals
- science knowledge + compliance rules
### Outputs
- QA response pipeline
- compliance-filtered output
- eval_report and ablation_report

## Product/PM Pair
### Outputs
- scenario definitions
- annotation and acceptance rubric
- mentor sync package
- weekly progress dashboard

## Tech artitecture
- contract freeze
- architecture review
- release/no-release decision based on eval gates
