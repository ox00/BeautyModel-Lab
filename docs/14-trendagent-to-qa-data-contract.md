# 14 - TrendAgent To QA Data Contract

## Purpose

This document defines the contract between `BeautyQA-TrendAgent/` and `BeautyQA-core/`.

The goal is to keep the QA pipeline independent from crawler implementation details while still consuming trend outputs as a first-party data product.

## Boundary Rule

`BeautyQA-core/` must not depend on:
- vendor crawler source code
- vendor crawler CLI behavior
- vendor raw PostgreSQL tables
- platform-specific crawl task details

`BeautyQA-core/` may depend on:
- first-party `trend_signal` records
- versioned trend refresh metadata
- quality and freshness flags
- first-party evidence ids and source references

## Upstream / Downstream Roles

### `BeautyQA-TrendAgent/`

Owns:
- trend keyword planning
- keyword expansion
- crawl task scheduling
- vendor crawler invocation
- raw capture cleaning
- signal generation

Output to QA:
- `trend_signal`
- `trend_signal_refresh_report`

### `BeautyQA-core/`

Owns:
- QA query intake
- retrieval over first-party knowledge assets
- science + trend reasoning
- safety and compliance gating
- response rendering

Input from TrendAgent:
- `trend_signal`
- optional signal freshness / confidence metadata

## Required Contract Object

The required object passed from TrendAgent to QA is `trend_signal`.

QA should treat this as a read-only upstream data product.

## `trend_signal` Contract Fields

Minimum fields required by QA:
- `signal_id`
- `normalized_keyword`
- `topic_cluster`
- `trend_type`
- `signal_summary`
- `signal_evidence`
- `source_platform`
- `source_url`
- `trend_score`
- `confidence`
- `risk_flag`
- `observed_at`
- `fresh_until`
- `keyword_id`
- `crawl_task_id`

Optional but recommended:
- `report_id`
- `signal_period_type`
- `signal_period_label`
- `source_scope`
- `support_count`
- `evidence_ids`

## Contract Semantics

### TrendAgent promises

TrendAgent promises that:
- every `trend_signal` is derived from first-party cleaned records, not directly from unvalidated crawler output
- every `trend_signal` can be traced back to at least one source reference
- every `trend_signal` has explicit freshness information
- every `trend_signal` has explicit confidence and risk fields

### QA promises

QA promises that:
- it consumes `trend_signal` as evidence, not as a final decision
- science and safety remain hard constraints
- trend relevance is a soft optimization only
- stale or low-confidence trend signals do not override science or compliance evidence

## Retrieval Contract

QA retrieval may query `trend_signal` by:
- `normalized_keyword`
- `topic_cluster`
- `trend_type`
- `source_platform`
- `risk_flag`
- freshness window
- minimum confidence
- minimum trend score

QA should not query:
- vendor raw table names
- crawl subprocess metadata
- platform login state

## Freshness Rule

Default freshness handling:
- `trend_signal` older than freshness window should be marked stale
- stale trend signals may still be used as weak context, not strong recommendation evidence
- freshness thresholds should follow the project-level `trend freshness <= 7 days` rule unless explicitly overridden

## Failure Isolation Rule

If TrendAgent is degraded:
- QA still runs on science / compliance / product evidence
- trend evidence may be absent or downweighted
- QA must not fail just because crawler or trend refresh failed

This is the core decoupling rule.

## Non-Goals

This contract does not define:
- crawler CLI arguments
- vendor database schema
- login and account rotation rules
- keyword expansion prompt details

Those remain upstream implementation concerns.

## Acceptance Rule

This contract is usable when:
- TrendAgent can produce `trend_signal` without exposing vendor internals to QA
- QA can retrieve and use `trend_signal` without knowing how crawling was executed
- trend outage does not block QA baseline behavior
