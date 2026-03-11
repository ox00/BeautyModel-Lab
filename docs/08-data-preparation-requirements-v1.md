# 08 - Data Preparation Requirements (v1)

## 1. 目标与范围
- 目标：为「科学理性护肤 + Trending 审美」QA 顾问提供可训练、可迭代、可合规的数据供给规范。
- 适用范围：MVP 阶段（课程项目），仅覆盖首轮可上线能力，不追求全行业全量数据。
- 原则：小切口高质量、分级供给、可追溯更新、严格去标识化。

## 2. 数据分级与使用边界
- `P0`（可训练包）：结构化、脱敏、抽样后的训练数据，可用于蒸馏和微调。
- `P1`（受限特征层）：仅开放特征或检索接口，不下发原始明细。
- `P2`（盲测集）：仅用于离线评测和发布门禁，禁止参与训练。

## 3. MVP 必备数据实体（6 张表）

| 表名 | 作用 | MVP必备字段（最小集） | 备注 |
|---|---|---|---|
| `product_sku` | 商品基础事实 | `sku_id`, `brand`, `category_lv1`, `category_lv2`, `price_band`, `launch_date`, `core_claims` | 商品主数据锚点 |
| `ingredient_knowledge` | 成分科学知识 | `ingredient_id`, `name_cn`, `function_tags`, `evidence_level`, `risk_tags`, `contraindications` | 支撑科学解释 |
| `review_feedback` | 口碑反馈信号 | `review_id`, `sku_id`, `source`, `rating_bucket`, `sentiment_tag`, `effect_tags`, `issue_tags`, `created_at` | 文本可只保留摘要/标签 |
| `trend_signal` | 趋势与热度 | `trend_id`, `keyword`, `topic_cluster`, `heat_index`, `growth_7d`, `platform`, `captured_at` | 趋势动态更新核心 |
| `compliance_rule` | 合规规则 | `rule_id`, `jurisdiction`, `rule_type`, `rule_text`, `effective_date`, `status` | 公开规则可全量 |
| `profile_bucket` | 匿名用户分群（可选） | `bucket_id`, `skin_type`, `concern_top3`, `budget_level`, `region_tier`, `age_bucket` | 仅弱画像，不含PII |

## 4. 数据源建议（按可用性分层）

| 层级 | 数据类型 | 建议来源 | 更新建议 |
|---|---|---|---|
| 内部优先 | 商品、评论、趋势基础信号 | 公司内部商品库、内容接口（含小红书相关趋势接口） | 日更/周更 |
| 公共增强 | 成分、法规、标准术语 | 监管公告、公开法规、行业词典/期刊 | 周更/月更 |
| 模型增强 | 弱画像与标签补全 | 第三方大模型蒸馏（仅生成标签，不沉淀PII） | 双周迭代 |

## 5. 供给量与采样要求（MVP）

### 5.1 基准配额（每轮）
- `product_sku`：`800-1500`（推荐 `1000`）
- `review_feedback`：`10000-30000`（推荐 `20000`）
- `trend_signal` 关键词：`200-500`（推荐 `300`）
- `ingredient_knowledge`：`300-500`
- `compliance_rule`：公开规则尽量全量

### 5.2 抽样策略
- 分层维度：类目、价格带、品牌梯度、生命周期（上新/成熟/长尾）。
- 建议占比：头部稳定 `40%`、核心中腰部 `35%`、长尾 `15%`、上新趋势 `10%`。
- 趋势过采样：至少 `20%` 样本来自高增长词（如 `7` 日增长 `>30%`）。
- 评论策略：优先标签化摘要，原文仅保留必要抽样用于审核与误差分析。

## 6. 数据质量与验收门槛
- 主键唯一性：`100%`
- 必填字段完整率：`>=95%`
- 重复率：`<=2%`
- 时间字段合法率（`YYYY-MM-DD HH:MM:SS`）：`>=98%`
- 趋势时效：核心趋势数据延迟 `<=24h`（最晚 `<=7` 天进入训练包）
- 编码与规范：统一 `UTF-8`、枚举值受控、单位标准化
- 隐私合规：训练包与导出物禁止PII，遵循最小必要原则

## 7. 供给量控制机制（给企业侧）
- 固定“轮次预算”：按双周批次供给，避免无限制临时拉数。
- 三包策略：
  - `Base Pack`：稳定训练底座（固定配额）
  - `Focus Pack`：围绕当期趋势专题增量（受配额上限）
  - `Holdout Pack`：评测盲测包（只读、隔离）
- 输出形态优先级：结构化标签 > 摘要 > 原始文本，降低数据泄露风险。
- 访问控制：团队按角色开通 `P0/P1/P2` 权限，不跨级共享。

## 8. 与蒸馏/多轮对撞飞轮的衔接
- Step 1（数据注入）：按本规范输出 `P0 + P1 + P2`。
- Step 2（教师蒸馏）：多模型生成候选答案与标签，保留分歧样本。
- Step 3（专家对撞）：用成分知识+合规规则校核，沉淀高价值样本。
- Step 4（学生回训）：只用通过门禁的数据更新学生模型，并用 `P2` 回归评测。

## 9. 每轮交付物（最小）
- `data_manifest_<batch>.csv`：批次清单（表名、条数、时间窗、来源）
- `quality_report_<batch>.md`：质量指标与异常项
- `sampling_report_<batch>.md`：分层占比与趋势过采样说明
- `release_note_<batch>.md`：可用于训练/评测的版本声明

## 10. 版本约定
- 当前版本：`v1.0`（基于 `docs/数据体系_vbeta.xlsx` 抽取并与MVP文档对齐）
- 后续更新触发：MVP范围变化、合规要求变化、趋势刷新机制升级
