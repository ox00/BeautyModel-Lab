# PM A 用户问法评审表格 - 3

| QID | 简述 | 建议 `question_type` | 建议 `answer_state` | 建议风险 | 冻结建议 | 建议证据表 | 备注 |
|---|---|---|---|---|---|---|---|
| Q1 | 混油皮早晚 routine | `skincare_recommendation` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge|product_sku|review_feedback` | 常规基础题，可做对照基线 |
| Q2 | 新手抗初老 routine | `skincare_recommendation` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge|product_sku|compliance_rule` | 常规推荐题 |
| Q3 | 敏感肌想试早C晚A | `skincare_recommendation` | `conservative_answer` | `medium` | `holdout_candidate` | `ingredient_knowledge|trend_signal|compliance_rule` | 趋势和耐受冲突，区分度高 |
| Q4 | 大油皮夏季清爽 routine | `skincare_recommendation` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge|product_sku|review_feedback` | 常规肤质场景 |
| Q5 | 孕期敏感护肤搭配 | `skincare_recommendation` | `conservative_answer` | `high` | `holdout_candidate` | `ingredient_knowledge|product_sku|compliance_rule` | 特殊人群，建议高风险处理 |
| Q6 | 熬夜暗沉预算 500 | `skincare_recommendation` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge|product_sku|review_feedback` | 预算约束明确，适合 dev |
| Q7 | 烟酰胺和维C能否同用 | `ingredient_suitability` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge|compliance_rule` | 搭配规则题 |
| Q8 | A醇和面霜能否同用 | `ingredient_suitability` | `conservative_answer` | `medium` | `holdout_candidate` | `ingredient_knowledge|compliance_rule` | 兼顾顺序与刺激风险 |
| Q9 | 备孕期视黄醇能否继续用 | `ingredient_suitability` | `conservative_answer` | `high` | `holdout_candidate` | `ingredient_knowledge|compliance_rule` | 特殊人群高风险题 |
| Q10 | 敏感肌+水杨酸面膜 | `ingredient_suitability` | `conservative_answer` | `medium` | `dev_keep` | `ingredient_knowledge|compliance_rule` | 典型风险判断题 |
| Q11 | 熊果苷能否长期用 | `ingredient_suitability` | `direct_answer` | `medium` | `dev_keep` | `ingredient_knowledge|compliance_rule` | 安全性判断但风险不算极高 |
| Q12 | 烟酰胺和维C冲突传闻 | `ingredient_suitability` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge` | 适合作 myth-busting 基础题 |
| Q13 | 果酸爽肤水叠加 A醇 | `ingredient_suitability` | `conservative_answer` | `high` | `holdout_candidate` | `ingredient_knowledge|compliance_rule` | 强刺激叠加，高区分度 |
| Q14 | 酒精面霜和烟酰胺同用 | `ingredient_suitability` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge` | 可保留，但区分度一般 |
| Q15 | 哺乳期能否用氢醌 | `ingredient_suitability` | `conservative_answer` | `high` | `holdout_candidate` | `ingredient_knowledge|compliance_rule` | 高风险特殊人群 |
| Q16 | 17岁能否用 A醇抗初老 | `ingredient_suitability` | `conservative_answer` | `medium` | `dev_keep` | `ingredient_knowledge|compliance_rule` | 年龄相关适配题 |
| Q17 | 屏障受损能否用香精 | `ingredient_suitability` | `conservative_answer` | `medium` | `dev_keep` | `ingredient_knowledge|review_feedback` | 可测保守回答 |
| Q18 | 大油皮跟风以油养肤 | `trend_alternative` | `conservative_answer` | `high` | `holdout_candidate` | `trend_signal|ingredient_knowledge|review_feedback|compliance_rule` | 核心趋势冲突题 |
| Q19 | 跟风在家高浓度刷酸 | `trend_alternative` | `refusal_constraint` | `high` | `holdout_candidate` | `trend_signal|ingredient_knowledge|compliance_rule` | 明确适合测限制回答 |
| Q20 | 孕期能否跟风早C晚A | `trend_alternative` | `conservative_answer` | `high` | `holdout_candidate` | `trend_signal|ingredient_knowledge|compliance_rule` | 趋势+特殊人群双重冲突 |
| Q21 | 纯净美妆/无防腐剂更安全 | `compliance_claim_safety` | `direct_answer` | `medium` | `needs_feasibility_check` | `trend_signal|compliance_rule` | 可能需要额外规则支撑 |
| Q22 | 7天见效美白霜靠谱吗 | `compliance_claim_safety` | `conservative_answer` | `high` | `holdout_candidate` | `trend_signal|compliance_rule|review_feedback` | 高风险宣称题，值得保留 |
| Q23 | 多活性成分“猛药”值不值得买 | `trend_alternative` | `conservative_answer` | `high` | `holdout_candidate` | `trend_signal|ingredient_knowledge|compliance_rule` | 热门产品风险题，区分度高 |
| Q24 | 烟酰胺不耐受的替代方案 | `trend_alternative` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge|review_feedback` | 标准替代题 |
| Q25 | 敏感肌替代 A醇方案 | `trend_alternative` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge|review_feedback` | 标准替代题 |
| Q26 | 替代早C的抗氧化方案 | `trend_alternative` | `direct_answer` | `low` | `dev_keep` | `ingredient_knowledge|review_feedback` | 标准替代题 |
| Q27 | 7天美白宣称是否靠谱 | `compliance_claim_safety` | `direct_answer` | `high` | `holdout_candidate` | `compliance_rule` | 高价值宣称判断题 |
| Q28 | 紧致提拉宣称是否可信 | `compliance_claim_safety` | `direct_answer` | `medium` | `dev_keep` | `compliance_rule|ingredient_knowledge` | 合规基础题 |
| Q29 | 医美级效果说法是否合规 | `compliance_claim_safety` | `direct_answer` | `high` | `holdout_candidate` | `compliance_rule` | 高价值合规题 |
| Q30 | 如何查进口产品备案 | `compliance_claim_safety` | `direct_answer` | `medium` | `needs_feasibility_check` | `compliance_rule` | 可能依赖外部备案库 |
| Q31 | 械字号是不是更安全 | `compliance_claim_safety` | `direct_answer` | `medium` | `needs_feasibility_check` | `compliance_rule` | 可能需要额外资质规则 |
| Q32 | 食品级安全宣称是否有问题 | `compliance_claim_safety` | `direct_answer` | `high` | `holdout_candidate` | `compliance_rule` | 高风险误导性宣称题 |
