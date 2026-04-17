# INT-002 - TrendAgent To Crawler Runtime Link

## Metadata
- Task ID: `INT-002`
- Module: `BeautyQA-TrendAgent + BeautyQA-vendor`
- Owner Type: `dev-agent / engineer / architecture-support`
- Status: `ready`
- Related Docs:
  - `docs/13-trendagent-dataflow-and-dependency-boundary.md`
  - `docs/17-trendagent-vendor-adapter-contract.md`
  - `docs/18-mediacrawler-runtime-playbook.md`
- Related Upstream Tasks:
  - `docs/check-issue/20-trendagent/TA-003-keyword-expansion-alignment.md`
  - `docs/check-issue/20-trendagent/TA-003-regression-backtest-plan.md`

## Goal
- Turn the current TrendAgent -> crawler line into a stable integration path:
  - keyword registry
  - platform-aware query expansion
  - crawl task creation
  - vendor crawler execution
  - cleaned trend data generation
  - first-party `trend_signal` generation
  - run completion summary / reminder artifact

## Why This Task Exists
- `TA-003` already stabilized query planning and scheduler output shape.
- vendor runtime smoke is now available for `xhs`, `dy`, and `bili`.
- the remaining gap is not keyword design; it is integration control.

The team now needs one stable runtime path that is traceable, replayable, and easy to diagnose.

## Core Position
- Do not keep expanding `BeautyQA-TrendAgent/backend/run_pipeline.py` as the long-term integration entrypoint.
- Keep the integration line aligned with the current first-party architecture:
  - `KeywordService`
  - `SchedulerAgent`
  - `TaskService`
  - crawler adapter / process manager
  - `CleaningAgent`
  - `SignalAgent`

## Required Runtime Chain
1. read due keywords from first-party keyword source
2. build platform-aware execution plan
3. create one crawl task per platform-aware query
4. dispatch vendor crawler through adapter boundary
5. write vendor raw rows into PostgreSQL
6. run cleaning against vendor raw rows
7. generate first-party `trend_signal`
8. write one run-level completion artifact for review

## Suggested V1 Scope
- one first-party integration runner script or service entrypoint
- one run-level report artifact such as:
  - `run_id`
  - scheduled task count
  - completed task count
  - failed task count
  - generated signal count
  - failed task ids / reasons
- one minimal reminder mechanism:
  - terminal summary
  - JSON or Markdown run report

For `v1`, do not build external IM notification.
The reminder target is the project runtime itself, not a team chat bot.

## Engineering Decisions

### 1. Keep vendor boundary narrow
- vendor still owns browser automation and raw-table writes
- TrendAgent still owns planning, orchestration, cleaning, and `trend_signal`

### 2. Keep run completion first-party
- completion should be represented by first-party run artifacts
- do not couple completion semantics to vendor subprocess logs

### 3. Keep query execution unit small
- one platform-aware query -> one crawl task
- this stays consistent with `TA-003`

### 4. Keep runtime status diagnosable
- if a run fails, reviewers should be able to tell whether failure happened at:
  - scheduling
  - crawler execution
  - cleaning
  - signal generation

## Out Of Scope
- no benchmark design here
- no QA retrieval redesign here
- no vendor crawler refactor here
- no attempt to solve platform anti-crawl in this task package

## Recommended Deliverables
- one integration runner entrypoint
- one run report schema
- one first-party batch history record for audit / replay
- one completed smoke report for a real small run
- one operator note describing restart / replay strategy

## Acceptance Criteria
- a reviewer can run the main TrendAgent -> crawler line without manually stitching multiple ad hoc commands
- one run produces:
  - task records
  - raw rows
  - cleaned rows
  - first-party `trend_signal`
  - completion report
- failure stage is visible in first-party logs or report artifacts

## Suggested Next Execution Order
1. finish `INT-002`
2. then implement `INT-003` export cron
3. then rerun `INT-001` smoke on the real handoff path

## Suggested Kickoff Instruction
```text
Task ID: INT-002
Goal: Stabilize the TrendAgent -> vendor crawler runtime link from keyword scheduling to first-party trend_signal output.
Scope: use current first-party scheduler/task/adapter/cleaning/signal layers; add one integration runner and one run-level completion artifact.
Non-goals: no benchmark work, no QA retrieval redesign, no vendor crawler refactor, no external bot notification.
Required outputs:
- changed files
- runtime chain summary
- run report artifact
- one small real smoke result
- open risks
Constraints:
- follow docs/17-trendagent-vendor-adapter-contract.md
- follow docs/18-mediacrawler-runtime-playbook.md
- keep one-query-per-task behavior from TA-003
- do not widen vendor coupling
```
