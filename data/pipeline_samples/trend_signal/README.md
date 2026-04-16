# Trend Signal Pipeline Samples

This folder stores shared pipeline-level samples for the TA -> QA handoff.

Files:
- `sample_cleaned_records.json` - deterministic cleaned-record input for TA-002 / INT-001
- `trend_signal_first_party_sample.csv` - shared first-party contract sample for QA-side ingestion
- `trend_signal_first_party_sample.json` - grouped trend_signal JSON export sample
- `int001_smoke_report.json` - latest smoke-test report

Working rule:
- this folder is the shared handoff sample layer
- `BeautyQA-core/tests/fixtures/` may keep local test copies if needed, but it is not the source of truth
