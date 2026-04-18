import os
import sys

# Add project root to path to allow importing from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.loaders.csv_loader import BatchLoader

def verify():
    data_path = os.path.join(project_root, "data/deliveries/2026-03-14-baseline-v1/p0")
    
    print(f"Loading data from: {data_path}...")
    bundle = BatchLoader.load_batch(data_path)
    
    print("\n--- Loaded Tables ---")
    for table_name, df in bundle.data.items():
        print(f"✅ {table_name}: {len(df)} rows")

    print("\n--- Batch Metadata ---")
    print(f"batch_version: {bundle.batch_version}")
    print(f"batch_timestamp: {bundle.batch_timestamp}")
    print(f"source_delivery_path: {bundle.source_delivery_path}")
    print(f"manifest_found: {bundle.manifest_found}")
    if bundle.warnings:
        print("warnings:")
        for warning in bundle.warnings:
            print(f"  - {warning}")
        
    print("\n--- Validating Data against Schemas ---")
    report = BatchLoader.validate_batch(bundle)
    
    if report.is_valid:
        print("✅ Validation PASSED: All data matches schemas!")
    else:
        print("❌ Validation FAILED. Errors found:")
        for table, errors in report.errors.items():
            print(f"\nErrors in {table} (showing first few):")
            for err in errors[:3]:
                print(f"  - {err}")

    print("\n--- Quality Checks ---")
    for table_name, checks in report.quality_checks.items():
        pk = checks["primary_key"]
        dup = checks["duplicate_rate"]
        print(
            f"{table_name}: pk_duplicates={pk['duplicate_count']} "
            f"duplicate_rate={dup['ratio']:.2%} passed={checks['passed']}"
        )

if __name__ == "__main__":
    verify()
