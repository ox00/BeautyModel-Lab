# INT-001 开工指令

## 任务定位

这项任务不是做大评测，而是证明主链真的已经连起来。

目标是验证这一条最小闭环：
- cleaned trend data
- `trend_signal` generation
- QA evidence ingestion
- evidence 缺失或弱时 graceful fallback

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/check-issue/20-trendagent/TA-002-trend-signal-generation-layer.md`
- `docs/check-issue/30-qacore/QA-003-trend-evidence-boundary-tightening.md`
- `docs/check-issue/40-integration/INT-001-e2e-smoke-test.md`

## 允许修改

- `BeautyQA-TrendAgent/` 与 `BeautyQA-core/` 的 test-only fixture / script / sample wiring
- smoke test 说明文档与结果报告

## 不允许修改

- 把这个任务扩成正式 benchmark
- 把这个任务扩成 crawler / keyword expansion 重构
- 把 QA answer policy 扩写成新的治理任务

## 交付物

- 一套可复跑的 smoke test 执行步骤或脚本
- sample input / output
- 一份 stage-by-stage 结果报告
- 1 个 evidence present case
- 1 个 evidence weak/absent case

## 回测要求

- 报告 cleaned input count
- 报告 generated signal count
- 报告 QA evidence retrieval 结果
- 报告 graceful fallback 结果
- 写清手动前置条件

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 INT-001。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/15-trend-signal-schema.md
- docs/check-issue/20-trendagent/TA-002-trend-signal-generation-layer.md
- docs/check-issue/30-qacore/QA-003-trend-evidence-boundary-tightening.md
- docs/check-issue/40-integration/INT-001-e2e-smoke-test.md

任务目标：
- 验证 cleaned_trend_data -> trend_signal -> QA evidence ingestion 这条最小闭环真实可跑
- 验证 trend evidence 缺失或弱时能够 graceful fallback

执行边界：
- 只做 sample 数据、fixture、最小 script、最小报告
- 不要扩成正式 benchmark
- 不要改写项目总架构

必须交付：
- changed files
- implementation summary
- smoke test result
- sample inputs / outputs
- open risks

回测要求：
- 报告 cleaned input count
- 报告 generated signal count
- 报告 evidence present case
- 报告 weak/absent case fallback

如果发现链路断点来自 contract 不清，暂停并返回 architecture-control。
```
