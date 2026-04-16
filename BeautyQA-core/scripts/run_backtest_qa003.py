from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from trend_evidence.pipeline import QAPipeline
from trend_evidence.trend_retrieval import TrendSignalRepository


SHARED_SAMPLE = Path(__file__).resolve().parents[2] / "data" / "pipeline_samples" / "trend_signal" / "trend_signal_first_party_sample.csv"


def _render_case(case_name: str, query: str, repo: TrendSignalRepository, now: datetime) -> dict[str, object]:
    pipeline = QAPipeline(
        repo,
        policy_hook=lambda r: f"downstream_hook_input:{r.behavior_flag}:{r.metadata['top_risk_flag']}",
    )
    result = pipeline.run(query, now=now)
    top = result.trend_evidence[0] if result.trend_evidence else None
    selected = result.selected_evidence
    return {
        "case": case_name,
        "query": query,
        "behavior_flag": result.behavior_flag,
        "policy_output": result.policy_output,
        "metadata": result.metadata,
        "selected_evidence": (
            {
                "signal_id": selected.signal.signal_id,
                "normalized_keyword": selected.signal.normalized_keyword,
                "risk_flag": selected.signal.risk_flag,
                "confidence": selected.signal.confidence,
                "fresh_until": selected.signal.fresh_until.isoformat(),
                "source_platform": selected.signal.source_platform,
                "source_url": selected.signal.source_url,
            }
            if selected
            else None
        ),
        "trend_evidence_top": (
            {
                "signal_id": top.signal.signal_id,
                "normalized_keyword": top.signal.normalized_keyword,
                "risk_flag": top.signal.risk_flag,
                "confidence": top.signal.confidence,
                "fresh_until": top.signal.fresh_until.isoformat(),
                "rejection_reason": top.rejection_reason,
            }
            if top
            else None
        ),
    }


def main() -> None:
    now_dt = datetime(2026, 4, 15, 12, 0, 0)
    runtime_repo = TrendSignalRepository.from_contract_csv(SHARED_SAMPLE, now=now_dt)

    cases = [
        _render_case("retrieved_and_passed_through", "最近外泌体很火，值得跟吗", runtime_repo, now_dt),
        _render_case("stale_graceful_fallback", "最近冰晶眼膜很火，值得跟吗", runtime_repo, now_dt),
        _render_case("high_risk_metadata_exposed", "最近猛药焕肤很火，值得跟吗", runtime_repo, now_dt),
    ]

    print(
        json.dumps(
            {
                "task_id": "QA-003",
                "backtest_date": "2026-04-15",
                "module_boundary": "trend_signal ingestion + retrieval/evidence assembly",
                "runtime_ingestion_path": "contract_only(signal_id schema)",
                "notes": [
                    "final safety/compliance answer policy is not hard-coded in this module",
                    "risk/freshness/confidence are exposed as metadata+flags for downstream QA/RAG",
                    "graceful fallback is represented via behavior_flag and metadata",
                ],
                "cases": cases,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
