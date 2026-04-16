# QA-001 Review

## Review Scope

- Module: `BeautyQA-core`
- Related package: `docs/check-issue/30-qacore/QA-001-trend-signal-retrieval-integration.md`
- Related contract docs:
  - `docs/14-trendagent-to-qa-data-contract.md`
  - `docs/15-trend-signal-schema.md`

## Overall Result

`QA-001` passes as a first integration scaffold, but it should not be treated as the stable quality gate version yet.

Current status:
- first-party `trend_signal` retrieval path exists
- stale / weak evidence downgrade exists
- QA still avoids vendor crawler runtime dependency

Current gaps:
- high-risk trend evidence is not filtered before entering strong-evidence path
- legacy CSV compatibility remains inside the runtime repository path
- backtest coverage is incomplete for safety gating

## Findings To Carry Forward

### 1. High-risk signals are not blocked from strong evidence

- Current strong-evidence logic checks freshness, confidence, and score only.
- `risk_flag` is not part of the gate.
- This allows `risk_flag=high` signals to produce `trend_supported`.

This conflicts with:
- `science and compliance remain hard constraints`
- `trend evidence is supportive, not authoritative`

### 2. Legacy CSV compatibility weakens the first-party contract boundary

- `TrendSignalRepository.from_contract_csv()` accepts both current contract CSV and legacy `trend_id` CSV.
- This is convenient for migration, but it makes the QA runtime boundary soft.
- The main runtime path should consume first-party contract data only.

### 3. Safety-filter state exists in model but is not used

- `trend_filtered_for_safety` exists in `behavior_flag`.
- Current pipeline never emits it.
- This means safety filtering is not observable in runtime output or backtest.

### 4. Backtest coverage is still minimal

Current covered cases:
- fresh usable trend evidence
- stale trend evidence

Missing cases:
- low-confidence trend evidence
- high-risk trend evidence
- explicit safety-filtered behavior

## Recommended Next Task

Do not reopen `QA-001`.

Use a follow-up task to harden the behavior:
- `docs/check-issue/30-qacore/QA-002-risk-gating-and-contract-hardening.md`

## Merge Guidance

`QA-001` can be kept as:
- baseline integration scaffold
- temporary demoable retrieval slice

`QA-001` should not be used as:
- stable evaluation gate
- final QA trend integration baseline
