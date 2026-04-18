import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.loaders.csv_loader import BatchLoader
from src.pipeline import answer_query
from src.retrieval import build_indexes


DEMO_QUERIES = [
    ("PHERETIMA GUILLELMI EXTRACT 有什么功效", None),
    ("冰晶眼膜 最近有什么趋势", {"need_trend": True}),
    ("乳黄素 是否合规", None),
    ("不存在的奇怪查询 123456", None),
]


def main():
    data_path = os.path.join(project_root, "data/deliveries/2026-03-14-baseline-v1/p0")
    batch_bundle = BatchLoader.load_batch(data_path, include_optional_tables=["review_feedback_raw"])
    retrieval_bundle = build_indexes(batch_bundle)

    print("=== Grounded Answer Demo ===")
    print(f"batch_version: {retrieval_bundle.batch_version}")

    for query, filters in DEMO_QUERIES:
        answer = answer_query(retrieval_bundle, query=query, filters=filters, mode="auto")
        print(f"\n--- query={query} ---")
        print(answer.answer_text)
        print(f"risk_note: {answer.risk_note}")
        print(f"missing_info_note: {answer.missing_info_note}")


if __name__ == "__main__":
    main()
