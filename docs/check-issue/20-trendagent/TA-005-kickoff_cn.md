# TA-005 开工指令

## 任务定位

这项任务把“什么时候该爬这个 query”从临时判断，升级成一方持久化 schedule state。

目标是让周期性抓取真正由 query-unit 状态控制，而不是只靠 task dedup 挡重复。

## 开工前必须阅读

- `docs/19-trendagent-runtime-strategy.md`
- `docs/20-trend-signal-timeseries-strategy.md`
- `docs/check-issue/20-trendagent/TA-005-query-schedule-state.md`
- `docs/check-issue/00-governance/trendagent-backtest-standard.md`

## 允许修改

- `BeautyQA-TrendAgent/` 内 scheduler / service / schema / migration
- crawl 成功或失败后的状态更新逻辑

## 不允许修改

- `BeautyQA-vendor/MediaCrawler/`
- QA 侧代码
- batch recovery 逻辑

## 必须交付

- query-unit schedule state schema
- watchlist-hot / normal / discovery 的 tier 规则
- `min_revisit_interval` / `retry_cooldown` / `next_due_at` 的状态更新逻辑
- scheduler 基于 schedule state 的 due 选择路径

## 回测要求

- 展示 success 后 `next_due_at` 更新
- 展示 failure 后 cooldown 生效
- 展示 A / B / C tier 的不同调度间隔

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 TA-005。

先阅读以下文件：
- docs/19-trendagent-runtime-strategy.md
- docs/20-trend-signal-timeseries-strategy.md
- docs/check-issue/20-trendagent/TA-005-query-schedule-state.md
- docs/check-issue/00-governance/trendagent-backtest-standard.md

任务目标：
- 为每个 query-unit 建立一方 schedule state
- 让周期性抓取由 revisit interval / cooldown / next_due 控制

执行边界：
- 可以改 TrendAgent 内 scheduler、service、schema、migration
- 不要改 vendor crawler
- 不要扩成 batch recovery

必须交付：
- changed files
- schema / implementation summary
- success / failure schedule example
- backtest result
- open risks

回测要求：
- success 后 next_due 更新
- failure 后 cooldown 生效
- A / B / C tier 间隔有差异
```
