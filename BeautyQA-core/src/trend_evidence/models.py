from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

ConfidenceLevel = Literal["low", "medium", "high"]
RiskLevel = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class TrendSignal:
    signal_id: str
    keyword_id: str
    crawl_task_id: str
    normalized_keyword: str
    topic_cluster: str
    trend_type: str
    signal_summary: str
    signal_evidence: str
    source_platform: str
    source_url: str
    trend_score: float
    confidence: ConfidenceLevel
    risk_flag: RiskLevel
    observed_at: datetime
    fresh_until: datetime


@dataclass(frozen=True)
class TrendEvidence:
    signal: TrendSignal
    is_stale: bool
    usable_as_strong_evidence: bool
    blocked_by_safety: bool = False
    rejection_reason: str | None = None


@dataclass(frozen=True)
class QAResult:
    query: str
    selected_evidence: TrendEvidence | None = None
    trend_evidence: list[TrendEvidence] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    policy_output: str | None = None
    behavior_flag: Literal[
        "trend_supported",
        "trend_weak_or_missing",
        "trend_filtered_for_safety",
    ] = "trend_weak_or_missing"
