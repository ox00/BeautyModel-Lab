# Task Package - Engineering A

## Goal
- Deliver the data-facing baseline for the MVP system.
- Freeze the reusable interfaces for data contracts, batch loading, and retrieval indexing.

## Scope
- `P0` schema contracts
- batch loader
- batch validation
- retrieval index
- evidence search interface

## Inputs
- `product_sku`
- `review_feedback`
- `trend_signal`
- `ingredient_knowledge`
- `compliance_rule`

## Deliverables
- loader interfaces for all five `P0` tables
- schema validation report
- retrieval index build process
- search interface returning normalized evidence items

## Interface Draft
- `load_batch(batch_path) -> BatchBundle`
- `validate_batch(batch_bundle) -> ValidationReport`
- `build_indexes(batch_bundle) -> RetrievalBundle`
- `search_all(query, intent) -> list[EvidenceItem]`

## Evidence Item Fields
- `source_table`
- `source_id`
- `title`
- `snippet`
- `score`
- `metadata`

## Acceptance Criteria
- Current baseline batch loads without schema errors.
- Duplicate and required-field checks run automatically.
- Search can return evidence from product, ingredient, trend, and compliance tables.
- Compliance questions can retrieve at least one compliance evidence item when the rule exists.

## Dependencies
- Depends on current `P0` delivery package only.
- Should not wait for model training or distillation loop.

## Coordination Notes
- Data pipeline changes and retrieval interfaces should align on stable field names.
- Any schema change must be reflected back into `03-data-contract.md`.

## Out Of Scope
- answer generation
- prompt design
- online serving
- model fine-tuning
