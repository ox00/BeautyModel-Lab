from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from .models import QAResult, TrendContextBlock, TrendContextItem
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

    def build_trend_context_block(self, query: str, *, now: datetime | None = None, limit: int = 5) -> TrendContextBlock:
        result = self.run(query, now=now)
        items: list[TrendContextItem] = []
        for evidence in result.trend_evidence[:limit]:
            items.append(
                TrendContextItem(
                    signal_id=evidence.signal.signal_id,
                    normalized_keyword=evidence.signal.normalized_keyword,
                    topic_cluster=evidence.signal.topic_cluster,
                    trend_type=evidence.signal.trend_type,
                    signal_summary=evidence.signal.signal_summary,
                    signal_evidence=evidence.signal.signal_evidence,
                    source_platform=evidence.signal.source_platform,
                    source_url=evidence.signal.source_url,
                    confidence=evidence.signal.confidence,
                    risk_flag=evidence.signal.risk_flag,
                    trend_score=evidence.signal.trend_score,
                    fresh_until=evidence.signal.fresh_until.isoformat(),
                    rejection_reason=evidence.rejection_reason,
                )
            )

        if result.selected_evidence is not None:
            summary = (
                f"Selected {result.selected_evidence.signal.normalized_keyword} trend evidence "
                f"from {result.selected_evidence.signal.source_platform}."
            )
        elif result.behavior_flag == "trend_filtered_for_safety":
            summary = "Trend evidence was retrieved but filtered from the strong-evidence path."
        else:
            summary = "No strong trend evidence was selected; downstream QA should degrade gracefully."

        return TrendContextBlock(
            query=query,
            behavior_flag=result.behavior_flag,
            summary=summary,
            items=items,
            metadata=result.metadata,
        )


def default_runtime_handoff_csv() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "handoff" / "trend_signal" / "current" / "trend_signal_latest.csv"


def default_runtime_handoff_json() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "handoff" / "trend_signal" / "current" / "trend_signal_latest.json"
