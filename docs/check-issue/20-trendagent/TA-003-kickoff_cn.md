# TA-003 开工指令

## 任务定位

这项任务处理的是关键词扩展链路和结构化 `trend_monitor` 策略对齐。

目标是减少“关键词元数据”和“实际扩展行为”之间的偏差，并明确 `crawl targets` 与 `reference sources` 的边界。

## 开工前必须阅读

- `docs/14-trendagent-to-qa-data-contract.md`
- `docs/check-issue/00-governance/trendagent-backtest-standard.md`
- `docs/check-issue/20-trendagent/TA-003-keyword-expansion-alignment.md`
- `data/eval/trend_monitor/trend_keyword_expansion_spec_cn.md`

## 前置说明

如果 `data/eval/trend_monitor/trend_keyword_expansion_spec_cn.md` 还没有进入当前执行分支，先向 architecture-control 要求补齐，不要自己猜测规范。

## 允许修改

- `BeautyQA-TrendAgent/` 内关键词扩展输入路径
- scheduler 侧元数据使用方式
- 一方对 target / reference 的过滤逻辑

## 不允许修改

- `BeautyQA-vendor/MediaCrawler/`
- 把 `taobao` 当成 crawler target
- 让 QA 直接知道 crawler 内部实现

## 交付物

- 对齐后的关键词扩展实现或对齐改造说明
- 1 组 before / after 扩展示例
- target / reference 处理说明

## 回测要求

- 展示 1 个关键词对齐前后的差异
- 展示 platform filtering 行为
- 证明 `reference sources` 不会进入 crawler target 执行链

## 遇到这些情况先停

- 规范文件缺失
- 想把 `taobao` 或 `industry_news` 混进 crawler target
- 需要 vendor 侧支持才能表达 target / reference 边界

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 TA-003。

先阅读以下文件：
- docs/14-trendagent-to-qa-data-contract.md
- docs/check-issue/00-governance/trendagent-backtest-standard.md
- docs/check-issue/20-trendagent/TA-003-keyword-expansion-alignment.md
- data/eval/trend_monitor/trend_keyword_expansion_spec_cn.md

任务目标：
- 让 TrendAgent 的关键词扩展行为和结构化 trend_monitor 策略对齐
- 明确 crawl targets 与 reference sources 的边界

执行边界：
- 只改 BeautyQA-TrendAgent 内的一方扩展与调度逻辑
- 不要修改 BeautyQA-vendor/MediaCrawler
- 不要把 taobao 视作 crawler target

必须交付：
- changed files
- implementation or alignment summary
- 1 组 before / after 扩展示例
- backtest result
- open risks

回测要求：
- 展示关键词对齐前后差异
- 展示 platform filtering
- 证明 reference sources 没有进入 crawler target 执行

如果发现规范文件缺失，或 contract 需要改动，暂停并返回 architecture-control。
```
