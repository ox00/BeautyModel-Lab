# INT-003 开工指令

## 任务定位

这项任务负责把 TrendAgent 已生成的 first-party `trend_signal` 定期导出到 QA 可直接消费的 CSV 目录。

这不是 sample fixture 任务，而是 runtime handoff 任务。

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/16-trend-signal-to-qa-usage-guide.md`
- `docs/check-issue/40-integration/INT-003-trend-signal-export-cron.md`

## 允许修改

- `BeautyQA-TrendAgent/backend/` 内与 export job 相关实现
- `scripts/` 下 export / cron 辅助脚本
- `data/` 下 runtime handoff 目录约定与示例 artifact
- operator docs

## 不允许修改

- 不要把 sample path 当作 runtime path
- 不要让 QA 直接读 vendor raw tables
- 不要扩成 benchmark 或 QA 检索治理任务

## 核心要求

- runtime 输出目录与 sample 目录分离
- QA 只读取稳定 handoff CSV
- export job 必须可重复执行，失败时不能覆盖 current 成品文件
- 需要产出 manifest，方便工程排查

## 必须交付

- changed files
- export job summary
- handoff directory 说明
- example export artifact
- cron / replay note
- open risks

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 INT-003。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/15-trend-signal-schema.md
- docs/16-trend-signal-to-qa-usage-guide.md
- docs/check-issue/40-integration/INT-003-trend-signal-export-cron.md

任务目标：
- 把 first-party trend_signal 定期导出到稳定的 QA handoff CSV 目录
- 产出 manifest 和 replay 说明，保证这个 handoff path 可运维

执行边界：
- 可以改 export script、runtime handoff 目录、operator doc
- 不要用 data/pipeline_samples 作为 runtime 输出
- 不要扩成 QA 检索或 benchmark 任务

必须交付：
- changed files
- implementation summary
- export artifact example
- cron / replay note
- open risks

如果发现 schema 不足以支持稳定 handoff，暂停并返回 architecture-control。
```
