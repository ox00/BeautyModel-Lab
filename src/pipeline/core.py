from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional

from src.retrieval import EvidenceItem, RetrievalBundle, search_all


HIGH_RISK_FLAGS = {"high_risk", "restricted", "warning", "compliance_review_required"}
MISSING_INFO_RECOMMENDATION = "暂不做强推荐，建议补充更具体的问题、成分或商品信息。"
LOW_EVIDENCE_SAFETY_WARNING = "当前未命中高风险合规证据，但仍需保持保守解释。"
HIGH_RISK_SAFETY_WARNING = "检测到高风险或限制性合规证据。回答必须附带限制条件、风险提示和免责声明。"
HIGH_RISK_RISK_NOTE = "高风险场景：仅在合规和安全边界内解释，不做越界推荐。"


@dataclass
class AnswerResult:
    query: str
    intent: str
    answer_text: str
    recommendation: str
    scientific_basis: List[str]
    trend_basis: List[str]
    safety_warning: Optional[str]
    missing_info_note: Optional[str]
    cited_trace_ids: List[str]
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    batch_version: Optional[str] = None
    risk_note: Optional[str] = None


def classify_intent(query: str, filters: Optional[Dict[str, Any]] = None) -> str:
    normalized = str(query or "").lower()
    if filters and filters.get("need_trend"):
        return "trend"
    if any(token in normalized for token in ["禁", "合规", "安全", "risk", "warning", "规则"]):
        return "compliance"
    if any(token in normalized for token in ["趋势", "热点", "流行", "trend", "眼膜"]):
        return "trend"
    if any(token in normalized for token in ["评论", "体验", "好用", "护手霜", "feedback"]):
        return "review"
    if any(token in normalized for token in ["成分", "功效", "extract", "ingredient", "inci"]):
        return "science"
    return "product"


def answer_query(
    retrieval_bundle: RetrievalBundle,
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    mode: str = "auto",
) -> AnswerResult:
    intent = classify_intent(query, filters)
    retrieval_query = _normalize_query_for_retrieval(query, intent)
    retrieval_mode = mode
    if mode == "auto":
        retrieval_mode = "hybrid" if intent in {"trend", "review"} else "keyword"
    evidence_items = search_all(
        retrieval_bundle,
        query=retrieval_query,
        intent=intent,
        filters=filters,
        mode=retrieval_mode,
    )

    if not evidence_items:
        missing_info_note = retrieval_bundle.last_missing_info_note or "Insufficient evidence for a grounded answer."
        answer_text = (
            f"Recommendation: {MISSING_INFO_RECOMMENDATION}\n"
            "Scientific basis: 当前没有足够科学证据。\n"
            "Trend basis: 当前没有足够趋势证据。\n"
            "Safety warning: 请先补充更具体的问题或产品/成分信息。\n"
            f"Missing-info note: {missing_info_note}"
        )
        return AnswerResult(
            query=query,
            intent=intent,
            answer_text=answer_text,
            recommendation=MISSING_INFO_RECOMMENDATION,
            scientific_basis=[],
            trend_basis=[],
            safety_warning="证据不足，不应给出强推荐。",
            missing_info_note=missing_info_note,
            cited_trace_ids=[],
            evidence_items=[],
            batch_version=retrieval_bundle.batch_version,
            risk_note="信息不足场景已触发保守回答。",
        )

    scientific_basis = [item.title for item in evidence_items if item.evidence_type == "scientific"][:2]
    trend_basis = [item.title for item in evidence_items if item.evidence_type == "trend"][:2]
    product_basis = [item.title for item in evidence_items if item.evidence_type == "product_fact"][:2]
    feedback_basis = [
        item.title for item in evidence_items if item.evidence_type in {"user_feedback", "user_feedback_raw"}
    ][:2]
    compliance_items = [item for item in evidence_items if item.evidence_type == "compliance"]
    cited_trace_ids = [item.trace_id for item in evidence_items if item.trace_id]

    if scientific_basis:
        recommendation = f"优先考虑与 {', '.join(scientific_basis)} 相关的科学证据。"
    elif product_basis:
        recommendation = f"优先从商品事实角度参考 {', '.join(product_basis)}。"
    elif feedback_basis:
        recommendation = f"可以先参考用户体验信号：{', '.join(feedback_basis)}。"
    elif trend_basis:
        recommendation = f"当前趋势相关信号集中在 {', '.join(trend_basis)}。"
    else:
        recommendation = "已检索到部分证据，但仍建议保守解释。"

    safety_warning = None
    risk_note = None
    if compliance_items:
        risk_titles = [item.title for item in compliance_items[:2]]
        flags = {item.risk_flag for item in compliance_items if item.risk_flag}
        if flags & HIGH_RISK_FLAGS:
            safety_warning = HIGH_RISK_SAFETY_WARNING + f" 证据：{', '.join(risk_titles)}。"
            risk_note = HIGH_RISK_RISK_NOTE
        else:
            safety_warning = f"检索到合规相关证据：{', '.join(risk_titles)}。"
            risk_note = "存在合规约束，回答需保留风险提示。"

    answer_lines = [
        f"Recommendation: {recommendation}",
        "Scientific basis: " + ("; ".join(scientific_basis) if scientific_basis else "当前未命中直接科学证据。"),
        "Trend basis: " + ("; ".join(trend_basis) if trend_basis else "当前未命中直接趋势证据或趋势不是主要依据。"),
    ]
    if safety_warning:
        answer_lines.append(f"Safety warning: {safety_warning}")
    else:
        answer_lines.append(f"Safety warning: {LOW_EVIDENCE_SAFETY_WARNING}")
    if feedback_basis:
        answer_lines.append("Experience basis: " + "; ".join(feedback_basis))
    answer_lines.append("Cited trace ids: " + (", ".join(cited_trace_ids) if cited_trace_ids else "none"))

    return AnswerResult(
        query=query,
        intent=intent,
        answer_text="\n".join(answer_lines),
        recommendation=recommendation,
        scientific_basis=scientific_basis,
        trend_basis=trend_basis,
        safety_warning=safety_warning,
        missing_info_note=None,
        cited_trace_ids=cited_trace_ids,
        evidence_items=evidence_items,
        batch_version=retrieval_bundle.batch_version,
        risk_note=risk_note,
    )


def _normalize_query_for_retrieval(query: str, intent: str) -> str:
    normalized = str(query or "").strip()
    generic_phrases = [
        "是否合规",
        "是否安全",
        "有什么功效",
        "最近有什么趋势",
        "最近趋势",
        "有什么趋势",
        "推荐",
    ]
    for phrase in generic_phrases:
        normalized = normalized.replace(phrase, " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    candidates = re.findall(r"[A-Za-z0-9_]+(?: [A-Za-z0-9_]+)*|[\u4e00-\u9fff]{2,}", normalized)
    if not candidates:
        return query
    if intent in {"science", "compliance", "trend"}:
        return max(candidates, key=len)
    return normalized
