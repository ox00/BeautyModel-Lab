# GitHub Tracking Issue 草稿

## 推荐标题
`MVP engineering kickoff with baseline data v1`

## 推荐标签
- `planning`
- `mvp`
- `data`
- `engineering`

## 正文草稿
```md
## Background
We have completed the first baseline data delivery for the BeautyModel-Lab MVP and now have a stable `P0` package for engineering kickoff.

The current MVP direction is a QA advisor for scientific skincare plus trend-aware beauty recommendations.

## Current Available Inputs
- `product_sku`
- `review_feedback`
- `trend_signal`
- `ingredient_knowledge`
- `compliance_rule`

## Current Data Deliverables
- baseline cleaned package: `data/deliveries/2026-03-14-baseline-v1/`
- cleaning script: `scripts/clean_baseline_0312.py`
- compliance extraction script: `scripts/build_compliance_rules_v1.py`
- intake checklist: `docs/09-data-intake-checklist.md`
- engineering plan: `docs/10-engineering-workplan.md`

## Scope For MVP Engineering
- freeze the current five `P0` tables as the baseline input
- build a retrieval-grounded QA pipeline before any training loop
- include compliance evidence in safety-sensitive answers
- prepare a small offline holdout evaluation set

## Target Outcome
By the end of the first engineering cycle, the team should have:
- a runnable loader for all five `P0` tables
- a retrieval layer for product, ingredient, trend, and compliance evidence
- a minimal QA orchestration flow
- an offline evaluation runner for the MVP question set

## Task Checklist
- [ ] implement schema validation and loaders for all `P0` tables
- [ ] build retrieval index and retrieval service
- [ ] implement grounded QA orchestration
- [ ] prepare MVP benchmark questions and holdout set
- [ ] refine compliance taxonomy and clause lineage

## Current Known Gaps
- `review_feedback.rating_bucket` is missing in the current source batch
- `trend_signal` is monthly-growth based in the current batch
- `compliance_rule` is first-pass structured and still needs taxonomy refinement
- no `P2` holdout package has been frozen yet

## Working Rule
- each engineering task should land in a separate PR
- each PR should reference this tracking issue
- do not expand data scope before the retrieval-grounded MVP is runnable
```

## 使用建议
- 这份内容适合直接复制为 GitHub issue 正文。
- 由你来发最合适，因为你本身承担架构、domain、数据和业务把控角色。
- 这能明确你是阶段 owner，同时避免工程同学各自理解不一致。
