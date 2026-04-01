# 01 - MVP Scope (Frozen)

## Goal
Deliver one runnable QA advisor that balances:
- scientific skincare correctness
- trend responsiveness

## In Scope (MVP)
- text-only QA interaction
- user inputs: skin concern, skin type bucket, budget bucket, optional trend preference
- dual evidence output: scientific rationale + trend rationale
- compliance filtering before final answer
- baseline and ablation evaluation

## Out of Scope (MVP)
- multimodal image makeup transfer
- personalized long-term profile modeling at user identity level
- real-time high-frequency streaming architecture
- full-scale production deployment

## Core scenarios
- Scenario A (Primary): scientific skincare recommendation QA
- Scenario B (Secondary): trend-aware alternative suggestion (same query session)

## MVP question types
- Type 1: skincare recommendation and regimen direction
- Type 2: ingredient suitability and risk clarification
- Type 3: trend-aware alternative suggestion
- Type 4: compliance and claim safety clarification

## Answer policy
- If required user information is missing, the system should ask a focused follow-up instead of giving a strong recommendation.
- If trend preference conflicts with science or safety, science and safety win as hard constraints.
- If evidence is insufficient or conflicting, the system should give a conservative answer with an explicit uncertainty note.
- The MVP does not provide medical diagnosis or treatment advice.

## Definition of Done
- 3 baselines completed
- 3 ablations completed
- safety gate enabled
- one end-to-end demo and report package
