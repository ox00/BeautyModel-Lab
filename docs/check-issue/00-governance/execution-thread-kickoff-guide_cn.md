# 执行线程开工说明

## 目的

这份文档给 architecture-control 使用。

作用只有两个：
- 把任务包转成可直接执行的开工输入
- 保证执行线程不在实现过程中擅自改 contract

## 推荐执行顺序

1. `TA-001`
2. `TA-002`
3. `TA-003`
4. `QA-001`

补充说明：
- `TA-001` 先把 `trend_signal` 输出边界立住。
- `TA-002` 再把 `trend_signal` 生成层做实。
- `TA-003` 处理关键词扩展和 crawl target / reference source 对齐，建议在 `TA-001` 边界明确后再做。
- `QA-001` 最好在 `TA-001` 至少产出一个稳定 sample signal 后开始，理想情况是在 `TA-002` 之后接入。

## 给执行者的标准输入

每次开新线程，至少给这 5 类信息：
- 任务 ID
- 目标与范围
- 不可改动的边界
- 必须阅读的文档
- 回传格式与回测要求

不要只丢一句“按这个文档做一下”。

## 给开发 Agent 的方式

- 新开一个单独线程
- 直接贴对应 `*_kickoff_cn.md` 里的“可直接复制”块
- 明确说明它是执行线程，不负责改设计边界
- 如果只想先开工，可直接用 `execution-thread-short-prompts_cn.md` 里的短口令版本

## 给工程同学的方式

- 发对应任务包
- 再发对应 `*_kickoff_cn.md`
- 明确回传物必须包含样例输出、回测结果、风险项

## 什么时候要暂停执行

出现下面任一情况，执行线程应暂停并回到 architecture-control：
- 发现现有 contract 无法落地
- 需要修改 `BeautyQA-vendor/MediaCrawler/`
- 发现 QA 侧必须读取 vendor raw table
- 上游输入文档缺失，无法可靠判断
- 回测无法证明结果满足任务包要求

## 回传格式

执行线程返回内容统一为：
- changed files
- what was implemented
- backtest result
- sample output or examples
- open risks
- suggested contract changes if any
