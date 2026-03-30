import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from .schemas import (
    ProductSKU, IngredientKnowledge, ComplianceRule,
    ReviewFeedback, TrendSignal
)

class BatchBundle:
    """Represents a loaded batch of data tables."""
    def __init__(self, data: Dict[str, pd.DataFrame], batch_path: str):
        self.data = data
        self.batch_path = batch_path

class ValidationReport:
    """Represents the outcome of validating a BatchBundle against schemas."""
    def __init__(self, is_valid: bool, errors: Dict[str, List[str]]):
        self.is_valid = is_valid
        self.errors = errors
        
    def __repr__(self):
        return f"<ValidationReport is_valid={self.is_valid} errors={len(self.errors)}>"

class BatchLoader:
    """Loads and validates P0 data batches."""
    
    SCHEMA_MAP = {
        "product_sku": ProductSKU,
        "ingredient_knowledge": IngredientKnowledge,
        "compliance_rule": ComplianceRule,
        "review_feedback": ReviewFeedback,
        "trend_signal": TrendSignal
    }

    @staticmethod
    def load_batch(batch_path: str) -> BatchBundle:
        """Loads CSV files from the given batch path into pandas DataFrames."""
        path = Path(batch_path)
        if not path.exists():
            raise FileNotFoundError(f"Batch path does not exist: {batch_path}")
            
        data = {}
        for table_name in BatchLoader.SCHEMA_MAP.keys():
            csv_file = path / f"{table_name}.csv"
            if csv_file.exists():
                # Read CSV as string to prevent pandas from mangling IDs (like dropping leading zeros)
                df = pd.read_csv(csv_file, dtype=str)
                # Convert pandas NaN to None for Pydantic compatibility
                df = df.where(pd.notnull(df), None)
                data[table_name] = df
            else:
                raise FileNotFoundError(f"Missing required file: {csv_file}")
                
        return BatchBundle(data=data, batch_path=batch_path)

    @staticmethod
    def validate_batch(batch_bundle: BatchBundle, max_errors_per_table: int = 50) -> ValidationReport:
        """Validates the loaded data against Pydantic schemas."""
        errors: Dict[str, List[str]] = {}
        is_valid = True
        
        for table_name, df in batch_bundle.data.items():
            schema_cls = BatchLoader.SCHEMA_MAP[table_name]
            table_errors = []
            
            # Convert DataFrame to list of dicts for validation
            records = df.to_dict(orient="records")
            for i, record in enumerate(records):
                try:
                    schema_cls(**record)
                except ValidationError as e:
                    is_valid = False
                    # Format error nicely
                    err_msgs = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
                    table_errors.append(f"Row {i} error: " + " | ".join(err_msgs))
                    
                    if len(table_errors) >= max_errors_per_table:
                        table_errors.append(f"... stopping after {max_errors_per_table} errors in {table_name}")
                        break
            
            if table_errors:
                errors[table_name] = table_errors
                
        return ValidationReport(is_valid=is_valid, errors=errors)
