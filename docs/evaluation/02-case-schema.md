# 02 - Case Schema

## Required fields
- `case_id`: stable unique identifier
- `split`: `dev` or `holdout`
- `question_type`: one of the 4 MVP question types
- `difficulty`: `easy`, `medium`, or `hard`
- `risk_level`: `low`, `medium`, or `high`
- `user_query`: original user wording

## Annotation fields
- `input_profile`: optional structured user context such as skin type, concern, or budget
- `expected_answer_state`: `direct_answer`, `clarification`, `conservative_answer`, or `refusal_constraint`
- `expected_evidence_tables`: expected supporting tables
- `must_include`: required answer points
- `must_not_include`: prohibited claims, unsafe suggestions, or common failure modes
- `notes`: optional reviewer notes on edge cases or ambiguity

## Review fields
- `correctness_score`
- `completeness_score`
- `safety_score`
- `trend_freshness_score`
- `explainability_score`
- `hallucination_flag`
- `reviewer`
- `review_notes`
- `system_version`

## Case writing rules
- One case should test one primary conflict or decision point.
- Queries should sound like plausible user requests, not internal test prompts.
- Cases must be answerable within the current MVP scope and data boundary.
- If a case depends on unavailable data, it should not enter the frozen set.
