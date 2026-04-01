# 06 - Collaboration Workflow

## Goal
- Let the team co-design the benchmark set efficiently without turning the process into an engineering bottleneck.

## Recommended ownership
- `2 PM + 1 data/domain owner` should lead the benchmark drafting and cleanup work.
- Engineers do not need to co-author the full case bank in the current stage.
- Engineers should only join at the feasibility-check and freeze-check points.

## Suggested role split
- PM A
- draft user-facing queries
- keep wording natural and scenario-driven
- make sure each case reflects a realistic user need

- PM B
- refine `must_include` and `must_not_include`
- check readability, usefulness, and business-facing clarity
- help control duplicated or overly similar cases

- Data/domain owner
- assign `question_type`, `risk_level`, and `expected_answer_state`
- verify evidence-table mapping
- do final merge and freeze decisions

- Engineer A or B
- optional checkpoint reviewer for system feasibility
- confirm whether the current pipeline can realistically retrieve the needed evidence

## Workflow
1. Draft cases in the shared seed files or a synchronized spreadsheet copy.
2. Label each case with `question_type`, `risk_level`, and `expected_answer_state`.
3. Fill `expected_evidence_tables`, `must_include`, and `must_not_include`.
4. Remove duplicates and merge near-identical cases.
5. Run one engineering feasibility check before freezing.
6. Freeze the selected `dev` and `holdout` subsets into the repo.

## Working rules
- One case should test one primary decision point.
- Do not freeze a case that depends on data the current MVP does not have.
- Do not let trend cases become pure marketing questions with no science or safety angle.
- High-risk cases should be reviewed twice before they enter the frozen set.
- Keep `seed` assets editable and treat frozen benchmark files as versioned artifacts.

## When engineers should be involved
- when the team is unsure whether a case is retrievable with the current data
- when a case depends on answer fields not produced by the current pipeline
- when the frozen set is about to be used for version comparison or release gating

## Current recommendation
- Use the current `36` starter cases as the shared drafting base.
- Let the three-person product/domain group do the first cleanup pass.
- Ask engineering for one short feasibility pass only after the first cleanup pass is complete.
