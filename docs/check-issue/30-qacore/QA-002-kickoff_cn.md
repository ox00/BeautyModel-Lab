# QA-002 开工指令

## 任务定位

这项任务不是继续扩功能，而是把 `QA-001` 补成可作为质量门基础的版本。

重点有两件事：
- 把 high-risk 趋势证据挡在强证据路径之外
- 把 QA 运行时对 `trend_signal` 的读取边界收紧到 first-party contract

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/check-issue/30-qacore/QA-001-review.md`
- `docs/check-issue/30-qacore/QA-002-risk-gating-and-contract-hardening.md`

## 允许修改

- `BeautyQA-core/` 内 retrieval / gating / pipeline 代码
- runtime loader 与 migration/backfill loader 的拆分
- tests / fixtures / backtest 脚本

## 不允许修改

- `BeautyQA-TrendAgent/`
- `BeautyQA-vendor/MediaCrawler/`
- 让 QA runtime 重新接受 vendor 依赖

## 交付物

- 风险门控后的 QA 证据判定逻辑
- `trend_filtered_for_safety` 可观测输出
- runtime contract-only ingestion 路径
- 补齐后的测试与 backtest 结果

## 回测要求

- fresh usable -> `trend_supported`
- stale -> `trend_weak_or_missing`
- low confidence -> `trend_weak_or_missing`
- high risk -> `trend_filtered_for_safety`

## 遇到这些情况先停

- 发现当前 contract 字段不足以表达安全门控
- 发现必须改 TrendAgent 才能完成 QA-002
- 发现测试样例缺少必要 contract 数据，且无法在 QA 侧补齐

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 QA-002。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/15-trend-signal-schema.md
- docs/check-issue/30-qacore/QA-001-review.md
- docs/check-issue/30-qacore/QA-002-risk-gating-and-contract-hardening.md

任务目标：
- 修正 QA 趋势证据门控，让 high-risk signal 不进入 strong-evidence path
- 收紧 QA runtime 的输入边界，只接受 first-party trend_signal contract 数据

执行边界：
- 只改 BeautyQA-core 内 retrieval / gating / pipeline / tests / backtest
- 不要修改 BeautyQA-TrendAgent
- 不要引入 vendor crawler runtime dependency

必须交付：
- changed files
- implementation summary
- QA examples
- backtest result
- open risks

回测要求：
- fresh usable -> trend_supported
- stale -> trend_weak_or_missing
- low confidence -> trend_weak_or_missing
- high risk -> trend_filtered_for_safety

如果发现 contract 不足，暂停并返回 architecture-control，不要自行改边界。
```
