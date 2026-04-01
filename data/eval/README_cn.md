# Eval 资产说明（中文）

这个目录放可机器读取的评测资产和结果文件。

## 目录结构
- `benchmark_dev_v0_seed.csv` - 供团队继续修改的 starter case 库
- `benchmark_holdout_v0_seed.csv` - 供团队继续修改的 starter holdout case 库
- `templates/` - 通用模板
- `results/` - 版本化评测结果

## 使用规则
- `*_seed.csv` 是草稿资产，不是最终冻结版 benchmark
- 真正冻结后的 benchmark 也放在这个目录下版本化管理
- 评测规则文档在 `docs/evaluation/`
- benchmark 有变动时，实验记录和 release review 也要同步更新
