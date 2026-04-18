from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import ValidationError

from .schemas import (
    ProductSKU, IngredientKnowledge, ComplianceRule,
    ReviewFeedback, ReviewFeedbackRaw, TrendSignal
)

@dataclass
class BatchBundle:
    """Represents a loaded batch of data tables plus batch metadata."""

    data: Dict[str, pd.DataFrame]
    batch_path: str
    batch_version: Optional[str] = None
    batch_timestamp: Optional[str] = None
    source_delivery_path: Optional[str] = None
    manifest_found: bool = False
    table_row_counts: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Represents the outcome of validating a BatchBundle against schemas."""

    is_valid: bool
    errors: Dict[str, List[str]]
    warnings: List[str] = field(default_factory=list)
    quality_checks: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"<ValidationReport is_valid={self.is_valid} "
            f"errors={len(self.errors)} quality_checks={len(self.quality_checks)}>"
        )

class BatchLoader:
    """Loads and validates P0 data batches."""

    SCHEMA_MAP = {
        "product_sku": ProductSKU,
        "ingredient_knowledge": IngredientKnowledge,
        "compliance_rule": ComplianceRule,
        "review_feedback": ReviewFeedback,
        "trend_signal": TrendSignal
    }
    OPTIONAL_SCHEMA_MAP = {
        "review_feedback_raw": ReviewFeedbackRaw,
    }
    PRIMARY_KEY_MAP = {
        "product_sku": "product_id",
        "ingredient_knowledge": "ingredient_id",
        "compliance_rule": "rule_id",
        "review_feedback": "review_id",
        "trend_signal": "trend_id",
        "review_feedback_raw": "review_id",
    }
    TIMESTAMP_FIELDS = {
        "product_sku": ["launch_date"],
        "ingredient_knowledge": [],
        "compliance_rule": ["effective_date"],
        "review_feedback": ["created_at"],
        "trend_signal": ["captured_at"],
        "review_feedback_raw": ["created_at"],
    }
    REQUIRED_COMPLETENESS_THRESHOLD = 0.95
    DUPLICATE_RATE_THRESHOLD = 0.02
    TIMESTAMP_VALIDITY_THRESHOLD = 0.98

    @staticmethod
    def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [str(col).replace("\ufeff", "").strip() for col in df.columns]
        df = df.replace({pd.NA: None, float("nan"): None})
        df = df.replace({"nan": None, "": None})
        return df

    @staticmethod
    def _find_delivery_root(path: Path) -> Optional[Path]:
        candidates = [path, *path.parents]
        for candidate in candidates:
            manifest_path = candidate / "reports" / "data_manifest.csv"
            if manifest_path.exists():
                return candidate
        return None

    @staticmethod
    def _infer_batch_timestamp(delivery_root: Path, manifest_path: Optional[Path]) -> Optional[str]:
        timestamp_source = manifest_path if manifest_path and manifest_path.exists() else delivery_root
        try:
            return datetime.fromtimestamp(timestamp_source.stat().st_mtime).isoformat(timespec="seconds")
        except OSError:
            return None

    @staticmethod
    def _load_manifest(delivery_root: Path) -> tuple[bool, Dict[str, int], List[str]]:
        manifest_path = delivery_root / "reports" / "data_manifest.csv"
        if not manifest_path.exists():
            return False, {}, [f"Manifest not found: {manifest_path}"]

        manifest_df = pd.read_csv(manifest_path, dtype=str, encoding="utf-8-sig")
        manifest_df = BatchLoader._normalize_dataframe(manifest_df)

        row_counts: Dict[str, int] = {}
        warnings: List[str] = []
        for table_name in {**BatchLoader.SCHEMA_MAP, **BatchLoader.OPTIONAL_SCHEMA_MAP}:
            match = manifest_df[manifest_df["table_name"] == table_name]
            if match.empty:
                warnings.append(f"Manifest missing row-count entry for table: {table_name}")
                continue
            raw_rows = match.iloc[0].get("rows")
            try:
                row_counts[table_name] = int(raw_rows) if raw_rows is not None else 0
            except (TypeError, ValueError):
                warnings.append(f"Manifest rows is not an integer for table: {table_name}")

        return True, row_counts, warnings

    @staticmethod
    def _required_fields(schema_cls: Any) -> List[str]:
        return [name for name, field_info in schema_cls.model_fields.items() if field_info.is_required()]

    @staticmethod
    def _compute_quality_checks(table_name: str, df: pd.DataFrame, schema_cls: Any) -> Dict[str, Any]:
        row_count = len(df)
        primary_key = BatchLoader.PRIMARY_KEY_MAP[table_name]
        pk_series = df[primary_key] if primary_key in df.columns else pd.Series(dtype="object")
        pk_duplicate_count = int(pk_series.dropna().duplicated().sum()) if not pk_series.empty else row_count
        pk_unique_rate = 1.0 if row_count == 0 else (row_count - pk_duplicate_count) / row_count

        required_fields = BatchLoader._required_fields(schema_cls)
        required_completeness: Dict[str, Dict[str, Any]] = {}
        completeness_pass = True
        for field_name in required_fields:
            non_null_count = int(df[field_name].notna().sum()) if field_name in df.columns else 0
            ratio = 1.0 if row_count == 0 else non_null_count / row_count
            passed = ratio >= BatchLoader.REQUIRED_COMPLETENESS_THRESHOLD
            completeness_pass = completeness_pass and passed
            required_completeness[field_name] = {
                "non_null_count": non_null_count,
                "ratio": ratio,
                "passed": passed,
            }

        duplicate_count = int(df.duplicated().sum())
        duplicate_rate = 0.0 if row_count == 0 else duplicate_count / row_count
        duplicate_pass = duplicate_rate <= BatchLoader.DUPLICATE_RATE_THRESHOLD

        timestamp_checks: Dict[str, Dict[str, Any]] = {}
        timestamp_pass = True
        for field_name in BatchLoader.TIMESTAMP_FIELDS[table_name]:
            if field_name not in df.columns:
                timestamp_checks[field_name] = {
                    "non_empty_count": 0,
                    "valid_count": 0,
                    "invalid_count": 0,
                    "ratio": 1.0,
                    "passed": True,
                }
                continue

            non_empty = df[field_name].dropna()
            valid = pd.to_datetime(non_empty, errors="coerce", format="mixed")
            valid_count = int(valid.notna().sum())
            non_empty_count = int(non_empty.shape[0])
            invalid_count = non_empty_count - valid_count
            ratio = 1.0 if non_empty_count == 0 else valid_count / non_empty_count
            passed = ratio >= BatchLoader.TIMESTAMP_VALIDITY_THRESHOLD
            timestamp_pass = timestamp_pass and passed
            timestamp_checks[field_name] = {
                "non_empty_count": non_empty_count,
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "ratio": ratio,
                "passed": passed,
            }

        overall_passed = (
            pk_duplicate_count == 0
            and completeness_pass
            and duplicate_pass
            and timestamp_pass
        )
        return {
            "row_count": row_count,
            "primary_key": {
                "field": primary_key,
                "duplicate_count": pk_duplicate_count,
                "unique_rate": pk_unique_rate,
                "passed": pk_duplicate_count == 0,
            },
            "required_fields": required_completeness,
            "duplicate_rate": {
                "duplicate_count": duplicate_count,
                "ratio": duplicate_rate,
                "passed": duplicate_pass,
            },
            "timestamp_validity": timestamp_checks,
            "passed": overall_passed,
        }

    @staticmethod
    def load_batch(batch_path: str, include_optional_tables: Optional[List[str]] = None) -> BatchBundle:
        """Loads CSV files from the given batch path into pandas DataFrames."""
        path = Path(batch_path)
        if not path.exists():
            raise FileNotFoundError(f"Batch path does not exist: {batch_path}")
        optional_tables = include_optional_tables or []

        delivery_root = BatchLoader._find_delivery_root(path) or path
        manifest_found, table_row_counts, manifest_warnings = BatchLoader._load_manifest(delivery_root)
        batch_version = delivery_root.name
        batch_timestamp = BatchLoader._infer_batch_timestamp(
            delivery_root,
            delivery_root / "reports" / "data_manifest.csv" if manifest_found else None,
        )

        data = {}
        for table_name in BatchLoader.SCHEMA_MAP.keys():
            csv_file = path / f"{table_name}.csv"
            if csv_file.exists():
                # Read CSV as string to prevent pandas from mangling IDs (like dropping leading zeros)
                df = pd.read_csv(csv_file, dtype=str, encoding="utf-8-sig")
                df = BatchLoader._normalize_dataframe(df)
                data[table_name] = df
            else:
                raise FileNotFoundError(f"Missing required file: {csv_file}")

        for table_name in optional_tables:
            schema_cls = BatchLoader.OPTIONAL_SCHEMA_MAP.get(table_name)
            if schema_cls is None:
                raise ValueError(f"Unsupported optional table: {table_name}")

            level_dir = "p1" if table_name == "review_feedback_raw" else "optional"
            csv_file = delivery_root / level_dir / f"{table_name}.csv"
            if not csv_file.exists():
                warnings = manifest_warnings + [f"Optional table not found: {csv_file}"]
                return BatchBundle(
                    data=data,
                    batch_path=str(path),
                    batch_version=batch_version,
                    batch_timestamp=batch_timestamp,
                    source_delivery_path=str(delivery_root),
                    manifest_found=manifest_found,
                    table_row_counts=table_row_counts,
                    warnings=warnings,
                )

            df = pd.read_csv(csv_file, dtype=str, encoding="utf-8-sig")
            df = BatchLoader._normalize_dataframe(df)
            data[table_name] = df

        warnings = list(manifest_warnings)
        for table_name, df in data.items():
            manifest_rows = table_row_counts.get(table_name)
            if manifest_rows is not None and manifest_rows != len(df):
                warnings.append(
                    f"Manifest row count mismatch for {table_name}: "
                    f"manifest={manifest_rows}, loaded={len(df)}"
                )

        return BatchBundle(
            data=data,
            batch_path=str(path),
            batch_version=batch_version,
            batch_timestamp=batch_timestamp,
            source_delivery_path=str(delivery_root),
            manifest_found=manifest_found,
            table_row_counts=table_row_counts,
            warnings=warnings,
        )

    @staticmethod
    def validate_batch(batch_bundle: BatchBundle, max_errors_per_table: int = 50) -> ValidationReport:
        """Validates the loaded data against Pydantic schemas."""
        errors: Dict[str, List[str]] = {}
        quality_checks: Dict[str, Dict[str, Any]] = {}
        warnings = list(batch_bundle.warnings)
        schema_map = {**BatchLoader.SCHEMA_MAP, **BatchLoader.OPTIONAL_SCHEMA_MAP}

        for table_name, df in batch_bundle.data.items():
            schema_cls = schema_map[table_name]
            table_errors = []
            quality_checks[table_name] = BatchLoader._compute_quality_checks(table_name, df, schema_cls)

            # Convert DataFrame to list of dicts for validation
            records = df.to_dict(orient="records")
            for i, record in enumerate(records):
                try:
                    schema_cls(**record)
                except ValidationError as e:
                    # Format error nicely
                    err_msgs = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
                    table_errors.append(f"Row {i} error: " + " | ".join(err_msgs))

                    if len(table_errors) >= max_errors_per_table:
                        table_errors.append(f"... stopping after {max_errors_per_table} errors in {table_name}")
                        break

            if table_errors:
                errors[table_name] = table_errors

            if not quality_checks[table_name]["passed"]:
                pk_info = quality_checks[table_name]["primary_key"]
                if not pk_info["passed"]:
                    errors.setdefault(table_name, []).append(
                        f"Quality check failed: primary key '{pk_info['field']}' has "
                        f"{pk_info['duplicate_count']} duplicates"
                    )

                for field_name, detail in quality_checks[table_name]["required_fields"].items():
                    if not detail["passed"]:
                        errors.setdefault(table_name, []).append(
                            f"Quality check failed: required field '{field_name}' completeness "
                            f"{detail['ratio']:.2%} below threshold "
                            f"{BatchLoader.REQUIRED_COMPLETENESS_THRESHOLD:.0%}"
                        )

                duplicate_info = quality_checks[table_name]["duplicate_rate"]
                if not duplicate_info["passed"]:
                    errors.setdefault(table_name, []).append(
                        f"Quality check failed: duplicate rate {duplicate_info['ratio']:.2%} "
                        f"above threshold {BatchLoader.DUPLICATE_RATE_THRESHOLD:.0%}"
                    )

                for field_name, detail in quality_checks[table_name]["timestamp_validity"].items():
                    if not detail["passed"]:
                        errors.setdefault(table_name, []).append(
                            f"Quality check failed: timestamp field '{field_name}' validity "
                            f"{detail['ratio']:.2%} below threshold "
                            f"{BatchLoader.TIMESTAMP_VALIDITY_THRESHOLD:.0%}"
                        )

        is_valid = not errors
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            quality_checks=quality_checks,
        )
