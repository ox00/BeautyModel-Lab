# TA-001 开工指令

## 任务定位

这项任务先把 `BeautyQA-TrendAgent/` 的一方输出边界立住。

目标不是把整套趋势聚合一次做完，而是让 TrendAgent 明确产出面向 QA 的 `trend_signal` 路径或最小可用接口。

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/check-issue/00-governance/trendagent-backtest-standard.md`
- `docs/check-issue/20-trendagent/TA-001-trendagent-to-qa-contract-adoption.md`

## 允许修改

- `BeautyQA-TrendAgent/` 内的一方代码
- 一方 schema / model / repository / service 层
- 模块说明文档

## 不允许修改

- `BeautyQA-vendor/MediaCrawler/`
- QA 检索逻辑
- vendor crawler 运行行为

## 交付物

- 一个明确的 `trend_signal` 输出路径、接口或占位实现
- 1 个 sample `trend_signal` 对象或 fixture
- 涉及到的 README / 模块说明更新

## 回测要求

- 展示一条 `cleaned_trend_data -> trend_signal` 的路径
- 证明没有引入 QA 对 vendor raw table 的依赖
- sample 输出字段能对齐 `docs/15-trend-signal-schema.md`

## 遇到这些情况先停

- 需要改 vendor crawler 才能继续
- schema 字段不够用，必须新增或删减 contract 字段
- 发现 QA 必须读取 vendor 表才可工作

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 TA-001。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/15-trend-signal-schema.md
- docs/check-issue/00-governance/trendagent-backtest-standard.md
- docs/check-issue/20-trendagent/TA-001-trendagent-to-qa-contract-adoption.md

任务目标：
- 在 BeautyQA-TrendAgent 内引入面向 QA 的 first-party trend_signal 输出路径
- cleaned_trend_data 可以继续作为中间层保留

执行边界：
- 只改 BeautyQA-TrendAgent 内的一方代码和必要文档
- 不要修改 BeautyQA-vendor/MediaCrawler
- 不要重做 QA 检索

必须交付：
- changed files
- implementation summary
- 1 个 sample trend_signal 输出
- backtest result
- open risks

回测要求：
- 展示 cleaned -> signal 的一条最小路径
- 确认没有把 vendor raw schema 暴露给 QA
- 确认 sample 输出和 schema 对齐

如果发现 contract 需要调整，暂停实现，先把问题返回 architecture-control，不要自行改边界。
```
