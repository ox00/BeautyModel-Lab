from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd


REQUIRED_TREND_COLUMNS = [
    "trend_id",
    "keyword",
    "topic_cluster",
    "heat_index",
    "growth_monthly",
    "platform",
    "captured_at",
]


@dataclass
class TrendBatchUpdateResult:
    status: str
    merged_df: pd.DataFrame
    imported_rows: int = 0
    duplicate_rows_removed: int = 0
    replaced_rows: int = 0
    retained_batch_versions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _normalize_trend_df(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(col).replace("\ufeff", "").strip() for col in normalized.columns]
    normalized = normalized.replace({pd.NA: None, float("nan"): None})
    normalized = normalized.replace({"nan": None, "": None})
    return normalized


def update_trend_table(
    existing_df: pd.DataFrame,
    incoming_df: pd.DataFrame,
    incoming_batch_version: str,
    incoming_batch_timestamp: Optional[str] = None,
    retained_batch_versions: Optional[List[str]] = None,
    retention_limit: int = 5,
) -> TrendBatchUpdateResult:
    existing = _normalize_trend_df(existing_df)
    incoming = _normalize_trend_df(incoming_df)
    versions = list(retained_batch_versions or [])

    missing_columns = [column for column in REQUIRED_TREND_COLUMNS if column not in incoming.columns]
    if missing_columns:
        return TrendBatchUpdateResult(
            status="rolled_back_invalid",
            merged_df=existing,
            warnings=[f"Incoming trend batch missing required columns: {', '.join(missing_columns)}"],
            retained_batch_versions=versions[-retention_limit:],
        )

    if incoming.empty:
        return TrendBatchUpdateResult(
            status="rolled_back_empty",
            merged_df=existing,
            warnings=["Incoming trend batch is empty; rollback to existing active trend table."],
            retained_batch_versions=versions[-retention_limit:],
        )

    incoming = incoming.copy()
    incoming["captured_at_dt"] = pd.to_datetime(incoming["captured_at"], errors="coerce")
    if incoming["captured_at_dt"].isna().any():
        return TrendBatchUpdateResult(
            status="rolled_back_invalid",
            merged_df=existing,
            warnings=["Incoming trend batch contains invalid captured_at values; rollback to existing active trend table."],
            retained_batch_versions=versions[-retention_limit:],
        )

    existing = existing.copy()
    existing["captured_at_dt"] = pd.to_datetime(existing["captured_at"], errors="coerce")

    incoming = incoming.sort_values(by=["captured_at_dt", "trend_id"], ascending=[False, True])
    incoming_before = len(incoming)
    incoming = incoming.drop_duplicates(subset=["keyword", "platform", "captured_at"], keep="first")
    duplicate_rows_removed = incoming_before - len(incoming)

    latest_incoming = (
        incoming.groupby(["keyword", "platform"], dropna=False)["captured_at_dt"]
        .max()
        .to_dict()
    )

    replace_mask = existing.apply(
        lambda row: (
            latest_incoming.get((row.get("keyword"), row.get("platform"))) is not None
            and pd.notna(row.get("captured_at_dt"))
            and row["captured_at_dt"] < latest_incoming[(row.get("keyword"), row.get("platform"))]
        ),
        axis=1,
    )
    replaced_rows = int(replace_mask.sum())
    existing = existing.loc[~replace_mask].copy()

    incoming_exact_keys = {
        (row.get("keyword"), row.get("platform"), row.get("captured_at"))
        for row in incoming.to_dict(orient="records")
    }
    existing_exact_mask = existing.apply(
        lambda row: (row.get("keyword"), row.get("platform"), row.get("captured_at")) in incoming_exact_keys,
        axis=1,
    )
    duplicate_rows_removed += int(existing_exact_mask.sum())
    existing = existing.loc[~existing_exact_mask].copy()

    merged = pd.concat([existing, incoming], ignore_index=True)
    merged = merged.sort_values(by=["captured_at_dt", "heat_index"], ascending=[False, False], na_position="last")
    merged = merged.drop(columns=["captured_at_dt"], errors="ignore").reset_index(drop=True)

    versions.append(incoming_batch_version)
    versions = versions[-retention_limit:]
    warnings: List[str] = []
    if incoming_batch_timestamp:
        warnings.append(f"Applied trend batch version={incoming_batch_version} timestamp={incoming_batch_timestamp}")
    else:
        warnings.append(f"Applied trend batch version={incoming_batch_version}")

    return TrendBatchUpdateResult(
        status="applied",
        merged_df=merged,
        imported_rows=len(incoming),
        duplicate_rows_removed=duplicate_rows_removed,
        replaced_rows=replaced_rows,
        retained_batch_versions=versions,
        warnings=warnings,
    )
