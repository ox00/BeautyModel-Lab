# QA-001 开工指令

## 任务定位

这项任务把 QA 对趋势数据的使用方式接上，但只允许读取一方 `trend_signal`。

重点是“趋势证据接入”，不是把 QA 变成 crawler 的下游。

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/15-trend-signal-schema.md`
- `docs/check-issue/30-qacore/QA-001-trend-signal-retrieval-integration.md`
- 当前 QA 架构相关文档

## 允许修改

- `BeautyQA-core/` 内 retrieval / evidence assembly 相关代码
- QA 对 trend evidence 的过滤、降权、降级逻辑
- QA 侧样例和测试

## 不允许修改

- `BeautyQA-vendor/MediaCrawler/`
- 直接读取 vendor raw table
- 让趋势证据覆盖 science / compliance 硬约束

## 交付物

- QA 接入 `trend_signal` 的实现或设计落地
- 1 个“有趋势证据”的 QA 例子
- 1 个“趋势缺失或过期”的 QA 例子

## 回测要求

- 展示 trend evidence 存在时 QA 如何使用
- 展示 trend evidence 缺失或 stale 时 QA 如何保守退化
- 说明低置信度趋势不会压过科学和合规证据

## 遇到这些情况先停

- 想直接调用 crawler
- 想直接依赖 vendor 表结构
- 发现 trend_signal schema 不足以支持 QA 检索

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 QA-001。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/15-trend-signal-schema.md
- docs/check-issue/30-qacore/QA-001-trend-signal-retrieval-integration.md
- 当前 QA 架构相关文档

任务目标：
- 在 BeautyQA-core 中接入 first-party trend_signal retrieval
- 保持 QA 与 crawler 实现细节解耦

执行边界：
- 只改 BeautyQA-core 和 QA-facing retrieval / evidence assembly
- 不要引入 vendor crawler runtime dependency
- 不要让 trend evidence 覆盖 science / compliance 硬约束

必须交付：
- changed files
- implementation summary
- 1 个有 trend evidence 的 QA 例子
- 1 个 trend evidence 缺失或过期的 QA 例子
- backtest result
- open risks

回测要求：
- 展示 trend evidence present / absent 两种情况
- 说明 stale / low-confidence signal 如何降权
- 证明 QA 没有引入 crawler 运行依赖

如果发现需要改 contract 或 schema，暂停并把问题返回 architecture-control。
```
