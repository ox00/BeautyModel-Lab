# QA-003 开工指令

## 任务定位

这项任务是边界回收，不是推翻已有开发。

目标是把 QA 侧这条线收紧回：
- `trend_signal` 的读取
- retrieval / ranking hooks
- evidence assembly
- metadata 透传给下游 QA / RAG

而不是在这个子任务里提前固化最终回答层的 safety / compliance 政策。

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/check-issue/30-qacore/QA-003-trend-evidence-boundary-tightening.md`

如需了解前序背景，再补读：
- `docs/check-issue/30-qacore/QA-001-trend-signal-retrieval-integration.md`
- `docs/check-issue/30-qacore/QA-002-risk-gating-and-contract-hardening.md`

## 允许修改

- `BeautyQA-core/` 内 `trend_signal` ingestion / retrieval / assembly 相关实现
- metadata / flag 输出方式
- 与 QA 主系统衔接的 hook 或接口
- tests / fixtures / backtest 脚本

## 不允许修改

- `BeautyQA-TrendAgent/`
- `BeautyQA-vendor/MediaCrawler/`
- 在这个子任务里擅自定义整个 QA 系统的最终 safety / compliance 回答策略

## 交付物

- 收紧后的 QA 侧 trend evidence 接入实现
- freshness / confidence / risk 的 metadata 或 flag 输出
- 一份回退/收紧说明，说明从 `QA-002` 保留了什么、回收了什么

## 回测要求

- 有趋势证据时，能进入 downstream QA / RAG 的 evidence assembly
- 趋势缺失或 stale 时，系统能 graceful fallback
- `risk_flag` 能暴露给下游，但不由本任务宣称“最终决策已经完成”

## 遇到这些情况先停

- 发现 contract 字段不足以支持 evidence assembly
- 发现必须改 TrendAgent 才能完成这个回收任务
- 发现 QA 主系统 owner 已明确给出另一套回答治理接口，需要 architecture-control 先更新边界文档

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 QA-003。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/15-trend-signal-schema.md
- docs/check-issue/30-qacore/QA-003-trend-evidence-boundary-tightening.md

如需了解前序背景，再补读：
- docs/check-issue/30-qacore/QA-001-trend-signal-retrieval-integration.md
- docs/check-issue/30-qacore/QA-002-risk-gating-and-contract-hardening.md

任务目标：
- 把 QA 侧实现收紧回 trend_signal ingestion + retrieval/evidence assembly 边界
- 保留 freshness / confidence / risk 等 metadata 给下游 QA/RAG 使用
- 不在这个子任务里固化最终 safety/compliance answer policy

执行边界：
- 只改 BeautyQA-core
- 不要修改 TrendAgent 或 vendor crawler
- 不要把这个子任务扩成整个 QA 回答治理系统

必须交付：
- changed files
- implementation summary
- rollback/tightening summary
- backtest result
- open risks

回测要求：
- 有趋势证据时能进入 evidence assembly
- 趋势缺失或 stale 时 graceful fallback
- risk_flag 对下游可见，但不由本任务承担最终回答治理

如果发现 contract 不足或边界不清，暂停并返回 architecture-control，不要自行改定义。
```
