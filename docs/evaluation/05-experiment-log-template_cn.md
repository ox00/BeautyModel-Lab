# 05 - 实验记录模板（中文）

## 头部信息
- benchmark 版本
- 数据 batch 版本
- system 版本
- 评测日期
- reviewers

## 指标说明
- `latency_p95` 指 benchmark case 的端到端响应时间 P95，统计范围是从 query 输入到最终回答输出完成。
- 这个时间应包含 retrieval、reasoning、compliance check 和答案组装，不是只统计某一个模块，比如模型生成时间。

## 对比表

| system_version | benchmark_version | split | correctness | completeness | safety | trend_freshness | explainability | hallucination_rate | latency_p95 | notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| example_v1 | benchmark_v1 | holdout | 1.5 | 1.3 | 1.9 | 1.4 | 1.5 | 0.03 | 4.2 | first runnable baseline |

## 必填说明
- 主要失败模式
- 高风险 case 结果
- 各 question type 的结果摘要
- release / no-release 结论
- 下一步动作
