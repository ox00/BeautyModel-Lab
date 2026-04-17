# Runtime Next-Wave Task Board

This board freezes the next execution wave after `INT-002`.

It exists to avoid:

- missing one of the newly identified runtime layers
- implementing tasks in the wrong order
- mixing tightly coupled model work with independent handoff work

## Frozen Order

### Phase 1

1. `INT-003` trend-signal export cron
2. `TA-004` expansion registry
3. `TA-005` query schedule state

### Phase 2

4. `INT-004` trend signal series aggregation
5. `INT-005` batch recovery and completion guarantee

## Why This Order

### `INT-003` first

Reason:

- QA handoff should stabilize early
- export can already use current first-party outputs
- operator SQL checklist is immediately useful during integration

### `TA-004` before `TA-005`

Reason:

- schedule state should not depend on ephemeral expansion output
- approved / candidate / deprecated expansion state must exist first

### `TA-005` before `INT-004`

Reason:

- time-bucket observation should depend on stable query units and revisit rules
- otherwise series aggregation will be built on unstable runtime semantics

### `INT-005` last

Reason:

- recovery logic needs stable batch intent and schedule state
- otherwise recovery rules will keep changing underneath implementation

## Recommended Execution Allocation

### Thread 1: Handoff / Ops Thread

Tasks:

- `INT-003`

Why:

- mostly export, manifest, cron, operator docs, SQL checklist
- weak coupling to expansion and schedule schema internals

### Thread 2: TrendAgent State Thread

Tasks:

- `TA-004`
- `TA-005`

Why:

- both are first-party state-model tasks
- both affect scheduler truth
- should stay in one implementation thread to avoid schema drift

### Thread 3: Integration Observation Thread

Tasks:

- `INT-004`

Why:

- depends on upstream state freeze
- should focus on aggregation and series semantics only

### Thread 4: Runtime Reliability Thread

Tasks:

- `INT-005`

Why:

- recovery and completion are reliability work
- should build on already-frozen batch and schedule semantics

## Architecture-Control Responsibilities

This thread should keep ownership of:

- `docs/20-trend-signal-timeseries-strategy.md`
- task package freeze
- schema freeze
- merge gate
- cross-thread dependency clarification

## Merge Gate Rule

Do not merge:

- `INT-004` before `TA-005`
- `INT-005` before batch item / schedule semantics are frozen

Do allow parallel execution of:

- `INT-003`
- `TA-004` / `TA-005`

because their implementation surfaces are mostly separate.
