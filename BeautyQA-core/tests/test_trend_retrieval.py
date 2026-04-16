from datetime import datetime
from pathlib import Path

import pytest

from trend_evidence.pipeline import QAPipeline
from trend_evidence.trend_retrieval import TrendSignalRepository


NOW = datetime(2026, 4, 15, 12, 0, 0)
SHARED_SAMPLE = Path(__file__).resolve().parents[2] / "data" / "pipeline_samples" / "trend_signal" / "trend_signal_first_party_sample.csv"


def _contract_repo() -> TrendSignalRepository:
    return TrendSignalRepository.from_contract_csv(SHARED_SAMPLE, now=NOW)


def test_runtime_contract_loader_rejects_legacy_schema() -> None:
    with pytest.raises(ValueError, match="Runtime ingestion requires first-party"):
        TrendSignalRepository.from_contract_csv(
            "../data/deliveries/2026-03-14-baseline-v1/p0/trend_signal.csv",
            now=NOW,
        )


def test_trend_evidence_present_and_fresh() -> None:
    pipeline = QAPipeline(_contract_repo())
    result = pipeline.run("最近外泌体很火，值得跟吗", now=NOW)

    assert result.behavior_flag == "trend_supported"
    assert result.trend_evidence
    assert result.trend_evidence[0].usable_as_strong_evidence is True
    assert result.selected_evidence is not None
    assert result.metadata["top_risk_flag"] == "medium"


def test_low_confidence_trend_falls_back() -> None:
    pipeline = QAPipeline(_contract_repo())
    result = pipeline.run("最近胶原蛋白很火，值得跟吗", now=NOW)

    assert result.behavior_flag == "trend_weak_or_missing"
    assert result.trend_evidence
    assert result.trend_evidence[0].rejection_reason == "low_confidence"
    assert result.selected_evidence is None
    assert result.metadata["graceful_fallback"] is True


def test_high_risk_trend_filtered_for_safety() -> None:
    pipeline = QAPipeline(_contract_repo())
    result = pipeline.run("最近猛药焕肤很火，值得跟吗", now=NOW)

    assert result.behavior_flag == "trend_filtered_for_safety"
    assert result.trend_evidence
    assert result.trend_evidence[0].blocked_by_safety is True
    assert "high_risk_blocked" in (result.trend_evidence[0].rejection_reason or "")
    assert result.metadata["top_risk_flag"] == "high"


def test_stale_trend_falls_back() -> None:
    pipeline = QAPipeline(_contract_repo())
    result = pipeline.run("最近冰晶眼膜很火，值得跟吗", now=NOW)

    assert result.behavior_flag == "trend_weak_or_missing"
    assert result.trend_evidence
    assert result.trend_evidence[0].is_stale is True
    assert result.metadata["top_rejection_reason"] == "stale"


def test_legacy_loader_is_migration_only() -> None:
    repo = TrendSignalRepository.from_legacy_csv_for_migration(
        "../data/deliveries/2026-03-14-baseline-v1/p0/trend_signal.csv",
        now=NOW,
    )
    pipeline = QAPipeline(repo)
    result = pipeline.run("最近冰晶眼膜很火，值得跟吗", now=NOW)

    assert result.behavior_flag == "trend_weak_or_missing"
    assert result.metadata["graceful_fallback"] is True


def test_policy_hook_is_pluggable_and_optional() -> None:
    pipeline = QAPipeline(
        _contract_repo(),
        policy_hook=lambda r: f"hook:{r.behavior_flag}:{r.metadata['top_risk_flag']}",
    )
    result = pipeline.run("最近猛药焕肤很火，值得跟吗", now=NOW)

    assert result.policy_output == "hook:trend_filtered_for_safety:high"
