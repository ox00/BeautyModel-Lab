from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pydantic import BaseModel, Field

from src.loaders.csv_loader import BatchBundle


class EvidenceItem(BaseModel):
    source_table: str
    source_id: str
    title: str
    snippet: str
    score: float = 0.0
    timestamp: Optional[str] = None
    evidence_type: str
    risk_flag: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None


@dataclass
class IndexedEvidence:
    evidence: EvidenceItem
    raw_record: Dict[str, Any]
    searchable_text: str
    source_priority: float = 0.0
    timestamp_dt: Optional[datetime] = None


@dataclass
class RetrievalBundle:
    indexes: Dict[str, List[IndexedEvidence]]
    batch_version: Optional[str] = None
    batch_timestamp: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    last_missing_info_note: Optional[str] = None


SEMANTIC_EXPANSIONS = {
    "护手霜": ["护手", "滋润", "手部", "干燥", "不油腻"],
    "手霜": ["护手", "滋润", "手部", "干燥"],
    "眼膜": ["眼部", "眼周", "贴片", "冰晶眼膜"],
    "眼部冰凉贴片": ["冰晶眼膜", "眼膜", "眼部", "贴片", "冰凉"],
    "眼部": ["眼膜", "眼周", "贴片", "冰晶眼膜"],
    "冰凉": ["冰晶眼膜", "眼膜", "眼部", "贴片"],
    "贴片": ["冰晶眼膜", "眼膜", "眼部", "眼周"],
    "趋势": ["热点", "流行", "热度", "trend"],
    "热度": ["热点", "流行", "趋势", "trend"],
    "功效": ["效果", "efficacy", "mechanism"],
    "安全": ["合规", "限制", "禁用", "warning"],
}


def _safe_join(parts: Iterable[Optional[str]]) -> str:
    return " | ".join(str(part).strip() for part in parts if part and str(part).strip())


def _safe_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _tokenize(value: str) -> List[str]:
    if not value:
        return []
    normalized = _normalize_text(value)
    raw_tokens = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_]+", normalized)
    return list(dict.fromkeys(raw_tokens))


def _character_ngrams(value: str, n: int = 2) -> List[str]:
    normalized = _normalize_text(value)
    if len(normalized) < n:
        return [normalized] if normalized else []
    return [normalized[i : i + n] for i in range(len(normalized) - n + 1)]


def _expand_semantic_terms(query_text: str) -> List[str]:
    expanded = [query_text]
    for term, related_terms in SEMANTIC_EXPANSIONS.items():
        if term in query_text:
            expanded.extend(related_terms)
    return list(dict.fromkeys([term for term in expanded if term]))


def _keyword_score(query: str, indexed: IndexedEvidence) -> float:
    query_text = _normalize_text(query)
    if not query_text:
        return 0.0

    search_text = indexed.searchable_text
    stopwords = {"the", "a", "an", "is", "are", "of", "to", "for", "and", "or", "not", "this", "that", "should", "exist"}
    tokens = [token for token in _tokenize(query_text) if token not in stopwords]
    score = 0.0
    matched_terms = 0
    phrase_hit = False

    if query_text in search_text:
        score += 8.0
        matched_terms += 2
        phrase_hit = True
    for token in tokens:
        if token and token in search_text:
            score += 1.0
            matched_terms += 1

    title_text = _normalize_text(indexed.evidence.title)
    if query_text in title_text:
        score += 3.0
        phrase_hit = True
    for token in tokens:
        if token and token in title_text:
            score += 1.5

    ascii_query = bool(re.fullmatch(r"[a-z0-9_ ]+", query_text))
    if phrase_hit:
        return score + indexed.source_priority
    if ascii_query and matched_terms < 2:
        return 0.0
    if not ascii_query and len(query_text) > 4 and matched_terms < 2:
        return 0.0
    if not ascii_query and matched_terms < 1:
        return 0.0
    return score + indexed.source_priority


def _semantic_score(query: str, indexed: IndexedEvidence) -> float:
    query_text = _normalize_text(query)
    if not query_text:
        return 0.0

    expanded_terms = _expand_semantic_terms(query_text)
    query_tokens = set()
    for term in expanded_terms:
        query_tokens.update(_tokenize(term))
        query_tokens.update(_character_ngrams(term))

    search_tokens = set(_tokenize(indexed.searchable_text))
    search_tokens.update(_character_ngrams(indexed.searchable_text))
    if not query_tokens or not search_tokens:
        return 0.0

    overlap = query_tokens & search_tokens
    if not overlap:
        return 0.0

    jaccard = len(overlap) / max(len(query_tokens | search_tokens), 1)
    coverage = len(overlap) / max(len(query_tokens), 1)
    if len(overlap) < 2 and coverage < 0.35:
        return 0.0
    if coverage < 0.2:
        return 0.0
    return round((jaccard * 12.0) + (coverage * 8.0) + (indexed.source_priority * 0.2), 4)


def _apply_filters(indexed_items: List[IndexedEvidence], filters: Optional[Dict[str, Any]]) -> List[IndexedEvidence]:
    if not filters:
        return indexed_items

    category = filters.get("category")
    product_id = filters.get("product_id")

    filtered = indexed_items
    if category:
        category = _normalize_text(category)
        filtered = [
            item for item in filtered
            if category in _normalize_text(item.raw_record.get("category_lv1"))
            or category in _normalize_text(item.raw_record.get("category_lv2"))
        ]
    if product_id:
        filtered = [item for item in filtered if str(item.raw_record.get("product_id")) == str(product_id)]
    return filtered


def _resolve_tables_for_intent(intent: str, filters: Optional[Dict[str, Any]]) -> List[str]:
    intent_normalized = _normalize_text(intent)
    need_trend = bool(filters and filters.get("need_trend"))

    if intent_normalized in {"science", "ingredient"}:
        tables = ["ingredient_knowledge", "compliance_rule"]
    elif intent_normalized in {"product", "sku"}:
        tables = ["product_sku", "review_feedback_raw", "review_feedback", "compliance_rule"]
    elif intent_normalized in {"trend", "hot", "freshness"}:
        tables = ["trend_signal", "product_sku", "compliance_rule"]
    elif intent_normalized in {"review", "feedback", "experience"}:
        tables = ["review_feedback_raw", "review_feedback", "product_sku", "compliance_rule"]
    elif intent_normalized in {"compliance", "safety", "rule"}:
        tables = ["compliance_rule"]
    else:
        tables = [
            "ingredient_knowledge",
            "product_sku",
            "review_feedback_raw",
            "review_feedback",
            "trend_signal",
            "compliance_rule",
        ]

    if need_trend and "trend_signal" not in tables:
        tables.append("trend_signal")
    return tables


def _risk_flag_for_rule(record: Dict[str, Any]) -> str:
    rule_type = _normalize_text(record.get("rule_type"))
    warning_text = _normalize_text(record.get("warning_text"))
    requirement_text = _normalize_text(record.get("requirement_text"))

    if any(flag in rule_type for flag in ["ban", "prohibit", "forbidden", "禁", "not_allowed"]):
        return "high_risk"
    if any(flag in rule_type for flag in ["limit", "restricted", "限", "warning"]):
        return "restricted"
    if warning_text:
        return "warning"
    if requirement_text:
        return "requirement"
    return "compliance_rule"


def _record_to_evidence(table_name: str, record: Dict[str, Any]) -> EvidenceItem:
    if table_name == "ingredient_knowledge":
        title = record.get("name_cn") or record.get("inci_name") or record["ingredient_id"]
        snippet = _safe_join(
            [
                record.get("efficacy_2023"),
                record.get("literature_evidence"),
                record.get("mechanism_legacy"),
                record.get("reference_1"),
                record.get("reference_2"),
            ]
        )
        return EvidenceItem(
            source_table=table_name,
            source_id=str(record["ingredient_id"]),
            title=title,
            snippet=snippet or title,
            timestamp=None,
            evidence_type="scientific",
            metadata={
                "inci_name": record.get("inci_name"),
                "cas_no": record.get("cas_no"),
                "use_purpose": record.get("use_purpose_2023"),
                "search_terms": "ingredient inci efficacy mechanism scientific evidence 成分 功效 作用 机制",
            },
            trace_id=f"{table_name}:{record['ingredient_id']}",
        )

    if table_name == "product_sku":
        title = _safe_join([record.get("brand"), record.get("product_id")]) or str(record["product_id"])
        snippet = _safe_join(
            [
                record.get("category_lv1"),
                record.get("category_lv2"),
                record.get("price_band"),
                record.get("core_claims"),
            ]
        )
        return EvidenceItem(
            source_table=table_name,
            source_id=str(record["product_id"]),
            title=title,
            snippet=snippet or title,
            timestamp=record.get("launch_date"),
            evidence_type="product_fact",
            metadata={
                "brand": record.get("brand"),
                "category_lv1": record.get("category_lv1"),
                "category_lv2": record.get("category_lv2"),
                "price_min": record.get("price_min"),
                "price_max": record.get("price_max"),
            },
            trace_id=f"{table_name}:{record['product_id']}",
        )

    if table_name == "review_feedback":
        title = _safe_join([record.get("product_id"), record.get("sentiment_tag")]) or str(record["review_id"])
        snippet = _safe_join(
            [
                record.get("sentiment_tag"),
                record.get("effect_tags"),
                record.get("issue_tags"),
            ]
        )
        return EvidenceItem(
            source_table=table_name,
            source_id=str(record["review_id"]),
            title=title,
            snippet=snippet or title,
            timestamp=record.get("created_at"),
            evidence_type="user_feedback",
            metadata={
                "product_id": record.get("product_id"),
                "source": record.get("source"),
                "rating_bucket": record.get("rating_bucket"),
            },
            trace_id=f"{table_name}:{record['review_id']}",
        )

    if table_name == "review_feedback_raw":
        title = _safe_join([record.get("product_id"), record.get("sentiment_tag"), "raw"]) or str(record["review_id"])
        snippet = _safe_join(
            [
                record.get("content"),
                record.get("effect_tags"),
                record.get("issue_tags"),
            ]
        )
        return EvidenceItem(
            source_table=table_name,
            source_id=str(record["review_id"]),
            title=title,
            snippet=snippet or title,
            timestamp=record.get("created_at"),
            evidence_type="user_feedback_raw",
            metadata={
                "product_id": record.get("product_id"),
                "source": record.get("source"),
                "rating_bucket": record.get("rating_bucket"),
                "sentiment_tag": record.get("sentiment_tag"),
            },
            trace_id=f"{table_name}:{record['review_id']}",
        )

    if table_name == "trend_signal":
        title = record.get("keyword") or str(record["trend_id"])
        snippet = _safe_join(
            [
                record.get("topic_cluster"),
                f"heat={record.get('heat_index')}" if record.get("heat_index") else None,
                f"growth_monthly={record.get('growth_monthly')}" if record.get("growth_monthly") else None,
            ]
        )
        return EvidenceItem(
            source_table=table_name,
            source_id=str(record["trend_id"]),
            title=title,
            snippet=snippet or title,
            timestamp=record.get("captured_at"),
            evidence_type="trend",
            metadata={
                "platform": record.get("platform"),
                "topic_cluster": record.get("topic_cluster"),
                "heat_index": record.get("heat_index"),
                "growth_monthly": record.get("growth_monthly"),
                "search_terms": "trend hotness heat popularity freshness 热度 趋势 热点 流行 最近",
            },
            trace_id=f"{table_name}:{record['trend_id']}",
        )

    title = record.get("entity_name_cn") or record.get("source_title") or str(record["rule_id"])
    snippet = _safe_join(
        [
            record.get("requirement_text"),
            record.get("warning_text"),
            record.get("limit_value"),
            record.get("applicable_scope"),
        ]
    )
    return EvidenceItem(
        source_table=table_name,
        source_id=str(record["rule_id"]),
        title=title,
        snippet=snippet or title,
        timestamp=record.get("effective_date"),
        evidence_type="compliance",
        risk_flag=_risk_flag_for_rule(record),
        metadata={
            "jurisdiction": record.get("jurisdiction"),
            "rule_type": record.get("rule_type"),
            "source_title": record.get("source_title"),
            "entity_name_en": record.get("entity_name_en"),
        },
        trace_id=f"{table_name}:{record['rule_id']}",
    )


def _source_priority(table_name: str, record: Dict[str, Any]) -> float:
    if table_name == "compliance_rule":
        risk_flag = _risk_flag_for_rule(record)
        return 24.0 if risk_flag in {"high_risk", "restricted"} else 18.0
    if table_name == "ingredient_knowledge":
        return 10.0
    if table_name == "product_sku":
        return 8.0
    if table_name == "review_feedback":
        return 6.0
    if table_name == "review_feedback_raw":
        return 7.0
    if table_name == "trend_signal":
        heat = float(record.get("heat_index") or 0.0)
        growth = float(record.get("growth_monthly") or 0.0)
        return 10.0 + min(heat / 100.0, 4.0) + min(growth / 1000.0, 4.0)
    return 0.0


def build_indexes(batch_bundle: BatchBundle) -> RetrievalBundle:
    indexes: Dict[str, List[IndexedEvidence]] = {}
    warnings = list(batch_bundle.warnings)

    for table_name, df in batch_bundle.data.items():
        items: List[IndexedEvidence] = []
        seen_trend_keys = set()
        for record in df.to_dict(orient="records"):
            if table_name == "trend_signal":
                dedupe_key = (
                    record.get("keyword"),
                    record.get("platform"),
                    record.get("captured_at"),
                )
                if dedupe_key in seen_trend_keys:
                    continue
                seen_trend_keys.add(dedupe_key)

            evidence = _record_to_evidence(table_name, record)
            searchable_text = _normalize_text(
                " ".join(
                    [
                        evidence.title,
                        evidence.snippet,
                        *[str(value) for value in evidence.metadata.values() if value],
                    ]
                )
            )
            items.append(
                IndexedEvidence(
                    evidence=evidence,
                    raw_record=record,
                    searchable_text=searchable_text,
                    source_priority=_source_priority(table_name, record),
                    timestamp_dt=_safe_datetime(evidence.timestamp),
                )
            )

        indexes[table_name] = items

    return RetrievalBundle(
        indexes=indexes,
        batch_version=batch_bundle.batch_version,
        batch_timestamp=batch_bundle.batch_timestamp,
        warnings=warnings,
    )


def search_all(
    retrieval_bundle: RetrievalBundle,
    query: str,
    intent: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    mode: str = "auto",
) -> List[EvidenceItem]:
    candidate_tables = _resolve_tables_for_intent(intent, filters)
    table_rank = {table_name: index for index, table_name in enumerate(candidate_tables)}
    scored_items: List[EvidenceItem] = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    normalized_query = _normalize_text(query)
    ascii_only_query = bool(re.fullmatch(r"[a-z0-9_ ]+", normalized_query))

    for table_name in candidate_tables:
        indexed_items = _apply_filters(retrieval_bundle.indexes.get(table_name, []), filters)
        for indexed in indexed_items:
            keyword_score = _keyword_score(query, indexed)
            semantic_score = _semantic_score(query, indexed)
            if mode == "keyword":
                score = keyword_score
            elif mode == "semantic":
                score = semantic_score
            elif mode == "hybrid":
                score = max(keyword_score, semantic_score) + min(keyword_score, semantic_score) * 0.35
            else:
                if ascii_only_query:
                    score = keyword_score
                else:
                    score = max(keyword_score, semantic_score) + min(keyword_score, semantic_score) * 0.25
            if score <= 0:
                continue

            if indexed.evidence.source_table == "trend_signal":
                if indexed.timestamp_dt is not None:
                    age_days = max((now - indexed.timestamp_dt).days, 0)
                    freshness_boost = max(0.0, 30.0 - min(age_days, 30)) / 10.0
                    score += freshness_boost
                heat_index = float(indexed.raw_record.get("heat_index") or 0.0)
                growth_monthly = float(indexed.raw_record.get("growth_monthly") or 0.0)
                score += min(heat_index / 100.0, 3.0)
                score += min(growth_monthly / 1000.0, 3.0)

            item = indexed.evidence.model_copy(deep=True)
            item.score = round(score, 4)
            if item.source_table == "compliance_rule" and not item.risk_flag:
                item.risk_flag = "compliance_review_required"
            scored_items.append(item)

    scored_items.sort(
        key=lambda item: (
            0 if item.source_table == "compliance_rule" and item.score >= 20 else 1,
            table_rank.get(item.source_table, 99),
            -item.score,
            item.timestamp or "",
        )
    )

    per_table_best: Dict[str, List[EvidenceItem]] = {}
    for item in scored_items:
        per_table_best.setdefault(item.source_table, []).append(item)

    deduped: List[EvidenceItem] = []
    seen = set()
    for table_name in candidate_tables:
        table_items = per_table_best.get(table_name, [])
        if not table_items:
            continue
        item = table_items[0]
        key = (item.source_table, item.source_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break

    for item in scored_items:
        key = (item.source_table, item.source_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break

    retrieval_bundle.last_missing_info_note = None
    if not deduped:
        retrieval_bundle.last_missing_info_note = (
            f"No evidence found for intent='{intent}' and query='{query}'."
        )

    return deduped
