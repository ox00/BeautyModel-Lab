from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from app.config.settings import settings


def _read_field(row: Any, field: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(field, default)
    return getattr(row, field, default)


def _normalize_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value.strip():
        dt = datetime.fromisoformat(value.strip())
    else:
        dt = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _normalize_platform(platform: str) -> str:
    mapping = {
        "xhs": "xiaohongshu",
        "dy": "douyin",
        "bili": "bilibili",
        "wb": "weibo",
        "ks": "kuaishou",
    }
    return mapping.get(platform, platform)


def _extract_source_url(raw_data: dict | None, source_id: str, platform: str) -> str:
    if isinstance(raw_data, dict):
        for key in ("source_url", "url", "note_url", "share_url", "jump_url"):
            value = raw_data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return f"about:source/{platform}/{source_id}"


def _risk_from_topics(topics: str | None) -> str:
    if not topics:
        return "low"

    risk_tokens_high = ("治疗", "医美", "激素", "处方", "注射")
    risk_tokens_medium = ("祛斑", "敏感", "功效", "抗衰", "孕妇")
    lowered = topics.lower()
    if any(token in lowered for token in risk_tokens_high):
        return "high"
    if any(token in lowered for token in risk_tokens_medium):
        return "medium"
    return "low"


def _group_key(row: Any, keyword_meta: dict[str, Any]) -> tuple[str, str, str, str]:
    normalized_keyword = (
        keyword_meta.get("normalized_keyword")
        or _read_field(row, "normalized_keyword")
        or _read_field(row, "keyword", "")
    )
    topic_cluster = keyword_meta.get("topic_cluster") or _read_field(row, "topic_cluster") or "unknown"
    trend_type = keyword_meta.get("trend_type") or _read_field(row, "trend_type") or "ingredient"
    source_platform = _normalize_platform(str(_read_field(row, "source_platform", "")))
    return normalized_keyword, topic_cluster, trend_type, source_platform


def _sort_rows(rows: list[Any]) -> list[Any]:
    def sort_key(row: Any) -> tuple[float, str, int]:
        score = float(_read_field(row, "trend_score", 0.0) or 0.0)
        created_at = _normalize_datetime(_read_field(row, "created_at"))
        row_id = int(_read_field(row, "id", 0) or 0)
        return (score, created_at.isoformat(), row_id)

    return sorted(rows, key=sort_key, reverse=True)


def _build_signal_id(group_rows: list[Any], observed_at: datetime) -> str:
    first = group_rows[0]
    task_id = _read_field(first, "crawl_task_id", "0")
    row_id = _read_field(first, "id", "0")
    return f"TS_{observed_at.strftime('%Y%m%d')}_{task_id}_{row_id}"


def _derive_trend_score(group_rows: list[Any]) -> float:
    scores = [float(_read_field(row, "trend_score", 0.0) or 0.0) for row in group_rows]
    if not scores:
        return 0.0

    max_score = max(scores)
    scale_divisor = 4.0 if max_score > 100 else 1.0
    normalized = (max_score / scale_divisor) + min(max(len(scores) - 1, 0), 5) * 5
    return round(min(100.0, normalized), 1)


def _derive_confidence(group_rows: list[Any], normalized_score: float, keyword_meta: dict[str, Any]) -> str:
    meta_confidence = keyword_meta.get("confidence") or _read_field(group_rows[0], "confidence")
    if meta_confidence in {"low", "medium", "high"}:
        return meta_confidence

    derived = "low"
    support_count = len(group_rows)

    if support_count >= 3 and normalized_score >= 70:
        derived = "high"
    elif support_count >= 2 and normalized_score >= 45:
        derived = "medium"
    elif normalized_score >= 65:
        derived = "medium"

    return derived


def _derive_risk(group_rows: list[Any], keyword_meta: dict[str, Any]) -> str:
    meta_risk = keyword_meta.get("risk_flag") or _read_field(group_rows[0], "risk_flag")
    if meta_risk == "high":
        return "high"

    row_risks = [_risk_from_topics(_read_field(row, "topics")) for row in group_rows]
    if "high" in row_risks:
        return "high"
    if meta_risk == "medium" or "medium" in row_risks:
        return "medium"
    return meta_risk if meta_risk in {"low", "medium", "high"} else "low"


def _representative_source_url(row: Any, platform: str) -> str:
    return _extract_source_url(_read_field(row, "raw_data"), str(_read_field(row, "source_id", "")), platform)


def generate_trend_signals(
    *,
    cleaned_rows: Iterable[Any],
    keyword_meta: dict[str, Any],
    freshness_days: int = 7,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[Any]] = defaultdict(list)
    input_rows = list(cleaned_rows)
    for row in input_rows:
        grouped[_group_key(row, keyword_meta)].append(row)

    trend_signals: list[dict[str, Any]] = []
    support_counts: list[int] = []

    for key in sorted(grouped.keys()):
        normalized_keyword, topic_cluster, trend_type, source_platform = key
        sorted_rows = _sort_rows(grouped[key])
        support_count = len(sorted_rows)
        support_counts.append(support_count)
        representative = sorted_rows[0]
        report_id = keyword_meta.get("report_id") or _read_field(representative, "report_id")
        signal_period_type = keyword_meta.get("signal_period_type") or _read_field(representative, "signal_period_type")
        signal_period_label = keyword_meta.get("signal_period_label") or _read_field(representative, "signal_period_label")
        source_scope = keyword_meta.get("source_scope") or _read_field(representative, "source_scope")
        observed_at = max(_normalize_datetime(_read_field(row, "created_at")) for row in sorted_rows)
        fresh_until = observed_at + timedelta(days=freshness_days)

        evidence_rows = sorted_rows[:3]
        evidence_bits = []
        for row in evidence_rows:
            snippet = " | ".join(
                [
                    bit.strip()
                    for bit in (
                        _read_field(row, "title", "") or "",
                        _read_field(row, "summary", "") or "",
                        _read_field(row, "topics", "") or "",
                    )
                    if bit and str(bit).strip()
                ]
            )
            if snippet:
                evidence_bits.append(snippet)

        normalized_score = _derive_trend_score(sorted_rows)
        confidence = _derive_confidence(sorted_rows, normalized_score, keyword_meta)
        risk_flag = _derive_risk(sorted_rows, keyword_meta)

        signal_summary = (
            f"{normalized_keyword} 在 {source_platform} 聚合出 {support_count} 条相关信号，"
            f"代表性主题为{topic_cluster}。"
        )
        signal_evidence = " || ".join(evidence_bits)[:800]

        trend_signals.append(
            {
                "signal_id": _build_signal_id(sorted_rows, observed_at),
                "keyword_id": keyword_meta.get("keyword_id") or f"KW_TASK_{_read_field(representative, 'crawl_task_id', 0)}",
                "crawl_task_id": _read_field(representative, "crawl_task_id", 0),
                "normalized_keyword": normalized_keyword,
                "topic_cluster": topic_cluster,
                "trend_type": trend_type,
                "signal_summary": signal_summary,
                "signal_evidence": signal_evidence,
                "source_platform": source_platform,
                "source_url": _representative_source_url(representative, source_platform),
                "trend_score": normalized_score,
                "confidence": confidence,
                "risk_flag": risk_flag,
                "observed_at": observed_at.isoformat(),
                "fresh_until": fresh_until.isoformat(),
                "report_id": report_id,
                "signal_period_type": signal_period_type,
                "signal_period_label": signal_period_label,
                "source_scope": source_scope,
                "support_count": support_count,
                "evidence_ids": [f"CTD_{_read_field(row, 'id', 0)}" for row in sorted_rows],
                "aggregation_method": "grouped_signal_v1",
                "version": "v0.2",
            }
        )

    run_summary = {
        "input_cleaned_count": len(input_rows),
        "generated_signal_count": len(trend_signals),
        "max_support_count": max(support_counts) if support_counts else 0,
        "grouping_rule": "normalized_keyword + topic_cluster + trend_type + source_platform",
        "score_rule": "max_trend_score normalized with support-count bonus",
        "deterministic": True,
    }

    return trend_signals, run_summary


def save_trend_signals_json(
    *,
    task_id: int,
    platform: str,
    keyword: str,
    trend_signals: list[dict[str, Any]],
    run_summary: dict[str, Any] | None = None,
) -> Path:
    """Persist first-party trend_signal output to local JSON file."""
    base_dir = Path(settings.DATA_DIR) / "trend_signal" / platform
    base_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = keyword.replace(" ", "_").replace("/", "_")
    filename = f"{safe_keyword}_task{task_id}_{ts}.json"
    filepath = base_dir / filename

    payload = {
        "task_id": task_id,
        "keyword": keyword,
        "normalized_keyword": trend_signals[0]["normalized_keyword"] if trend_signals else keyword,
        "platform": platform,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(trend_signals),
        "run_summary": run_summary or {},
        "trend_signals": trend_signals,
    }

    filepath.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return filepath
