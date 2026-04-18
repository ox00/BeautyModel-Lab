# Trend Signal Runtime Handoff

This directory stores the runtime handoff outputs for QA consumption.

## Structure

- `current/`
  - stable latest export files for QA runtime
- `history/`
  - immutable export snapshots by export run id

## Expected runtime files

Under `current/`:

- `trend_signal_latest.csv`
- `trend_signal_latest.json`
- `manifest.json`

Under `history/<run_id>/`:

- `trend_signal_latest.csv`
- `trend_signal_latest.json`
- `manifest.json`

## Rule

QA should read `current/` only.

History snapshots are for:

- audit
- replay
- diff inspection
- rollback support
