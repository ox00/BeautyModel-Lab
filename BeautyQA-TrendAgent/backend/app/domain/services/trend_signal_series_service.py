from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select

from app.config.settings import settings
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.database.models import TrendSignalSeries


def _parse_iso_dt(value: str | None) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _bucket_start(dt: datetime, bucket_type: str) -> datetime:
    dt_utc = dt.astimezone(timezone.utc)
    if bucket_type == "12h":
        hour = 0 if dt_utc.hour < 12 else 12
        return dt_utc.replace(hour=hour, minute=0, second=0, microsecond=0, tzinfo=None)
    # default 1d
    return dt_utc.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def _bucket_end(start: datetime, bucket_type: str) -> datetime:
    if bucket_type == "12h":
        return start + timedelta(hours=12)
    return start + timedelta(days=1)


@dataclass
class BucketAgg:
    normalized_keyword: str
    source_platform: str
    bucket_type: str
    bucket_start: datetime
    bucket_end: datetime
    signal_ids: list[str]
    task_ids: list[int]
    scores: list[float]
    evidences: list[str]


def _series_status(delta_score: float) -> str:
    if delta_score >= 10:
        return "emerging"
    if delta_score <= -10:
        return "cooling"
    return "stable"


class TrendSignalSeriesService:
    """Aggregate trend_signal handoff rows into time-bucket trend_signal_series."""

    def __init__(self) -> None:
        self._handoff_root = Path(settings.TREND_SIGNAL_HANDOFF_DIR)

    def _load_handoff_rows(self) -> list[dict[str, Any]]:
        latest_json = self._handoff_root / "current" / "trend_signal_latest.json"
        if not latest_json.exists():
            return []
        payload = json.loads(latest_json.read_text(encoding="utf-8"))
        results = payload.get("results", [])
        return [row for row in results if isinstance(row, dict)]

    def _aggregate_buckets(self, rows: list[dict[str, Any]], bucket_type: str) -> list[BucketAgg]:
        grouped: dict[tuple[str, str, datetime], BucketAgg] = {}
        for row in rows:
            normalized_keyword = str(row.get("normalized_keyword", "")).strip()
            source_platform = str(row.get("source_platform", "")).strip()
            if not normalized_keyword or not source_platform:
                continue
            observed_at = _parse_iso_dt(row.get("observed_at"))
            b_start = _bucket_start(observed_at, bucket_type)
            key = (normalized_keyword, source_platform, b_start)
            if key not in grouped:
                grouped[key] = BucketAgg(
                    normalized_keyword=normalized_keyword,
                    source_platform=source_platform,
                    bucket_type=bucket_type,
                    bucket_start=b_start,
                    bucket_end=_bucket_end(b_start, bucket_type),
                    signal_ids=[],
                    task_ids=[],
                    scores=[],
                    evidences=[],
                )
            agg = grouped[key]
            signal_id = str(row.get("signal_id", ""))
            if signal_id:
                agg.signal_ids.append(signal_id)
            task_id = row.get("crawl_task_id")
            if isinstance(task_id, int):
                agg.task_ids.append(task_id)
            score = float(row.get("trend_score", 0.0) or 0.0)
            agg.scores.append(score)
            evidence = str(row.get("signal_evidence", ""))
            if evidence:
                agg.evidences.append(evidence)

        return sorted(grouped.values(), key=lambda x: (x.normalized_keyword, x.source_platform, x.bucket_start))

    async def aggregate_and_persist(self, bucket_type: str = "1d") -> dict[str, Any]:
        rows = self._load_handoff_rows()
        if not rows:
            return {
                "bucket_type": bucket_type,
                "source_count": 0,
                "series_count": 0,
                "message": "no_handoff_rows",
            }

        bucket_aggs = self._aggregate_buckets(rows, bucket_type)
        previous_map: dict[tuple[str, str], TrendSignalSeries] = {}
        created_rows: list[dict[str, Any]] = []

        async with async_session_factory() as session:
            # Rebuild current bucket_type snapshot from latest handoff for deterministic export.
            await session.execute(delete(TrendSignalSeries).where(TrendSignalSeries.bucket_type == bucket_type))
            await session.flush()

            for agg in bucket_aggs:
                key_no_bucket = (agg.normalized_keyword, agg.source_platform)
                prev = previous_map.get(key_no_bucket)

                unique_signal_ids = sorted(set(agg.signal_ids))
                unique_task_ids = sorted(set(agg.task_ids))
                support_count = len(unique_signal_ids)
                avg_score = sum(agg.scores) / len(agg.scores) if agg.scores else 0.0
                prev_avg = float(prev.avg_trend_score) if prev else 0.0
                delta_score = avg_score - prev_avg
                delta_support = support_count - (int(prev.support_count) if prev else 0)

                delta_vs_prev = {
                    "delta_avg_trend_score": round(delta_score, 4),
                    "delta_support_count": delta_support,
                    "prev_bucket_start": prev.bucket_start.isoformat() if prev else None,
                }
                row = TrendSignalSeries(
                    series_key=f"{agg.normalized_keyword.lower()}__{agg.source_platform.lower()}__{agg.bucket_type}__{agg.bucket_start.isoformat()}",
                    bucket_type=agg.bucket_type,
                    bucket_start=agg.bucket_start,
                    bucket_end=agg.bucket_end,
                    normalized_keyword=agg.normalized_keyword,
                    source_platform=agg.source_platform,
                    support_count=support_count,
                    avg_trend_score=round(avg_score, 4),
                    delta_vs_prev_bucket=delta_vs_prev,
                    top_evidence=agg.evidences[0] if agg.evidences else "",
                    signal_ids=unique_signal_ids,
                    task_ids=unique_task_ids,
                    aggregation_method="bucket_avg_v1",
                    series_status=_series_status(delta_score),
                )
                session.add(row)
                await session.flush()

                previous_map[key_no_bucket] = row
                created_rows.append(
                    {
                        "series_key": row.series_key,
                        "normalized_keyword": row.normalized_keyword,
                        "source_platform": row.source_platform,
                        "bucket_type": row.bucket_type,
                        "bucket_start": row.bucket_start.isoformat(),
                        "bucket_end": row.bucket_end.isoformat(),
                        "support_count": row.support_count,
                        "avg_trend_score": row.avg_trend_score,
                        "delta_vs_prev_bucket": row.delta_vs_prev_bucket,
                        "signal_ids": row.signal_ids or [],
                        "task_ids": row.task_ids or [],
                        "series_status": row.series_status,
                    }
                )

            await session.commit()

        output_dir = Path(settings.SHARED_DATA_DIR) / "handoff" / "trend_signal_series"
        output_dir.mkdir(parents=True, exist_ok=True)
        run_id = datetime.now(timezone.utc).strftime("int004_%Y%m%d_%H%M%S")
        payload = {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "bucket_type": bucket_type,
            "source_signal_count": len(rows),
            "series_count": len(created_rows),
            "results": created_rows,
        }
        history = output_dir / "history"
        history.mkdir(parents=True, exist_ok=True)
        (history / f"{run_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_dir / "current.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "run_id": run_id,
            "bucket_type": bucket_type,
            "source_count": len(rows),
            "series_count": len(created_rows),
            "current_path": str(output_dir / "current.json"),
            "history_path": str(history / f"{run_id}.json"),
        }
