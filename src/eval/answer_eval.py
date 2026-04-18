from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.pipeline import AnswerResult, answer_query
from src.retrieval import RetrievalBundle

from .case_defs import AnswerEvalCase, AnswerEvalCaseResult, AnswerEvalReport
from .datasets import get_default_answer_eval_cases


def evaluate_answer_bundle(
    retrieval_bundle: RetrievalBundle,
    cases: Optional[List[AnswerEvalCase]] = None,
    mode: str = "auto",
) -> AnswerEvalReport:
    cases = cases or get_default_answer_eval_cases()
    results: List[AnswerEvalCaseResult] = []

    for case in cases:
        answer = answer_query(retrieval_bundle, case.query, filters=case.filters, mode=mode)
        scientificity_pass = (not case.requires_scientific_basis) or bool(answer.scientific_basis)
        trend_relevance_pass = (not case.requires_trend_basis) or bool(answer.trend_basis)
        safety_pass = (not case.requires_safety_warning) or bool(answer.safety_warning or answer.risk_note)
        missing_info_behavior_pass = (not case.expects_missing_info) or bool(answer.missing_info_note)
        trace_coverage_pass = (not case.requires_trace_coverage) or bool(answer.cited_trace_ids)
        balance_pass = _evaluate_balance(case, answer)

        results.append(
            AnswerEvalCaseResult(
                case=case,
                answer=answer,
                scientificity_pass=scientificity_pass,
                trend_relevance_pass=trend_relevance_pass,
                safety_pass=safety_pass,
                balance_pass=balance_pass,
                missing_info_behavior_pass=missing_info_behavior_pass,
                trace_coverage_pass=trace_coverage_pass,
            )
        )

    metrics = {
        "scientificity": _avg([r.scientificity_pass for r in results]),
        "trend_relevance": _avg([r.trend_relevance_pass for r in results]),
        "safety": _avg([r.safety_pass for r in results]),
        "balance": _avg([r.balance_pass for r in results]),
        "missing_info_behavior": _avg([r.missing_info_behavior_pass for r in results]),
        "trace_coverage": _avg([r.trace_coverage_pass for r in results]),
    }
    release_checklist = {
        "scientificity_ready": metrics["scientificity"] >= 0.8,
        "trend_ready": metrics["trend_relevance"] >= 0.8,
        "safety_ready": metrics["safety"] >= 1.0,
        "balance_ready": metrics["balance"] >= 0.8,
        "missing_info_ready": metrics["missing_info_behavior"] >= 1.0,
        "trace_ready": metrics["trace_coverage"] >= 0.8,
    }

    return AnswerEvalReport(results=results, metrics=metrics, release_checklist=release_checklist)


def _evaluate_balance(case: AnswerEvalCase, answer: AnswerResult) -> bool:
    if case.expects_missing_info:
        return bool(answer.missing_info_note)
    if case.requires_safety_warning:
        return bool(answer.safety_warning or answer.risk_note)
    if case.requires_scientific_basis and case.requires_trend_basis:
        return bool(answer.scientific_basis) and bool(answer.trend_basis)
    if case.requires_scientific_basis:
        return bool(answer.scientific_basis)
    if case.requires_trend_basis:
        return bool(answer.trend_basis)
    return bool(answer.cited_trace_ids)


def _avg(values: List[bool]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
