from __future__ import annotations

from datetime import datetime

from trend_evidence.pipeline import QAPipeline, default_runtime_handoff_json
from trend_evidence.trend_retrieval import TrendSignalRepository


def main() -> None:
    now_dt = datetime(2026, 4, 19, 12, 0, 0)
    repo = TrendSignalRepository.from_contract_json(default_runtime_handoff_json(), now=now_dt)
    pipeline = QAPipeline(repo)
    result = pipeline.run("最近快速美白很火，值得跟吗", now=now_dt)
    block = pipeline.build_trend_context_block("最近快速美白很火，值得跟吗", now=now_dt)

    assert result.trend_evidence, "expected runtime handoff to yield trend evidence"
    assert block.items, "expected trend context block to contain at least one item"
    assert block.items[0].normalized_keyword == "快速美白", "expected runtime handoff top keyword to be 快速美白"

    print("QA-004 runtime closure check passed")


if __name__ == "__main__":
    main()
