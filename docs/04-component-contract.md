# 04 - Component Contract

## Team split basis
- Engineer A owns upstream volatility (data/trend pipeline)
- Engineer B owns downstream determinism (QA reasoning/safety/eval)
- Product/PM pair owns scenario quality, acceptance, and reporting
- Tech artitecture owns architecture, data contract, domain guardrails

## Engineer A (Data + Trend)
### Inputs
- source connectors
- sampling budget
- trend trigger rules
### Outputs
- normalized datasets
- trend_signals
- data_quality_report
- `BatchBundle` with `batch_version / batch_timestamp / table_row_counts / warnings`
- `RetrievalBundle` with normalized evidence indexes for upper-layer consumption

### Current delivery contract
- `load_batch(batch_path) -> BatchBundle`
- `validate_batch(batch_bundle) -> ValidationReport`
- `build_indexes(batch_bundle) -> RetrievalBundle`
- `search_all(retrieval_bundle, query, intent, filters=None, limit=10) -> list[EvidenceItem]`

### Retrieval input contract
- required: `query`, `intent`
- optional `filters`: `category`, `product_id`, `need_trend`
- `profile_bucket` is reserved for future use and should not be required in MVP

### Evidence output contract
- `EvidenceItem.source_table`
- `EvidenceItem.source_id`
- `EvidenceItem.title`
- `EvidenceItem.snippet`
- `EvidenceItem.score`
- `EvidenceItem.timestamp`
- `EvidenceItem.evidence_type`
- `EvidenceItem.risk_flag`
- `EvidenceItem.metadata`

### Retrieval behavior constraints
- upper-layer modules must consume normalized evidence instead of reading raw tables directly
- `science / compliance` are hard constraints, `trend` is a soft optimization
- high-risk `compliance_rule` evidence should be ranked ahead of non-risk evidence when matched
- when no usable evidence exists, retrieval must return an empty list and expose a missing-info note instead of fabricating support

### Table-to-retrieval mapping
- `ingredient_knowledge`: scientific evidence, keyword-first retrieval
- `product_sku`: product fact evidence, structured filter + keyword retrieval
- `review_feedback`: experience evidence, tag-based retrieval
- `trend_signal`: trend evidence, structured filter + keyword retrieval with freshness weighting
- `compliance_rule`: compliance evidence, keyword-first retrieval with risk flags

## Engineer B (Reasoning + Safety + Eval)
### Inputs
- `RetrievalBundle` and normalized evidence items returned by `search_all(...)`
- normalized data and trend_signals when retrieval-side preprocessing is required
- science knowledge + compliance rules
### Outputs
- QA response pipeline
- compliance-filtered output
- eval_report and ablation_report

### Upstream dependency rules
- answer generation must cite or summarize evidence returned from retrieval
- if retrieval exposes `risk_flag`, the answer layer must preserve the risk signal rather than suppress it
- if retrieval exposes missing-info, the answer layer should prefer explicit insufficiency over strong recommendation

## Product/PM Pair
### Outputs
- scenario definitions
- annotation and acceptance rubric
- mentor sync package
- weekly progress dashboard

## Tech artitecture
- contract freeze
- architecture review
- release/no-release decision based on eval gates
