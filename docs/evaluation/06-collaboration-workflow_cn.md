# 06 - 协作方式（中文）

## 目标
- 让团队能高效共创 benchmark，同时不要把流程做成工程瓶颈。

## 当前建议的主负责人
- 由 `2 PM + 1 data/domain owner` 主导 benchmark 的整理和收口
- 现阶段不需要工程师参与完整题库共写
- 工程师只在“可执行性检查”和“冻结前检查”两个节点介入

## 分工建议
- PM A
- 负责写用户问法
- 保证问法自然、像真实用户
- 保证场景不是空想题

- PM B
- 负责补 `must_include` 和 `must_not_include`
- 检查可读性、业务合理性、重复度

- Data/domain owner
- 负责定 `question_type`、`risk_level`、`expected_answer_state`
- 负责检查证据表映射是否合理
- 负责最后 merge 和 freeze

- Engineer A / B
- 只做关键节点抽查
- 主要看当前系统是否真的能检索到这题需要的证据

## 工作流程
1. 先在 `seed` 文件或同步表格里写题
2. 给每条题补 `question_type`、`risk_level`、`expected_answer_state`
3. 补 `expected_evidence_tables`、`must_include`、`must_not_include`
4. 去重，合并太像的 case
5. 冻结前做一次工程可执行性检查
6. 把选中的 `dev` 和 `holdout` 集正式写回 repo

## 工作规则
- 一条题只测一个主判断点
- 当前数据支撑不了的题，不要先放进冻结集
- 趋势题不能写成纯营销题，还是要有科学或安全判断
- 高风险题建议双人复核
- `seed` 文件保持可编辑，冻结文件单独版本化

## 工程师什么时候介入
- 团队不确定当前数据能不能支撑这题时
- 题目依赖的输出字段当前 pipeline 还没有时
- 准备正式拿这套 benchmark 做版本对比或 release gate 时

## 当前执行建议
- 先用现有 `36` 条 starter cases 做第一轮整理
- 先由你们三个人做第一轮清洗
- 清洗完后，再请工程同学做一次短的 feasibility check
