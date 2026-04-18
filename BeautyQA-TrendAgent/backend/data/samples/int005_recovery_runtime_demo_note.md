# INT-005 Runtime Demo Note

## Environment Fix During Demo

During the real recovery demo, DB schema state was partially ahead of Alembic version history:

- tables `runtime_batch_items` and `trend_signal_series` already existed
- `alembic_version` was still `98d4a7b21f33`
- new column `runtime_batch_runs.completion_classification` was missing

To unblock validation, the following minimal repair was applied:

1. `ALTER TABLE runtime_batch_runs ADD COLUMN IF NOT EXISTS completion_classification VARCHAR(24)`
2. `UPDATE alembic_version SET version_num='b31ce6892e4b' WHERE version_num='98d4a7b21f33'`

This keeps runtime behavior aligned with INT-004/005 code changes for this thread.
