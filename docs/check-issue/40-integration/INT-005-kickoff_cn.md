# INT-005 开工指令

## 任务定位

这项任务负责把“批次执行”从可审计，升级成可恢复、可补完、可判断 full / partial / failed。

目标是让一个周期内的同批任务，在中断后还能继续推进，而不是靠人工重新猜哪些没跑完。

## 开工前必须阅读

- `docs/19-trendagent-runtime-strategy.md`
- `docs/20-trend-signal-timeseries-strategy.md`
- `docs/check-issue/40-integration/INT-005-batch-recovery-and-completion-guarantee.md`

## 允许修改

- `BeautyQA-TrendAgent/backend/` 内 batch item schema / recovery / audit summary
- migration 与 operator docs
- replay / reconciliation 脚本

## 不允许修改

- vendor crawler
- QA retrieval 逻辑
- benchmark 逻辑

## 必须交付

- batch item schema
- recovery reconciler 或 replay worker
- completion audit summary
- interrupted batch continuation 的运维说明

## 回测要求

- 展示一个 interrupted batch 的恢复
- 展示 stale-running item 的回收或重试
- 展示 full / partial / failed 的批次判定

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 INT-005。

先阅读以下文件：
- docs/19-trendagent-runtime-strategy.md
- docs/20-trend-signal-timeseries-strategy.md
- docs/check-issue/40-integration/INT-005-batch-recovery-and-completion-guarantee.md

任务目标：
- 让一个 runtime batch 在中断后可恢复并最终判定 full / partial / failed

执行边界：
- 可以改一方 batch schema、recovery、audit summary、operator doc
- 不要改 vendor crawler
- 不要扩成 QA retrieval 或 benchmark 任务

必须交付：
- changed files
- schema / implementation summary
- recovery example
- completion audit example
- open risks

回测要求：
- interrupted batch 恢复
- stale-running reconcile
- full / partial / failed 判定
```
