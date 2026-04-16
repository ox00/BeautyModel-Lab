from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from trend_evidence.pipeline import QAPipeline
from trend_evidence.trend_retrieval import TrendSignalRepository


SHARED_SAMPLE = Path(__file__).resolve().parents[2] / "data" / "pipeline_samples" / "trend_signal" / "trend_signal_first_party_sample.csv"


def _render_case(case_name: str, query: str, repo: TrendSignalRepository, now: datetime) -> dict[str, object]:
    pipeline = QAPipeline(repo)
    result = pipeline.run(query, now=now)
    first = result.trend_evidence[0] if result.trend_evidence else None
    return {
        "case": case_name,
        "query": query,
        "behavior_flag": result.behavior_flag,
        "metadata": result.metadata,
        "policy_output": result.policy_output,
        "trend_evidence_top": (
            {
                "signal_id": first.signal.signal_id,
                "normalized_keyword": first.signal.normalized_keyword,
                "risk_flag": first.signal.risk_flag,
                "confidence": first.signal.confidence,
                "trend_score": first.signal.trend_score,
                "fresh_until": first.signal.fresh_until.isoformat(),
                "is_stale": first.is_stale,
                "usable_as_strong_evidence": first.usable_as_strong_evidence,
                "blocked_by_safety": first.blocked_by_safety,
                "rejection_reason": first.rejection_reason,
                "signal_evidence": first.signal.signal_evidence,
                "source_platform": first.signal.source_platform,
                "source_url": first.signal.source_url,
            }
            if first
            else None
        ),
    }


def main() -> None:
    now_dt = datetime(2026, 4, 15, 12, 0, 0)

    repo = TrendSignalRepository.from_contract_csv(SHARED_SAMPLE, now=now_dt)
    migration_repo = TrendSignalRepository.from_legacy_csv_for_migration(
        "../data/deliveries/2026-03-14-baseline-v1/p0/trend_signal.csv",
        now=now_dt,
    )

    cases = [
        _render_case("trend_evidence_present", "最近外泌体很火，值得跟吗", repo, now_dt),
        _render_case("trend_evidence_low_confidence", "最近胶原蛋白很火，值得跟吗", repo, now_dt),
        _render_case("trend_evidence_high_risk", "最近猛药焕肤很火，值得跟吗", repo, now_dt),
        _render_case("trend_evidence_stale", "最近冰晶眼膜很火，值得跟吗", repo, now_dt),
    ]
    migration_case = _render_case("migration_legacy_stale", "最近冰晶眼膜很火，值得跟吗", migration_repo, now_dt)

    print(
        json.dumps(
            {
                "task_id": "QA-002",
                "backtest_date": "2026-04-15",
                "runtime_ingestion_path": "contract_only(signal_id schema)",
                "migration_ingestion_path": "legacy_loader_only(non-runtime)",
                "cases": cases,
                "migration_case": migration_case,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
