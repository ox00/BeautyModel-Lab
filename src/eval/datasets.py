from __future__ import annotations

from typing import List

from .case_defs import AnswerEvalCase, RetrievalEvalCase


def get_default_retrieval_eval_cases() -> List[RetrievalEvalCase]:
    return [
        RetrievalEvalCase(
            case_id="science_ingredient_lookup",
            query="PHERETIMA GUILLELMI EXTRACT",
            intent="science",
            expected_tables=["ingredient_knowledge"],
            description="Scientific ingredient lookup should retrieve ingredient evidence.",
        ),
        RetrievalEvalCase(
            case_id="science_mechanism_lookup",
            query="地龙提取物 功效",
            intent="science",
            expected_tables=["ingredient_knowledge"],
            description="Chinese science phrasing should still retrieve ingredient evidence.",
        ),
        RetrievalEvalCase(
            case_id="science_inci_lookup",
            query="INCI ingredient efficacy",
            intent="science",
            expected_tables=["ingredient_knowledge"],
            description="English ingredient wording should retrieve scientific evidence.",
        ),
        RetrievalEvalCase(
            case_id="science_synonym_lookup",
            query="威廉环毛蚓 提取物",
            intent="science",
            expected_tables=["ingredient_knowledge"],
            description="Synonym-like ingredient query should retrieve scientific evidence.",
        ),
        RetrievalEvalCase(
            case_id="science_compliance_pair",
            query="PHERETIMA GUILLELMI EXTRACT 安全",
            intent="science",
            expected_tables=["ingredient_knowledge", "compliance_rule"],
            description="Science-plus-safety query should retrieve both ingredient and compliance evidence.",
            requires_risk_flag=True,
        ),
        RetrievalEvalCase(
            case_id="science_mechanism_terms",
            query="ingredient mechanism efficacy",
            intent="science",
            expected_tables=["ingredient_knowledge"],
            description="Mechanism-oriented query should retrieve scientific evidence.",
        ),
        RetrievalEvalCase(
            case_id="science_legacy_query",
            query="成分 功效 作用",
            intent="science",
            expected_tables=["ingredient_knowledge"],
            description="Generic science intent should still return scientific evidence.",
        ),
        RetrievalEvalCase(
            case_id="product_feedback_lookup",
            query="护手霜",
            intent="review",
            expected_tables=["review_feedback_raw", "review_feedback"],
            description="Experience query should retrieve raw or aggregated review evidence.",
        ),
        RetrievalEvalCase(
            case_id="product_raw_feedback_lookup",
            query="手霜 好用 不油腻",
            intent="review",
            expected_tables=["review_feedback_raw"],
            description="Raw feedback-style query should hit raw review evidence.",
        ),
        RetrievalEvalCase(
            case_id="product_feedback_issue_lookup",
            query="护手霜 干燥 起皮",
            intent="review",
            expected_tables=["review_feedback_raw", "review_feedback"],
            description="Issue-oriented feedback query should retrieve review evidence.",
        ),
        RetrievalEvalCase(
            case_id="product_lookup",
            query="护手",
            intent="product",
            expected_tables=["product_sku"],
            description="Product query should retrieve product fact evidence.",
        ),
        RetrievalEvalCase(
            case_id="product_brand_lookup",
            query="HBN",
            intent="product",
            expected_tables=["product_sku"],
            description="Brand-only query should retrieve product fact evidence.",
        ),
        RetrievalEvalCase(
            case_id="product_category_lookup",
            query="眼膜",
            intent="product",
            expected_tables=["product_sku"],
            description="Category-like query should retrieve product facts.",
        ),
        RetrievalEvalCase(
            case_id="trend_freshness_lookup",
            query="冰晶眼膜",
            intent="trend",
            expected_tables=["trend_signal"],
            description="Trend query should retrieve trend evidence.",
        ),
        RetrievalEvalCase(
            case_id="trend_hotness_lookup",
            query="冰晶眼膜 最近有什么趋势",
            intent="trend",
            expected_tables=["trend_signal"],
            description="Trend phrasing should retrieve trend evidence under the auto intent path.",
        ),
        RetrievalEvalCase(
            case_id="trend_synonym_lookup",
            query="眼部 冰凉 贴片",
            intent="trend",
            expected_tables=["trend_signal"],
            description="Synonym-expanded trend query should retrieve trend evidence.",
        ),
        RetrievalEvalCase(
            case_id="trend_platform_lookup",
            query="热度 趋势",
            intent="trend",
            expected_tables=["trend_signal"],
            description="Generic trend query should retrieve trend evidence.",
        ),
        RetrievalEvalCase(
            case_id="trend_product_pair",
            query="HBN 冰晶眼膜 趋势",
            intent="trend",
            expected_tables=["trend_signal", "product_sku"],
            description="Trend-plus-product query should retrieve both trend and product evidence.",
        ),
        RetrievalEvalCase(
            case_id="compliance_guardrail_lookup",
            query="乳黄素",
            intent="compliance",
            expected_tables=["compliance_rule"],
            description="Compliance query should retrieve rule evidence with risk flag.",
            requires_risk_flag=True,
        ),
        RetrievalEvalCase(
            case_id="compliance_safety_lookup",
            query="乳黄素 是否合规",
            intent="compliance",
            expected_tables=["compliance_rule"],
            description="Safety phrasing should retrieve compliance evidence.",
            requires_risk_flag=True,
        ),
        RetrievalEvalCase(
            case_id="compliance_rule_lookup",
            query="规则 安全 约束",
            intent="compliance",
            expected_tables=["compliance_rule"],
            description="Rule-oriented query should retrieve compliance evidence.",
        ),
        RetrievalEvalCase(
            case_id="compliance_limit_lookup",
            query="限制 禁用 安全",
            intent="compliance",
            expected_tables=["compliance_rule"],
            description="Restriction-oriented query should retrieve compliance evidence.",
            requires_risk_flag=True,
        ),
        RetrievalEvalCase(
            case_id="compliance_product_pair",
            query="HBN 乳黄素 安全",
            intent="compliance",
            expected_tables=["compliance_rule", "product_sku"],
            description="Product-plus-compliance query should retrieve both compliance and product evidence.",
            requires_risk_flag=True,
        ),
        RetrievalEvalCase(
            case_id="mixed_science_trend_lookup",
            query="PHERETIMA GUILLELMI EXTRACT 趋势",
            intent="science",
            expected_tables=["ingredient_knowledge", "trend_signal"],
            description="Mixed science-trend query should retrieve both evidence types.",
        ),
        RetrievalEvalCase(
            case_id="mixed_review_product_lookup",
            query="护手霜 推荐",
            intent="review",
            expected_tables=["review_feedback_raw", "review_feedback", "product_sku"],
            description="Review recommendation query should retrieve feedback and product evidence.",
        ),
    ]


def get_default_answer_eval_cases() -> List[AnswerEvalCase]:
    return [
        AnswerEvalCase(
            case_id="science_priority_case",
            query="PHERETIMA GUILLELMI EXTRACT 有什么功效",
            expected_intent="science",
            requires_scientific_basis=True,
        ),
        AnswerEvalCase(
            case_id="trend_priority_case",
            query="冰晶眼膜 最近有什么趋势",
            expected_intent="trend",
            requires_trend_basis=True,
            filters={"need_trend": True},
        ),
        AnswerEvalCase(
            case_id="safety_redline_case",
            query="乳黄素 是否合规",
            expected_intent="compliance",
            requires_safety_warning=True,
        ),
        AnswerEvalCase(
            case_id="balance_case",
            query="护手霜 现在流行什么而且要安全",
            expected_intent="compliance",
            requires_safety_warning=True,
        ),
        AnswerEvalCase(
            case_id="missing_info_case",
            query="不存在的奇怪查询 123456",
            expected_intent="product",
            expects_missing_info=True,
            requires_trace_coverage=False,
        ),
    ]
