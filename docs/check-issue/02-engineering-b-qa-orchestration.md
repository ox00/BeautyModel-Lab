# Task Package - Engineering B

## Goal
- Deliver the grounded QA baseline for the MVP system.
- Build a stable path from user query to evidence-backed answer.

## Scope
- intent classification
- retrieval routing
- evidence assembly
- answer template or prompt template
- compliance and risk note insertion

## Inputs
- retrieval outputs from Engineering A
- frozen MVP question set
- domain rules from `07-domain-faq.md`

## Deliverables
- QA orchestration module
- answer generation baseline
- grounded response format
- risk note and compliance note logic

## Interface Draft
- `classify_intent(query) -> IntentResult`
- `run_qa(query, context=None) -> QAResult`
- `render_answer(evidence_bundle, intent_result) -> QAResponse`

## QA Response Fields
- `answer`
- `evidence_ids`
- `risk_note`
- `compliance_note`
- `missing_info_note`

## Acceptance Criteria
- Supports at least four MVP question types:
- scientific skincare QA
- ingredient risk QA
- trend-aware QA
- product recommendation explanation
- Every final answer includes evidence ids.
- Compliance-related answers include constraints when matching rules exist.

## Dependencies
- Depends on Engineering A retrieval interfaces.
- Depends on benchmark questions prepared by testing and evaluation owners.

## Coordination Notes
- Intent taxonomy must stay stable during the first MVP cycle.
- Response format should be fixed before the first evaluation run.

## Out Of Scope
- full agent system
- model distillation
- production UI
