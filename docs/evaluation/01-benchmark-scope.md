# 01 - Benchmark Scope

## Goal
- Build one frozen benchmark set that supports model iteration, version comparison, and release gating for the beauty QA MVP.

## Scope
- Cover all 4 MVP question types:
- skincare recommendation and regimen direction
- ingredient suitability and risk clarification
- trend-aware alternative suggestion
- compliance and claim safety clarification

## Split design
- `dev`: visible to the team and used for iterative debugging
- `holdout`: frozen for release comparison and no-release decisions

## Recommended size
- first version total: `30-50` cases
- recommended ratio: `70-80%` `dev`, `20-30%` `holdout`

## Coverage requirements
- Every question type must appear in both `dev` and `holdout`.
- Every benchmark version must include low-, medium-, and high-risk cases.
- Every benchmark version must include some cases that require clarification, conservative answering, or refusal/constraint behavior.
- Every case must map to at least one required evidence table among `product_sku`, `ingredient_knowledge`, `trend_signal`, `review_feedback`, `compliance_rule`.

## Non-goals
- no external user study in this stage
- no free-form open-domain beauty chat benchmark
- no benchmark expansion beyond the current MVP data boundary
