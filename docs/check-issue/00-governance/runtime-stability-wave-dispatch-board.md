# Runtime Stability Wave Dispatch Board

## Purpose

This file defines how the current runtime wave is split across threads.

Current principle:

- main thread focuses on stabilizing the baseline runtime loop
- non-blocking next-wave tasks are dispatched out in parallel
- architecture control keeps merge order and acceptance gates

## Main-Thread Scope

Keep in the current architecture / integration thread:

- baseline frozen seeds
- baseline regression reruns
- multi-platform runtime checks for `xhs`, `dy`, `bili`
- export / handoff verification
- final pass/fail judgment for the current stable-running gate

Primary working docs:

- `docs/check-issue/40-integration/INT-003-baseline-frozen-seeds.md`
- `docs/check-issue/40-integration/INT-003-baseline-regression-checklist.md`
- `docs/18-mediacrawler-runtime-playbook.md`
- `docs/21-cross-platform-runtime-baseline.md`

## Parallel Dispatch Packages

### Thread A

- task: `INT-004`
- package: `docs/check-issue/40-integration/INT-004-trend-signal-series-aggregation.md`
- kickoff: `docs/check-issue/40-integration/INT-004-kickoff_cn.md`
- goal: time-bucket `trend_signal_series`
- dependency note: do not block current baseline regression on this work
- merge gate: merge only after the current seed/query-state semantics stay stable

### Thread B

- task: `INT-005`
- package: `docs/check-issue/40-integration/INT-005-batch-recovery-and-completion-guarantee.md`
- kickoff: `docs/check-issue/40-integration/INT-005-kickoff_cn.md`
- goal: interrupted batch recovery and full / partial / failed completion audit
- dependency note: do not block current baseline regression on this work
- merge gate: merge only after current batch semantics are not changing underneath the implementation

## Distribution Note

When handing these tasks out, send:

1. the task package path
2. the kickoff doc path
3. the return format requirement
4. the rule that execution must happen in a separate thread and separate git worktree / branch

## Return Format Requirement

Each parallel thread should return:

- changed files
- implementation summary
- backtest / replay result
- open risks

## What Not To Dispatch In This Wave

Do not widen the current parallel wave with:

- `EVAL-001`
- broad benchmark asset generation
- large watchlist redesign
- vendor crawler refactor beyond the current adapter/runtime boundary

## Merge Discipline

- architecture control reviews before merge
- do not merge directly from the same dirty worktree used by the main integration loop
- keep each execution thread on its own branch/worktree to avoid accidental context and file pollution
