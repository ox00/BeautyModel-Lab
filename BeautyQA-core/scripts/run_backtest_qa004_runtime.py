from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from trend_evidence.pipeline import QAPipeline, default_runtime_handoff_json
from trend_evidence.trend_retrieval import TrendSignalRepository


def main() -> None:
    now_dt = datetime(2026, 4, 19, 12, 0, 0)
    handoff_json = default_runtime_handoff_json()
    repo = TrendSignalRepository.from_contract_json(handoff_json, now=now_dt)
    pipeline = QAPipeline(repo)

    query = "最近快速美白很火，值得跟吗"
    qa_result = pipeline.run(query, now=now_dt)
    context_block = pipeline.build_trend_context_block(query, now=now_dt)

    print(
        json.dumps(
            {
                "task_id": "QA-004",
                "backtest_date": "2026-04-19",
                "runtime_handoff_json": str(handoff_json),
                "source_exists": Path(handoff_json).exists(),
                "query": query,
                "behavior_flag": qa_result.behavior_flag,
                "top_signal_id": qa_result.metadata.get("top_signal_id"),
                "top_risk_flag": qa_result.metadata.get("top_risk_flag"),
                "trend_context_block": {
                    "summary": context_block.summary,
                    "behavior_flag": context_block.behavior_flag,
                    "item_count": len(context_block.items),
                    "top_item": (
                        {
                            "signal_id": context_block.items[0].signal_id,
                            "normalized_keyword": context_block.items[0].normalized_keyword,
                            "source_platform": context_block.items[0].source_platform,
                            "risk_flag": context_block.items[0].risk_flag,
                            "confidence": context_block.items[0].confidence,
                        }
                        if context_block.items
                        else None
                    ),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
