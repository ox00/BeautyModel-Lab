from __future__ import annotations

from typing import Dict, List, Optional

from src.retrieval import RetrievalBundle, search_all

from .case_defs import RetrievalEvalCase, RetrievalEvalCaseResult, RetrievalEvalReport
from .datasets import get_default_retrieval_eval_cases


def evaluate_retrieval_bundle(
    retrieval_bundle: RetrievalBundle,
    cases: Optional[List[RetrievalEvalCase]] = None,
    limit: int = 5,
) -> RetrievalEvalReport:
    cases = cases or get_default_retrieval_eval_cases()
    results: List[RetrievalEvalCaseResult] = []
    grouped_hits: Dict[str, List[bool]] = {}

    for case in cases:
        items = search_all(
            retrieval_bundle,
            query=case.query,
            intent=case.intent,
            filters=case.filters,
            limit=limit,
        )
        returned_tables = [item.source_table for item in items]
        hit = any(table in returned_tables for table in case.expected_tables)
        risk_flag_hit = not case.requires_risk_flag or any(item.risk_flag for item in items)
        results.append(
            RetrievalEvalCaseResult(
                case=case,
                returned_tables=returned_tables,
                hit=hit,
                risk_flag_hit=risk_flag_hit,
                missing_info_note=retrieval_bundle.last_missing_info_note,
            )
        )
        grouped_hits.setdefault(case.intent, []).append(hit)

    metrics = {
        "overall_hit_rate": sum(result.hit for result in results) / len(results) if results else 0.0,
        "science_recall": _intent_rate(grouped_hits, "science"),
        "trend_recall": _intent_rate(grouped_hits, "trend"),
        "compliance_hit_rate": _intent_rate(grouped_hits, "compliance"),
        "risk_flag_hit_rate": (
            sum(result.risk_flag_hit for result in results if result.case.requires_risk_flag)
            / max(1, sum(result.case.requires_risk_flag for result in results))
        ),
    }
    metrics["balance_score"] = round(
        (metrics["science_recall"] + metrics["trend_recall"] + metrics["compliance_hit_rate"]) / 3,
        4,
    )
    release_checklist = {
        "science_recall_ready": metrics["science_recall"] >= 1.0,
        "trend_recall_ready": metrics["trend_recall"] >= 1.0,
        "compliance_hit_ready": metrics["compliance_hit_rate"] >= 1.0,
        "risk_flag_ready": metrics["risk_flag_hit_rate"] >= 1.0,
        "overall_ready": metrics["overall_hit_rate"] >= 0.75,
    }

    return RetrievalEvalReport(results=results, metrics=metrics, release_checklist=release_checklist)


def _intent_rate(grouped_hits: Dict[str, List[bool]], intent: str) -> float:
    values = grouped_hits.get(intent, [])
    if not values:
        return 0.0
    return sum(values) / len(values)
