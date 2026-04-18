import os
import sys

# Add project root to path to allow importing from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.loaders.csv_loader import BatchLoader
from src.retrieval import build_indexes, search_all


DEMO_QUERIES = [
    ("science", "PHERETIMA GUILLELMI EXTRACT"),
    ("product", "护手"),
    ("trend", "冰晶眼膜"),
    ("compliance", "乳黄素"),
]


def _section(title: str) -> str:
    return f"\n{'=' * 18} {title} {'=' * 18}"


def main():
    data_path = os.path.join(project_root, "data/deliveries/2026-03-14-baseline-v1/p0")
    batch_bundle = BatchLoader.load_batch(data_path, include_optional_tables=["review_feedback_raw"])
    retrieval_bundle = build_indexes(batch_bundle)

    print(_section("Retrieval Demo"))
    print(f"batch_version: {retrieval_bundle.batch_version}")
    print(f"batch_timestamp: {retrieval_bundle.batch_timestamp}")
    if retrieval_bundle.warnings:
        print("warnings:")
        for warning in retrieval_bundle.warnings:
            print(f"  - {warning}")

    for intent, query in DEMO_QUERIES:
        print(_section(f"intent={intent} | query={query}"))
        items = search_all(retrieval_bundle, query=query, intent=intent, limit=3)
        if not items:
            print(f"missing_info_note: {retrieval_bundle.last_missing_info_note}")
            continue

        for index, item in enumerate(items, start=1):
            print(f"[{index}] trace_id={item.trace_id}")
            print(f"    source: {item.source_table}#{item.source_id}")
            print(f"    score: {item.score} | type: {item.evidence_type} | risk: {item.risk_flag}")
            print(f"    title: {item.title}")
            print(f"    snippet: {item.snippet}")
            print(f"    timestamp: {item.timestamp}")
            print(f"    metadata: {item.metadata}")

        if retrieval_bundle.last_missing_info_note:
            print(f"missing_info_note: {retrieval_bundle.last_missing_info_note}")


if __name__ == "__main__":
    main()
