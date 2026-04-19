# 2026-04-19 Runtime Wave Progress Summary

## Purpose

This note summarizes the recent architecture-control wave around:

- `TA-003`
- `TA-004`
- `TA-005`
- `INT-003`
- `INT-004`
- `INT-005`

The goal is to answer two questions clearly:

1. what is already stable enough to treat as first-party project mainline
2. what is still missing before we can say the TrendAgent -> QA data line is fully closed

## Current Bottom Line

The project is no longer at the "design only" stage.

The current state is:

- trend keyword planning is structured
- expansion and schedule state are first-party persistent objects
- runtime batch execution is auditable
- first-party `trend_signal` handoff export exists
- QA-side evidence-layer ingestion exists
- QA-side runtime smoke on the real handoff path has passed

But the strongest accurate statement is still:

`TrendAgent runtime handoff is closed; QA runtime consumption is closed at the evidence-layer boundary.`

## What TA-003 To TA-005 Achieved

### TA-003 - keyword expansion alignment

This task moved TrendAgent away from loosely coupled temporary expansion behavior.

What is now stable:

- platform-aware expansion planning
- explicit split between:
  - crawl targets
  - reference-only sources
- one query-unit maps to one crawl task
- risk-oriented keywords preserve review markers

Why this matters:

- `taobao` and `industry_news` are no longer mixed into crawler execution semantics
- scheduler output is explainable
- future runtime work can build on query-unit semantics instead of ad hoc prompt output

### TA-004 - expansion registry

This task turned expansion output into first-party persistent state.

What is now stable:

- approved expansions can be stored and reused
- candidate expansions can be separated from runtime execution
- deprecated expansions can be kept out of scheduling

Why this matters:

- runtime does not need to regenerate every expansion on every run
- candidate terms do not directly pollute live crawling
- expansion review becomes a project-owned process, not an implicit LLM side effect

### TA-005 - query schedule state

This task introduced durable runtime state at the `query_unit` level:

`normalized_keyword + platform + expanded_query`

What is now stable:

- `next_due_at`
- `last_success_at`
- `last_failed_at`
- revisit interval
- retry cooldown
- watchlist tier semantics

Why this matters:

- periodic observation is now a first-party scheduling capability
- repeated crawling is governed by state, not only task dedup
- the project now has a credible path toward time-series trend monitoring

## What INT-003 To INT-005 Achieved

### INT-003 - stable trend_signal handoff

This task created the first stable QA-consumable runtime handoff path:

- `data/handoff/trend_signal/current/trend_signal_latest.csv`
- `data/handoff/trend_signal/current/trend_signal_latest.json`
- `data/handoff/trend_signal/current/manifest.json`

What is now stable:

- first-party export path is separated from pipeline samples
- export can read runtime batch history rather than guessing from loose files
- explicit `source_run_id` export is now strict and traceable
- export run-id collision on same-second reruns has been removed

Why this matters:

- QA now has one stable runtime handoff target
- TrendAgent runtime output is no longer tied to sample fixtures

### INT-004 - trend_signal_series groundwork

This task implemented the first version of time-bucket series aggregation.

What is now available:

- `trend_signal_series` schema and service
- bucketed aggregation output path
- backtest/sample artifacts

Why this matters:

- it upgrades single-run signals into observation over time
- it supports the longer-term monitoring strategy

Current status judgment:

- important and directionally correct
- not the current main-thread blocker

### INT-005 - batch recovery and completion guarantee

This task added first-party runtime recovery and completion audit semantics.

What is now stable:

- `runtime_batch_items`
- recovery / reconciliation logic
- completion audit summary
- `completed_full / completed_partial / failed` classification path

What was additionally fixed in the latest wave:

- a batch that crawled successfully but produced `0 cleaned / 0 signal` is no longer treated as a true success
- old misleading runs can now be reconciled into failed completion state

Why this matters:

- runtime is now judged by business output, not only process execution
- interruption and replay logic has a real state base

## Current Runtime Mainline Status

The following mainline is now substantially real:

`keyword registry -> expansion registry -> query schedule state -> crawl task -> vendor crawler -> raw rows -> cleaning -> trend_signal -> handoff export`

This is no longer only a design diagram.
It has implementation, runtime evidence, and recovery semantics.

## What Is Already Closed

### Closed enough for mainline use

- first-party keyword planning direction
- expansion persistence
- query scheduling persistence
- first-party runtime batch audit
- first-party trend_signal export handoff

### Closed enough for engineering review

- runtime false-success classification issue
- export strict source selection
- cleaning fallback for malformed LLM JSON output

## What Is Not Fully Closed Yet

The remaining key gap is not TrendAgent architecture.

The runtime handoff line is now closed at the evidence-layer boundary.

What is still not fully closed:

- full QA answer-policy integration
- wider multi-platform repeated live regression
- benchmark v1 coverage

## Current Release Judgment

### TrendAgent runtime line

Status: `green-yellow`

Meaning:

- green on first-party architecture direction and handoff design
- yellow on multi-platform repeated live regression completeness

### TrendAgent -> QA line

Status: `green-yellow`

Meaning:

- contract and handoff are ready
- QA evidence layer is ready
- runtime-consumption smoke has passed on the real handoff path

## Recommended Immediate Next Step

Do not widen architecture scope first.

The runtime handoff closure is now done.

Do this next:

1. keep one short evidence artifact showing:
   - input handoff file
   - parsed trend evidence
   - output trend context block
   - behavior flag
2. widen baseline runtime regression across more frozen seeds / platforms
3. then decide whether to prioritize benchmark v1 or series integration

## Recommended After That

After runtime handoff closure, choose one of three directions:

1. widen baseline runtime regression across more frozen seeds / platforms
2. integrate `trend_signal_series` into downstream evidence usage
3. start `EVAL-001` benchmark v1 around the now-stable handoff path

## Current Most Practical Priority Order

1. one short TA -> QA runtime smoke report
2. widen baseline runtime regression
3. then decide between:
   - runtime widening
   - series integration
   - benchmark v1
