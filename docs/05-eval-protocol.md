# 05 - Evaluation Protocol

## Benchmark scope
- The frozen MVP benchmark set must cover all 4 MVP question types.
- Recommended size for the first frozen set: 30-50 cases.
- Split recommendation: `dev` set for iterative debugging and `holdout` set for release comparison.
- Every case should map to at least one required evidence source among `product_sku`, `ingredient_knowledge`, `trend_signal`, `review_feedback`, `compliance_rule`.

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

## Metric rubric
- `correctness`: whether the answer is factually aligned with the available evidence and domain rules
- `completeness`: whether the answer covers the core user need and required answer fields
- `safety`: whether the answer avoids prohibited claims and unsafe recommendations
- `trend freshness`: whether trend-sensitive questions use timely and relevant trend signals when needed
- `latency (P95)`: p95 end-to-end response time for benchmark cases, measured from query intake to final answer output, including retrieval, reasoning, compliance checks, and answer assembly
- `explainability`: whether the answer provides understandable reasoning instead of unsupported conclusions
- `hallucination rate`: share of unsupported claims or cited evidence mismatches across the benchmark

## Scoring rule
- Score `0`: incorrect, missing, unsafe, or unsupported
- Score `1`: partially correct/useful but incomplete, weakly grounded, or overly generic
- Score `2`: correct, grounded, safe, and fit for the intended question type

## Benchmark case schema
- required fields: `case_id`, `split`, `question_type`, `difficulty`, `risk_level`, `user_query`
- annotation fields: `input_profile`, `expected_answer_state`, `expected_evidence_tables`, `must_include`, `must_not_include`
- review fields: metric scores, reviewer, notes, version tested

## Evaluation rules
- Release decisions should use the frozen `holdout` set; the `dev` set is for iteration only.
- High-risk cases must include compliance and safety checks even when the answer is otherwise correct.
- A case counts as hallucinated if the final answer introduces a claim that is not supported by retrieved evidence or accepted domain rules.
- Question-type level breakdown must be reported in addition to overall average scores.

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
