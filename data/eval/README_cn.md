# Eval 资产说明（中文）

这个目录放可机器读取的评测资产和结果文件。

## 目录结构
- `benchmark_dev_v0_seed.csv` - 供团队继续修改的 starter case 库
- `benchmark_holdout_v0_seed.csv` - 供团队继续修改的 starter holdout case 库
- `drafts/` - 原始问法稿、PM 输入稿等草稿文件
- `review/` - 评审结论、筛选表、结构化评审文件
- `trend_monitor/` - 趋势报告登记表、关键词种子表、工程接入说明和供 agents 使用的输入文件
- `templates/` - 通用模板
- `results/` - 版本化评测结果

## 使用规则
- `*_seed.csv` 是草稿资产，不是最终冻结版 benchmark
- `drafts/` 里的文件保持可编辑，主要作为输入素材使用
- `review/` 里的文件是中间评审产物，不直接当冻结 benchmark 使用
- `trend_monitor/` 里的文件用于趋势监控和关键词采集，不和 benchmark case 混用
- 真正冻结后的 benchmark 也放在这个目录下版本化管理
- 评测规则文档在 `docs/evaluation/`
- benchmark 有变动时，实验记录和 release review 也要同步更新
