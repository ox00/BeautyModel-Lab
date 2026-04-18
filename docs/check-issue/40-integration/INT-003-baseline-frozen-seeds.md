# INT-003 Baseline Frozen Seeds

## Purpose

This file freezes the small baseline seed set for the current runtime regression wave.

The goal is not broad coverage.
The goal is to keep one stable, repeatable, explainable seed pack while the team verifies:

- seed bootstrap
- expansion registry generation
- multi-platform crawl scheduling
- raw ingestion
- cleaning
- trend signal output
- export / handoff

## Freeze Rule

During the current regression wave:

- do not add new baseline seeds in the middle of reruns
- do not change the platform baseline from `xhs | dy | bili`
- do not treat `taobao` or `industry_news` as crawler targets
- do not widen this pack until the current loop is stable

## Frozen Seed Set

### Control seed

1. `KW_0014` / DB `14` / `护肤`
- role: shared category control seed
- why included: already has first-party cross-platform schedule state and live proof on `xhs` and `bili`
- required platforms: `xhs`, `dy`, `bili`
- expected use: first platform-stability check and rerun control

### Category seed

2. `KW_0031` / DB `31` / `面部清洁`
- role: category-focused business seed
- why included: close to current beauty/personal-care business line and easier to interpret
- required platforms: `xhs`, `dy`, `bili`
- reference-only sources in metadata: `taobao`

### Frontier ingredient seed

3. `KW_0002` / DB `2` / `外泌体`
- role: frontier ingredient / concept-trend seed
- why included: tests expansion quality and cross-platform vocabulary differences
- required platforms: `xhs`, `dy`, `bili`
- reference-only sources in metadata: `industry_news`

### Risk seed

4. `KW_0040` / DB `40` / `快速美白`
- role: risk-monitoring seed
- why included: forces the runtime to keep risk-oriented metadata and review boundaries visible
- required platforms: `xhs`, `dy`, `bili`
- execution note: run after the other three seeds are stable

## Execution Order

### Stage 1

Run the control seed first:

- `KW_0014` / `护肤`

Reason:

- it is the simplest shared seed
- it already has partial live proof
- it is the best control case for checking rerun behavior

### Stage 2

Run the normal business seeds:

- `KW_0031` / `面部清洁`
- `KW_0002` / `外泌体`

Reason:

- one category-oriented seed
- one concept / ingredient-oriented seed
- together they cover two different expansion and cleaning patterns

### Stage 3

Run the risk seed last:

- `KW_0040` / `快速美白`

Reason:

- high-risk seeds should not be the first thing used to debug platform or account stability
- use it after the normal runtime path is already stable

## Current Known State

As of `2026-04-18`:

- `KW_0014` / DB `14` has cross-platform `query_schedule_states`
- `xhs` live proof exists for `护肤`
- `bili` live proof exists for `护肤`
- `dy` still needs to be closed in the same first-party runtime loop for this regression wave

## Out Of Scope

This frozen set does not try to solve:

- benchmark coverage
- time-bucket series output
- batch interruption recovery
- large-scale watchlist design

Those belong to later tasks after the current runtime loop is stable.
