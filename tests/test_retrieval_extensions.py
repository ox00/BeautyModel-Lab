from pathlib import Path

import pandas as pd

from src.eval import evaluate_retrieval_bundle, get_default_retrieval_eval_cases
from src.loaders.csv_loader import BatchLoader
from src.loaders.trend_updates import update_trend_table
from src.retrieval import build_indexes, search_all


P0_DATA_PATH = Path("data/deliveries/2026-03-14-baseline-v1/p0").resolve()


def test_load_batch_with_optional_raw_feedback():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH), include_optional_tables=["review_feedback_raw"])

    assert "review_feedback_raw" in bundle.data
    assert not bundle.data["review_feedback_raw"].empty


def test_search_all_returns_raw_feedback_evidence_when_optional_table_loaded():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH), include_optional_tables=["review_feedback_raw"])
    retrieval_bundle = build_indexes(bundle)

    items = search_all(retrieval_bundle, query="护手霜", intent="review", limit=5)

    assert items
    assert any(item.source_table == "review_feedback_raw" for item in items)
    assert any(item.trace_id and item.trace_id.startswith("review_feedback_raw:") for item in items)


def test_update_trend_table_applies_new_batch_and_replaces_stale_rows():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    existing_df = bundle.data["trend_signal"]
    baseline_row = existing_df.iloc[0].to_dict()

    incoming_df = pd.DataFrame(
        [
            {
                "trend_id": "trend_new_001",
                "keyword": baseline_row["keyword"],
                "topic_cluster": baseline_row["topic_cluster"],
                "heat_index": "999",
                "growth_monthly": "8888.0",
                "platform": baseline_row["platform"],
                "captured_at": "2026-03-01 00:00:00",
            },
            {
                "trend_id": "trend_new_001_dup",
                "keyword": baseline_row["keyword"],
                "topic_cluster": baseline_row["topic_cluster"],
                "heat_index": "999",
                "growth_monthly": "8888.0",
                "platform": baseline_row["platform"],
                "captured_at": "2026-03-01 00:00:00",
            },
        ]
    )

    update_result = update_trend_table(
        existing_df=existing_df,
        incoming_df=incoming_df,
        incoming_batch_version="2026-04-08-trend-hotfix",
        incoming_batch_timestamp="2026-04-08T10:00:00",
        retained_batch_versions=["2026-03-14-baseline-v1"],
    )

    assert update_result.status == "applied"
    assert update_result.imported_rows == 1
    assert update_result.duplicate_rows_removed >= 1
    assert update_result.replaced_rows >= 1
    assert update_result.retained_batch_versions[-1] == "2026-04-08-trend-hotfix"

    bundle.data["trend_signal"] = update_result.merged_df
    retrieval_bundle = build_indexes(bundle)
    items = search_all(retrieval_bundle, query=baseline_row["keyword"], intent="trend")

    trend_items = [item for item in items if item.source_table == "trend_signal"]
    assert trend_items
    assert trend_items[0].timestamp == "2026-03-01 00:00:00"


def test_update_trend_table_rolls_back_on_empty_batch():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    existing_df = bundle.data["trend_signal"]
    empty_df = pd.DataFrame(columns=existing_df.columns)

    update_result = update_trend_table(
        existing_df=existing_df,
        incoming_df=empty_df,
        incoming_batch_version="2026-04-08-empty",
    )

    assert update_result.status == "rolled_back_empty"
    assert update_result.merged_df.equals(existing_df)
    assert update_result.warnings


def test_evaluate_retrieval_bundle_reports_ready_metrics():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH), include_optional_tables=["review_feedback_raw"])
    retrieval_bundle = build_indexes(bundle)

    report = evaluate_retrieval_bundle(retrieval_bundle, get_default_retrieval_eval_cases())

    assert report.metrics["science_recall"] >= 1.0
    assert report.metrics["trend_recall"] >= 1.0
    assert report.metrics["compliance_hit_rate"] >= 1.0
    assert report.release_checklist["overall_ready"] is True
