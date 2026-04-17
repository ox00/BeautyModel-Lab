# Check-Issue Task Packages

## Purpose

This folder is the shared execution board for architecture-controlled delivery.

The architecture-control thread owns:
- design framing
- contract freeze
- schema freeze
- task package definition
- backtest rule
- merge decision

Implementation runs in separate execution threads so design context and debugging context stay separated.

## Structure

- `_templates/` - reusable package templates
- `00-governance/` - workflow and backtest rules
- `20-trendagent/` - task packages for `BeautyQA-TrendAgent/`
- `30-qacore/` - task packages for `BeautyQA-core/`
- `40-integration/` - cross-module integration and smoke-test packages
- `50-evaluation/` - benchmark and quality-gate packages
- root-level older flat packages remain as legacy MVP packages and should not receive new work by default

## Required Flow

1. Freeze or update the relevant design doc.
2. Freeze or update the contract / schema doc.
3. Create or revise the task package.
4. Open a dedicated execution thread.
5. Execute implementation and backtest there.
6. Return evidence to architecture control.
7. Approve merge or request rework.

## Current Core Docs

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `00-governance/architecture-control-workflow.md`
- `00-governance/execution-thread-kickoff-guide_cn.md`
- `00-governance/trendagent-backtest-standard.md`
- `_templates/task-package-template.md`

## Current Ready Packages

- `20-trendagent/TA-001-trendagent-to-qa-contract-adoption.md`
- `20-trendagent/TA-002-trend-signal-generation-layer.md`
- `20-trendagent/TA-003-keyword-expansion-alignment.md`
- `20-trendagent/TA-004-expansion-registry.md`
- `20-trendagent/TA-005-query-schedule-state.md`
- `30-qacore/QA-001-trend-signal-retrieval-integration.md`
- `40-integration/INT-001-e2e-smoke-test.md`
- `40-integration/INT-003-trend-signal-export-cron.md`
- `40-integration/INT-004-trend-signal-series-aggregation.md`
- `40-integration/INT-005-batch-recovery-and-completion-guarantee.md`
- `50-evaluation/EVAL-001-benchmark-v1.md`

## Execution Thread Inputs

Use the kickoff docs below when handing work to a separate implementation thread or engineer:

- `00-governance/execution-thread-kickoff-guide_cn.md`
- `00-governance/execution-thread-short-prompts_cn.md`
- `20-trendagent/TA-001-kickoff_cn.md`
- `20-trendagent/TA-002-kickoff_cn.md`
- `20-trendagent/TA-003-kickoff_cn.md`
- `20-trendagent/TA-004-kickoff_cn.md`
- `20-trendagent/TA-005-kickoff_cn.md`
- `30-qacore/QA-001-kickoff_cn.md`
- `30-qacore/QA-002-kickoff_cn.md`
- `30-qacore/QA-003-kickoff_cn.md`
- `40-integration/INT-001-kickoff_cn.md`
- `40-integration/INT-003-kickoff_cn.md`
- `40-integration/INT-004-kickoff_cn.md`
- `40-integration/INT-005-kickoff_cn.md`
- `50-evaluation/EVAL-001-kickoff_cn.md`
