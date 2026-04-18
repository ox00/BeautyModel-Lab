# INT-004 + INT-005 Backtest Report

## INT-004 (Series Aggregation)

### Input
- Handoff source:
  - `data/handoff/trend_signal/current/trend_signal_latest.json`
- Includes one keyword (`发酵赋能`) across two day-buckets.

### Execution
- Command:
  - `./.venv/bin/python scripts/run_int004_series_aggregation.py --bucket-type 1d`
- Result:
  - `source_count=4`
  - `series_count=2`
  - output:
    - `data/handoff/trend_signal_series/current.json`
    - `data/handoff/trend_signal_series/history/int004_*.json`

### Checks
- two buckets generated for one keyword/platform
- `delta_vs_prev_bucket` exists and computed:
  - first bucket delta from null baseline
  - second bucket delta from previous bucket (`+40.0` avg trend score)
- traceability preserved via:
  - `signal_ids`
  - `task_ids`

### Fix Coverage (2026-04-18)
- Regression target:
  - dedup consistency between `support_count` and `signal_ids`
  - skip invalid rows with empty `normalized_keyword` / `source_platform`
- Method:
  - replaced handoff fixture temporarily with duplicated `signal_id` and 2 invalid rows
  - ran:
    - `./.venv/bin/python scripts/run_int004_series_aggregation.py --bucket-type 1d`
- Result:
  - output run: `int004_20260418_044320`
  - `source_signal_count=6`, `series_count=2`
  - first bucket:
    - `signal_ids=["TS_FIX_1","TS_FIX_2"]`
    - `support_count=2` (aligned after dedup)
  - invalid rows were ignored (no empty-key series row produced)
- Artifact:
  - `data/handoff/trend_signal_series/history/int004_20260418_044320.json`

## INT-005 (Batch Recovery + Completion Guarantee)

### Schema / Logic Checks
- Added `runtime_batch_items` execution unit state.
- Added batch-level `completion_classification`.
- Recovery service supports:
  - stale running reconciliation
  - requeue planned/retryable
  - completion audit classification (`completed_full` / `completed_partial` / `failed`)

### Repro Sample
- sample fixture:
  - `BeautyQA-TrendAgent/backend/data/samples/int005_recovery_backtest_sample.json`
- includes:
  - interrupted/stale-running item
  - retryable failure item
  - expected completion audit shape

### Runtime Hook Checks
- runtime scheduling path records batch items from scheduled tasks
- task pipeline updates batch item state from task result
- final runtime report now includes completion audit block

### End-to-End Recovery Demo
- Script:
  - `./.venv/bin/python scripts/run_int005_batch_recovery.py --run-id int002_20260418_041947 --stale-minutes 1 --requeue-limit 20`
- Output (real run):
  - no recoverable items for this specific run id (`total_items=0`, classification `completed_full`)
- Additional deterministic runtime demo:
  - output: `BeautyQA-TrendAgent/backend/data/samples/int005_recovery_runtime_demo.json`
  - demonstrates:
    - interrupted/stale-running item reconciled to `requeue_planned`
    - retryable failure preserved
    - completion audit generated (`failed`, with per-status counts)

### Fix Coverage (2026-04-18)
- Regression target:
  - empty batch classification should not be forced to `failed`
  - batch containing unresolved `failed_retryable` should not become `completed_partial`
- Method:
  - created temporary DB fixtures and executed `build_completion_audit` directly
  - persisted output:
    - `BeautyQA-TrendAgent/backend/data/samples/int005_completion_classification_fix_backtest.json`
- Result:
  - empty batch:
    - `total_items=0`
    - `completion_classification=completed_full`
    - `batch_status=completed`
  - succeeded + retryable_failed + no running:
    - `total_items=2`, `succeeded_items=1`, `failed_retryable_items=1`
    - `completion_classification=failed`
    - `batch_status=failed`

## Open Gaps In This Backtest
- Existing DB migration history was partially out-of-sync with schema objects; a minimal environment repair note is recorded in:
  - `BeautyQA-TrendAgent/backend/data/samples/int005_recovery_runtime_demo_note.md`
