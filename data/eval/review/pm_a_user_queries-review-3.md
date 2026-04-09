# PM A 用户问法评审版清单 - 3

## 1. 总体判断
- 这 32 条问法已经可以作为一轮正式整理的输入底稿。
- 相比上一版，第三类“趋势相关替代建议”明显更贴近项目核心任务，已经不再只是“大牌平替”。
- 当前最适合的定位仍然是“待结构化的高质量用户问法池”，还不是可直接冻结的 benchmark。

## 2. 这版做得比较好的地方
- 四类 `question_type` 都有覆盖，数量也在第一版 benchmark 建议范围内。
- 问法整体自然，比较像真实用户，而不是内部测试 prompt。
- 趋势类新增了“趋势热度 vs 科学/安全”冲突场景，这一点很关键。
- 高风险题的比例比上一版更合理，更适合后续做 holdout 候选集。

## 3. 当前还差什么
- 还没有补 `split`
- 还没有补 `difficulty`
- 还没有逐条补 `expected_answer_state`
- 还没有逐条补 `expected_evidence_tables`
- 还没有补 `must_include` 和 `must_not_include`

这些字段不补完，就还不能直接变成冻结 benchmark。

## 4. 本轮评审建议
- 适合直接进入 `dev` 整理队列：`15` 条
- 适合作为 `holdout` 候选重点整理：`14` 条
- 需要先做可执行性检查再决定是否保留：`3` 条

## 5. 建议重点处理的题
- 高优先级 holdout 候选：
`Q3`、`Q5`、`Q9`、`Q13`、`Q15`、`Q18`、`Q19`、`Q20`、`Q22`、`Q23`、`Q27`、`Q29`、`Q32`
- 这些题的价值在于：
- 能测保守回答或限制回答能力
- 能测趋势与科学/安全冲突
- 能测高风险宣称判断

## 6. 需要先做可执行性确认的题
- `Q21` “纯净美妆 / 无防腐剂更安全吗”
- `Q30` “怎么查进口护肤品正规备案”
- `Q31` “械字号是不是比妆字号更安全”

原因：
- 这几题可能不只依赖当前五张表，还可能需要额外规则或外部资质信息。
- 在没有确认数据与规则边界前，不建议先放进冻结集。

## 7. 下一步怎么做
1. 先按配套表格把 32 条题逐条补上 `expected_answer_state`
2. 再补 `expected_evidence_tables`
3. 按评审建议区分 `dev_keep / holdout_candidate / needs_feasibility_check`
4. PM B 再补 `must_include / must_not_include`
5. 最后再决定第一轮冻结哪些题

## 8. 配套文件
- 表格版清单：
`data/eval/pm_a_user_queries-review-table-3.md`
- CSV 样例：
`data/eval/pm_a_user_queries-review-sample-3.csv`
