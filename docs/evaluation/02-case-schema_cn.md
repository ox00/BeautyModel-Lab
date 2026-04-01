# 02 - Case 字段（中文）

## 必填字段
- `case_id`：稳定唯一 ID
- `split`：`dev` 或 `holdout`
- `question_type`：4 类 MVP 问题之一
- `difficulty`：`easy`、`medium`、`hard`
- `risk_level`：`low`、`medium`、`high`
- `user_query`：用户原始问法

## 标注字段
- `input_profile`：可选的用户背景信息，比如肤质、诉求、预算
- `expected_answer_state`：`direct_answer`、`clarification`、`conservative_answer`、`refusal_constraint`
- `expected_evidence_tables`：这题应该依赖哪些证据表
- `must_include`：回答里必须出现的点
- `must_not_include`：不能出现的说法、风险点或常见错误
- `notes`：补充说明

## 评审字段
- `correctness_score`
- `completeness_score`
- `safety_score`
- `trend_freshness_score`
- `explainability_score`
- `hallucination_flag`
- `reviewer`
- `review_notes`
- `system_version`

## 写题规则
- 一条 case 只测一个主冲突或主判断点
- 问法要像真实用户，不要写成内部测试 prompt
- case 必须在当前 MVP 范围和数据边界内可回答
- 如果当前数据支撑不了，这条题就不要进冻结集
