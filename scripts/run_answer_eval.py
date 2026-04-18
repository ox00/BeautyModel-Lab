import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.eval import evaluate_answer_bundle, get_default_answer_eval_cases
from src.loaders.csv_loader import BatchLoader
from src.retrieval import build_indexes


def main():
    data_path = os.path.join(project_root, "data/deliveries/2026-03-14-baseline-v1/p0")
    batch_bundle = BatchLoader.load_batch(data_path, include_optional_tables=["review_feedback_raw"])
    retrieval_bundle = build_indexes(batch_bundle)
    report = evaluate_answer_bundle(retrieval_bundle, get_default_answer_eval_cases())

    print("=== Answer Eval Report ===")
    print(f"batch_version: {retrieval_bundle.batch_version}")
    for metric_name, value in report.metrics.items():
        print(f"{metric_name}: {value:.4f}")

    print("\n--- Release Checklist ---")
    for item, passed in report.release_checklist.items():
        print(f"{item}: {'PASS' if passed else 'FAIL'}")

    print("\n--- Case Results ---")
    for result in report.results:
        print(
            f"{result.case.case_id}: scientificity={result.scientificity_pass} "
            f"trend={result.trend_relevance_pass} safety={result.safety_pass} "
            f"balance={result.balance_pass} missing_info={result.missing_info_behavior_pass} "
            f"trace={result.trace_coverage_pass}"
        )


if __name__ == "__main__":
    main()
