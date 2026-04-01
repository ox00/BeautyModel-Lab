# Evaluation 文档说明（中文）

这个目录放当前 MVP 的评测规则文档。

## 作用
- 说明 benchmark 怎么设计、review、冻结和使用
- 让质量控制口径在多轮迭代里保持一致
- 把评测规则和真正跑分用的数据文件分开

## 文件
1. `01-benchmark-scope_cn.md` - benchmark 的目标、拆分方式和覆盖要求
2. `02-case-schema_cn.md` - case 字段和标注要求
3. `03-scoring-rubric_cn.md` - 评分维度和打分标准
4. `04-release-gates_cn.md` - release gate 和阻断条件
5. `05-experiment-log-template_cn.md` - 版本对比和实验记录模板
6. `06-collaboration-workflow_cn.md` - 结合当前团队结构的协作方式

## 使用规则
- `docs/evaluation/` 放规则和流程
- `data/eval/` 放 benchmark 资产和结果文件
- benchmark 版本变化时，规则和记录要一起更新
