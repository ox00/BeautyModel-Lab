# 16 - Trend Signal To QA Usage Guide

## Core Positioning

**TrendAgent 负责生产 trend evidence；QA evidence layer 负责读取和筛选；QA 主系统负责最终回答治理。**

这句话是这份说明的主线。

`trend_signal` 的角色是 first-party trend evidence package，不是最终答案，也不是科学知识库本身。

## Purpose

这份文档说明三件事：
- `trend_signal` 相关文件分别是什么，作用是什么
- QA / RAG 应该如何理解和使用这包数据
- 工程上如何解析、检索、过滤、追踪这包数据

相关定义文档：
- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`

## 1. Trend-Signal 相关文件

### 1.1 协议定义层

这两份文档定义正式协议：
- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`

作用：
- 定义 TA -> QA 的 first-party data contract
- 定义字段、边界、freshness、risk、confidence 等语义

### 1.2 协议样例层

这组文件是 handoff sample，不是协议定义文档本身：
- `data/pipeline_samples/trend_signal/trend_signal_first_party_sample.csv`
- `data/pipeline_samples/trend_signal/trend_signal_first_party_sample.json`

作用：
- 给 QA / RAG 工程侧一个可直接解析的样例
- 给联调和 smoke test 提供共享输入
- 作为后续真实周期推送数据的结构参考

### 1.3 上游输入样例层

- `data/pipeline_samples/trend_signal/sample_cleaned_records.json`

作用：
- 作为 TrendAgent 侧的 deterministic sample input
- 用于验证 cleaned trend data 如何生成 `trend_signal`

### 1.4 联调与验证层

- `data/pipeline_samples/trend_signal/int001_smoke_report.json`
- `docs/check-issue/40-integration/INT-001-smoke-report.md`

作用：
- 记录当前最小主链是否跑通
- 说明 sample input -> trend_signal -> QA ingestion 的 stage result

### 1.5 TrendAgent 运行输出层

真实运行时，TrendAgent 的 first-party 输出位于：
- `BeautyQA-TrendAgent/backend/data/trend_signal/{platform}/*.json`

作用：
- 存放真实任务运行后生成的 first-party `trend_signal`
- 供 QA 周期拉取或由数据管道推送到 QA evidence layer

## 2. QA 对 Trend-Signal 的关键定位

QA 不应把 `trend_signal` 当作：
- 最终回答
- 科学结论
- 合规规则本身

QA 应把 `trend_signal` 当作：
- 趋势证据层
- trend-aware retrieval / evidence augmentation 的输入
- 主 QA / RAG 系统的辅助上下文

从系统职责上看：
- TrendAgent 负责生产结构化 trend evidence
- QA evidence layer 负责读取、筛选、透传 evidence
- QA 主系统负责最终回答策略、知识融合、合规与安全治理

## 3. QA 应如何集成这包数据

QA evidence layer 的推荐处理方式：

1. 周期读取或接收 first-party `trend_signal`
2. 将每条 `trend_signal` 解析为 trend evidence item
3. 建立检索索引与 metadata filter
4. 对 query 召回相关 trend evidence
5. 根据 freshness / confidence / risk / score 做筛选
6. 将筛出的 trend context block 交给主 QA / RAG 系统
7. 主 QA / RAG 系统再决定最终如何回答

这意味着：
- `trend_signal` 是 QA 的上游 evidence input
- 不是 QA 的最终决策模块

## 4. 工程解析方式

### 4.1 检索与过滤字段

这些字段适合用于 retrieval / ranking / filtering：
- `normalized_keyword`
- `topic_cluster`
- `trend_type`
- `source_platform`
- `risk_flag`
- `confidence`
- `trend_score`
- `fresh_until`
- `signal_period_type`
- `signal_period_label`

主要用途：
- query 召回
- freshness filter
- confidence threshold
- risk-aware filter
- platform-aware filter

### 4.2 Evidence 增强内容字段

这些字段最适合进 trend-aware RAG context：
- `signal_summary`
- `signal_evidence`

主要用途：
- 向模型提供压缩后的趋势说明
- 向模型提供支持这条趋势的证据短文本

### 4.3 Trace / Debug 字段

这些字段主要用于追踪、解释和工程排查：
- `signal_id`
- `keyword_id`
- `crawl_task_id`
- `source_url`
- `support_count`
- `evidence_ids`
- `observed_at`
- `aggregation_method`
- `version`

主要用途：
- trace back
- citation / source explanation
- pipeline debug
- output comparison

## 5. QA / RAG 的关键输入说明

### 5.1 RAG 索引最需要什么

如果 QA 侧要做 trend evidence 索引，最重要的是两类内容：

文本索引字段：
- `normalized_keyword`
- `topic_cluster`
- `trend_type`
- `signal_summary`
- `signal_evidence`

metadata 索引字段：
- `source_platform`
- `confidence`
- `risk_flag`
- `trend_score`
- `fresh_until`

### 5.2 QA 主系统最需要什么

主 QA / RAG 系统最应该收到的是一个经过筛选的 trend context block，而不是整包原始 JSON。

推荐最小 trend context block：

```json
{
  "normalized_keyword": "外泌体",
  "trend_type": "ingredient",
  "signal_summary": "外泌体在护肤讨论中持续升温。",
  "signal_evidence": "多条内容将外泌体与修护、抗衰场景绑定。",
  "source_platform": "xiaohongshu",
  "confidence": "medium",
  "risk_flag": "medium",
  "fresh_until": "2026-04-22T11:15:00+08:00"
}
```

这个 block 的目标是让主 QA / RAG 系统知道：
- 当前是什么趋势
- 证据是什么
- 这条趋势强不强
- 风险高不高
- 还新不新

## 6. 字段使用建议

### 6.1 对模型最有用的字段

- `signal_summary`
- `signal_evidence`
- `normalized_keyword`

原因：
- 这些字段最直接影响模型对“当前趋势上下文”的理解

### 6.2 对系统策略最有用的字段

- `confidence`
- `risk_flag`
- `fresh_until`
- `trend_score`

原因：
- 这些字段适合用来决定是否召回、是否降权、是否只作弱上下文

### 6.3 对解释与追踪最有用的字段

- `signal_id`
- `source_platform`
- `source_url`
- `support_count`
- `evidence_ids`

原因：
- 这些字段更适合做引用、追踪、日志和 debug

## 7. 处理工程逻辑

推荐的工程逻辑如下：

1. parse `trend_signal`
2. 将每条记录转为 trend evidence object
3. 建立文本索引和 metadata filter
4. query 时先做召回
5. 再按 freshness / confidence / risk / score 做筛选
6. 将筛选后的结果压成 trend context block
7. 将 trend context block 交给 QA 主系统做最终回答增强

建议保留两层输出：
- evidence item layer
- trend context block layer

这样做的好处是：
- 工程层更可解释
- 检索与回答层的职责更清晰
- 后续 evaluation 更容易追踪

## 8. 核心 Trend 增强处理步骤

从 query 到 trend augmentation，推荐最小流程：

1. 用户 query 进入 QA 系统
2. QA evidence layer 在 `trend_signal` 中做召回
3. 对候选 trend evidence 按 freshness / confidence / risk / score 过滤
4. 生成 trend context block
5. trend context block 与 science / product / compliance 等其他证据一起送入主 QA / RAG
6. 主 QA / RAG 系统输出最终回答

这一步里需要特别注意：
- `trend_signal` 负责提供 trend evidence
- 主 QA 系统负责做最终知识融合和回答治理

## 9. 工程与 Evaluation 如何追踪

工程追踪建议关注：
- `signal_id`
- `source_url`
- `support_count`
- `evidence_ids`
- `fresh_until`
- `aggregation_method`
- `version`

evaluation 追踪建议关注：
- 是否命中了相关 trend evidence
- 命中的 trend evidence 是否 fresh
- 命中的 trend evidence 是否 low-confidence / high-risk
- trend evidence 是被强使用、弱使用、还是仅作为 metadata
- trend evidence 缺失时系统是否 graceful fallback

## 10. 结论

这份文档可以收成一句话：

**TrendAgent 负责生产 trend evidence；QA evidence layer 负责读取和筛选；QA 主系统负责最终回答治理。**

围绕这句话，`trend_signal` 的正确理解是：
- 它是 TA -> QA 的 first-party evidence handoff
- 它不是最终答案
- 它不是科学知识本体
- 它是 RAG / QA 的趋势增强输入层
