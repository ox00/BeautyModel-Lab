#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRENDAGENT_BACKEND = REPO_ROOT / "BeautyQA-TrendAgent" / "backend"
QACORE_SRC = REPO_ROOT / "BeautyQA-core" / "src"
PIPELINE_SAMPLE_DIR = REPO_ROOT / "data" / "pipeline_samples" / "trend_signal"

sys.path.insert(0, str(TRENDAGENT_BACKEND))
sys.path.insert(0, str(QACORE_SRC))

from app.domain.services.signal_service import generate_trend_signals  # noqa: E402
from trend_evidence.pipeline import QAPipeline  # noqa: E402
from trend_evidence.trend_retrieval import TrendSignalRepository  # noqa: E402


SAMPLE_INPUT = PIPELINE_SAMPLE_DIR / "sample_cleaned_records.json"
CSV_OUTPUT = PIPELINE_SAMPLE_DIR / "trend_signal_first_party_sample.csv"
JSON_OUTPUT = PIPELINE_SAMPLE_DIR / "trend_signal_first_party_sample.json"
REPORT_OUTPUT = PIPELINE_SAMPLE_DIR / "int001_smoke_report.json"


def _write_contract_csv(signals: list[dict]) -> None:
    fieldnames = [
        "signal_id",
        "keyword_id",
        "crawl_task_id",
        "normalized_keyword",
        "topic_cluster",
        "trend_type",
        "signal_summary",
        "signal_evidence",
        "source_platform",
        "source_url",
        "trend_score",
        "confidence",
        "risk_flag",
        "observed_at",
        "fresh_until",
    ]
    with CSV_OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for signal in signals:
            writer.writerow({field: signal.get(field, "") for field in fieldnames})


def _render_case(pipeline: QAPipeline, case_name: str, query: str, now: datetime) -> dict[str, object]:
    result = pipeline.run(query, now=now)
    top = result.trend_evidence[0] if result.trend_evidence else None
    selected = result.selected_evidence
    return {
        "case": case_name,
        "query": query,
        "behavior_flag": result.behavior_flag,
        "selected_evidence": (
            {
                "signal_id": selected.signal.signal_id,
                "normalized_keyword": selected.signal.normalized_keyword,
                "source_platform": selected.signal.source_platform,
                "support_count": selected.signal.signal_evidence.count("||") + 1 if selected.signal.signal_evidence else 0,
            }
            if selected
            else None
        ),
        "top_metadata": result.metadata,
        "top_rejection_reason": top.rejection_reason if top else None,
    }


def main() -> None:
    PIPELINE_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    sample_rows = json.loads(SAMPLE_INPUT.read_text(encoding="utf-8"))
    signals, run_summary = generate_trend_signals(cleaned_rows=sample_rows, keyword_meta={})

    payload = {
        "generated_at": datetime.now().isoformat(),
        "input_file": str(SAMPLE_INPUT.relative_to(REPO_ROOT)),
        "run_summary": run_summary,
        "trend_signals": signals,
    }
    JSON_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_contract_csv(signals)

    now = datetime(2026, 4, 16, 12, 0, 0)
    repo = TrendSignalRepository.from_contract_csv(CSV_OUTPUT, now=now)
    pipeline = QAPipeline(
        repo,
        policy_hook=lambda result: f"downstream_hook_input:{result.behavior_flag}:{result.metadata['top_risk_flag']}",
    )

    cases = [
        _render_case(pipeline, "trend_evidence_present", "最近外泌体很火，值得跟吗", now),
        _render_case(pipeline, "trend_evidence_high_risk", "最近猛药焕肤很火，值得跟吗", now),
        _render_case(pipeline, "trend_evidence_stale", "最近冰晶眼膜很火，值得跟吗", now),
    ]

    report = {
        "task_id": "INT-001",
        "stage_summary": {
            "cleaned_input_count": run_summary["input_cleaned_count"],
            "generated_signal_count": run_summary["generated_signal_count"],
            "qa_cases": len(cases),
            "shared_csv_path": str(CSV_OUTPUT.relative_to(REPO_ROOT)),
            "shared_json_path": str(JSON_OUTPUT.relative_to(REPO_ROOT)),
        },
        "cases": cases,
    }
    REPORT_OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
