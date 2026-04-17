# INT-003 - Trend Signal Export Cron

## Metadata
- Task ID: `INT-003`
- Module: `BeautyQA-TrendAgent + shared data handoff`
- Owner Type: `dev-agent / engineer / architecture-support`
- Status: `ready`
- Related Docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`
  - `docs/16-trend-signal-to-qa-usage-guide.md`
- Related Upstream Tasks:
  - `docs/check-issue/20-trendagent/TA-002-trend-signal-generation-layer.md`
  - `docs/check-issue/40-integration/INT-002-trendagent-crawler-runtime-link.md`

## Goal
- Add a stable scheduled export job that publishes first-party `trend_signal` into a QA-consumable CSV handoff directory.

## Why This Task Exists
- the current sample CSV path under `data/pipeline_samples/trend_signal/` is for shared sample and smoke only
- QA should not depend on sample fixtures for runtime data
- the project needs a stable, repeated, file-based handoff path before broader QA integration
- export cron should be able to read first-party runtime batch history instead of guessing from ad hoc files

## Core Position
- runtime export path and sample path must be separated
- QA should read one stable handoff CSV, not scan per-task JSON files directly
- the export job should be first-party and idempotent

## Recommended Runtime Handoff Directory
- `data/handoff/trend_signal/current/`
- `data/handoff/trend_signal/history/`

Recommended files:
- `data/handoff/trend_signal/current/trend_signal_latest.csv`
- `data/handoff/trend_signal/current/trend_signal_latest.json`
- `data/handoff/trend_signal/current/manifest.json`

History snapshots:
- `data/handoff/trend_signal/history/<run_id>/trend_signal_latest.csv`
- `data/handoff/trend_signal/history/<run_id>/trend_signal_latest.json`
- `data/handoff/trend_signal/history/<run_id>/manifest.json`

## Source And Sink

### Source
- `BeautyQA-TrendAgent/backend/data/trend_signal/{platform}/*.json`

### Sink
- stable QA handoff CSV in `data/handoff/trend_signal/current/`

## Export Rules
1. scan latest first-party `trend_signal` JSON outputs
2. flatten signal records into contract CSV rows
3. deduplicate by `signal_id`
4. if duplicate `signal_id` appears, keep the freshest `observed_at`
5. write `manifest.json` with:
  - `run_id`
  - `generated_at`
  - source file count
  - exported row count
  - schema version
6. write to temp file first, then replace current file atomically

## Cron Strategy

### Recommended V1
- use one standalone export script plus system cron
- keep it outside the crawler execution path

Reason:
- simpler operator model
- easier failure isolation
- easier manual replay

### Later Option
- move to Celery Beat only after the file contract and operator path are stable

## QA Consumption Rule
- QA runtime reads only:
  - `data/handoff/trend_signal/current/trend_signal_latest.csv`
  - optional `manifest.json`
- QA should not read:
  - vendor raw tables
  - TrendAgent per-task JSON directories
  - sample fixtures under `data/pipeline_samples/`

## Out Of Scope
- no QA retrieval ranking redesign here
- no benchmark logic here
- no attempt to stream live events into QA here

## Recommended Deliverables
- one export script
- one export manifest schema
- one cron setup note
- one example export artifact
- one replay note for partial-failure recovery

## Acceptance Criteria
- repeated export runs are idempotent
- current handoff CSV is always complete or left untouched on failure
- QA has one stable file path to consume
- sample path and runtime handoff path are clearly separated

## Suggested Kickoff Instruction
```text
Task ID: INT-003
Goal: Publish first-party trend_signal into a stable QA-consumable CSV handoff directory with a scheduled export job.
Scope: add one export script, one manifest, one runtime handoff directory convention, and one cron setup note.
Non-goals: no QA retrieval redesign, no benchmark work, no raw-table coupling.
Required outputs:
- changed files
- export job summary
- example handoff artifact
- cron / replay note
- open risks
Constraints:
- follow docs/14-trendagent-to-qa-data-contract.md
- follow docs/15-trend-signal-schema.md
- do not use data/pipeline_samples as runtime output
```
