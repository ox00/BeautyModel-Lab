# 01 - Benchmark 范围（中文）

## 目标
- 建一套冻结的 benchmark，用来支持模型迭代、版本对比和 release 决策。

## 覆盖范围
- 覆盖 4 类 MVP 问题：
- 护肤推荐与 routine 方向
- 成分适配与风险判断
- 趋势相关替代建议
- 合规与宣称安全判断

## 拆分方式
- `dev`：团队可见，用于日常调试和迭代
- `holdout`：冻结使用，用于版本比较和 release 判断

## 建议规模
- 第一版总量：`30-50` 条
- 建议比例：`70-80%` `dev`，`20-30%` `holdout`

## 覆盖要求
- 4 类问题都要同时出现在 `dev` 和 `holdout`
- 每版都要包含低、中、高风险 case
- 每版都要包含需要补问、保守回答、拒绝/限制回答的 case
- 每条 case 都要能对应到至少一个证据表：`product_sku`、`ingredient_knowledge`、`trend_signal`、`review_feedback`、`compliance_rule`

## 当前不做
- 不做外部用户研究
- 不做开放域美妆闲聊 benchmark
- 不超出当前 MVP 数据边界扩题
