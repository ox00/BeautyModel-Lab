# 03 - Data Contract

## Data levels
- P0: trainable package (safe and controlled)
- P1: restricted access (feature/API only)
- P2: blind-test holdout

## MVP tables
- product_sku
- ingredient_knowledge
- trend_signal
- review_feedback
- compliance_rule
- profile_bucket (optional, anonymized only)

## Quality gates
- key uniqueness: 100%
- completeness: >= 95%
- duplicate rate: <= 2%
- timestamp validity: >= 98%
- trend freshness: <= 7 days

## Update cadence
- compliance rules: monthly or policy-triggered
- ingredient knowledge: weekly
- trend signals: daily + event trigger
- reviews/feedback: daily batch

## Privacy and compliance
- no PII in training/export artifacts
- minimum necessary principle
- course-research-only data usage
