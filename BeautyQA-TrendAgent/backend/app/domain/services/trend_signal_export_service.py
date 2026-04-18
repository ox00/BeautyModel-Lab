from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable

from sqlalchemy import select

from app.config.settings import settings
from app.domain.services.runtime_batch_service import RuntimeBatchService
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.database.models import RuntimeBatchRun, RuntimeBatchRunEvent


TREND_SIGNAL_CSV_COLUMNS = [
    "signal_id",
    "keyword_id",
    "crawl_task_id",
    "normalized_keyword",
    "topic_cluster",
    "trend_type",
    "signal_summary",
    "signal_evidence",
    "source_platform",
    "source_url",
    "trend_score",
    "confidence",
    "risk_flag",
    "observed_at",
    "fresh_until",
    "report_id",
    "signal_period_type",
    "signal_period_label",
    "source_scope",
    "support_count",
    "evidence_ids",
    "aggregation_method",
    "version",
]


def _normalize_dt(value: str | None) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _stable_sort_key(signal: dict[str, Any]) -> tuple[str, str, str]:
    return (
        signal.get("normalized_keyword", ""),
        signal.get("source_platform", ""),
        signal.get("signal_id", ""),
    )


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _write_csv_atomic(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="") as tmp:
        writer = csv.DictWriter(tmp, fieldnames=TREND_SIGNAL_CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            evidence_ids = csv_row.get("evidence_ids", [])
            if isinstance(evidence_ids, list):
                csv_row["evidence_ids"] = json.dumps(evidence_ids, ensure_ascii=False)
            writer.writerow({key: csv_row.get(key, "") for key in TREND_SIGNAL_CSV_COLUMNS})
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


class TrendSignalExportService:
    """Build stable QA handoff exports from first-party runtime batch history."""

    def __init__(self) -> None:
        self._handoff_root = Path(settings.TREND_SIGNAL_HANDOFF_DIR)

    async def export_latest(
        self,
        *,
        trigger_source: str = "manual",
        source_run_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        export_run_id = datetime.now(timezone.utc).strftime("int003_%Y%m%d_%H%M%S")
        requested_options = {
            "source_run_ids": source_run_ids or [],
            "handoff_root": str(self._handoff_root),
        }
        batch_run = await self._create_export_run(export_run_id, trigger_source, requested_options)

        try:
            source_runs, source_events = await self._load_source_runtime_events(source_run_ids)
            source_files, source_mode = self._extract_signal_output_files(source_runs, source_events)
            if not source_files:
                raise RuntimeError("No eligible trend_signal source files found from completed runtime batches")

            rows, source_file_rows = self._load_signal_rows(source_files)
            if not rows:
                raise RuntimeError("Trend signal source files were found, but no valid signal rows were parsed")

            deduped_rows = self._dedupe_signals(rows)
            generated_at = datetime.now(timezone.utc).isoformat()

            current_dir = self._handoff_root / "current"
            history_dir = self._handoff_root / "history" / export_run_id
            current_csv = current_dir / "trend_signal_latest.csv"
            current_json = current_dir / "trend_signal_latest.json"
            current_manifest = current_dir / "manifest.json"
            history_csv = history_dir / "trend_signal_latest.csv"
            history_json = history_dir / "trend_signal_latest.json"
            history_manifest = history_dir / "manifest.json"

            export_payload = {
                "run_id": export_run_id,
                "generated_at": generated_at,
                "source_mode": source_mode,
                "source_runtime_run_ids": [run.run_id for run in source_runs],
                "source_signal_file_count": len(source_files),
                "count": len(deduped_rows),
                "results": deduped_rows,
            }
            manifest = {
                "run_id": export_run_id,
                "generated_at": generated_at,
                "run_type": "trend_signal_export",
                "schema_version": "trend_signal_export_v1",
                "source_mode": source_mode,
                "source_runtime_run_ids": [run.run_id for run in source_runs],
                "source_runtime_run_count": len(source_runs),
                "source_signal_file_count": len(source_files),
                "source_signal_row_count": len(rows),
                "exported_row_count": len(deduped_rows),
                "paths": {
                    "current_csv": str(current_csv),
                    "current_json": str(current_json),
                    "history_csv": str(history_csv),
                    "history_json": str(history_json),
                },
                "source_files": sorted(source_file_rows),
            }

            _write_csv_atomic(history_csv, deduped_rows)
            _write_json_atomic(history_json, export_payload)
            _write_json_atomic(history_manifest, manifest)
            _write_csv_atomic(current_csv, deduped_rows)
            _write_json_atomic(current_json, export_payload)
            _write_json_atomic(current_manifest, manifest)

            summary = {
                "success": True,
                "source_mode": source_mode,
                "source_runtime_run_count": len(source_runs),
                "source_signal_file_count": len(source_files),
                "source_signal_row_count": len(rows),
                "exported_row_count": len(deduped_rows),
            }
            report_paths = {
                "current_csv": str(current_csv),
                "current_json": str(current_json),
                "current_manifest": str(current_manifest),
                "history_csv": str(history_csv),
                "history_json": str(history_json),
                "history_manifest": str(history_manifest),
            }
            await self._record_export_sources(batch_run["id"], export_run_id, source_files)
            await self._finalize_export_run(
                batch_run_id=batch_run["id"],
                summary=summary,
                report_paths=report_paths,
                status="completed",
                error_message="",
            )
            return {
                "run_id": export_run_id,
                "summary": summary,
                "report_paths": report_paths,
                "source_runtime_run_ids": [run.run_id for run in source_runs],
            }
        except Exception as exc:
            await self._finalize_export_run(
                batch_run_id=batch_run["id"],
                summary={"success": False},
                report_paths=None,
                status="failed",
                error_message=str(exc),
            )
            raise

    async def _create_export_run(
        self,
        run_id: str,
        trigger_source: str,
        requested_options: dict[str, Any],
    ) -> dict[str, Any]:
        async with async_session_factory() as session:
            service = RuntimeBatchService(session)
            batch = await service.create_run(
                run_id=run_id,
                run_type="trend_signal_export",
                trigger_source=trigger_source,
                profile_name="int003_export",
                platforms=[],
                requested_options=requested_options,
                effective_options=requested_options,
            )
            await session.commit()
            return {"id": batch.id, "run_id": batch.run_id}

    async def _load_source_runtime_events(
        self,
        source_run_ids: list[str] | None,
    ) -> tuple[list[RuntimeBatchRun], list[RuntimeBatchRunEvent]]:
        async with async_session_factory() as session:
            run_stmt = (
                select(RuntimeBatchRun)
                .where(RuntimeBatchRun.run_type == "int002_runtime")
                .where(RuntimeBatchRun.status == "completed")
                .order_by(RuntimeBatchRun.completed_at.desc(), RuntimeBatchRun.id.desc())
            )
            if source_run_ids:
                run_stmt = run_stmt.where(RuntimeBatchRun.run_id.in_(source_run_ids))
            runs = list((await session.execute(run_stmt)).scalars().all())
            if not runs:
                return [], []

            event_stmt = (
                select(RuntimeBatchRunEvent)
                .where(RuntimeBatchRunEvent.run_id.in_([run.run_id for run in runs]))
                .where(RuntimeBatchRunEvent.event_type == "task_completed")
                .order_by(RuntimeBatchRunEvent.id.asc())
            )
            events = list((await session.execute(event_stmt)).scalars().all())
            return runs, events

    async def _record_export_sources(self, batch_run_id: int, run_id: str, source_files: list[Path]) -> None:
        async with async_session_factory() as session:
            service = RuntimeBatchService(session)
            for file_path in source_files:
                await service.add_event(
                    batch_run_id=batch_run_id,
                    run_id=run_id,
                    event_type="export_source",
                    payload={"signal_output_file": str(file_path)},
                    message=f"Using signal source file {file_path.name}",
                )
            await session.commit()

    async def _finalize_export_run(
        self,
        *,
        batch_run_id: int,
        summary: dict[str, Any],
        report_paths: dict[str, str] | None,
        status: str,
        error_message: str,
    ) -> None:
        async with async_session_factory() as session:
            service = RuntimeBatchService(session)
            await service.finalize_run(
                batch_run_id=batch_run_id,
                summary=summary,
                report_paths=report_paths,
                status=status,
                error_message=error_message,
            )
            await session.commit()

    def _extract_signal_output_files(
        self,
        source_runs: list[RuntimeBatchRun],
        source_events: list[RuntimeBatchRunEvent],
    ) -> tuple[list[Path], str]:
        files: list[Path] = []
        seen: set[str] = set()
        source_mode = "batch_events"
        for event in source_events:
            payload = event.payload or {}
            signal_output_file = payload.get("signal_output_file") if isinstance(payload, dict) else None
            if not signal_output_file:
                continue
            path = Path(signal_output_file)
            if not path.exists():
                continue
            if str(path) in seen:
                continue
            seen.add(str(path))
            files.append(path)

        for run in source_runs:
            report_paths = run.report_paths or {}
            report_json_path = report_paths.get("json") if isinstance(report_paths, dict) else None
            if not report_json_path:
                continue
            report_path = Path(report_json_path)
            if not report_path.exists():
                continue
            try:
                report_payload = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            task_results = report_payload.get("task_results", [])
            if not isinstance(task_results, list):
                continue
            for task_result in task_results:
                if not isinstance(task_result, dict):
                    continue
                signal_output_file = task_result.get("signal_output_file")
                if not isinstance(signal_output_file, str) or not signal_output_file.strip():
                    continue
                path = Path(signal_output_file)
                if not path.exists():
                    continue
                if str(path) in seen:
                    continue
                seen.add(str(path))
                files.append(path)
                source_mode = "batch_reports"

        if files:
            return files, source_mode

        legacy_files = sorted((Path(settings.DATA_DIR) / "trend_signal").glob("*/*.json"), reverse=True)
        for path in legacy_files:
            if not path.exists():
                continue
            if str(path) in seen:
                continue
            seen.add(str(path))
            files.append(path)
        return files, "legacy_filesystem"

    def _load_signal_rows(self, source_files: list[Path]) -> tuple[list[dict[str, Any]], set[str]]:
        rows: list[dict[str, Any]] = []
        loaded_files: set[str] = set()
        for path in source_files:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            signals = payload.get("trend_signals", [])
            if not isinstance(signals, list):
                continue

            for signal in signals:
                if not isinstance(signal, dict) or not signal.get("signal_id"):
                    continue
                rows.append(signal)
                loaded_files.add(str(path))
        return rows, loaded_files

    def _dedupe_signals(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for row in rows:
            signal_id = row["signal_id"]
            current = deduped.get(signal_id)
            if current is None:
                deduped[signal_id] = row
                continue
            if _normalize_dt(row.get("observed_at")) >= _normalize_dt(current.get("observed_at")):
                deduped[signal_id] = row
        return sorted(deduped.values(), key=lambda item: (_normalize_dt(item.get("observed_at")), *_stable_sort_key(item)), reverse=True)
