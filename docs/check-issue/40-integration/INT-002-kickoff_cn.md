# INT-002 开工指令

## 任务定位

这项任务负责把 TrendAgent 到 crawler 的主链真正收口。

目标不是再讨论关键词策略，而是把下面这条链路变成稳定可跑的工程路径：
- keyword source
- platform-aware planning
- crawl task creation
- vendor crawler execution
- cleaned trend data
- first-party `trend_signal`
- run completion summary

## 开工前必须阅读

- `docs/17-trendagent-vendor-adapter-contract.md`
- `docs/18-mediacrawler-runtime-playbook.md`
- `docs/check-issue/20-trendagent/TA-003-regression-backtest-plan.md`
- `docs/check-issue/40-integration/INT-002-trendagent-crawler-runtime-link.md`

## 允许修改

- `BeautyQA-TrendAgent/backend/` 内与 integration runner / orchestrator / report artifact 相关实现
- `scripts/` 下联调辅助脚本
- 必要的 smoke report / operator docs

## 不允许修改

- 不要把任务扩成 benchmark
- 不要把任务扩成 QA 检索重构
- 不要重写 vendor crawler
- 不要加入外部 IM / 机器人通知耦合

## 核心要求

- 保持 `TA-003` 的一条 query 对应一个 crawl task
- 保持 vendor 只负责 crawler 执行和 raw table 写入
- TrendAgent 负责 orchestration / cleaning / `trend_signal`
- 产出一份 first-party run completion artifact，能让 reviewer 看出每个阶段是否成功

## 必须交付

- changed files
- implementation summary
- integration runner 说明
- 一次小规模真实 smoke result
- run completion artifact 示例
- open risks

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 INT-002。

先阅读以下文件：
- docs/17-trendagent-vendor-adapter-contract.md
- docs/18-mediacrawler-runtime-playbook.md
- docs/check-issue/20-trendagent/TA-003-regression-backtest-plan.md
- docs/check-issue/40-integration/INT-002-trendagent-crawler-runtime-link.md

任务目标：
- 把 TrendAgent -> crawler -> cleaned data -> trend_signal 这条主链收成一个稳定的 integration runtime path
- 产出一份 first-party run completion artifact，便于 review 和 replay

执行边界：
- 可以改 integration runner、script、report artifact
- 不要扩成 benchmark
- 不要改写 QA 检索逻辑
- 不要重写 vendor crawler

必须交付：
- changed files
- implementation summary
- smoke result
- run completion artifact
- open risks

如果发现问题来自 contract 不清或 ownership 边界冲突，暂停并返回 architecture-control。
```
