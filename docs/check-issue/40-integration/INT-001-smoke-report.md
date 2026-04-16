# INT-001 Smoke Report

## Run Summary
- task: `INT-001`
- shared sample input:
  - `data/pipeline_samples/trend_signal/sample_cleaned_records.json`
- generated first-party contract sample:
  - `data/pipeline_samples/trend_signal/trend_signal_first_party_sample.csv`
- generated grouped JSON sample:
  - `data/pipeline_samples/trend_signal/trend_signal_first_party_sample.json`
- machine-readable smoke report:
  - `data/pipeline_samples/trend_signal/int001_smoke_report.json`

## Stage Result
1. cleaned sample input loaded: `6`
2. grouped `trend_signal` generated: `4`
3. QA runtime ingested shared contract CSV successfully
4. evidence-present case returned `trend_supported`
5. high-risk case returned `trend_filtered_for_safety`
6. stale case returned `trend_weak_or_missing`

## Meaning
- TA side can produce first-party grouped `trend_signal`
- QA side can read the shared handoff sample without vendor internals
- the minimum pipeline is connected:
  - cleaned trend data
  - grouped signal generation
  - QA evidence ingestion
  - graceful fallback

## Open Risks
- this is still a deterministic sample-driven smoke test, not a live production validation
- contract sample currently lives as CSV + JSON artifacts; later repository hardening can replace storage without changing the handoff contract
