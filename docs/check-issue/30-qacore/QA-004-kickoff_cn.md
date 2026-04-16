# QA-004 开工指令

## 任务定位

这项任务专门面向 QA evidence layer。

目标不是做整个 QA 主系统，而是把 first-party `trend_signal` 接成一个清楚可用的 trend evidence layer，供 downstream QA / RAG 使用。

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/16-trend-signal-to-qa-usage-guide.md`
- `docs/check-issue/30-qacore/QA-004-trend-evidence-layer-integration.md`

## 允许修改

- `BeautyQA-core/` 内 `trend_evidence` 相关实现
- tests / fixtures / backtest helpers
- evidence item 与 trend context block 的接口

## 不允许修改

- `BeautyQA-TrendAgent/`
- `BeautyQA-vendor/MediaCrawler/`
- 在这个任务里接管主 QA 系统的最终回答治理

## 交付物

- first-party `trend_signal` ingestion
- evidence item parsing
- retrieval / filter hooks
- trend context block 输出
- trace / debug 字段保留

## 回测要求

- 1 个 evidence item 示例
- 1 个 trend context block 示例
- 1 个 query retrieval 示例
- 1 个弱/过期/高风险 metadata 示例

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 QA-004。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/15-trend-signal-schema.md
- docs/16-trend-signal-to-qa-usage-guide.md
- docs/check-issue/30-qacore/QA-004-trend-evidence-layer-integration.md

任务目标：
- 把 first-party trend_signal 接成 QA evidence layer
- 提供 ingestion、evidence item parsing、retrieval/filter hooks、trend context block 输出
- 不在这个任务里接管主 QA 系统的最终回答治理

执行边界：
- 只改 BeautyQA-core
- 不要修改 TrendAgent / vendor crawler
- 不要把任务扩成整个 QA 引擎开发

必须交付：
- changed files
- implementation summary
- sample trend context block
- backtest result
- open risks

回测要求：
- 展示 evidence item 示例
- 展示 trend context block 示例
- 展示 retrieval/filter 示例
- 展示弱/过期/高风险 metadata 示例

如果发现 contract 不足或边界不清，暂停并返回 architecture-control。
```
