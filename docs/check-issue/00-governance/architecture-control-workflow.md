# Architecture Control Workflow

## Purpose

This workflow is for architecture-control-led delivery.

The architecture-control thread defines:
- contract
- schema
- task package
- backtest rule
- merge decision rule

Execution happens in separate implementation threads so that design reasoning and implementation debugging do not pollute each other.

## Threads

### Architecture Control Thread

Owns:
- problem framing
- contract freeze
- task decomposition
- backtest design
- merge review

### Execution Thread

Owns:
- implementation
- local validation
- backtest run
- evidence return

## Standard Flow

1. Freeze or update the design document.
2. Freeze or update contract / schema docs.
3. Create a task package.
4. Open a dedicated execution thread.
5. Run implementation and backtest in that execution thread.
6. Return evidence to architecture control.
7. Approve merge / request rework / split task.

## Core Rule

No implementation thread should redefine the contract on its own.

If contract pressure appears during implementation:
- pause execution
- return the pressure to architecture control
- revise the package first

## Required Return Format From Execution Threads

Every execution thread should return:
- changed files
- implementation summary
- backtest result
- unresolved risks
- any suggested contract changes
