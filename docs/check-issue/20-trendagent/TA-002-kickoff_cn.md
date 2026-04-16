# TA-002 开工指令

## 任务定位

这项任务把 `trend_signal` 从“有边界”推进到“稳定可生成”。

重点是把 TA-001 的脚手架升级成稳定的一方信号生成层，而不是去改 crawler 或 vendor 实现。

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/check-issue/00-governance/trendagent-backtest-standard.md`
- `docs/check-issue/20-trendagent/TA-002-trend-signal-generation-layer.md`

## 允许修改

- `BeautyQA-TrendAgent/` 内 signal generation 相关代码
- 一方存储、repository、service 层
- sample fixture / export 逻辑

## 不允许修改

- `BeautyQA-vendor/MediaCrawler/`
- crawler 运行流程
- QA 侧调用逻辑

## 交付物

- 可重复运行的 `trend_signal` 生成实现
- 至少一组 grouped signal 示例
- grouping / freshness / confidence / risk 的实现说明
- 一份 run summary 或 refresh summary

## 回测要求

- 报告 sample 输入的 cleaned record 数量
- 报告生成出的 signal 数量
- 至少展示 1 个 grouped signal 示例，若样例允许，`support_count > 1`
- 展示 freshness、confidence、risk 的赋值示例
- 说明同一批输入重复运行时结果结构是否稳定

## 遇到这些情况先停

- 需要直接读取或改写 vendor raw schema 才能完成
- 生成逻辑无法映射到当前 schema
- 需要 QA 先改 contract 才能继续

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 TA-002。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/15-trend-signal-schema.md
- docs/check-issue/00-governance/trendagent-backtest-standard.md
- docs/check-issue/20-trendagent/TA-002-trend-signal-generation-layer.md

任务目标：
- 在 BeautyQA-TrendAgent 中把 TA-001 的 trend_signal 脚手架升级成稳定 generation layer
- 从 cleaned_trend_data 生成 grouped first-party trend_signal

执行边界：
- 只改 BeautyQA-TrendAgent 内的一方聚合、存储、服务层
- 不要修改 BeautyQA-vendor/MediaCrawler
- 不要重做 QA 检索

必须交付：
- changed files
- implementation summary
- sample generated signals
- grouping / scoring notes
- backtest result
- open risks

回测要求：
- 报告 cleaned input count
- 报告 generated signal count
- 给出至少 1 个 grouped signal 示例
- 展示 freshness / confidence / risk 的赋值行为
- 说明 repeated-run stability

如果发现 schema 或 contract 无法支撑实现，暂停并把压力返回 architecture-control，不要自行改设计边界。
```
*** Add File: /Users/liuzhicheng/1data/workspace2026/LN-projs/BeautyModel-Lab/docs/check-issue/40-integration/README.md
# Integration Task Packages

This folder stores cross-module execution packages.

Current sequence:
- `INT-001-e2e-smoke-test.md`
- `INT-001-kickoff_cn.md`
