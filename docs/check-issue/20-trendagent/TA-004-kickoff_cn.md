# TA-004 开工指令

## 任务定位

这项任务把“关键词扩展”从运行时临时结果，升级成一方持久化管理对象。

目标不是提高所有扩词质量，而是先把扩词的状态边界固定下来：

- approved
- candidate
- deprecated

## 开工前必须阅读

- `docs/19-trendagent-runtime-strategy.md`
- `docs/20-trend-signal-timeseries-strategy.md`
- `docs/check-issue/20-trendagent/TA-004-expansion-registry.md`
- `docs/check-issue/00-governance/trendagent-backtest-standard.md`

## 允许修改

- `BeautyQA-TrendAgent/` 内 expansion model / service / scheduler read path
- 一方数据库 schema 与 migration
- planner / scheduler 读取 approved expansions 的逻辑

## 不允许修改

- `BeautyQA-vendor/MediaCrawler/`
- QA 侧代码
- 把 `taobao` 变成 crawler target

## 必须交付

- expansion registry schema
- approved / candidate / deprecated 的状态说明与实现
- scheduler 使用 approved expansions 的路径
- 1 组 planner before / after 示例

## 回测要求

- 证明 approved expansions 会进入执行计划
- 证明 candidate expansions 不会直接进入 runtime
- 证明 deprecated expansions 不会被调度

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 TA-004。

先阅读以下文件：
- docs/19-trendagent-runtime-strategy.md
- docs/20-trend-signal-timeseries-strategy.md
- docs/check-issue/20-trendagent/TA-004-expansion-registry.md
- docs/check-issue/00-governance/trendagent-backtest-standard.md

任务目标：
- 把 TrendAgent 的扩展词从临时运行结果升级成一方 registry
- 固定 approved / candidate / deprecated 的边界

执行边界：
- 可以改 BeautyQA-TrendAgent 内 schema、service、scheduler read path
- 不要修改 vendor crawler
- 不要让 QA 依赖 expansion internals

必须交付：
- changed files
- schema / implementation summary
- planner example
- backtest result
- open risks

回测要求：
- approved expansions 进入计划
- candidate expansions 不进入 runtime
- deprecated expansions 被排除
```
