# Task Package - Architecture / Domain / Data Owner

## Goal
- Keep the MVP technically coherent, domain-correct, and data-governed.
- Own the production side of the batch loop: data pipeline, compliance and trend refresh, evaluation gate, and distillation gate.

## Scope
- batch delivery planning
- data pipeline maintenance
- compliance and trend updates
- evaluation protocol and release gate
- distillation loop design and data readiness gate

## Core Responsibilities
- freeze and revise data contracts when needed
- maintain `P0/P1/P2` boundaries
- decide whether a new batch is fit for engineering consumption
- decide whether a version is fit for evaluation or distillation
- maintain alignment between domain rules and system behavior

## Deliverables
- versioned batch delivery package
- quality and risk notes for each batch
- compliance and trend update summary
- benchmark and evaluation gate definition
- distillation sample policy and rejection rules

## Interface Draft
- `publish_batch(batch_version) -> DeliveryManifest`
- `approve_for_engineering(batch_version) -> BatchGateResult`
- `approve_for_eval(run_version) -> EvalGateResult`
- `approve_for_distillation(sample_pack) -> DistillGateResult`

## Acceptance Criteria
- Every shared batch has a manifest, quality report, and explicit scope note.
- Compliance and trend updates are traceable to source refreshes.
- Engineering receives stable field names and stable version identifiers.
- Evaluation gate is explicit before any model or pipeline comparison is announced.
- Distillation only starts after retrieval-grounded baseline is stable.

## Dependencies
- depends on data source refresh and cleaning scripts
- coordinates directly with Engineering A on schema and retrieval-facing fields
- coordinates directly with Engineering B on answer boundary and safety rules
- coordinates with testing and reporting owners on benchmark and summary outputs

## Coordination Notes
- This package is upstream to engineering and downstream to raw data updates.
- Scope should stay narrow: improve batch quality and decision quality, not add new business lines.

## Out Of Scope
- full-time implementation of all engineering modules
- proposal rewriting
- ad hoc data sharing outside the agreed package boundary
