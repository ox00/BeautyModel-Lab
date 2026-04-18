import pytest
from pathlib import Path
from src.loaders.csv_loader import BatchLoader, BatchBundle, ValidationReport
from src.retrieval import EvidenceItem, RetrievalBundle, build_indexes, search_all

# Use the real P0 data path for integration testing
P0_DATA_PATH = Path("data/deliveries/2026-03-14-baseline-v1/p0").resolve()

def test_load_batch_success():
    """Test loading the P0 batch successfully."""
    # Ensure the path exists, otherwise skip or fail
    assert P0_DATA_PATH.exists(), f"Test data not found at {P0_DATA_PATH}"
    
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    
    assert isinstance(bundle, BatchBundle)
    assert bundle.batch_version == "2026-03-14-baseline-v1"
    assert bundle.manifest_found is True
    assert bundle.source_delivery_path.endswith("data/deliveries/2026-03-14-baseline-v1")
    assert bundle.table_row_counts["product_sku"] == 1000
    # Check all 5 tables are loaded
    assert len(bundle.data) == 5
    for table_name in BatchLoader.SCHEMA_MAP.keys():
        assert table_name in bundle.data
        df = bundle.data[table_name]
        assert not df.empty, f"Table {table_name} is empty"
        assert "\ufeff" not in df.columns[0]

def test_validate_batch_success():
    """Test validation of the P0 batch."""
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    report = BatchLoader.validate_batch(bundle)
    
    # Check if valid. If it fails, print errors for debugging.
    if not report.is_valid:
        print("Validation errors:", report.errors)
        
    assert isinstance(report, ValidationReport)
    assert report.is_valid is True, f"Validation failed with errors: {report.errors}"
    assert "product_sku" in report.quality_checks
    assert report.quality_checks["product_sku"]["primary_key"]["passed"] is True
    assert report.quality_checks["trend_signal"]["timestamp_validity"]["captured_at"]["passed"] is True

def test_validate_batch_detects_quality_issues():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    broken_df = bundle.data["trend_signal"].copy()
    broken_df.loc[0, "trend_id"] = broken_df.loc[1, "trend_id"]
    broken_df.loc[0:9, "captured_at"] = "not-a-date"
    bundle.data["trend_signal"] = broken_df

    report = BatchLoader.validate_batch(bundle)

    assert report.is_valid is False
    assert "trend_signal" in report.errors
    assert any("primary key" in err for err in report.errors["trend_signal"])
    assert any("timestamp field 'captured_at'" in err for err in report.errors["trend_signal"])

def test_build_indexes_maps_all_tables_to_evidence():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    retrieval_bundle = build_indexes(bundle)

    assert isinstance(retrieval_bundle, RetrievalBundle)
    assert retrieval_bundle.batch_version == bundle.batch_version
    for table_name in BatchLoader.SCHEMA_MAP:
        indexed_items = retrieval_bundle.indexes[table_name]
        assert indexed_items, f"No evidence indexed for {table_name}"
        assert isinstance(indexed_items[0].evidence, EvidenceItem)
        assert indexed_items[0].evidence.title
        assert indexed_items[0].evidence.snippet

def test_search_all_returns_science_evidence():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    retrieval_bundle = build_indexes(bundle)

    items = search_all(retrieval_bundle, query="PHERETIMA GUILLELMI EXTRACT", intent="science")

    assert items
    assert items[0].source_table in {"ingredient_knowledge", "compliance_rule"}
    assert any(item.source_table == "ingredient_knowledge" for item in items)

def test_search_all_returns_product_and_review_evidence():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    retrieval_bundle = build_indexes(bundle)

    items = search_all(retrieval_bundle, query="护手", intent="product")

    assert items
    assert any(item.source_table == "review_feedback" for item in items)

def test_search_all_returns_trend_and_orders_recent_items():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    retrieval_bundle = build_indexes(bundle)

    items = search_all(retrieval_bundle, query="冰晶眼膜", intent="trend")

    assert items
    assert any(item.source_table == "trend_signal" for item in items)
    trend_items = [item for item in items if item.source_table == "trend_signal"]
    assert trend_items[0].timestamp is not None

def test_search_all_prioritizes_compliance_risk_flags():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    retrieval_bundle = build_indexes(bundle)

    items = search_all(retrieval_bundle, query="乳黄素", intent="compliance")

    assert items
    assert items[0].source_table == "compliance_rule"
    assert items[0].risk_flag is not None

def test_search_all_sets_missing_info_note_on_empty_result():
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    retrieval_bundle = build_indexes(bundle)

    items = search_all(retrieval_bundle, query="this query should not exist 123456", intent="science")

    assert items == []
    assert retrieval_bundle.last_missing_info_note is not None
