# 15 - Trend Signal Schema

## Purpose

This document defines the first-party `trend_signal` schema.

`trend_signal` is the normalized trend output produced by `BeautyQA-TrendAgent/` for downstream QA consumption.

It is not a raw crawl table and not a vendor-owned data structure.

## Entity Definition

A `trend_signal` record represents one trend observation distilled from cleaned trend data.

Each record should preserve:
- what the trend is
- why we think it matters
- where it came from
- how strong it is
- how fresh it is
- how risky it is

## Minimum Schema

| field | type | required | meaning |
|------|------|------|------|
| `signal_id` | string | yes | unique id for the signal record |
| `keyword_id` | string | yes | upstream keyword seed id |
| `crawl_task_id` | integer/string | yes | trace back to task execution |
| `normalized_keyword` | string | yes | normalized trend theme |
| `topic_cluster` | string | yes | topic grouping |
| `trend_type` | string | yes | ingredient / claim / category / scenario / risk_compliance |
| `signal_summary` | string | yes | short normalized summary for downstream use |
| `signal_evidence` | string | yes | short evidence statement grounded in cleaned content |
| `source_platform` | string | yes | xiaohongshu / douyin / etc. |
| `source_url` | string | yes | one representative source link |
| `trend_score` | float | yes | normalized signal score |
| `confidence` | string | yes | low / medium / high |
| `risk_flag` | string | yes | low / medium / high |
| `observed_at` | datetime/date string | yes | when the signal was observed |
| `fresh_until` | datetime/date string | yes | until when the signal is considered fresh |

## Recommended Extension Fields

| field | type | meaning |
|------|------|------|
| `report_id` | string | source report linkage when relevant |
| `signal_period_type` | string | annual / monthly / special_topic / cross_period |
| `signal_period_label` | string | e.g. `2026-02`, `2026 annual` |
| `source_scope` | string | industry_research / social_content / mixed |
| `support_count` | integer | number of supporting cleaned records |
| `evidence_ids` | array[string] | ids of cleaned evidence items |
| `sentiment_distribution` | object | optional sentiment mix |
| `aggregation_method` | string | how the signal was aggregated |
| `version` | string | schema or generation version |

## Example Record

```json
{
  "signal_id": "TS_20260415_0001",
  "keyword_id": "KW_0002",
  "crawl_task_id": 184,
  "normalized_keyword": "外泌体",
  "topic_cluster": "ingredient_frontier",
  "trend_type": "ingredient",
  "signal_summary": "外泌体在小红书护肤讨论中持续出现，并与抗衰、修护表达高频共现。",
  "signal_evidence": "近一轮清洗结果中，多条内容将外泌体与精华、修护、抗衰场景绑定。",
  "source_platform": "xiaohongshu",
  "source_url": "<representative-source-url>",
  "trend_score": 82.4,
  "confidence": "high",
  "risk_flag": "medium",
  "observed_at": "2026-04-15T10:30:00+08:00",
  "fresh_until": "2026-04-22T10:30:00+08:00",
  "support_count": 14,
  "evidence_ids": ["CTD_1001", "CTD_1007", "CTD_1011"],
  "version": "v0.1"
}
```

## Generation Rule

A `trend_signal` should be generated from first-party cleaned records, not directly from raw crawler rows.

Recommended flow:
- raw crawler result
- cleaned content record
- grouped / scored signal candidate
- reviewed or auto-approved `trend_signal`

## Grouping Rule

Signals should be grouped primarily by:
- `normalized_keyword`
- `topic_cluster`
- `trend_type`
- `source_platform`
- freshness window

This avoids mixing unrelated evidence into one signal bucket.

## Confidence Rule

Suggested logic:
- `high`: multiple consistent cleaned records + stable topic match + clear evidence
- `medium`: some support exists but evidence is narrower or noisier
- `low`: weak support, sparse evidence, or partial pattern only

## Risk Rule

Suggested logic:
- `high`: strong compliance or claim sensitivity
- `medium`: possible ambiguity, hype, or overclaim risk
- `low`: normal category / ingredient trend without obvious compliance concern

## Freshness Rule

Suggested default:
- social trend signals use a 7-day freshness window unless a task specifies otherwise
- older signals may remain queryable but should be treated as stale context

## Downstream Use Rule

QA may use `trend_signal` for:
- trend basis in evidence-backed answers
- trend-aware alternative suggestions
- risk note enhancement when trend hype conflicts with science

QA may not use `trend_signal` as:
- sole scientific proof
- sole compliance decision basis
- substitute for ingredient or compliance knowledge

## Acceptance Rule

The schema is ready when:
- TrendAgent can write signals in this structure
- QA can retrieve and cite signals without vendor-specific knowledge
- signal freshness, confidence, and risk are explicit
