# TA-006 - Cross-Platform Runtime Baseline

## Metadata
- Task ID: `TA-006`
- Module: `BeautyQA-TrendAgent`
- Owner Type: `architecture-control / dev-agent / engineer`
- Status: `ready`
- Related Docs:
  - `docs/20-trend-signal-timeseries-strategy.md`
  - `docs/21-cross-platform-runtime-baseline.md`
  - `docs/19-trendagent-runtime-strategy.md`

## Goal

Turn runtime seeding from single-platform keyword assumptions into a controlled cross-platform baseline:

- same theme keyword can seed `xhs / dy / bili`
- expansions remain platform-specific
- reference sources remain reference-only

## Scope

- add a first-party baseline seeding script
- support explicit keyword-id based seeding
- support platform override such as `xhs dy bili`
- generate approved expansion registry rows and query schedule state
- make the baseline usable for `safe_live` runtime verification

## Non-Goals

- do not force all production runs to hit all platforms every cycle
- do not change vendor crawler code
- do not redesign QA handoff format

## Inputs

- active trend keywords in first-party DB
- existing keyword execution plan logic
- `TA-004` expansion registry
- `TA-005` query schedule state

## Required Outputs

- one script to bootstrap runtime baseline seeds
- one documented strategy for cross-platform theme coverage
- one smoke-proven example on at least one additional platform

## Constraints

- `taobao` and `industry_news` stay reference-only
- platform safety policy still applies
- platform expansion rules may differ
- cleaned evidence output must still converge into the same first-party model

## Acceptance Criteria

- one keyword can be seeded into `xhs / dy / bili` baseline without editing vendor code
- runtime registry and query state are created by script, not ad hoc SQL
- at least one additional `safe_live` run is proven with the seeded baseline

## Return Format

- changed files
- seeded keyword example
- smoke result
- remaining risks
