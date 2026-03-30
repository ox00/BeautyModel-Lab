import pytest
from pathlib import Path
from src.loaders.csv_loader import BatchLoader, BatchBundle, ValidationReport

# Use the real P0 data path for integration testing
P0_DATA_PATH = Path("data/deliveries/2026-03-14-baseline-v1/p0").resolve()

def test_load_batch_success():
    """Test loading the P0 batch successfully."""
    # Ensure the path exists, otherwise skip or fail
    assert P0_DATA_PATH.exists(), f"Test data not found at {P0_DATA_PATH}"
    
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    
    assert isinstance(bundle, BatchBundle)
    # Check all 5 tables are loaded
    assert len(bundle.data) == 5
    for table_name in BatchLoader.SCHEMA_MAP.keys():
        assert table_name in bundle.data
        df = bundle.data[table_name]
        assert not df.empty, f"Table {table_name} is empty"

def test_validate_batch_success():
    """Test validation of the P0 batch."""
    bundle = BatchLoader.load_batch(str(P0_DATA_PATH))
    report = BatchLoader.validate_batch(bundle)
    
    # Check if valid. If it fails, print errors for debugging.
    if not report.is_valid:
        print("Validation errors:", report.errors)
        
    assert report.is_valid is True, f"Validation failed with errors: {report.errors}"
