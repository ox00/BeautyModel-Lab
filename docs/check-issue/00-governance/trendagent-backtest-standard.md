# TrendAgent Backtest Standard

## Purpose

This document defines the minimum backtest standard for `BeautyQA-TrendAgent/` tasks.

The goal is not to produce full production-grade evaluation. The goal is to make implementation tasks return comparable evidence.

## Backtest Layers

### Layer A - Contract Check

Confirm:
- required fields still exist
- field names have not drifted
- downstream assumptions are still valid

### Layer B - Pipeline Check

Confirm the expected stage still runs:
- keyword intake
- keyword expansion
- task generation
- crawler invocation path
- cleaning path
- signal generation path if relevant

### Layer C - Boundary Check

Confirm the task did not break:
- vendor path resolution
- CLI contract assumptions
- raw-table read assumptions
- first-party output schema assumptions

### Layer D - Output Quality Check

Where relevant, report:
- output count
- skipped count
- failure count
- representative sample output
- obvious noise or drift

## Minimum Evidence By Task Type

### Contract / schema task
- updated docs
- one sample object
- one downstream usage example

### Scheduling / expansion task
- input sample
- scheduled task sample
- expanded keyword sample
- filtered platform sample

### Crawl orchestration task
- generated command sample
- subprocess start / completion result
- failure behavior if any

### Cleaning / signal task
- cleaned record sample
- signal sample
- count summary
- risk / confidence sample

## Failure Reporting Rule

If backtest fails, the return must include:
- exact failing stage
- whether failure is contract-level or implementation-level
- whether the task should be split
