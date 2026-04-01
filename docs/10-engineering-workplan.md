# 10 - Engineering Workplan

## 1. Goal
- Build the MVP for a beauty QA advisor focused on scientific skincare plus trend-aware recommendations.
- Freeze the current engineering scope around retrieval, grounding, compliance checks, and evaluation.
- Use the current `P0` package as the single baseline for the first runnable system.

## 2. Current Inputs
- `product_sku`
- `review_feedback`
- `trend_signal`
- `ingredient_knowledge`
- `compliance_rule`

These five tables are enough for the first engineering loop. Do not add more data entities before the MVP pipeline runs end-to-end.

## 3. Engineering Split
- Technical lead / data owner: maintain data contracts, batch delivery, evaluation protocol, architecture decisions.
- Engineer A: build data access layer, schema validation, loaders, local indexes, and retrieval services.
- Engineer B: build QA orchestration, prompt assembly, evidence grounding, and answer generation flow.
- PM / product side: define user question set, acceptance criteria, demo script, and weekly status sync.

## 4. System Modules
- `data-loader`: reads `P0/P1` package, validates schema, versions batches.
- `retrieval-core`: supports product, ingredient, trend, and compliance retrieval.
- `qa-orchestrator`: classifies query intent and routes to the right retrieval mix.
- `answer-builder`: assembles evidence-backed answer with confidence and safety notes.
- `eval-runner`: runs offline benchmark set and compares versions.

## 5. Recommended Repo Structure
- `scripts/`: data cleaning and batch build scripts
- `data/deliveries/`: versioned delivery packages
- `src/loaders/`: schema and table readers
- `src/retrieval/`: hybrid retrieval logic
- `src/pipeline/`: QA orchestration
- `src/eval/`: benchmark and scoring
- `tests/`: loader, retrieval, and pipeline tests

## 6. Two-Week Plan
1. Week 1: freeze schema and implement loaders for all five `P0` tables.
2. Week 1: build retrieval endpoints for product, ingredient, trend, and compliance evidence.
3. Week 1: freeze 30-50 benchmark cases across the 4 MVP question types and expected answer format.
4. Week 2: implement QA orchestration and evidence-grounded answer generation.
5. Week 2: add compliance guardrails and trend freshness checks.
6. Week 2: run offline evaluation and produce a demo-ready version.

## 7. Module Contracts
- Input to pipeline: user query, optional profile bucket, optional target product/category.
- Output from retrieval: ranked evidence items with source table, source id, score, and snippet.
- Output from answer builder: final answer, cited evidence ids, risk note, missing-info note.
- Output from evaluation: accuracy, grounding quality, compliance miss rate, trend freshness hit rate, and question-type breakdown.

## 8. Definition Of Done
- Loaders pass schema validation on the current `P0` batch.
- Retrieval returns usable evidence for each major question type.
- QA pipeline answers the frozen MVP question set end-to-end.
- Compliance-related questions always include rule-based constraints when available.
- The frozen benchmark set distinguishes `dev` and `holdout` usage.
- Every release has a batch version, manifest, and evaluation summary.

## 9. Immediate Priorities
- Priority 1: implement `P0` loader plus retrieval index.
- Priority 2: implement minimal QA orchestration with grounded evidence.
- Priority 3: construct `P2` holdout evaluation set.
- Priority 4: start distillation only after the retrieval-grounded baseline is stable.

## 10. Non-Goals For This Stage
- No full model training pipeline yet.
- No broad user profile modeling yet.
- No production deployment concerns yet.
- No extra data domains beyond the current five `P0` tables.
