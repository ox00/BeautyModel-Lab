from __future__ import annotations

from datetime import datetime
from typing import Callable

from .models import QAResult
from .trend_retrieval import TrendSignalRepository


PolicyHook = Callable[[QAResult], str | None]


class QAPipeline:
    """Trend evidence assembly pipeline with optional downstream policy hook."""

    def __init__(self, trend_repo: TrendSignalRepository, *, policy_hook: PolicyHook | None = None) -> None:
        self._trend_repo = trend_repo
        self._policy_hook = policy_hook

    def run(self, query: str, *, now: datetime | None = None) -> QAResult:
        evidence = self._trend_repo.retrieve_for_query(query, now=now)
        selected = next((e for e in evidence if e.usable_as_strong_evidence), None)
        top = evidence[0] if evidence else None
        has_high_risk = any(e.blocked_by_safety for e in evidence)

        if selected is not None:
            behavior = "trend_supported"
        elif has_high_risk:
            behavior = "trend_filtered_for_safety"
        else:
            behavior = "trend_weak_or_missing"

        result = QAResult(
            query=query,
            selected_evidence=selected,
            trend_evidence=evidence,
            metadata={
                "top_signal_id": top.signal.signal_id if top else None,
                "top_normalized_keyword": top.signal.normalized_keyword if top else None,
                "top_source_platform": top.signal.source_platform if top else None,
                "top_source_url": top.signal.source_url if top else None,
                "top_fresh_until": top.signal.fresh_until.isoformat() if top else None,
                "top_confidence": top.signal.confidence if top else None,
                "top_risk_flag": top.signal.risk_flag if top else None,
                "top_rejection_reason": top.rejection_reason if top else None,
                "has_trend_evidence": bool(evidence),
                "has_strong_trend_evidence": selected is not None,
                "has_high_risk_signal": has_high_risk,
                "graceful_fallback": selected is None,
            },
            behavior_flag=behavior,
        )
        if self._policy_hook is None:
            return result
        return QAResult(
            query=result.query,
            selected_evidence=result.selected_evidence,
            trend_evidence=result.trend_evidence,
            metadata=result.metadata,
            policy_output=self._policy_hook(result),
            behavior_flag=result.behavior_flag,
        )
