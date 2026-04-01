# 2026-04-01 Active Docs Audit And Benchmark Prerequisites

## 1. Audit goal
- Check whether the active MVP docs are already stable enough to support a shared evaluation benchmark set.
- Focus only on the current active docs, not on `archive/`, `progress/`, or mentor feedback history.

## 2. What is already stable
- Project direction is stable: retrieval-grounded beauty QA with science and safety as hard constraints.
- Collaboration structure is stable: `archive`, `progress`, `feedback`, and `check-issue` do not need restructuring now.
- Current data boundary is stable enough for benchmark design: `product_sku`, `ingredient_knowledge`, `trend_signal`, `review_feedback`, `compliance_rule`.

## 3. What was missing before this audit
- The repo referenced a frozen MVP question set, but the 4 MVP question types were not explicitly defined in the active docs.
- The minimum answer format existed, but the benchmark-relevant answer states were not written clearly enough.
- The evaluation protocol listed metrics and release gates, but not the benchmark split, case schema, or scoring interpretation.

## 4. What has now been tightened
- `01-mvp-scope.md`
- Added the 4 MVP question types and explicit answer policy.
- `02-system-architecture.md`
- Added question-type routing, runtime answer states, and benchmark-relevant output fields.
- `05-eval-protocol.md`
- Added benchmark scope, split recommendation, case schema, metric rubric, and evaluation rules.
- `07-domain-faq.md`
- Added missing-info handling to the minimum answer format and clarified when the system should avoid a direct answer.
- `10-engineering-workplan.md`
- Aligned the workplan with a frozen benchmark set and question-type breakdown reporting.
- `check-issue/03-testing-experiment-design.md`
- Aligned the task package with the explicit 4-type benchmark scope.

## 5. Current conclusion
- The active docs are now stable enough to start designing the first frozen evaluation benchmark set.
- The next step should not be another broad docs rewrite.
- The next step should be to define the benchmark case template and then let the team co-design the first `30-50` cases against that template.

## 6. Recommended next work package
- Freeze the benchmark schema.
- Create the first shared case bank in spreadsheet form for collaboration.
- Export the frozen `dev` and `holdout` sets into the repo for versioned evaluation.
