# BeautyModel-Lab Docs (MVP Working Set)

This folder has been reset to a minimal, execution-focused documentation set.
Only the files below are active for current team collaboration.

## Active docs
1. `01-mvp-scope.md` - frozen MVP boundaries and out-of-scope items
2. `02-system-architecture.md` - end-to-end architecture and data flow
3. `03-data-contract.md` - data schema, quality gates, update cadence
4. `04-component-contract.md` - module I/O and ownership boundaries
5. `05-eval-protocol.md` - baselines, metrics, ablations, release gates
6. `06-roadmap-owner.md` - milestones, owners, weekly execution board
7. `07-domain-faq.md` - domain rules for scientific skincare and trend decisions
8. `08-data-preparation-requirements-v1.md` - MVP data scope, sampling, quotas, delivery checklist
9. `09-data-intake-checklist.md` - batch intake steps, acceptance gates, mapping rules
10. `10-engineering-workplan.md` - engineering split, module boundaries, two-week MVP plan
11. `check-issue/README.md` - architecture-controlled task-package workflow and execution board
12. `progress/` - dated progress notes for shared team execution updates
13. `feedback/20260306/` - proposal iteration and mentor discussion archive moved under docs
14. `11-data-source-collection-strategy.md` - upstream data-source, collection, and batch-update strategy
15. `evaluation/` - benchmark design, scoring rubric, release gates, and experiment templates
16. `12-repo-structure-normalization.md` - target monorepo structure, module boundary, and migration order
17. `13-trendagent-dataflow-and-dependency-boundary.md` - TrendAgent dataflow, vendor dependency boundary, and modification guidance
18. `14-trendagent-to-qa-data-contract.md` - TrendAgent to QA first-party data contract
19. `15-trend-signal-schema.md` - first-party trend_signal schema for downstream QA use
20. `16-trend-signal-to-qa-usage-guide.md` - how QA / RAG should parse, index, filter, and use trend_signal
21. `17-trendagent-vendor-adapter-contract.md` - TrendAgent and vendor crawler adapter contract, stability checks, and hardening direction
22. `18-mediacrawler-runtime-playbook.md` - standard MediaCrawler runtime entrypoint, DB alignment, and xhs/dy/bili smoke commands
23. `19-trendagent-runtime-strategy.md` - first-party runtime defaults, platform safety policy, and batch audit tables
24. `20-trend-signal-timeseries-strategy.md` - unified design for expansion registry, query schedule state, time-bucket series, export, and batch recovery

## Archive
Legacy and exploratory docs were archived to:
- `archive/2026-03-10-pre-mvp-reset/`

## Working rule
- New execution docs should be added only when they are required for delivery.
- Shared progress and mentor-feedback materials should stay under `docs/progress/` and `docs/feedback/`.
