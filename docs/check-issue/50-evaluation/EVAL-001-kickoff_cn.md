# EVAL-001 开工指令

## 任务定位

这项任务是设计 benchmark v1，不是一次性把全部 case 写完。

目标是把下一轮团队协作需要的结构先定清楚：
- benchmark 测什么
- 如何分 `dev / holdout`
- case 怎么覆盖
- `data/eval/` 下面的资产怎么组织

## 开工前必须阅读

- `docs/evaluation/README.md`
- `docs/evaluation/01-benchmark-scope.md`
- `docs/evaluation/02-case-schema.md`
- `docs/evaluation/03-scoring-rubric.md`
- `docs/evaluation/04-release-gates.md`
- `docs/check-issue/50-evaluation/EVAL-001-benchmark-v1.md`

## 允许修改

- `docs/evaluation/` 下的补充规划文档
- `docs/check-issue/50-evaluation/` 下的任务设计材料
- `data/eval/` 的目录组织建议文档

## 不允许修改

- 把这个任务扩成大规模 case 生成
- 先跑完整模型评分
- 在结构还不稳定时过早冻结大量资产文件

## 交付物

- benchmark v1 package design
- case coverage matrix
- draft case inventory
- `dev / holdout` split 建议
- `data/eval/` 资产组织建议

## 回测要求

- 说明总 case 数建议
- 说明每类 case 的覆盖数量
- 给出至少每个 major band 的 1 个样例
- 写清 benchmark 冻结前还缺什么

## 可直接复制到执行线程

```text
你现在负责独立执行线程中的 EVAL-001。

先阅读以下文件：
- docs/evaluation/README.md
- docs/evaluation/01-benchmark-scope.md
- docs/evaluation/02-case-schema.md
- docs/evaluation/03-scoring-rubric.md
- docs/evaluation/04-release-gates.md
- docs/check-issue/50-evaluation/EVAL-001-benchmark-v1.md

任务目标：
- 设计 benchmark v1 的结构、coverage matrix、dev/holdout split 与资产组织方案
- 让团队下一步能在清楚结构下协作写 case

执行边界：
- 只做 benchmark 设计与组织方案
- 不要扩成大规模 case 生成
- 不要先跑完整评分实验

必须交付：
- changed files
- implementation summary
- benchmark package summary
- coverage matrix
- draft case inventory
- open risks

回测要求：
- 说明 case 总量建议
- 说明各类覆盖数量
- 给出 major band 示例
- 写清冻结前仍缺的依赖

如果发现 evaluation policy 层本身需要先改，再暂停并返回 architecture-control。
```
