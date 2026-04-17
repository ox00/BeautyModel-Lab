# INT-004 开工指令

## 任务定位

这项任务把当前“单次 task 输出的 trend_signal”，升级成“按时间桶聚合的 trend_signal_series”。

目标是支持动态趋势观察，而不是只保留一次性快照。

## 开工前必须阅读

- `docs/15-trend-signal-schema.md`
- `docs/16-trend-signal-to-qa-usage-guide.md`
- `docs/20-trend-signal-timeseries-strategy.md`
- `docs/check-issue/40-integration/INT-004-trend-signal-series-aggregation.md`

## 允许修改

- `BeautyQA-TrendAgent/backend/` 内 series aggregation 相关实现
- export / handoff 相关说明文档
- runtime artifact 示例

## 不允许修改

- vendor crawler
- QA 检索治理逻辑
- batch recovery 逻辑

## 必须交付

- series schema 或 storage path
- 一个时间桶聚合作业
- 一组 bucketed output 示例
- 与 handoff 路径的衔接说明

## 回测要求

- 展示一个关键词跨两个 bucket 的聚合结果
- 展示 `delta_vs_prev_bucket`
- 证明 series 结果还能追溯回 signal 或 task

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 INT-004。

先阅读以下文件：
- docs/15-trend-signal-schema.md
- docs/16-trend-signal-to-qa-usage-guide.md
- docs/20-trend-signal-timeseries-strategy.md
- docs/check-issue/40-integration/INT-004-trend-signal-series-aggregation.md

任务目标：
- 把单次 trend_signal 输出升级成时间桶 trend_signal_series
- 让趋势观察具备 bucket 和 delta 语义

执行边界：
- 可以改 TrendAgent 内 aggregation 和 handoff 路径
- 不要改 vendor crawler
- 不要扩成 QA retrieval redesign 或 batch recovery

必须交付：
- changed files
- implementation summary
- series artifact example
- backtest result
- open risks

回测要求：
- 一个关键词跨两个 bucket
- 展示 delta_vs_prev_bucket
- 保留 source traceability
```
